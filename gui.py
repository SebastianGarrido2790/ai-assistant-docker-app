"""
Streamlit Graphical User Interface for the AI Assistant.

A lightweight frontend that communicates with the FastAPI backend
microservice over HTTP. Maintains local session state for seamless UI
rendering while relying on the backend for heavy lifting and long-term memory.

Usage:
    uv run streamlit run gui.py
"""

import streamlit as st
import requests
import uuid
import os

# Configuration: Backend API URL
# In Docker, this will be http://backend:8000
# Locally, it will fall back to http://localhost:8000
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/v1/chat"

# Initialize session state for memory
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI Assistant with Memory")

# Model selection
model_choice = st.checkbox(
    "Use cloud model (Think harder...)", value=False, key="model_choice"
)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Demo Actions
col1, col2 = st.columns(2)
demo_prompt = None

with col1:
    if st.button("Save Conversation"):
        st.success(
            "Conversation is automatically persisted by the Agent Graph in checkpoints.sqlite!"
        )

with col2:
    # This button forces the agent to query its vector store and fetch facts from long-term memory
    if st.button("What do you remember about me?"):
        demo_prompt = "Search your long-term memory. What do you remember about me?"

# Chat input
prompt = st.chat_input("Type your message...")

# Resolve active prompt
active_prompt = prompt or demo_prompt

if active_prompt:
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": active_prompt})

    with st.chat_message("user"):
        st.markdown(active_prompt)

    # Generate response
    with st.spinner("Generating response..."):
        try:
            payload = {
                "prompt": active_prompt,
                "use_cloud": model_choice,
                "session_id": st.session_state.session_id,
            }
            res = requests.post(API_URL, json=payload)
            res.raise_for_status()

            data = res.json()
            response = data.get("response", "Error: No response from API.")

        except Exception as e:
            response = f"An error occurred while calling the API: {str(e)}. Make sure the FastAPI backend is running on port 8000."

    # Add assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)
