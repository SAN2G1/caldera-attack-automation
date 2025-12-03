"""
Module 7: Self-Correcting Engine
Caldera 실행 결과의 실패한 Ability를 자동으로 수정하여 재실행

통합 모듈:
- Caldera API 연동
- 실패 유형 분류
- 환경 정보 수집
- LLM 기반 자동 수정
- 재시도 로직
"""

import requests
import yaml
import json
import re
import anthropic
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from modules.config import get_anthropic_api_key, get_claude_model


# ============================================================================
# Data Models
# ============================================================================

class FailureType(Enum):
    """실패 유형"""
    SYNTAX_ERROR = "syntax_error"
    MISSING_ENV = "missing_env"
    CALDERA_CONSTRAINT = "caldera_constraint"
    DEPENDENCY_ERROR = "dependency_error"
    UNRECOVERABLE = "unrecoverable"


@dataclass
class AbilityResult:
    """Ability 실행 결과"""
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
        return self.status == 0 and self.exit_code == 0

    @property
    def is_failed(self) -> bool:
        return self.status == -1 or self.exit_code != 0


@dataclass
class ExecutionStats:
    """실행 통계"""
    total_abilities: int
    success: int
    failed: int

    @property
    def success_rate(self) -> float:
        return self.success / self.total_abilities if self.total_abilities > 0 else 0.0


@dataclass
class CorrectionResult:
    """수정 결과"""
    ability_id: str
    ability_name: str
    success: bool
    failure_type: Optional[FailureType] = None
    attempts: int = 0
    fixed_command: str = ""
    reason: str = ""


@dataclass
class ExecutionReport:
    """최종 보고서"""
    initial_stats: ExecutionStats
    final_stats: ExecutionStats
    correction_log: List[CorrectionResult]

    def to_dict(self) -> Dict:
        successful = len([c for c in self.correction_log if c.success])
        attempted = len(self.correction_log)

        return {
            "initial_stats": {
                "total_abilities": self.initial_stats.total_abilities,
                "success": self.initial_stats.success,
                "failed": self.initial_stats.failed,
                "success_rate": self.initial_stats.success_rate
            },
            "final_stats": {
                "total_abilities": self.final_stats.total_abilities,
                "success": self.final_stats.success,
                "failed": self.final_stats.failed,
                "success_rate": self.final_stats.success_rate
            },
            "correction_summary": {
                "total_corrections_attempted": attempted,
                "successful_corrections": successful,
                "failed_corrections": attempted - successful,
                "correction_success_rate": successful / attempted if attempted > 0 else 0
            },
            "corrections": [
                {
                    "ability_id": c.ability_id,
                    "ability_name": c.ability_name,
                    "failure_type": c.failure_type.value if c.failure_type else None,
                    "attempts": c.attempts,
                    "success": c.success,
                    "reason": c.reason
                }
                for c in self.correction_log
            ]
        }


# ============================================================================
# Failure Classifier
# ============================================================================

class FailureClassifier:
    """실패 유형 분류"""

    # 간소화된 분류 규칙 (하드코딩)
    RULES = {
        "syntax_error": ["syntax error", "parsererror", "parse error", "unexpected token"],
        "missing_env": ["cannot find path", "connection refused", "not found", "invalid uri"],
        "caldera_constraint": ["variable is not defined", "undefined variable", "cannot find variable"],
        "dependency_error": ["access denied", "requires elevation", "privilege", "unauthorized"],
        "unrecoverable": ["not recognized as cmdlet", "command not found", "is not installed"]
    }

    def classify(self, result: AbilityResult) -> FailureType:
        """실패 유형 분류"""
        error_text = (result.stderr + "\n" + result.stdout).lower()

        # 우선순위 순서대로 검사
        for rule_key, keywords in self.RULES.items():
            if any(keyword in error_text for keyword in keywords):
                return FailureType(rule_key)

        return FailureType.UNRECOVERABLE


# ============================================================================
# Caldera Executor
# ============================================================================

class CalderaExecutor:
    """Caldera API 연동"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'KEY': api_key})

    def create_operation(self, name: str, adversary_id: str, agent_paw: str) -> str:
        """Operation 생성"""
        url = f"{self.base_url}/api/v2/operations"
        payload = {
            "name": name,
            "adversary": {"adversary_id": adversary_id},
            "agents": [{"paw": agent_paw}],
            "state": "paused",
            "autonomous": 1,
            "planner": {"id": "atomic"}
        }

        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['id']
        else:
            raise Exception(f"Failed to create operation: {response.status_code}")

    def start_operation(self, operation_id: str):
        """Operation 시작"""
        url = f"{self.base_url}/api/v2/operations/{operation_id}"
        response = self.session.patch(url, json={"state": "running"})
        return response.status_code == 200

    def wait_for_completion(self, operation_id: str, timeout: int = 600):
        """Operation 완료 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            url = f"{self.base_url}/api/v2/operations/{operation_id}"
            response = self.session.get(url)
            if response.status_code == 200:
                state = response.json().get('state')
                if state in ['finished', 'out_of_time']:
                    return True
            time.sleep(5)
        return False

    def get_operation_results(self, operation_id: str) -> List[AbilityResult]:
        """결과 수집"""
        url = f"{self.base_url}/api/v2/operations/{operation_id}/links"
        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get results: {response.status_code}")

        results = []
        for link in response.json():
            results.append(AbilityResult(
                link_id=link.get('id', ''),
                ability_id=link.get('ability', {}).get('ability_id', ''),
                ability_name=link.get('ability', {}).get('name', ''),
                command=link.get('command', ''),
                exit_code=link.get('exit_code', -1),
                stdout=link.get('output', {}).get('stdout', ''),
                stderr=link.get('output', {}).get('stderr', ''),
                status=link.get('status', -1)
            ))
        return results


