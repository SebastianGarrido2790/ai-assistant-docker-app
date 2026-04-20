import os
import logging
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from typing import Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)


class AIChatApp:
    def __init__(self):
        self.config = self.load_config()
        self.memory = ConversationBufferMemory(return_messages=True)
        self.llms = self.initialize_llms()

    def load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables."""
        try:
            config = {
                "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
                "LOCAL_MODEL_NAME": os.environ.get("LOCAL_MODEL_NAME", "ai/gemma3"),
                "REMOTE_MODEL_NAME": os.environ.get(
                    "REMOTE_MODEL_NAME", "openai/gpt-oss-20b"
                ),
                "LOCAL_BASE_URL": os.environ.get(
                    "LOCAL_BASE_URL",
                    "http://llm:8080/engines/llama.cpp/v1",
                ),
                "REMOTE_BASE_URL": os.environ.get(
                    "REMOTE_BASE_URL", "https://openrouter.ai/api/v1"
                ),
            }
            if not config["OPENROUTER_API_KEY"]:
                logger.warning("OPENROUTER_API_KEY not set")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise

    def initialize_llms(self) -> Dict[str, ChatOpenAI]:
        """Initialize local and cloud LLMs."""
        try:
            return {
                "local": ChatOpenAI(
                    model=self.config["LOCAL_MODEL_NAME"],
                    api_key="nope",
                    base_url=self.config["LOCAL_BASE_URL"],
                    timeout=30,
                ),
                "cloud": ChatOpenAI(
                    model=self.config["REMOTE_MODEL_NAME"],
                    api_key=self.config["OPENROUTER_API_KEY"],
                    base_url=self.config["REMOTE_BASE_URL"],
                    timeout=30,
                ),
            }
        except Exception as e:
            logger.error(f"Failed to initialize LLMs: {str(e)}")
            raise

    def get_conversation_chain(self, use_cloud: bool) -> ConversationChain:
        """Create a conversation chain with memory."""
        selected_llm = self.llms["cloud"] if use_cloud else self.llms["local"]
        return ConversationChain(llm=selected_llm, memory=self.memory, verbose=False)

    def process_message(self, prompt: str, use_cloud: bool) -> str:
        """Process user input and generate response."""
        try:
            self.memory.chat_memory.add_user_message(prompt)
            conversation = self.get_conversation_chain(use_cloud)
            response = conversation.predict(input=prompt)
            self.memory.chat_memory.add_ai_message(response)
            logger.info(
                f"Generated response using {'cloud' if use_cloud else 'local'} model"
            )
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise

    def save_conversation_history(self, messages: list):
        """Save conversation history to a file."""
        import json

        try:
            with open("conversation_history.json", "w") as f:
                json.dump(messages, f)
            logger.info("Conversation history saved")
        except Exception as e:
            logger.error(f"Failed to save conversation history: {str(e)}")
