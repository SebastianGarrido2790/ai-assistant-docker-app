import streamlit as st
from app import AIChatApp

# Initialize the AI chat app
try:
    app = AIChatApp()
except Exception as e:
    st.error(f"Failed to initialize application: {str(e)}. Please check configuration.")
    st.stop()

##############################
# GUI
##############################

st.title("AI Assistant with Memory")

# Model selection
model_choice = st.checkbox(
    "Use cloud model (Think harder...)", value=False, key="model_choice"
)

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Type your message...")

if prompt:
    try:
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.spinner("Generating response..."):
            response = app.process_message(prompt, model_choice)

        # Add assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})

        with st.chat_message("assistant"):
            st.markdown(response)

    except Exception as e:
        st.error(
            f"An error occurred while generating the response: {str(e)}. Please try again."
        )

# Save conversation button
if st.button("Save Conversation"):
    app.save_conversation_history(st.session_state.messages)
