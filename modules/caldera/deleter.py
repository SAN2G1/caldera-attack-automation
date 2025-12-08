"""Caldera 삭제 모듈."""
import requests
from typing import List
from modules.core.config import get_caldera_url, get_caldera_api_key


class CalderaDeleter:
    """Caldera에서 Ability와 Adversary를 삭제하는 클래스."""

    def __init__(self):
        self.base_url = get_caldera_url()
        self.api_key = get_caldera_api_key()
        self.session = requests.Session()
        self.session.headers.update({'KEY': self.api_key})

        # 삭제 통계
        self.deleted_abilities = 0
        self.deleted_adversaries = 0
        self.failed_abilities = 0
        self.failed_adversaries = 0

    def delete_adversaries(self, adversary_ids: List[str]):
        """Adversaries 삭제 (먼저 삭제해야 함).

        Args:
            adversary_ids: 삭제할 Adversary ID 목록.
        """
        if not adversary_ids:
            print("\n  No adversaries to delete")
            return

        print("\n" + "="*70)
        print("Adversaries 삭제 시작")
        print("="*70)
        print(f"  Total adversaries to delete: {len(adversary_ids)}")

        for i, adversary_id in enumerate(adversary_ids, 1):
            print(f"\n  [{i}/{len(adversary_ids)}] Deleting adversary: {adversary_id[:8]}...")

            url = f"{self.base_url}/api/v2/adversaries/{adversary_id}"
            response = self.session.delete(url)

            if response.status_code == 200:
                print(f"    [OK] Deleted successfully")
                self.deleted_adversaries += 1
            elif response.status_code == 404:
                print(f"    [WARNING] Not found (already deleted?)")
                self.deleted_adversaries += 1
            else:
                print(f"    [FAILED] Status: {response.status_code}")
                print(f"    Error: {response.text[:200]}")
                self.failed_adversaries += 1

        print(f"\n{'='*70}")
        print(f"Adversaries 삭제 완료: {self.deleted_adversaries} 성공, {self.failed_adversaries} 실패")
        print(f"{'='*70}")

    def delete_abilities(self, ability_ids: List[str]):
        """Abilities 삭제.

        Args:
            ability_ids: 삭제할 Ability ID 목록.
        """
        if not ability_ids:
            print("\n  No abilities to delete")
            return

        print("\n" + "="*70)
        print("Abilities 삭제 시작")
        print("="*70)
        print(f"  Total abilities to delete: {len(ability_ids)}")

        for i, ability_id in enumerate(ability_ids, 1):
            print(f"\n  [{i}/{len(ability_ids)}] Deleting ability: {ability_id[:8]}...")

            url = f"{self.base_url}/api/v2/abilities/{ability_id}"
            response = self.session.delete(url)

            if response.status_code == 200:
                print(f"    [OK] Deleted successfully")
                self.deleted_abilities += 1
            elif response.status_code == 404:
                print(f"    [WARNING] Not found (already deleted?)")
                self.deleted_abilities += 1
            else:
                print(f"    [FAILED] Status: {response.status_code}")
                print(f"    Error: {response.text[:200]}")
                self.failed_abilities += 1

        print(f"\n{'='*70}")
        print(f"Abilities 삭제 완료: {self.deleted_abilities} 성공, {self.failed_abilities} 실패")
        print(f"{'='*70}")

    def print_summary(self):
        """삭제 요약 출력."""
        print("\n" + "="*70)
        print("삭제 요약")
        print("="*70)
        print(f"  Adversaries: {self.deleted_adversaries} 삭제, {self.failed_adversaries} 실패")
        print(f"  Abilities: {self.deleted_abilities} 삭제, {self.failed_abilities} 실패")
        print("="*70)
