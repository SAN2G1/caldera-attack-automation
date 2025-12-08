"""프롬프트 템플릿 관리자."""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


class PromptManager:
    """프롬프트 템플릿 로드 및 렌더링.
    
    YAML 템플릿 구조:
        description: 프롬프트 역할 설명 (한국어)
        prompt: |
            실제 프롬프트 내용
    """

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            self.template_dir = Path(__file__).parent / "templates"
        else:
            self.template_dir = Path(template_dir)

    def load_template(self, template_name: str) -> Dict[str, str]:
        """YAML 템플릿 파일 로드.

        Args:
            template_name: 템플릿 파일명 (.yaml 확장자).

        Returns:
            Dict[str, str]: description과 prompt를 포함한 딕셔너리.

        Raises:
            FileNotFoundError: 파일이 없는 경우.
        """
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"프롬프트 템플릿을 찾을 수 없음: {template_path}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return data

    def get_prompt(self, template_name: str) -> str:
        """템플릿에서 prompt 부분만 반환.

        Args:
            template_name: 템플릿 파일명.

        Returns:
            str: 프롬프트 문자열.
        """
        data = self.load_template(template_name)
        return data.get('prompt', '')

    def render(self, template_name: str, **kwargs) -> str:
        """템플릿 로드 후 변수 치환.

        Args:
            template_name: 템플릿 파일명 (.yaml).
            **kwargs: 치환할 변수들.

        Returns:
            str: 완성된 프롬프트 문자열.
        """
        prompt = self.get_prompt(template_name)
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"템플릿 변수 누락: {e}")

    def get_description(self, template_name: str) -> str:
        """템플릿의 description (한국어 설명) 반환.

        Args:
            template_name: 템플릿 파일명.

        Returns:
            str: 설명 문자열.
        """
        data = self.load_template(template_name)
        return data.get('description', '')
