"""Caldera 업로더 모듈."""
import requests
import yaml
import json
from typing import List
from modules.core.config import get_caldera_url, get_caldera_api_key


class CalderaUploader:
    """Caldera에 Ability와 Adversary를 업로드하는 클래스."""

    def __init__(self):
        self.base_url = get_caldera_url().rstrip('/')
        self.api_key = get_caldera_api_key()
        self.session = requests.Session()
        self.session.headers.update({
            'KEY': self.api_key,
            'Content-Type': 'application/json'
        })
        self.uploaded_ability_ids = []
        self.uploaded_adversary_ids = []

    def _upsert(self, endpoint: str, item_id: str, data: dict) -> tuple[bool, str, str]:
        """공통 upsert 로직: 존재하면 PUT, 없으면 POST.

        Args:
            endpoint: API 엔드포인트 (예: 'abilities', 'adversaries').
            item_id: 항목 ID.
            data: 데이터 딕셔너리.

        Returns:
            tuple[bool, str, str]: (성공 여부, 수행한 작업 'UPDATE'/'CREATE', 에러 메시지).
        """
        check_url = f"{self.base_url}/api/v2/{endpoint}/{item_id}"
        
        try:
            exists = self.session.get(check_url).status_code == 200

            if exists:
                response = self.session.put(check_url, json=data)
                action = "UPDATE"
            else:
                url = f"{self.base_url}/api/v2/{endpoint}"
                response = self.session.post(url, json=data)
                action = "CREATE"

            if response.status_code in (200, 201):
                return True, action, ""
            else:
                return False, "", f"HTTP {response.status_code}: {response.text}"
        
        except requests.exceptions.RequestException as e:
            return False, "", f"Network Error: {str(e)}"
        except Exception as e:
            return False, "", f"Unknown Error: {str(e)}"


    def upload_abilities(self, abilities_file: str) -> List[str]:
        """Abilities 업로드 (upsert).

        Args:
            abilities_file: abilities.yml 파일 경로.

        Returns:
            List[str]: 업로드된 Ability ID 목록.
        """
        print("\n" + "="*70)
        print("Abilities 업로드")
        print("="*70)

        with open(abilities_file, 'r', encoding='utf-8') as f:
            abilities = yaml.safe_load(f) or []

        if not abilities:
            print("  [ERROR] No abilities found")
            return []

        uploaded_ids = []
        created, updated = 0, 0

        for i, ability in enumerate(abilities, 1):
            ability_id = ability.get('ability_id')
            print(f"  [{i}/{len(abilities)}] {ability.get('name', 'Unknown')}")

            success, action, error_msg = self._upsert('abilities', ability_id, ability)
            if success:
                print(f"    [OK] {action}")
                uploaded_ids.append(ability_id)
                self.uploaded_ability_ids.append(ability_id)
                created += 1 if action == "CREATE" else 0
                updated += 1 if action == "UPDATE" else 0
            else:
                print(f"    [FAILED] {error_msg}")

        print(f"\n  완료: {len(uploaded_ids)}/{len(abilities)} (신규: {created}, 수정: {updated})")
        return uploaded_ids

    def upload_adversaries(self, adversaries_file: str) -> List[str]:
        """Adversaries 업로드 (upsert).

        Args:
            adversaries_file: adversaries.yml 파일 경로.

        Returns:
            List[str]: 업로드된 Adversary ID 목록.
        """
        print("\n" + "="*70)
        print("Adversaries 업로드")
        print("="*70)

        with open(adversaries_file, 'r', encoding='utf-8') as f:
            adversaries = yaml.safe_load(f) or []

        if not adversaries:
            print("  [ERROR] No adversaries found")
            return []

        uploaded_ids = []
        created, updated = 0, 0

        for i, adversary in enumerate(adversaries, 1):
            adversary_id = adversary.get('adversary_id')
            print(f"  [{i}/{len(adversaries)}] {adversary.get('name', 'Unknown')}")

            success, action, error_msg = self._upsert('adversaries', adversary_id, adversary)
            if success:
                print(f"    [OK] {action}")
                uploaded_ids.append(adversary_id)
                self.uploaded_adversary_ids.append(adversary_id)
                created += 1 if action == "CREATE" else 0
                updated += 1 if action == "UPDATE" else 0
            else:
                print(f"    [FAILED] {error_msg}")

        print(f"\n  완료: {len(uploaded_ids)}/{len(adversaries)} (신규: {created}, 수정: {updated})")
        return uploaded_ids

    def delete_abilities(self, ability_ids: List[str]) -> int:
        """Caldera 서버에서 Ability 삭제.

        Args:
            ability_ids: 삭제할 Ability ID 목록.

        Returns:
            int: 삭제된 Ability 수.
        """
        deleted = 0
        for ability_id in ability_ids:
            url = f"{self.base_url}/api/v2/abilities/{ability_id}"
            try:
                response = self.session.delete(url)
                if response.status_code in (200, 204):
                    deleted += 1
            except Exception:
                pass
        return deleted

    def delete_adversaries(self, adversary_ids: List[str]) -> int:
        """Caldera 서버에서 Adversary 삭제.

        Args:
            adversary_ids: 삭제할 Adversary ID 목록.

        Returns:
            int: 삭제된 Adversary 수.
        """
        deleted = 0
        for adversary_id in adversary_ids:
            url = f"{self.base_url}/api/v2/adversaries/{adversary_id}"
            try:
                response = self.session.delete(url)
                if response.status_code in (200, 204):
                    deleted += 1
            except Exception:
                pass
        return deleted

    def save_tracking_file(self, output_file: str):
        """업로드된 ID 추적 파일 저장.

        Args:
            output_file: 저장할 파일 경로.
        """
        tracking_data = {
            'abilities': self.uploaded_ability_ids,
            'adversaries': self.uploaded_adversary_ids
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(tracking_data, f, allow_unicode=True, sort_keys=False)
        print(f"\n[OK] Tracking file: {output_file}")
