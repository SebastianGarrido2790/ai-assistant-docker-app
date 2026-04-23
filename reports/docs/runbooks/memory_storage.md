## Memory Storage and Retrieval

The system is designed with a **Three-Layer Memory Architecture** that follows professional Agentic design principles. Here is how you can store and retrieve information:

### 1. Automatic Short-Term Memory (Context)
You don't have to do anything! The system uses **LangGraph Checkpoints** backed by `checkpoints.sqlite`. 
*   **What it does**: Remembers the current conversation thread.
*   **How to use**: Just keep chatting. If you close the app and come back with the same session ID, it will remember the immediate context.

### 2. Explicit Long-Term Memory (Knowledge Bank)
To store a fact permanently across different days or sessions, you need to trigger the agent's **Memory Tool**.
*   **How to use**: Simply tell the agent: 
    > *"Remember that my professional background is in MLOps and I prefer using Python for agentic workflows."*
*   **The Mechanism**: The agent will recognize your intent and call the `save_memory_tool`. This converts your statement into a "fact" and stores it in our **ChromaDB Vector Database**.

### 3. Automatic Retrieval (The "Recall" Pattern)
Every time you send a message, the agent performs a **Semantic Search** in the background before answering.
*   **How it works**: It looks at your new message, searches the Vector DB for related facts, and injects them into its "System Prompt" before generating a response.
*   **Try it**: After telling it a fact, start a new chat later and ask:
    > *"What do you know about my professional background?"* 

---

### Example Interaction
**User:** *"Remember that my current project is focused on Dockerized AI Assistants."*
**Agent:** *[Calls `save_memory_tool`] "Got it! I've saved that to my long-term memory. I'll keep your focus on Dockerized AI Assistants in mind for future sessions."*

---

### UI Memory Controls
The Intelligent Dashboard provides two specialized controls for interacting with the memory system:

#### 1. **Save Conversation** Button
*   **Purpose**: Provides immediate visual confirmation of the persistent state.
*   **Behavior**: While the system automatically checkpoints every message to `checkpoints.sqlite` (Short-Term/Persistent Memory), clicking this button validates that the agent graph is active and correctly persisting the current thread.

#### 2. **What do you remember about me?** Button
*   **Purpose**: Manually triggers a **Long-Term Memory Search**.
*   **Behavior**: This is a shortcut that sends a hidden prompt to the agent: *"Search your long-term memory. What do you remember about me?"*.
*   **Expectation**: If you have previously used the `save_memory_tool` (by telling the agent to "Remember X"), clicking this button will cause the agent to retrieve those facts from the ChromaDB vector store and summarize its knowledge of you.
