"""
Module 7: Offline Self-Correcting Engine
로컬에서 Operation 로그를 분석하여 실패한 Ability를 자동으로 수정

워크플로우:
1. Caldera 서버에서 fetch_operation_logs.py로 로그 수집
2. 로컬로 로그 파일 복사
3. 이 모듈로 로그 분석 + LLM 수정
4. 수정된 abilities.yml 생성
5. Caldera 서버로 복사 후 재업로드
"""

import yaml
import json
import re
import anthropic
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
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
class FailedAbility:
    """실패한 Ability 정보"""
    ability_id: str
    ability_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    failure_type: Optional[FailureType] = None


@dataclass
class CorrectionResult:
    """수정 결과"""
    ability_id: str
    ability_name: str
    original_command: str
    fixed_command: str
    failure_type: FailureType
    success: bool
    reason: str = ""


# ============================================================================
# Failure Classifier
# ============================================================================

class FailureClassifier:
    """실패 유형 분류"""

    RULES = {
        "syntax_error": ["syntax error", "parsererror", "parse error", "unexpected token"],
        "missing_env": ["cannot find path", "connection refused", "not found", "invalid uri"],
        "caldera_constraint": ["variable is not defined", "undefined variable", "cannot find variable"],
        "dependency_error": ["access is denied", "access denied", "requires elevation", "privilege", "unauthorized"],
        "unrecoverable": ["not recognized as cmdlet", "command not found", "is not installed"]
    }

    def classify(self, stderr: str, stdout: str) -> FailureType:
        """실패 유형 분류"""
        error_text = (stderr + "\n" + stdout).lower()

        for rule_key, keywords in self.RULES.items():
            if any(keyword in error_text for keyword in keywords):
                return FailureType(rule_key)

        return FailureType.UNRECOVERABLE


# ============================================================================
# Ability Fixer (LLM)
# ============================================================================

class AbilityFixer:
    """LLM 기반 Ability 수정"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=get_anthropic_api_key())
        self.model = get_claude_model()

    def fix_ability(
        self,
        original_ability: Dict,
        failed: FailedAbility,
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

[Failure Type]: {failed.failure_type.value}

[Error Output (stderr)]:
```
{failed.stderr[:500]}
```

[Standard Output (stdout)]:
```
{failed.stdout[:500]}
```

[Environment Description]:
{env_description}

[CRITICAL Rules]
1. Each Ability runs in INDEPENDENT PowerShell process - NO variable sharing
2. Use actual values from Environment Description
3. PowerShell 5.1 compatible only
4. Output ONLY the corrected PowerShell command

{self._get_fix_strategy(failed.failure_type)}

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

    def _get_fix_strategy(self, failure_type: FailureType) -> str:
        """실패 유형별 수정 전략"""

        strategies = {
            FailureType.SYNTAX_ERROR: """
[Fix Strategy for SYNTAX_ERROR]
1. Check PowerShell 5.1 syntax rules
2. Verify variable declarations
3. Escape special characters properly
4. Use proper quoting (single vs double quotes)
5. Fix cmdlet parameter names
""",

            FailureType.MISSING_ENV: """
[Fix Strategy for MISSING_ENV]
1. Replace ALL placeholders with actual values from Environment Description
2. Use exact IP addresses, URLs, and credentials from Environment Description
3. Check for hardcoded placeholder strings like TARGET_IP, WEB_URL, etc.
4. Ensure all paths exist and are correct
""",

            FailureType.CALDERA_CONSTRAINT: """
[Fix Strategy for CALDERA_CONSTRAINT]
1. Remove dependencies on previous Ability variables
2. Make the command completely self-contained
3. If you need data from a previous step, re-execute that logic
4. DO NOT use variables like $output, $result from previous Abilities
5. Hardcode values or recalculate them in this command
""",

            FailureType.DEPENDENCY_ERROR: """
[Fix Strategy for DEPENDENCY_ERROR]
1. Check if elevation is required
2. Add error handling for privilege issues
3. Use alternative methods that don't require high privileges
""",

            FailureType.UNRECOVERABLE: """
