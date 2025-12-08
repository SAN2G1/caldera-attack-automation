"""Caldera Operation API 조사 스크립트."""
import sys
sys.path.insert(0, '.')
import requests
import json
from modules.core.config import get_caldera_url, get_caldera_api_key

url = get_caldera_url().rstrip('/')
key = get_caldera_api_key()
headers = {'KEY': key, 'Content-Type': 'application/json'}

print("=" * 70)
print("Caldera Operation API Research")
print("=" * 70)

# 1. Get operations
print("\n[1] GET /api/v2/operations")
r = requests.get(f'{url}/api/v2/operations', headers=headers)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    ops = r.json()
    print(f"  Total operations: {len(ops)}")
    for op in ops[:3]:
        print(f"    - ID: {op.get('id', 'N/A')}")
        print(f"      Name: {op.get('name', 'N/A')}")
        print(f"      State: {op.get('state', 'N/A')}")
        print(f"      Adversary: {op.get('adversary', {}).get('adversary_id', 'N/A')}")

# 2. Get planners
print("\n[2] GET /api/v2/planners (플래너 옵션)")
r = requests.get(f'{url}/api/v2/planners', headers=headers)
if r.status_code == 200:
    planners = r.json()
    for p in planners:
        print(f"  - {p.get('planner_id', 'N/A')}: {p.get('name', 'N/A')}")
        if p.get('description'):
            print(f"    Description: {p.get('description', '')[:80]}")

# 3. Get sources (Fact sources)
print("\n[3] GET /api/v2/sources (데이터 소스)")
r = requests.get(f'{url}/api/v2/sources', headers=headers)
if r.status_code == 200:
    sources = r.json()
    for s in sources[:5]:
        print(f"  - {s.get('id', 'N/A')}: {s.get('name', 'N/A')}")

# 4. Get obfuscators
print("\n[4] GET /api/v2/obfuscators (난독화 옵션)")
r = requests.get(f'{url}/api/v2/obfuscators', headers=headers)
if r.status_code == 200:
    obfs = r.json()
    for o in obfs:
        print(f"  - {o.get('name', 'N/A')}: {o.get('description', 'N/A')[:50]}")

# 5. Test POST Operation (dry run - 주석 처리)
print("\n[5] POST /api/v2/operations (Operation 생성 옵션)")
operation_schema = {
    "name": "string (필수)",
    "adversary": {"adversary_id": "string (필수)"},
    "planner": {"id": "atomic (기본)"},
    "source": {"id": "basic (기본)"},
    "group": "red (대상 에이전트 그룹)",
    "state": "running | paused",
    "auto_close": "boolean (자동 종료)",
    "autonomous": "boolean (자율 실행)",
    "jitter": "3/8 (min/max 지연)",
    "visibility": "51 (로깅 레벨)",
    "obfuscator": "plain-text | base64 등"
}
print("  요청 스키마:")
print(json.dumps(operation_schema, indent=4, ensure_ascii=False))

# 6. Get agents
print("\n[6] GET /api/v2/agents (사용 가능한 에이전트)")
r = requests.get(f'{url}/api/v2/agents', headers=headers)
if r.status_code == 200:
    agents = r.json()
    print(f"  Total agents: {len(agents)}")
    for a in agents[:5]:
        print(f"    - PAW: {a.get('paw', 'N/A')}")
        print(f"      Group: {a.get('group', 'N/A')}")
        print(f"      Platform: {a.get('platform', 'N/A')}")
        print(f"      Privilege: {a.get('privilege', 'N/A')}")
        print(f"      Executors: {a.get('executors', [])}")
        print()

print("\n" + "=" * 70)
print("Research Complete")
print("=" * 70)
