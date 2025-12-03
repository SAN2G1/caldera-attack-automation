"""
Fetch Operation Logs from Caldera
Caldera 서버에서 실행한 Operation의 결과를 JSON 파일로 저장

사용법:
    python fetch_operation_logs.py --operation-id <operation_id> --output operation_logs.json
"""

import requests
import json
import sys
import argparse
from pathlib import Path


class OperationLogFetcher:
    def __init__(self, base_url="http://localhost:8888", api_key="ADMIN123"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'KEY': api_key})

    def get_operation_info(self, operation_id: str) -> dict:
        """Operation 기본 정보 조회"""
        url = f"{self.base_url}/api/v2/operations/{operation_id}"
        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get operation info: {response.status_code}")

        return response.json()

    def get_operation_links(self, operation_id: str) -> list:
        """Operation의 모든 Link (Ability 실행 결과) 조회"""
        url = f"{self.base_url}/api/v2/operations/{operation_id}/links"
        response = self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get operation links: {response.status_code}")

        return response.json()

    def fetch_logs(self, operation_id: str, output_file: str):
        """Operation 로그 수집 및 저장"""
        print("="*70)
        print("Fetch Operation Logs from Caldera")
        print("="*70)
        print(f"\nOperation ID: {operation_id}")

        # Operation 정보 조회
        print("\n[1/3] Fetching operation info...")
        operation_info = self.get_operation_info(operation_id)

        print(f"  Operation Name: {operation_info.get('name', 'Unknown')}")
        print(f"  State: {operation_info.get('state', 'Unknown')}")
        print(f"  Adversary: {operation_info.get('adversary', {}).get('name', 'Unknown')}")

        # Links (실행 결과) 조회
        print("\n[2/3] Fetching operation links (ability execution results)...")
        links = self.get_operation_links(operation_id)

        print(f"  Total abilities executed: {len(links)}")

        # 성공/실패 통계
        success_count = sum(1 for link in links if link.get('status') == 0)
        failed_count = len(links) - success_count

        print(f"  Success: {success_count}")
        print(f"  Failed: {failed_count}")

        # 로그 데이터 구성
        log_data = {
            "operation_id": operation_id,
            "operation_name": operation_info.get('name', ''),
            "state": operation_info.get('state', ''),
            "adversary": operation_info.get('adversary', {}),
            "stats": {
                "total": len(links),
                "success": success_count,
                "failed": failed_count
            },
            "links": links
        }

        # JSON 파일로 저장
        print(f"\n[3/3] Saving logs to {output_file}...")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Logs saved successfully")

        print("\n" + "="*70)
        print("[SUCCESS] Log fetch completed!")
        print("="*70)
        print(f"\nNext step:")
        print(f"  1. Copy {output_file} to your local machine")
        print(f"  2. Run: python modules/module7_self_correcting.py \\")
        print(f"           --caldera-dir <caldera_dir> \\")
        print(f"           --operation-logs {output_file} \\")
        print(f"           --env <environment.md>")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Operation logs from Caldera",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--operation-id",
        type=str,
        required=True,
        help="Caldera Operation ID"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="operation_logs.json",
        help="Output JSON file path (default: operation_logs.json)"
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

    args = parser.parse_args()

    try:
        fetcher = OperationLogFetcher(
            base_url=args.caldera_url,
            api_key=args.caldera_key
        )

        fetcher.fetch_logs(args.operation_id, args.output)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Execution cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n[ERROR] Failed to fetch logs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
