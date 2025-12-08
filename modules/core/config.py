"""
Configuration utility for loading environment variables
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def get_claude_model() -> str:
    """Get Claude model name from environment variable.

    Returns:
        str: Claude model name (default: claude-sonnet-4-20250514)
    """
    return os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')


def get_anthropic_api_key() -> str:
    """Get Anthropic API key from environment variable.

    Returns:
        str: Anthropic API key

    Raises:
        ValueError: If API key is not found
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return api_key


def get_caldera_url() -> str:
    """Get Caldera server URL from environment variable.

    Returns:
        str: Caldera server URL (default: http://localhost:8888)
    """
    return os.getenv("CALDERA_URL", "http://localhost:8888")


def get_caldera_api_key() -> str:
    """Get Caldera API key from environment variable.

    Returns:
        str: Caldera API key (default: ADMIN123)
    """
    return os.getenv("CALDERA_API_KEY", "ADMIN123")


def get_llm_provider() -> str:
    """Get LLM provider from environment variable.

    Returns:
        str: LLM provider name (default: claude)
    """
    return os.getenv("LLM_PROVIDER", "claude").lower()
