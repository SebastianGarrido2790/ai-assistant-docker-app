"""
Diagnostic utility to verify LLM connectivity and configuration.

This script independently validates that the OpenRouter API key and model 
settings are correctly loaded and functional outside of the main FastAPI 
application context.
"""

import asyncio
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.config.configuration import ConfigurationManager


async def main():
    """
    Execute a test invocation to the remote LLM provider.

    Loads the current configuration via ConfigurationManager, initializes 
    a ChatOpenAI instance, and attempts a basic 'Hello' prompt to verify 
    authentication and network connectivity.
    """
    config = ConfigurationManager().get_config()
    print(f"Key loaded: {config.openrouter_api_key[:15]}...")
    print(f"Base URL: {config.remote_base_url}")
    print(f"Model: {config.remote_model_name}")

    llm = ChatOpenAI(
        model=config.remote_model_name,
        api_key=SecretStr(config.openrouter_api_key),
        base_url=config.remote_base_url,
    )
    try:
        response = llm.invoke([HumanMessage(content="Hello")])
        print("Success:", response.content)
    except Exception as e:
        print("Error:", repr(e))


if __name__ == "__main__":
    asyncio.run(main())
