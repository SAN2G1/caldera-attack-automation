"""Google Gemini 클라이언트 구현체."""
from typing import Optional
import time
import google.generativeai as genai
from modules.core.config import get_google_api_key, get_gemini_model
from modules.core.metrics import get_metrics_tracker
from .base import LLMClient


class GeminiClient(LLMClient):
    """Gemini API 클라이언트."""

    def __init__(self):
        genai.configure(api_key=get_google_api_key())
        self.model_name = get_gemini_model()
        # model 객체는 파이프라인(joblib) 멀티프로세싱 시 JSON 직렬화 오류 방지를 위해 __init__에서 보관하지 않습니다.

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4096) -> str:
        """Gemini를 사용하여 텍스트 생성.

        Usage:
            공격 시나리오 생성, 명령어 수정 등 LLM의 추론 능력이 필요한 모든 곳에서 사용됩니다.

        Args:
            prompt: 사용자 프롬프트.
            system_prompt: 시스템 프롬프트.
            max_tokens: 최대 생성 토큰 수.

        Returns:
            str: 생성된 응답 텍스트.
        """
        # 시스템 프롬프트 지원 여부에 따라 모델 일회성 초기화 (JSON 직렬화 문제 회피)
        try:
            if system_prompt:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_prompt
                )
                full_prompt = prompt
            else:
                model = genai.GenerativeModel(model_name=self.model_name)
                full_prompt = prompt
        except TypeError:
            # 예전 버전의 google-generativeai 패키지는 system_instruction 파라미터를 미지원
            model = genai.GenerativeModel(model_name=self.model_name)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

        # Gemini의 경우 생성을 위한 옵션 설정
        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7
        )

        max_attempts = 15
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            try:
                # 안전 설정 없이 호출하여 옵션으로 인한 추가 필터링 방지 (Gemini 2.5 기본값 OFF 의존)
                response = model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                # 응답 객체가 비정상 차단되었는지 검사 (finish_reason=2)
                if response.candidates and getattr(response.candidates[0], 'finish_reason', None) == 2:
                    print(f"\n[AI INFO] Gemini Safety Block triggered (finish_reason=2) on attempt {attempt}/{max_attempts}. Retrying exact prompt...")
                    
                    # 차단된 경우에도 요금(토큰)은 소모되므로 메트릭에 기록해야 함
                    tracker = get_metrics_tracker()
                    if tracker and hasattr(response, 'usage_metadata'):
                        tracker.record_llm_call(
                            model=self.model_name,
                            input_tokens=response.usage_metadata.prompt_token_count,
                            output_tokens=response.usage_metadata.candidates_token_count
                        )
                        
                    time.sleep(1) # 부하 방지용 짧은 대기
                    continue
                
                # 메트릭 추적
                tracker = get_metrics_tracker()
                if tracker and hasattr(response, 'usage_metadata'):
                    tracker.record_llm_call(
                        model=self.model_name,
                        input_tokens=response.usage_metadata.prompt_token_count,
                        output_tokens=response.usage_metadata.candidates_token_count
                    )
                
                return response.text
                
            except Exception as e:
                # StopCandidateException 등 다른 형태의 차단 예외나 서버 에러 처리
                print(f"\n[AI WARNING] Gemini Exception on attempt {attempt}/{max_attempts}: {e}. Retrying...")
                time.sleep(2)
                continue
                
        # 최대 재시도 횟수 초과 시
        raise RuntimeError(f"Gemini API consistently blocked generation or failed after {max_attempts} attempts.")
