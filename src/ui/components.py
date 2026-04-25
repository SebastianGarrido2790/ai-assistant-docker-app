"""
Reusable Streamlit UI components and state management for the AI Assistant.
"""

import uuid

import streamlit as st


def initialize_session() -> None:
    """
    Initializes the Streamlit session state for memory.

    Ensures a unique session_id exists for the current browser session
    and initializes the message history list if it's the first run.
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_chat_history() -> None:
    """
    Renders the chat history from the session state.

    Iterates through stored messages and displays them using Streamlit's
    native chat message containers.
    """
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_demo_actions() -> str | None:
    """
    Renders demo action buttons and returns a triggered prompt, if any.

    Provides a two-column layout for saving conversations and triggering
    long-term memory retrieval demos.

    Returns:
        The text of a demo prompt if a specific demo button was clicked, else None.
    """
    col1, col2 = st.columns(2)
    demo_prompt = None

    with col1:
        if st.button("Save Conversation"):
            st.success(
                "Conversation is automatically persisted by the Agent Graph in checkpoints.sqlite!"
            )

    with col2:
        if st.button("What do you remember about me?"):
            demo_prompt = "Search your long-term memory. What do you remember about me?"

    return demo_prompt


def add_message(role: str, content: str) -> None:
    """
    Adds a message to the session state and renders it to the screen.

    Args:
        role: The role of the speaker ('user' or 'assistant').
        content: The text content of the message.
    """
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)
