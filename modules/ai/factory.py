"""LLM 클라이언트 팩토리."""
from typing import Optional
from .base import LLMClient
from .claude import ClaudeClient
from modules.core.config import get_llm_provider


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """설정된 공급자에 맞는 LLM 클라이언트 반환.

    Args:
        provider: AI 공급자 이름. None일 경우 환경변수에서 읽음.

    Returns:
        LLMClient: 생성된 클라이언트 인스턴스.

    Raises:
        ValueError: 지원하지 않는 공급자인 경우.
    """
    if provider is None:
        provider = get_llm_provider()

    if provider.lower() == "claude":
        return ClaudeClient()
    # Future: Add support for GPT, Gemini, etc.
    else:
        raise ValueError(f"지원하지 않는 AI 공급자: {provider}")
