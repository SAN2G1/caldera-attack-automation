"""
Module 3: Concrete Attack Flow Generation (WITHOUT MITRE Injection)
Combine abstract flow + environment description (MD) → concrete attack flow (Kill Chain)
AI generates technique_id/name from internal knowledge (no MITRE data in prompt)

실험용: MITRE 데이터 미주입 버전
"""

import yaml
import os
import json
import re
from typing import Dict, List, Set
import sys
from pathlib import Path
from datetime import datetime

# 모듈 패키지를 정상 인식하도록 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.ai.factory import get_llm_client
from modules.prompts.manager import PromptManager


class ConcreteFlowGenerator:
    def __init__(self):
        self.llm = get_llm_client()
        self.prompt_manager = PromptManager()
        self.mitre_techniques: Dict[str, Dict] = {}  # OS별 캐시 (검증용)
        self.valid_technique_ids: Dict[str, Set[str]] = {}  # OS별 유효 ID (검증용)

    def _extract_os_from_environment(self, env_description: str) -> str:
        """Extract OS type from environment description"""
        os_match = re.search(r'OS:\s*(Windows|Linux|macOS|Ubuntu|CentOS|Debian)[^\n]*', env_description, re.IGNORECASE)
        if os_match:
            os_str = os_match.group(1).lower()
            if 'windows' in os_str:
                return 'windows'
            elif os_str in ['linux', 'ubuntu', 'centos', 'debian']:
                return 'linux'
            elif 'macos' in os_str or 'mac' in os_str:
                return 'macos'

        # OS 정보 미감지 시 중단
        print("\n" + "="*70)
        print("[ERROR] OS 정보를 환경설명 파일에서 찾을 수 없습니다.")
        print("="*70)
        print("\n환경설명 파일에 다음 형식으로 OS를 명시해주세요:\n")
        print("  ## 공통 환경 정보")
        print("  - OS: Windows 10")
        print("  또는")
        print("  - OS: Ubuntu 22.04")
        print("  또는")
        print("  - OS: macOS Ventura")
        print("\n" + "="*70)
        raise ValueError("OS 정보가 환경설명에 명시되어 있지 않습니다. 환경설명 파일을 수정해주세요.")

    def _load_mitre_for_validation(self, os_type: str = 'windows'):
        """Load MITRE data for validation only (not for prompt injection)"""
        if os_type in self.mitre_techniques:
            return

        refined_dir = PROJECT_ROOT / "data" / "mitre" / "refined"
        mitre_files = list(refined_dir.glob(f"enterprise-attack-*-{os_type}-detailed.json"))

        if not mitre_files:
            legacy_path = refined_dir / f"mitre_{os_type}_option_b.json"
            if legacy_path.exists():
                mitre_files = [legacy_path]

        if mitre_files:
            mitre_path = sorted(mitre_files, reverse=True)[0]
            try:
                with open(mitre_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.mitre_techniques[os_type] = data.get('tactics', {})
                self.valid_technique_ids[os_type] = set()

                for tactic, techniques in self.mitre_techniques[os_type].items():
                    for tech_id in techniques.keys():
                        self.valid_technique_ids[os_type].add(tech_id)

                version = data.get('metadata', {}).get('version', 'unknown')
                technique_count = len(self.valid_technique_ids[os_type])
                print(f"  [OK] MITRE v{version} loaded for validation ({technique_count} techniques)")
            except Exception as e:
                print(f"  [WARNING] Failed to load MITRE data for validation: {e}")
                self.mitre_techniques[os_type] = {}
        else:
            print(f"  [WARNING] MITRE data not found for validation")
            self.mitre_techniques[os_type] = {}

    def generate_concrete_flow(self, abstract_flow_file: str,
                              environment_md_file: str,
                              output_file: str = None,
                              version_id: str = None):
        """Generate concrete attack flow by combining abstract flow + environment MD"""
        print("\n[Step 3] Concrete Attack Flow Generation started (NO MITRE INJECTION)...")

        # Load abstract flow
        with open(abstract_flow_file, 'r', encoding='utf-8') as f:
            abstract_data = yaml.safe_load(f)

        abstract_flow = abstract_data.get('abstract_flow', {})
        metadata = abstract_data.get('metadata', {})

        # pdf_name, version_id 추출
        pdf_name = metadata.get('pdf_name')
        if not pdf_name:
            pdf_name = Path(abstract_flow_file).stem.replace("_step2", "")
            if Path(abstract_flow_file).parents:
                pdf_name = Path(abstract_flow_file).parent.parent.name or pdf_name

        derived_version = (
            version_id
            or metadata.get('version_id')
            or Path(abstract_flow_file).parent.name
        )
        version_id = derived_version or datetime.now().strftime("%Y%m%d_%H%M%S")

        # Read environment description (Markdown)
        with open(environment_md_file, 'r', encoding='utf-8') as f:
            environment_description = f.read()

        print(f"  Abstract goals: {len(abstract_flow.get('attack_goals', []))}")
        print(f"  Environment description: {len(environment_description)} characters")

        # Extract OS from environment
        os_type = self._extract_os_from_environment(environment_description)

        # Load MITRE data for validation only
        self._load_mitre_for_validation(os_type)

        # Generate concrete flow (AI uses internal knowledge for techniques)
        concrete_flow = self._generate_flow(abstract_flow, environment_description, os_type)

        # Validate AI-generated technique IDs
        concrete_flow = self._validate_technique_ids(concrete_flow, os_type)

        # Save results
        output_data = {
            'metadata': {
                'sources': {
                    'abstract_flow': abstract_flow_file,
                    'environment': environment_md_file
                },
                'pdf_name': pdf_name,
                'version_id': version_id,
                'step': 3,
                'description': 'Concrete attack flow - AI internal knowledge (NO MITRE injection)',
                'os_type': os_type,
                'experiment': 'without_mitre_injection'
            },
            'concrete_flow': concrete_flow
        }

        if output_file is None:
            output_file = Path("../../data/processed") / pdf_name / version_id / f"{pdf_name}_step3.yml"

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, sort_keys=False)

        print(f"[SUCCESS] Concrete flow generation completed -> {output_file}")
        print(f"  - PDF: {pdf_name}")
        print(f"  - Version: {version_id}")
        self._print_summary(concrete_flow)

    def _generate_flow(self, abstract_flow: Dict, environment_description: str, os_type: str) -> Dict:
        """Generate concrete attack flow using LLM (NO MITRE data in prompt)"""
        print(f"  [Generating concrete attack flow ({os_type}) - AI internal knowledge...]")

        abstract_flow_yaml = yaml.dump(abstract_flow, allow_unicode=True)

        # NOTE: mitre_techniques NOT passed to prompt
        prompt = self.prompt_manager.render(
            "step3_generate_flow.yaml",
            abstract_flow=abstract_flow_yaml,
            environment_description=environment_description,
            os_type=os_type.capitalize()
        )

        MAX_RETRIES = 3
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    print(f"  [Retry {attempt}/{MAX_RETRIES}] Regenerating flow...")
                    retry_prompt = f"{prompt}\n\n[IMPORTANT] Previous attempt failed with error: {last_error}\nPlease generate valid YAML format without syntax errors."
                    response_text = self.llm.generate_text(prompt=retry_prompt, max_tokens=12000)
                else:
                    response_text = self.llm.generate_text(prompt=prompt, max_tokens=12000)

                yaml_text = self._extract_yaml(response_text)

                if not yaml_text or len(yaml_text.strip()) < 10:
                    raise ValueError("Extracted YAML is empty or too short")

                yaml_text = self._fix_backslashes(yaml_text)
                flow = yaml.safe_load(yaml_text)

                if not isinstance(flow, dict):
                    raise ValueError(f"Flow must be a dictionary, got {type(flow)}")

                if 'nodes' not in flow or not isinstance(flow.get('nodes'), list):
                    raise ValueError("Flow must contain 'nodes' as a list")

                if len(flow.get('nodes', [])) == 0:
                    raise ValueError("Flow must contain at least one node")

                print(f"  [OK] Generated {len(flow.get('nodes', []))} concrete steps")
                return flow

            except yaml.YAMLError as e:
                last_error = f"YAML parsing error: {str(e)}"
                print(f"  [ERROR] Attempt {attempt}/{MAX_RETRIES}: {last_error}")
                if attempt < MAX_RETRIES:
                    continue

            except (ValueError, KeyError, TypeError) as e:
                last_error = f"Structure validation error: {str(e)}"
                print(f"  [ERROR] Attempt {attempt}/{MAX_RETRIES}: {last_error}")
                if attempt < MAX_RETRIES:
                    continue

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                print(f"  [ERROR] Attempt {attempt}/{MAX_RETRIES}: {last_error}")
                if attempt < MAX_RETRIES:
                    continue

        raise RuntimeError(f"Failed to generate valid concrete flow after {MAX_RETRIES} attempts. Last error: {last_error}")

    def _validate_technique_ids(self, flow: Dict, os_type: str) -> Dict:
        """Validate AI-generated technique IDs (count valid/invalid)"""
        valid_ids = self.valid_technique_ids.get(os_type, set())
        if not valid_ids:
            print("  [WARNING] No valid technique IDs for validation, counting only")

        print("  [Validating AI-generated technique IDs...]")

        nodes = flow.get('nodes', [])
        valid_count = 0
        invalid_count = 0
        missing_count = 0

        for node in nodes:
            technique = node.get('technique', {})

            if not technique:
                node['technique'] = {'id': 'T0000', 'name': 'Unknown'}
                missing_count += 1
                continue

            tech_id = technique.get('id', '')

            if tech_id in valid_ids:
                valid_count += 1
            elif tech_id == 'T0000' or not tech_id:
                missing_count += 1
            else:
                # 조건 B에서는 invalid도 그대로 유지 (실험용)
                invalid_count += 1
                print(f"    [INFO] Unverified ID: {tech_id} for '{node.get('name', 'unknown')}'")

        total = valid_count + invalid_count + missing_count
        valid_rate = (valid_count / total * 100) if total > 0 else 0

        print(f"  [OK] Technique validation: {valid_count} valid ({valid_rate:.1f}%), {invalid_count} unverified, {missing_count} missing")
        return flow

    def _extract_yaml(self, text: str) -> str:
        """Extract YAML from response"""
        if '```yaml' in text:
            return text.split('```yaml')[1].split('```')[0].strip()
        elif '```' in text:
            return text.split('```')[1].split('```')[0].strip()
        return text

    def _fix_backslashes(self, yaml_text: str) -> str:
        """Fix Windows path backslash escaping in YAML"""
        def fix_quoted_string(match):
            content = match.group(1)
            normalized = re.sub(r'\\+', r'\\', content)
            fixed = normalized.replace('\\', '\\\\')
            return f'"{fixed}"'

        fixed_yaml = re.sub(r'"([^"]*)"', fix_quoted_string, yaml_text)
        return fixed_yaml

    def _print_summary(self, flow: Dict):
        """Print flow summary"""
        print("\n" + "="*70)
        print("Concrete Attack Flow Summary (WITHOUT MITRE INJECTION):")
        print("="*70)

        nodes = flow.get('nodes', [])
        edges = flow.get('edges', [])

        print(f"\nTotal Steps: {len(nodes)}")
        print(f"Dependencies: {len(edges)}")

        # Technique statistics
        valid_techniques = 0
        unknown_techniques = 0
        for node in nodes:
            tech = node.get('technique', {})
            if tech.get('id', 'T0000') != 'T0000':
                valid_techniques += 1
            else:
                unknown_techniques += 1

        print(f"\nTechnique Mapping:")
        print(f"  With ID: {valid_techniques}")
        print(f"  Unknown: {unknown_techniques}")

        if 'execution_order' in flow:
            print(f"\nExecution Order:")
            for i, node_id in enumerate(flow['execution_order'], 1):
                node = next((n for n in nodes if n['id'] == node_id), None)
                if node:
                    technique = node.get('technique', {})
                    if technique and technique.get('id') != 'T0000':
                        technique_str = f"{technique['id']} ({technique.get('name', 'Unknown')})"
                        print(f"  {i}. {node.get('name', 'Unknown')} [{node.get('tactic', 'unknown')}] ({technique_str})")
                    else:
                        print(f"  {i}. {node.get('name', 'Unknown')} [{node.get('tactic', 'unknown')}] (no technique)")

        print("\n" + "="*70)


def main():
    """Test runner"""
    if len(sys.argv) < 4:
        print("Usage: python step3_concrete_flow.py <abstract_flow.yml> <environment.md> <output.yml>")
        sys.exit(1)

    ConcreteFlowGenerator().generate_concrete_flow(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
