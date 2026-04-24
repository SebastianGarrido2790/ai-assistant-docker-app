"""
Streamlit Graphical User Interface for the AI Assistant.

A lightweight frontend that communicates with the FastAPI backend
microservice over HTTP. Maintains local session state for seamless UI
rendering while relying on the backend for heavy lifting and long-term memory.

Usage:
    uv run streamlit run src/ui/app.py
"""

import streamlit as st

from src.ui.client import BackendClient
from src.ui.components import (
    add_message,
    initialize_session,
    render_chat_history,
    render_demo_actions,
)
from src.ui.styles import STYLES

# Apply global styles
st.markdown(STYLES, unsafe_allow_html=True)

# Initialize state
initialize_session()

st.title("AI Assistant with Memory")

# Model selection
model_choice = st.checkbox(
    "Use cloud model (Think harder...)", value=False, key="model_choice"
)

# Render history
render_chat_history()

# Demo actions
demo_prompt = render_demo_actions()

# Chat input
prompt = st.chat_input("Type your message...")
active_prompt = prompt or demo_prompt

if active_prompt:
    # Render user message
    add_message("user", active_prompt)

    # Generate and render response
    with st.spinner("Generating response..."):
        response = BackendClient.send_chat_message(
            prompt=active_prompt,
            use_cloud=model_choice,
            session_id=st.session_state.session_id,
        )

    add_message("assistant", response)
