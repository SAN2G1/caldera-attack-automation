# M7: Self-Correcting Module

KISA TTPs → Caldera Adversary 파이프라인의 Self-Correcting 모듈

## 개요

M7 모듈은 Caldera에서 실행된 공격 시나리오의 실패한 Ability를 자동으로 감지하고 LLM을 활용하여 수정합니다.

## 워크플로우

```
[Caldera 서버]              [로컬]                    [Caldera 서버]
     │                        │                           │
     ▼                        │                           │
 Operation 실행               │                            │
     │                        │                           │
     ▼                        │                           │
 Report 수집 ─────────────────▶ 로그 분석                  │
 (get_operation_report.py)    │                           │
                              ▼                           │
                         실패 분류                         │
                              │                           │
                              ▼                           │
                         LLM 수정                          │
                    (module7_self_correcting)             │
                              │                           │
                              ▼                           │
                    abilities.yml 수정 ──────────────────▶ 재업로드
                                                          │
                                                          ▼
                                                      재실행
```

---

## 사전 준비

### 필수 요구사항

- Python 3.10+
- Anthropic API Key (`.env` 파일에 설정)
- Caldera 서버 실행 중
- Caldera Agent 배포 완료

### 설치

```bash
pip install -r requirements.txt
```

---

## Step 1: Caldera에서 Operation 실행

### 1.1 Abilities & Adversary 업로드

```bash
python upload_to_caldera.py --caldera-dir data/processed/[날짜-시간]/caldera
```

### 1.2 Operation 실행

1. `http://localhost:8888` 접속
2. **Operations** → **Create Operation**
3. 설정:
   - Adversary: 업로드한 Adversary 선택
   - Agents: 대상 Agent 선택
   - Planner: `atomic`
4. **Start** 클릭
5. Operation 완료 대기

### 1.3 Operation Report 수집

```bash
python get_operation_report.py --name "Operation이름" --output report.json
```

또는 Caldera UI에서:
1. Operation 완료 후 **Download Report** 클릭
2. **JSON** 형식 선택

---

## Step 2: Self-Correcting 실행

### 2.1 실행 명령어

```bash
# 자동 탐색 (Report의 adversary_id로 abilities.yml 위치 자동 찾기)
python -m modules.module7_self_correcting \
  --report report.json \
  --env environment_description.md

# 수동 지정
python -m modules.module7_self_correcting \
  --abilities data/processed/[날짜-시간]/caldera/abilities.yml \
  --report report.json \
  --env environment_description.md \
  --output corrected_output
```

### 2.2 옵션 설명

| 옵션 | 필수 | 설명 |
|------|:----:|------|
| `--abilities` | X | abilities.yml 파일 경로 (미지정 시 자동 탐색) |
| `--report` | O | Operation Report JSON 파일 경로 |
| `--env` | O | 환경 설명 파일 경로 |
| `--output` | X | 출력 디렉토리 (기본: abilities.yml과 같은 위치) |

> **자동 탐색**: Report의 `adversary_id` (예: `kisa-ttp-adversary-20251203_142900`)에서 버전 ID를 추출하여 `data/processed/20251203_142900/caldera/abilities.yml`을 자동으로 찾습니다.

### 2.3 출력 예시

```
======================================================================
M7: Offline Self-Correcting Engine
======================================================================

[로드 완료] 38 abilities
[로드 완료] Operation: TTPS1
[통계] 전체: 69, 성공: 44, 실패: 25

[수정 단계] 8개 실패 처리

  [Create Service for Persistence]
    실패 유형: dependency_error
    LLM 수정 중...
    [완료] $currentUser = [Security.Principal.WindowsIdentity]::GetCurr...

  [Copy Caldera Agent to Internal Host]
    실패 유형: missing_env
    LLM 수정 중...
    [완료] $payloadUrl = "http://192.168.56.1:8888/file/download"...

[저장] abilities.yml: corrected_output/abilities.yml
[저장] correction_report.json: corrected_output/correction_report.json

======================================================================
[결과] 2/8 abilities 수정 완료
======================================================================
```

### 2.4 생성 파일

- `abilities.yml` - 수정된 명령어가 반영된 abilities 파일
- `correction_report.json` - 수정 내역 보고서

---

## Step 3: 재업로드 및 재실행

### 3.1 기존 Abilities 삭제 (선택)

```bash
python delete_from_caldera.py data/processed/[날짜-시간]/caldera/uploaded_ids.yml
```

### 3.2 수정된 Abilities 업로드

```bash
python upload_to_caldera.py --caldera-dir corrected_output/
```

### 3.3 새 Operation 실행

Caldera UI에서 새 Operation 생성 및 실행

---

## 실패 유형 분류

| 유형 | 설명 | 수정 가능 |
|------|------|:--------:|
| `syntax_error` | PowerShell 문법 오류 | O |
| `missing_env` | 환경 정보 누락 (IP, URL 등) | O |
| `caldera_constraint` | Caldera 변수 공유 불가 | O |
| `dependency_error` | 권한 부족 (Access Denied) | O |
| `unrecoverable` | 도구 미설치 등 복구 불가 | X |

---

## 다중 Agent 실패 판단

여러 Agent에서 같은 Ability가 실행된 경우:

- **모든 Agent에서 실패** → 진짜 실패 (수정 대상)
- **하나라도 성공** → 성공으로 간주 (권한 있는 Agent에서 성공한 것)

예시:
```
Create Scheduled Task: reejhw(실패) + oiravv(성공) → 성공 처리
Create Service:        reejhw(실패) + oiravv(실패) → 실패 (수정 대상)
```

---

## 문제 해결

### Q1: abilities.yml을 찾을 수 없다면?

```bash
ls data/processed/
```
최신 날짜-시간 폴더에서 `caldera/abilities.yml` 확인

### Q2: 환경 설명 파일은 어디에?

프로젝트 루트의 `environment_description.md` 파일 사용

### Q3: LLM 수정이 안 된다면?

- `.env` 파일에 `ANTHROPIC_API_KEY` 확인
- `environment_description.md`에 상세 정보 추가
- `correction_report.json`에서 실패 유형 확인

### Q4: Agent PAW를 모르는 경우

Caldera API로 확인:
```bash
curl http://localhost:8888/api/v2/agents -H "KEY: ADMIN123"
```

---

## 제약사항

### PowerShell 제약
- PowerShell 5.1 호환 필수
- 각 Ability는 독립 프로세스 (변수 공유 불가)

### Caldera 제약
- 이전 Ability 변수 참조 불가
- Payload는 Caldera가 자동 배포

### API 제한
- Anthropic API rate limit 주의

---

## 관련 문서

- [M1-M6 파이프라인 README](README.md)
- [Caldera API 문서](https://caldera.readthedocs.io/)
- [Anthropic API 문서](https://docs.anthropic.com/)
