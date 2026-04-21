## Verify App Functionality

To verify that the refactored Agentic AI Assistant is working correctly, you can use a combination of automated tests and manual verification. 

### **1. Run the Automated Test Suite**
Since we implemented a comprehensive test suite in `tests/`, this is the fastest way to ensure the core logic (Config, Schema, Exceptions, and API Logic) is intact.

Run this command in your terminal:
```powershell
uv run pytest
```
*If all 12 tests pass, the backend logic is technically sound.*

---

### **2. Manual Verification (Step-by-Step)**

To see the app in action, you need to start both the **Backend API** and the **Frontend GUI**.

#### **Step A: Start the FastAPI Backend**
Open a terminal and run:
```powershell
uv run uvicorn src.api.app:app --reload --port 8000
```
*   **Check:** Go to `http://localhost:8000/v1/health` in your browser. You should see `{"status": "ok"}`.
*   **Documentation:** You can also visit `http://localhost:8000/docs` to see the interactive Swagger UI for your API.

#### **Step B: Start the Streamlit Frontend**
Open a **new** terminal (keep the backend running) and run:
```powershell
uv run streamlit run gui.py
```
*   **Check:** Your browser should open to the Streamlit UI. Try sending a message like "Hello!".
*   **Memory Test:** Send a second message like "What is my name?" (after telling it your name) to verify the **LangGraph + SQLite** persistent memory is working.

---

### **3. Check the Persistent Memory**
After chatting, look for a file called `checkpoints.sqlite` in your project root. This file confirms that the **LangGraph memory layer** is actively saving your conversation states.

### **4. Verify Docker Readiness**
If you want to test the production hardening we did:
```powershell
docker-compose up --build
```
This will build the new multi-stage image using the `appuser` and start the full stack (App + LLM Runner).

The logs should show that both services have started successfully inside their containers:
*   **Backend (FastAPI):** `Uvicorn running on http://0.0.0.0:8000`
*   **Frontend (Streamlit):** `You can now view your Streamlit app in your browser. URL: http://0.0.0.0:8501`

### **How to verify it:**
1.  **Open the UI:** Go to [http://localhost:8501](http://localhost:8501) in your browser.
2.  **Test the Connection:**
    *   Try sending a message **without** the "Use cloud model" box checked. It will use the local `llm` container. 
    *   *Note:* The first message to the local LLM might take a minute while the model loads into memory in the `llm` container.
3.  **Test the Memory:** Refresh the page after a chat. Because we set up `checkpoints.sqlite` with a Docker volume, your chat history should persist!
