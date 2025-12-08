"""LLM 클라이언트 팩토리."""
from .base import LLMClient
from .claude import ClaudeClient

def get_llm_client(provider: str = "claude") -> LLMClient:
    """설정된 공급자에 맞는 LLM 클라이언트 반환.

    Args:
        provider: AI 공급자 이름 (기본값: "claude").

    Returns:
        LLMClient: 생성된 클라이언트 인스턴스.

    Raises:
        ValueError: 지원하지 않는 공급자인 경우.
    """
    if provider.lower() == "claude":
        return ClaudeClient()
    # 추후 gpt, gemini 추가 가능
    else:
        raise ValueError(f"지원하지 않는 AI 공급자: {provider}")
