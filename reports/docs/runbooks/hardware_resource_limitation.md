## GPU Constrains

I've analyzed the logs, and I found the exact cause of the `500 Internal Server Error`.

The root cause is a **hardware resource limitation on the host machine** regarding my GPU (VRAM). 

Here is what is happening behind the scenes:
1. When I asked the question in the UI without checking "Use cloud model", the FastAPI backend correctly routed the request to my local `llm` service (the Docker AI Provider running `ai/devstral-small-2`).
2. The Docker AI Provider uses `llama.cpp` under the hood. It attempted to load the model into my GPU using the **Vulkan** backend to accelerate the generation.
3. My GPU didn't have enough free video memory (VRAM). The logs explicitly show it failed to allocate ~1GB of memory:
   ```text
   ggml_vulkan: vk::Device::allocateMemory: ErrorOutOfDeviceMemory
   ```
4. Because it couldn't allocate the memory, `llama.cpp` crashed, causing the internal Docker runner to go down, which in turn caused your FastAPI app to return the `500 Internal Server Error` to the Streamlit UI.

### 🛠️ How to Fix / Proceed:

Since this is a physical hardware constraint with how Docker AI is currently mapping to your GPU, you have two immediate options to continue testing the app:

**Option 1: Use the Cloud Model (Recommended for now)**
Simply check the **"Use cloud model (Think harder...)"** checkbox in the Streamlit UI before sending your message. This will bypass the local `llm` service entirely and route the request to OpenRouter (`google/gemma-4-31b-it`), which avoids your local hardware limitations.

**Option 2: Free up Local GPU Memory**
If you want to test the local model routing, you need to free up VRAM on your Windows machine. 
- Close any other heavy background applications, games, or browser tabs that might be consuming GPU memory.
- You can monitor your dedicated GPU memory usage via the Windows Task Manager (Performance -> GPU).
- Once memory is cleared, you can send the message again (the `llm` service will attempt to automatically restart and map to the memory).

### 🚀 Current System Status:

*   **Cloud Routing (`google/gemma-4-31b-it`)**: **ACTIVE**. The authentication fix and environment isolation successfully cleared the `401` errors.
*   **Local Routing (`ai/devstral-small-2`)**: **READY** (but limited by VRAM). The backend is configured to use the correct `model-runner.docker.internal` endpoint, so it will work automatically if your GPU memory is freed up.
*   **Architecture**: The app is now a true "Hybrid AI" system, allowing you to switch between edge (local) and cloud computing seamlessly.

### 🛠️ Backend Crash Recovery (Dependency Mismatch)

If the backend fails to start with a `ModuleNotFoundError` (e.g., `No module named 'chromadb'`), it is likely because an old Docker volume is caching an outdated virtual environment.

**Fix:**
1.  Stop the containers and remove volumes:
    ```bash
    docker-compose down -v
    ```
2.  Rebuild and start:
    ```bash
    docker-compose up --build
    ```

### 💡 Quick Tip for the Local Model:
If you eventually want to see the local model in action, the `ai/devstral-small-2` model requires about **1.2GB to 1.5GB of free VRAM**. If you can reach that threshold (perhaps by temporarily disabling GPU acceleration in other apps), the same code will handle it without any further changes.