[Fix Strategy for UNRECOVERABLE]
1. Use only built-in Windows/PowerShell cmdlets
2. DO NOT rely on external tools unless they're in Environment Description
3. Replace missing cmdlets with native alternatives
"""
        }

        return strategies.get(failure_type, "")


# ============================================================================
# Offline Corrector
# ============================================================================

class OfflineCorrector:
    """오프라인 Self-Correcting 엔진"""

    def __init__(self):
        self.classifier = FailureClassifier()
        self.fixer = AbilityFixer()

    def correct_from_logs(
        self,
        caldera_dir: str,
        operation_logs_file: str,
        env_description_file: str,
        output_dir: str
    ):
        """로그 파일로부터 Self-Correcting 수행"""

        print("="*70)
        print("M7: Offline Self-Correcting Engine")
        print("="*70)

        # 파일 로드
        abilities = self._load_yaml(f"{caldera_dir}/abilities.yml")
        env_description = Path(env_description_file).read_text(encoding='utf-8')

        with open(operation_logs_file, 'r', encoding='utf-8') as f:
            operation_report = json.load(f)

        print(f"\n[Loaded] {len(abilities)} abilities")
        print(f"[Loaded] Operation: {operation_report.get('name', 'Unknown')}")

        # 통계 계산 (steps에서 집계)
        total_steps = 0
        success_steps = 0
        failed_steps = 0

        for agent_paw, agent_data in operation_report.get('steps', {}).items():
            for step in agent_data.get('steps', []):
                total_steps += 1
                status = step.get('status', 0)
                if status == 0:
                    success_steps += 1
                elif status == 1:
                    failed_steps += 1

        print(f"[Stats] Total: {total_steps}, "
              f"Success: {success_steps}, "
              f"Failed: {failed_steps}")

        # Abilities lookup 생성
        abilities_lookup = {a['ability_id']: a for a in abilities}

        # 실패한 Ability 추출
        failed_abilities = self._extract_failed_abilities(operation_report)

        if not failed_abilities:
            print("\n[OK] No failed abilities to correct!")
            return

        print(f"\n[Correction Phase] {len(failed_abilities)} failures")

        # 각 실패한 Ability 수정
        correction_results = []
        corrected_abilities = []

        for failed in failed_abilities:
            print(f"\n  [{failed.ability_name}]")

            # 실패 유형 분류
            failed.failure_type = self.classifier.classify(failed.stderr, failed.stdout)
            print(f"    Failure Type: {failed.failure_type.value}")

            # Unrecoverable이면 스킵
            if failed.failure_type == FailureType.UNRECOVERABLE:
                correction_results.append(CorrectionResult(
                    ability_id=failed.ability_id,
                    ability_name=failed.ability_name,
                    original_command=failed.command,
                    fixed_command="",
                    failure_type=failed.failure_type,
                    success=False,
                    reason="Unrecoverable error type"
                ))
                continue

            # 원본 Ability 조회
            original_ability = abilities_lookup.get(failed.ability_id)
            if not original_ability:
                print(f"    [WARNING] Original ability not found")
                continue

            # LLM으로 수정
            print(f"    Fixing with LLM...")
            fixed_ability = self.fixer.fix_ability(original_ability, failed, env_description)

            fixed_command = fixed_ability['executors'][0]['command']
            print(f"    [OK] Fixed: {fixed_command[:80]}...")

            corrected_abilities.append(fixed_ability)

            correction_results.append(CorrectionResult(
                ability_id=failed.ability_id,
                ability_name=failed.ability_name,
                original_command=failed.command,
                fixed_command=fixed_command,
                failure_type=failed.failure_type,
                success=True
            ))

        # 출력 디렉토리 생성
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 수정된 abilities.yml 저장
        abilities_output = f"{output_dir}/abilities_corrected.yml"
        with open(abilities_output, 'w', encoding='utf-8') as f:
            yaml.dump(corrected_abilities, f, allow_unicode=True, sort_keys=False)

        print(f"\n[OK] Corrected abilities saved to: {abilities_output}")

        # 수정 보고서 저장
        report_output = f"{output_dir}/correction_report.json"
        report = {
            "operation": {
                "name": operation_report.get('name', ''),
                "initial_stats": {
                    "total": total_steps,
                    "success": success_steps,
                    "failed": failed_steps
                }
            },
            "corrections": [
                {
                    "ability_id": r.ability_id,
                    "ability_name": r.ability_name,
                    "failure_type": r.failure_type.value,
                    "success": r.success,
                    "reason": r.reason,
                    "original_command": r.original_command[:200],
                    "fixed_command": r.fixed_command[:200] if r.fixed_command else ""
                }
                for r in correction_results
            ],
            "summary": {
                "total_failed": len(failed_abilities),
                "corrected": len([r for r in correction_results if r.success]),
                "skipped": len([r for r in correction_results if not r.success])
            }
        }

        with open(report_output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"[OK] Correction report saved to: {report_output}")

        print("\n" + "="*70)
        print(f"[SUCCESS] Corrected {report['summary']['corrected']}/{report['summary']['total_failed']} abilities")
        print("="*70)

    def _load_yaml(self, file_path: str) -> List[Dict]:
        """YAML 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _extract_failed_abilities(self, operation_report: Dict) -> List[FailedAbility]:
        """실패한 Ability 추출 (Caldera Operation Report 형식)"""
        failed = []

        # steps 섹션에서 추출 (시간순 정렬됨)
        steps = operation_report.get('steps', {})

        for agent_paw, agent_data in steps.items():
            for step in agent_data.get('steps', []):
                status = step.get('status', 0)

                # status 값 분석:
                # 0 = 성공
                # 1 = 실패 (exit_code != 0)
                # -3 = 미실행 (스킵됨)
                # 실패한 것만 추출 (status == 1)
                if status == 1:
                    output = step.get('output', {})
                    exit_code_str = output.get('exit_code', '0')

                    # exit_code는 문자열로 저장되어 있음
                    try:
                        exit_code = int(exit_code_str)
                    except (ValueError, TypeError):
                        exit_code = 1

                    ability = step.get('attack', {})

                    failed.append(FailedAbility(
                        ability_id=step.get('ability_id', ''),
                        ability_name=step.get('name', ''),
                        command=step.get('plaintext_command', step.get('command', '')),
                        exit_code=exit_code,
                        stdout=output.get('stdout', ''),
                        stderr=output.get('stderr', '')
                    ))

        return failed


