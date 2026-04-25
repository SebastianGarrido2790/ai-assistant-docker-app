## `X-API-Key` Authentication

```python
APP_API_KEY = os.getenv("APP_API_KEY", "dev-key-1234")
```

That line defines the resolution logic for the **`APP_API_KEY`**, which is the internal security token implemented to protect the FastAPI backend.

Here is exactly how it works:

1.  **The Purpose**: It acts as a "password" between the Streamlit frontend and FastAPI backend. It ensures that only the UI (or authorized users) can trigger the AI Assistant, preventing unauthorized access to the LLM credits and memory.
2.  **Precedence (How it's loaded)**:
    *   **Tier 1 (Environment)**: It first looks for an environment variable named `APP_API_KEY`.
    *   **Tier 2 (YAML)**: If not found in the environment, it checks the `config.yaml` file.
    *   **Tier 3 (Fallback)**: If neither exists, it defaults to `"dev-key-1234"` so the app works immediately out-of-the-box for local development.
3.  **Usage**: When the Streamlit UI calls the API, it sends this key in the `X-API-Key` header. The backend then uses the logic in that line to verify the key matches.

> [!IMPORTANT]
> For a **production** deployment, change this value in the `.env` file to a long, random string to ensure the API remains secure.