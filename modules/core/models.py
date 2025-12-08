"""파이프라인 데이터 모델 정의."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


class FailureType(Enum):
    """Ability 실행 실패 유형."""
    SYNTAX_ERROR = "syntax_error"
    MISSING_ENV = "missing_env"
    CALDERA_CONSTRAINT = "caldera_constraint"
    DEPENDENCY_ERROR = "dependency_error"
    UNRECOVERABLE = "unrecoverable"


@dataclass
class AbilityResult:
    """Caldera Ability 실행 결과."""
    link_id: str
    ability_id: str
    ability_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    status: int

    @property
    def is_success(self) -> bool:
        """실행 성공 여부."""
        return self.status == 0 and self.exit_code == 0

    @property
    def is_failed(self) -> bool:
        """실행 실패 여부."""
        return self.status == -1 or self.exit_code != 0


@dataclass
class FailedAbility:
    """실패한 Ability 정보 (Self-Correcting용)."""
    ability_id: str
    ability_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    failure_type: Optional['FailureType'] = None
    tactic: str = ""
    technique_id: str = ""
    technique_name: str = ""


@dataclass
class ExecutionStats:
    """실행 통계."""
    total_abilities: int
    success: int
    failed: int

    @property
    def success_rate(self) -> float:
        """성공률 계산."""
        return self.success / self.total_abilities if self.total_abilities > 0 else 0.0


@dataclass
class CorrectionResult:
    """Ability 수정 시도 결과."""
    ability_id: str
    ability_name: str
    success: bool
    failure_type: Optional[FailureType] = None
    attempts: int = 0
    fixed_command: str = ""
    reason: str = ""


@dataclass
class ExecutionReport:
    """최종 실행 및 수정 보고서."""
    initial_stats: ExecutionStats
    final_stats: ExecutionStats
    correction_log: List[CorrectionResult]

    def to_dict(self) -> Dict[str, Any]:
        """보고서를 딕셔너리로 변환."""
        successful = len([c for c in self.correction_log if c.success])
        attempted = len(self.correction_log)

        return {
            "initial_stats": {
                "total_abilities": self.initial_stats.total_abilities,
                "success": self.initial_stats.success,
                "failed": self.initial_stats.failed,
                "success_rate": self.initial_stats.success_rate,
            },
            "final_stats": {
                "total_abilities": self.final_stats.total_abilities,
                "success": self.final_stats.success,
                "failed": self.final_stats.failed,
                "success_rate": self.final_stats.success_rate,
            },
            "correction_summary": {
                "total_corrections_attempted": attempted,
                "successful_corrections": successful,
                "failed_corrections": attempted - successful,
                "correction_success_rate": (
                    successful / attempted if attempted > 0 else 0.0
                ),
            },
            "corrections": [
                {
                    "ability_id": c.ability_id,
                    "ability_name": c.ability_name,
                    "failure_type": c.failure_type.value if c.failure_type else None,
                    "attempts": c.attempts,
                    "success": c.success,
                    "reason": c.reason,
                }
                for c in self.correction_log
            ],
        }