def main():
    """Main entry point"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="M7: Offline Self-Correcting (Local Execution)",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--caldera-dir",
        type=str,
        required=True,
        help="Caldera output directory containing abilities.yml"
    )

    parser.add_argument(
        "--operation-logs",
        type=str,
        required=True,
        help="Operation logs JSON file (from fetch_operation_logs.py)"
    )

    parser.add_argument(
        "--env",
        type=str,
        required=True,
        help="Environment description file (*.md)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="caldera_corrected",
        help="Output directory for corrected abilities (default: caldera_corrected)"
    )

    args = parser.parse_args()

    # 파일 존재 확인
    caldera_dir = Path(args.caldera_dir)
    abilities_file = caldera_dir / "abilities.yml"

    if not abilities_file.exists():
        print(f"[ERROR] abilities.yml not found: {abilities_file}")
        sys.exit(1)

    if not Path(args.operation_logs).exists():
        print(f"[ERROR] Operation logs not found: {args.operation_logs}")
        sys.exit(1)

    if not Path(args.env).exists():
        print(f"[ERROR] Environment description not found: {args.env}")
        sys.exit(1)

    # Corrector 실행
    try:
        corrector = OfflineCorrector()
        corrector.correct_from_logs(
            caldera_dir=str(caldera_dir),
            operation_logs_file=args.operation_logs,
            env_description_file=args.env,
            output_dir=args.output
        )

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
