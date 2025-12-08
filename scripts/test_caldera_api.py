"""Caldera API 통신 테스트 스크립트."""
import requests
import json
import yaml
from modules.core.config import get_caldera_url, get_caldera_api_key


def test_caldera_api():
    url = get_caldera_url()
    key = get_caldera_api_key()
    
    headers = {
        'KEY': key,
        'Content-Type': 'application/json'
    }
    
    print("=" * 70)
    print(f"Caldera API Test - Server: {url}")
    print("=" * 70)
    
    # 1. Test connection
    print("\n[1] Basic Connection Test")
    try:
        r = requests.get(f'{url}/api/v2/health', headers=headers, timeout=5)
        print(f"  GET /api/v2/health: {r.status_code}")
    except Exception as e:
        print(f"  GET /api/v2/health: Error - {e}")
    
    # 2. List endpoints
    print("\n[2] Available API Endpoints")
    endpoints = [
        ('/api/v2/abilities', 'GET'),
        ('/api/v2/adversaries', 'GET'),
        ('/api/v2/agents', 'GET'),
        ('/api/v2/operations', 'GET'),
        ('/api/v2/sources', 'GET'),
        ('/api/v2/planners', 'GET'),
    ]
    
    for endpoint, method in endpoints:
        try:
            r = requests.get(f'{url}{endpoint}', headers=headers, timeout=5)
            count = len(r.json()) if r.status_code == 200 else 'N/A'
            print(f"  {method} {endpoint}: {r.status_code} (count: {count})")
        except Exception as e:
            print(f"  {method} {endpoint}: Error - {str(e)[:50]}")
    
    # 3. Test ability creation methods
    print("\n[3] Ability Creation Methods")
    
    test_ability = {
        "ability_id": "test-ability-12345678",
        "name": "Test Ability",
        "description": "API Test",
        "tactic": "discovery",
        "technique_id": "T1033",
        "technique_name": "System Owner/User Discovery",
        "executors": [
            {
                "platform": "windows",
                "name": "psh",
                "command": "whoami"
            }
        ]
    }
    
    # Method 1: POST /api/v2/abilities
    print("\n  Method 1: POST /api/v2/abilities")
    try:
        r = requests.post(f'{url}/api/v2/abilities', headers=headers, json=test_ability, timeout=10)
        print(f"    Status: {r.status_code}")
        print(f"    Response: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # Method 2: PUT /api/v2/abilities/{id}
    print("\n  Method 2: PUT /api/v2/abilities/{id}")
    try:
        r = requests.put(f'{url}/api/v2/abilities/{test_ability["ability_id"]}', headers=headers, json=test_ability, timeout=10)
        print(f"    Status: {r.status_code}")
        print(f"    Response: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # Method 3: POST /api/v1/ability (V1 API)
    print("\n  Method 3: POST /api/v1/ability (V1 API)")
    try:
        r = requests.post(f'{url}/api/v1/ability', headers=headers, json=test_ability, timeout=10)
        print(f"    Status: {r.status_code}")
        print(f"    Response: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # Method 4: POST with different format (platforms structure)
    print("\n  Method 4: POST with platforms structure")
    test_ability_v2 = {
        "id": "test-ability-12345678",
        "name": "Test Ability",
        "description": "API Test",
        "tactic": "discovery",
        "technique": {
            "attack_id": "T1033",
            "name": "System Owner/User Discovery"
        },
        "platforms": {
            "windows": {
                "psh": {
                    "command": "whoami"
                }
            }
        }
    }
    try:
        r = requests.post(f'{url}/api/v2/abilities', headers=headers, json=test_ability_v2, timeout=10)
        print(f"    Status: {r.status_code}")
        print(f"    Response: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # 4. Check existing abilities
    print("\n[4] Sample Existing Abilities")
    try:
        r = requests.get(f'{url}/api/v2/abilities', headers=headers, timeout=10)
        if r.status_code == 200:
            abilities = r.json()
            for a in abilities[:3]:
                print(f"  - {a.get('ability_id', 'N/A')[:8]}...: {a.get('name', 'N/A')}")
            print(f"  ... and {len(abilities) - 3} more")
    except Exception as e:
        print(f"  Error: {e}")
    
    # 5. Check adversaries
    print("\n[5] Adversary Creation Test")
    test_adversary = {
        "adversary_id": "test-adversary-12345",
        "name": "Test Adversary",
        "description": "API Test",
        "atomic_ordering": []
    }
    
    try:
        r = requests.post(f'{url}/api/v2/adversaries', headers=headers, json=test_adversary, timeout=10)
        print(f"  POST /api/v2/adversaries: {r.status_code}")
        print(f"  Response: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    test_caldera_api()