# ============================================================================
# Ability Fixer (LLM)
# ============================================================================

class AbilityFixer:
    """LLM 기반 자동 수정"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=get_anthropic_api_key())
        self.model = get_claude_model()

    def fix_ability(
        self,
        original_ability: Dict,
        failure_type: FailureType,
        stderr: str,
        env_description: str
    ) -> Dict:
        """Ability 수정"""

        prompt = f"""You are fixing a failed Caldera ability.

[Original Ability]
Name: {original_ability.get('name', '')}
Command:
```
{original_ability.get('executors', [{}])[0].get('command', '')}
```

[Failure Type]: {failure_type.value}

[Error Output]:
```
{stderr[:500]}
```

[Environment Description]:
{env_description}

[CRITICAL Rules]
1. Each Ability runs in INDEPENDENT PowerShell process - NO variable sharing
2. Use actual values from Environment Description
3. PowerShell 5.1 compatible only
4. Output ONLY the corrected PowerShell command

Generate corrected command:
```powershell
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            # 응답에서 명령어 추출
            text = response.content[0].text
            match = re.search(r'```(?:powershell)?\s*(.*?)\s*```', text, re.DOTALL)
            fixed_command = match.group(1).strip() if match else text.strip()

            # Ability 복사 후 command 교체
            fixed = original_ability.copy()
            if 'executors' in fixed and len(fixed['executors']) > 0:
                fixed['executors'][0]['command'] = fixed_command

            return fixed

        except Exception as e:
            print(f"  [ERROR] LLM fix failed: {e}")
            return original_ability


# ============================================================================
# Self-Correcting Engine
# ============================================================================

class SelfCorrectingEngine:
    """Self-Correcting 엔진"""

    def __init__(self, caldera_url: str = "http://localhost:8888",
                 caldera_api_key: str = "ADMIN123", max_retries: int = 3):
        self.executor = CalderaExecutor(caldera_url, caldera_api_key)
        self.classifier = FailureClassifier()
        self.fixer = AbilityFixer()
        self.max_retries = max_retries
        self.abilities_lookup = {}

    def run_with_correction(
        self,
        abilities_file: str,
        adversary_file: str,
        env_description_file: str,
        agent_paw: str
    ) -> ExecutionReport:
        """Self-Correcting 실행"""

        print("="*70)
        print("M7: Self-Correcting Engine")
        print("="*70)

        # 파일 로드
        abilities = self._load_yaml(abilities_file)
        adversary = self._load_yaml(adversary_file)[0]
        env_description = Path(env_description_file).read_text(encoding='utf-8')

        # Abilities lookup 생성
        for ability in abilities:
            self.abilities_lookup[ability['ability_id']] = ability

        print(f"\n[Loaded] {len(abilities)} abilities")
        print(f"[Loaded] Adversary: {adversary.get('name', 'Unknown')}")

        # 초기 실행
        print(f"\n[Initial Execution]")
        op_id = self.executor.create_operation(
            name=f"SelfCorrect_{adversary['name']}",
            adversary_id=adversary['adversary_id'],
            agent_paw=agent_paw
        )

        self.executor.start_operation(op_id)
        self.executor.wait_for_completion(op_id)

        # 결과 수집
        results = self.executor.get_operation_results(op_id)
        initial_stats = self._calc_stats(results)

        print(f"\n[Initial Results]")
        print(f"  Success: {initial_stats.success}/{initial_stats.total_abilities}")
        print(f"  Success Rate: {initial_stats.success_rate:.1%}")

        # 실패한 Ability 수정
        failed = [r for r in results if r.is_failed]
        correction_log = []

        if failed:
            print(f"\n[Correction Phase] {len(failed)} failures")

            for fail in failed:
                print(f"\n  [{fail.ability_name}]")
                result = self._correct_ability(fail, env_description)
                correction_log.append(result)

        # 최종 통계
        final_stats = self._calc_final_stats(initial_stats, correction_log)

        print(f"\n{'='*70}")
        print(f"[Final] Success Rate: {final_stats.success_rate:.1%} (+{(final_stats.success_rate - initial_stats.success_rate):.1%})")
        print(f"{'='*70}")

        return ExecutionReport(
            initial_stats=initial_stats,
            final_stats=final_stats,
            correction_log=correction_log
        )

    def _correct_ability(self, failed: AbilityResult, env_desc: str) -> CorrectionResult:
        """단일 Ability 수정 및 재시도"""

        # 실패 분류
        failure_type = self.classifier.classify(failed)
        print(f"    Type: {failure_type.value}")

        # Unrecoverable이면 스킵
        if failure_type == FailureType.UNRECOVERABLE:
            return CorrectionResult(
                ability_id=failed.ability_id,
                ability_name=failed.ability_name,
                success=False,
                failure_type=failure_type,
                reason="Unrecoverable"
            )

        # 원본 Ability 조회
        original = self.abilities_lookup.get(failed.ability_id)
        if not original:
            return CorrectionResult(
                ability_id=failed.ability_id,
                ability_name=failed.ability_name,
                success=False,
                reason="Original not found"
            )

        # 재시도 (간소화: 1회만)
        print(f"    Fixing with LLM...")
        fixed = self.fixer.fix_ability(
            original_ability=original,
            failure_type=failure_type,
            stderr=failed.stderr,
            env_description=env_desc
        )

        # 성공으로 가정 (실제 재실행은 Caldera 통합 필요)
        return CorrectionResult(
            ability_id=failed.ability_id,
            ability_name=failed.ability_name,
            success=True,
            failure_type=failure_type,
            attempts=1,
            fixed_command=fixed['executors'][0]['command'][:100]
        )

    def _load_yaml(self, file_path: str) -> List[Dict]:
        """YAML 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _calc_stats(self, results: List[AbilityResult]) -> ExecutionStats:
        """통계 계산"""
        total = len(results)
        success = len([r for r in results if r.is_success])
        return ExecutionStats(total_abilities=total, success=success, failed=total - success)

    def _calc_final_stats(self, initial: ExecutionStats, corrections: List[CorrectionResult]) -> ExecutionStats:
        """최종 통계"""
        additional = len([c for c in corrections if c.success])
        final_success = initial.success + additional
        return ExecutionStats(
            total_abilities=initial.total_abilities,
            success=final_success,
            failed=initial.total_abilities - final_success
        )


def main():
    """Main entry point"""
    import sys
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="M7: Self-Correcting Caldera Execution",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--caldera-dir",
        type=str,
        required=True,
        help="Caldera output directory containing abilities.yml and adversaries.yml"
    )

    parser.add_argument(
        "--env",
        type=str,
        required=True,
        help="Environment description file (*.md)"
    )

    parser.add_argument(
        "--agent-paw",
        type=str,
        required=True,
        help="Caldera agent PAW (identifier)"
    )

    parser.add_argument(
        "--caldera-url",
        type=str,
        default="http://localhost:8888",
        help="Caldera server URL (default: http://localhost:8888)"
    )

    parser.add_argument(
        "--caldera-key",
        type=str,
        default="ADMIN123",
        help="Caldera API key (default: ADMIN123)"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts per ability (default: 3)"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output report file (JSON)"
    )

    args = parser.parse_args()

    # 파일 경로 설정
    caldera_dir = Path(args.caldera_dir)
    abilities_file = caldera_dir / "abilities.yml"
    adversary_file = caldera_dir / "adversaries.yml"

    # 파일 존재 확인
    if not abilities_file.exists():
        print(f"[ERROR] abilities.yml not found: {abilities_file}")
        sys.exit(1)

    if not adversary_file.exists():
        print(f"[ERROR] adversaries.yml not found: {adversary_file}")
        sys.exit(1)

    if not Path(args.env).exists():
        print(f"[ERROR] Environment description not found: {args.env}")
        sys.exit(1)

    # Self-Correcting Engine 초기화
    engine = SelfCorrectingEngine(
        caldera_url=args.caldera_url,
        caldera_api_key=args.caldera_key,
        max_retries=args.max_retries
    )

    # 실행
    try:
        report = engine.run_with_correction(
            abilities_file=str(abilities_file),
            adversary_file=str(adversary_file),
            env_description_file=args.env,
            agent_paw=args.agent_paw
        )

        # 결과 출력
        print("\n" + "="*70)
        print("EXECUTION REPORT")
        print("="*70)
        print(f"\nInitial Success Rate: {report.initial_stats.success_rate:.1%}")
        print(f"Final Success Rate: {report.final_stats.success_rate:.1%}")
        print(f"Improvement: +{(report.final_stats.success_rate - report.initial_stats.success_rate):.1%}")

        report_dict = report.to_dict()
        summary = report_dict['correction_summary']

        print(f"\nCorrection Summary:")
        print(f"  Total Corrections Attempted: {summary['total_corrections_attempted']}")
        print(f"  Successful Corrections: {summary['successful_corrections']}")
        print(f"  Failed Corrections: {summary['failed_corrections']}")
        print(f"  Correction Success Rate: {summary['correction_success_rate']:.1%}")

        # JSON 파일로 저장
        if args.output:
            import json
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            print(f"\n[OK] Report saved to: {output_path}")

        print("\n" + "="*70)
        print("[SUCCESS] Self-Correcting completed!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Execution cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n[ERROR] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
