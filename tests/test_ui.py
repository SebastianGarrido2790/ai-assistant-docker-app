"""
Unit tests for the Streamlit UI layer and backend client.
"""

import uuid
from unittest.mock import MagicMock, patch

from src.ui.client import BackendClient
from src.ui.components import initialize_session, render_demo_actions


class TestBackendClient:
    """Tests for the BackendClient class."""

    @patch("requests.post")
    def test_send_chat_message_success(self, mock_post):
        """Validates successful chat message delivery and response handling."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Hello from the agent!"}
        mock_post.return_value = mock_response

        # Execute
        response = BackendClient.send_chat_message(
            prompt="Hi", use_cloud=False, session_id="test-session"
        )

        # Assert
        assert response == "Hello from the agent!"
        mock_post.assert_called_once()
        _args, kwargs = mock_post.call_args
        assert kwargs["json"]["prompt"] == "Hi"
        assert kwargs["json"]["session_id"] == "test-session"
        assert "X-API-Key" in kwargs["headers"]

    @patch("requests.post")
    def test_send_chat_message_error(self, mock_post):
        """Validates error handling when the backend API call fails."""
        # Setup mock to raise an exception
        mock_post.side_effect = Exception("Connection refused")

        # Execute
        response = BackendClient.send_chat_message(
            prompt="Hi", use_cloud=False, session_id="test-session"
        )

        # Assert
        assert "An error occurred" in response
        assert "Connection refused" in response


class TestUIComponents:
    """Tests for Streamlit UI components and state management."""

    @patch("streamlit.session_state", {})
    def test_initialize_session_new(self):
        """Ensures session state is correctly initialized if empty."""

        # Use a mock that supports attribute access since st.session_state.key = val is used
        with patch("streamlit.session_state", MagicMock()) as mock_state:
            # Re-initialize the mock_state as a clean object if needed,
            # but MagicMock handles attribute assignment fine.
            # We just need to make sure 'in' check works.
            mock_state.__contains__.side_effect = lambda k: False

            initialize_session()

            # Verify assignments
            assert mock_state.session_id is not None
            assert isinstance(mock_state.messages, list)
            # Verify it's a valid UUID
            uuid.UUID(mock_state.session_id)

    @patch("streamlit.session_state")
    def test_initialize_session_existing(self, mock_session_state):
        """Ensures existing session state is not overwritten."""
        mock_session_state.__contains__.side_effect = lambda k: (
            k
            in [
                "session_id",
                "messages",
            ]
        )
        mock_session_state.session_id = "existing-id"
        mock_session_state.messages = [{"role": "user", "content": "hello"}]

        initialize_session()

        assert mock_session_state.session_id == "existing-id"
        assert len(mock_session_state.messages) == 1

    @patch("streamlit.button")
    @patch("streamlit.columns")
    @patch("streamlit.success")
    def test_render_demo_actions_no_click(
        self, mock_success, mock_columns, mock_button
    ):
        """Validates demo actions return None when no button is clicked."""
        mock_columns.return_value = [MagicMock(), MagicMock()]
        mock_button.return_value = False

        result = render_demo_actions()

        assert result is None
        assert mock_button.call_count == 2

    @patch("streamlit.button")
    @patch("streamlit.columns")
    @patch("streamlit.success")
    def test_render_demo_actions_memory_click(
        self, mock_success, mock_columns, mock_button
    ):
        """Validates demo actions return correct prompt when memory button is clicked."""
        mock_columns.return_value = [MagicMock(), MagicMock()]

        # Mock button behavior: False for first button (Save), True for second (Memory)
        mock_button.side_effect = [False, True]

        result = render_demo_actions()

        assert result == "Search your long-term memory. What do you remember about me?"
        mock_success.assert_not_called()
