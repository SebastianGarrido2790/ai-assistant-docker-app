"""
Agentic Workflow implemented as a LangGraph StateGraph.

This module wires the agent states, defines the processing nodes
acting on those states, and binds them with persistent memory (checkpointing)
via an SQLite backing.
"""

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from src.config.configuration import ConfigurationManager
import sqlite3


class GraphState(TypedDict):
    """Represents the shared state passed between nodes in the graph."""

    messages: Annotated[list[BaseMessage], add_messages]


def build_graph():
    """
    Constructs and compiles the conversational agent's directed graph.

    Initializes the required local and cloud ChatOpenAI instances dynamically
    via ConfigurationManager, sets up an SQLite-backed checkpointer, and
    compiles the execution graph.

    Returns:
        CompiledGraph: A LangGraph executable graph ready for invocations.
    """
    config_mgr = ConfigurationManager()
    config = config_mgr.get_config()

    llms = {
        "local": ChatOpenAI(
            model=config.local_model_name,
            api_key="nope",
            base_url=config.local_base_url,
            timeout=30,
        ),
        "cloud": ChatOpenAI(
            model=config.remote_model_name,
            api_key=config.openrouter_api_key or "sk-none",
            base_url=config.remote_base_url,
            timeout=30,
        ),
    }

    def chat_node(state: GraphState, config: RunnableConfig):
        use_cloud = config.get("configurable", {}).get("use_cloud", False)
        llm = llms["cloud"] if use_cloud else llms["local"]
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    builder = StateGraph(GraphState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)

    from langgraph.checkpoint.sqlite import SqliteSaver
    from src.constants import PROJECT_ROOT

    db_path = str(PROJECT_ROOT / "checkpoints.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    memory.setup()

    return builder.compile(checkpointer=memory)


agent_graph = build_graph()
