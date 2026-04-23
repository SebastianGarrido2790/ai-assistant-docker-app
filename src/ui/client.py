"""
Client for interacting with the FastAPI backend agent service.
"""

import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/v1/chat"


class BackendClient:
    """
    Client for interacting with the FastAPI backend.

    This class provides static methods to communicate with the agentic
    backend service, abstracting away the HTTP request/response logic.
    """

    @staticmethod
    def send_chat_message(prompt: str, use_cloud: bool, session_id: str) -> str:
        """
        Sends a message to the backend and returns the response.

        Args:
            prompt: The user's input text.
            use_cloud: Whether to use a high-reasoning cloud model.
            session_id: The unique identifier for the current conversation session.

        Returns:
            The agent's response text, or an error message if the request fails.
        """
        payload = {
            "prompt": prompt,
            "use_cloud": use_cloud,
            "session_id": session_id,
        }
        try:
            res = requests.post(API_URL, json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("response", "Error: No response from API.")
        except Exception as e:
            port = BACKEND_URL.split(":")[-1]
            return (
                f"An error occurred while calling the API: {e!s}. "
                f"Make sure the FastAPI backend is running on port {port}."
            )
