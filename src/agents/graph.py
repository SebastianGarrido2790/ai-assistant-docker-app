"""
Agentic Workflow implemented as a LangGraph StateGraph.

This module wires the agent states, defines the processing nodes
acting on those states, and binds them with persistent memory (checkpointing)
via an SQLite backing. It integrates deterministic tools, adhering to the
Brain/Brawn divide.

HITL Gate
---------
A ``hitl_gate`` node sits between the ``chat`` node and the ``tools`` node.
When ``HITL_ENABLED=true``, any call to ``save_memory_tool`` triggers a
LangGraph ``interrupt()``, pausing the graph until it is resumed via
``Command(resume={"approved": True})``. When ``HITL_ENABLED=false`` (default),
the gate is a transparent pass-through and normal execution continues.
"""

import os
import sqlite3
from datetime import datetime
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt
from pydantic import SecretStr

from src.agents.memory import search_memory
from src.agents.prompts import ACTIVE_SYSTEM_PROMPT
from src.config.configuration import ConfigurationManager
from src.constants import PROJECT_ROOT
from src.tools.tools import (
    calculate_tool,
    save_memory_tool,
    search_memory_tool,
    search_web_tool,
    summarize_document_tool,
)
from src.utils.logger import get_logger

logger = get_logger(__name__, headline="hitl")

# Tools that require human approval before execution when HITL is enabled.
_HITL_PROTECTED_TOOLS: frozenset[str] = frozenset({"save_memory_tool"})


class GraphState(TypedDict):
    """Represents the shared state passed between nodes in the graph."""

    messages: Annotated[list[BaseMessage], add_messages]


def build_graph(conn: sqlite3.Connection | None = None) -> CompiledStateGraph:
    """
    Constructs and compiles the conversational agent's directed graph.

    Initializes the required local and cloud ChatOpenAI instances dynamically
    via ConfigurationManager, sets up an SQLite-backed checkpointer, and
    compiles the execution graph with tool capabilities and an optional
    Human-in-the-Loop gate.

    The agent autonomously decides when to persist facts or retrieve past knowledge.
    Memory writes route through ``hitl_gate`` before reaching ``ToolNode``.
    Set ``HITL_ENABLED=true`` to activate the approval interrupt.

    Args:
        conn: Optional existing SQLite connection for checkpointing. If not
            provided, a new connection is created using ``CHECKPOINT_DB_PATH``
            env var (default: ``<project_root>/checkpoints.sqlite``).

    Returns:
        CompiledGraph: A LangGraph executable graph ready for invocations.
    """
    config_mgr = ConfigurationManager()
    config = config_mgr.get_config()
    hitl_enabled = config.hitl_enabled

    # Define tools available to the agent
    tools = [
        search_web_tool,
        calculate_tool,
        summarize_document_tool,
        save_memory_tool,
        search_memory_tool,
    ]
    tool_names = ", ".join([t.name for t in tools])

    # Initialize LLMs and bind tools
    llms = {
        "local": ChatOpenAI(
            model=config.local_model_name,
            api_key=SecretStr("nope"),
            base_url=config.local_base_url,
            timeout=30,
        ).bind_tools(tools),
        "cloud": ChatOpenAI(
            model=config.remote_model_name,
            api_key=SecretStr(config.openrouter_api_key or "sk-none"),
            base_url=config.remote_base_url,
            timeout=30,
        ).bind_tools(tools),
    }

    def chat_node(
        state: GraphState, config: RunnableConfig
    ) -> dict[str, list[BaseMessage]]:
        use_cloud = config.get("configurable", {}).get("use_cloud", False)
        llm = llms["cloud"] if use_cloud else llms["local"]

        # 1. Fetch relevant memories for the current turn (Preload Memory Pattern)
        last_message = state["messages"][-1].content if state["messages"] else ""
        memories = search_memory(str(last_message))
        relevant_memories = "\n".join(memories) if memories else "None."

        # 2. Format the versioned System Prompt
        system_prompt = ACTIVE_SYSTEM_PROMPT.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            tool_names=tool_names,
            relevant_memories=relevant_memories,
        )

        # 3. Prepend System Message to the current conversation for the LLM call
        # (We do not save this system message to state to keep history clean)
        messages_with_system = [SystemMessage(content=system_prompt)] + state[
            "messages"
        ]

        response = llm.invoke(messages_with_system)
        return {"messages": [response]}

    def hitl_gate_node(
        state: GraphState, config: RunnableConfig
    ) -> dict[str, list[BaseMessage]]:
        """
        Human-in-the-Loop gate for high-stakes tool calls.

        When ``HITL_ENABLED=true``, any tool call targeting a protected tool
        (e.g., ``save_memory_tool``) triggers a LangGraph ``interrupt()``,
        suspending the graph. Resume with:
            ``graph.invoke(Command(resume={"approved": True}), config=config)``

        When disabled (default), this node is a transparent pass-through.

        Args:
            state: Current graph state with message history.
            config: LangGraph runnable configuration.

        Returns:
            Empty dict — this node does not modify state.
        """
        if not hitl_enabled:
            return {}

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", []) or []
        protected_calls = [
            tc for tc in tool_calls if tc.get("name") in _HITL_PROTECTED_TOOLS
        ]

        if protected_calls:
            facts = [tc.get("args", {}).get("fact", "") for tc in protected_calls]
            logger.warning(
                "HITL gate triggered. Memory write requires human approval.",
                extra={"facts": facts},
            )
            # Suspend graph execution — requires Command(resume=...) to continue.
            # This satisfies Rule 1.6: HITL for irreversible operations.
            decision = interrupt(
                {
                    "message": "⚠️ HITL Gate: Memory write detected. Approve to persist.",
                    "tool": "save_memory_tool",
                    "facts": facts,
                }
            )
            logger.info(f"HITL gate resolved with decision: {decision}")

        return {}

    builder = StateGraph(GraphState)

    # Add nodes
    builder.add_node("chat", chat_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("tools", ToolNode(tools))

    # Add edges and conditional routing.
    # tools_condition routes to "tools" when the LLM returns a tool call, else END.
    # We redirect all "tools" destinations through hitl_gate first.
    builder.add_edge(START, "chat")
    builder.add_conditional_edges(
        "chat",
        tools_condition,
        {"tools": "hitl_gate", END: END},
    )
    builder.add_edge("hitl_gate", "tools")
    builder.add_edge("tools", "chat")

    # Setup persistent memory checkpointing.
    # Path is configurable via CHECKPOINT_DB_PATH env var.
    if conn is None:
        db_path = os.environ.get(
            "CHECKPOINT_DB_PATH", str(PROJECT_ROOT / "checkpoints.sqlite")
        )
        conn = sqlite3.connect(db_path, check_same_thread=False)

    memory = SqliteSaver(conn)
    memory.setup()

    return builder.compile(checkpointer=memory)
