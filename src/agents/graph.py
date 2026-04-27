"""
Agentic Workflow implemented as a LangGraph StateGraph.

This module wires the agent states, defines the processing nodes
acting on those states, and binds them with persistent memory (checkpointing)
via an SQLite backing. It integrates deterministic tools, adhering to the
Brain/Brawn divide.
"""

import sqlite3
from datetime import datetime
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
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


class GraphState(TypedDict):
    """Represents the shared state passed between nodes in the graph."""

    messages: Annotated[list[BaseMessage], add_messages]


def build_graph() -> CompiledStateGraph:
    """
    Constructs and compiles the conversational agent's directed graph.

    Initializes the required local and cloud ChatOpenAI instances dynamically
    via ConfigurationManager, sets up an SQLite-backed checkpointer, and
    compiles the execution graph with tool capabilities.

    The agent autonomously decides when to persist facts or retrieve past knowledge.

    Returns:
        CompiledGraph: A LangGraph executable graph ready for invocations.
    """
    config_mgr = ConfigurationManager()
    config = config_mgr.get_config()

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

    builder = StateGraph(GraphState)

    # Add nodes
    builder.add_node("chat", chat_node)
    builder.add_node("tools", ToolNode(tools))

    # Add edges and conditional routing
    builder.add_edge(START, "chat")
    # Condition: If the LLM returned a tool call, route to tools, otherwise END
    builder.add_conditional_edges("chat", tools_condition)
    builder.add_edge("tools", "chat")

    # Setup persistent memory checkpointing
    db_path = str(PROJECT_ROOT / "checkpoints.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    memory.setup()

    return builder.compile(checkpointer=memory)
