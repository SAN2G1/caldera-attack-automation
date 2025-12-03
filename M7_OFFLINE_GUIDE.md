# M7 Offline Self-Correcting 실행 가이드

로컬에서 Caldera Operation 로그를 분석하여 실패한 Ability를 자동으로 수정하는 가이드입니다.

## 전체 워크플로우

```
[Caldera 서버] → [로컬] → [Caldera 서버]
   로그 수집       수정        재업로드
```

---

## Step 1: Caldera에서 Operation 실행 (Caldera 서버)

### 1.1 Abilities & Adversary 업로드

```bash
# Caldera 서버에 프로젝트 폴더 복사 후
python upload_to_caldera.py --caldera-dir data/processed/20251203_163450/caldera
```

### 1.2 Caldera 웹 UI에서 Operation 실행

1. `http://localhost:8888` 접속
2. **Operations** 탭 → **Create Operation** 클릭
3. 설정:
   - Name: 임의 지정
   - Adversary: 업로드한 Adversary 선택
   - Agents: 대상 Agent 선택
   - Planner: `atomic` 선택
4. **Start** 클릭
5. Operation 완료 대기 (State: `finished`)
6. **Operation ID** 복사 (URL에서 확인 가능)
   - 예: `http://localhost:8888/operations/abc123-def456...`
   - Operation ID: `abc123-def456...`

---

## Step 2: Operation 로그 수집 (Caldera 서버)

```bash
python fetch_operation_logs.py \
  --operation-id abc123-def456-... \
  --output operation_logs.json
```

**출력:**
```
======================================================================
Fetch Operation Logs from Caldera
======================================================================

Operation ID: abc123-def456-...

[1/3] Fetching operation info...
  Operation Name: My Operation
  State: finished
  Adversary: KISA TTP Adversary

[2/3] Fetching operation links (ability execution results)...
  Total abilities executed: 36
  Success: 27
  Failed: 9

[3/3] Saving logs to operation_logs.json...
  [OK] Logs saved successfully

======================================================================
[SUCCESS] Log fetch completed!
======================================================================
```

**생성된 파일:**
- `operation_logs.json` - Operation 실행 결과 (success/failure, stdout, stderr 포함)

---

## Step 3: 로그 파일을 로컬로 복사

Caldera 서버에서 로컬로 `operation_logs.json` 파일을 복사합니다.

**방법:**
- SCP: `scp user@caldera-server:~/operation_logs.json ./`
- USB 드라이브
- 네트워크 공유 폴더

**로컬 경로 예시:**
```
c:\Users\swlab-jueon\caldera-attack-automation\operation_logs.json
```

---

## Step 4: 로컬에서 Self-Correcting 실행 (로컬)

### 4.1 환경 설명 파일 작성

`templates/environment_description.md` 파일을 실제 테스트 환경에 맞게 작성:

```markdown
# 환경 설명

## 네트워크
- Target IP: 192.168.1.100
- Gateway IP: 192.168.1.1
- Web URL: http://192.168.1.100/admin

## 계정 정보
- Username: administrator
- Password: P@ssw0rd123!

## Payload 파일
- mimikatz.exe
- cmd.asp
- reverse_shell.exe

## 기타
- Windows 버전: Windows 10 Pro
- PowerShell 버전: 5.1
```

### 4.2 Self-Correcting 실행

```bash
python modules/module7_offline_corrector.py \
  --caldera-dir data/processed/20251203_163450/caldera \
  --operation-logs operation_logs.json \
  --env templates/environment_description.md \
  --output caldera_corrected
```

**출력 예시:**
```
======================================================================
M7: Offline Self-Correcting Engine
======================================================================

[Loaded] 36 abilities
[Loaded] Operation: My Operation
[Stats] Total: 36, Success: 27, Failed: 9

[Correction Phase] 9 failures

  [Web Login Attempt]
    Failure Type: missing_env
    Fixing with LLM...
    [OK] Fixed: $url = "http://192.168.1.100/admin"; Invoke-WebRequest -Uri $url...

  [Credential Dump]
    Failure Type: caldera_constraint
    Fixing with LLM...
    [OK] Fixed: $mimikatzPath = "C:\...\mimikatz.exe"; & $mimikatzPath "priv...

  ...

[OK] Corrected abilities saved to: caldera_corrected/abilities_corrected.yml
[OK] Correction report saved to: caldera_corrected/correction_report.json

======================================================================
[SUCCESS] Corrected 7/9 abilities
======================================================================
```

**생성된 파일:**
- `caldera_corrected/abilities_corrected.yml` - 수정된 Abilities
- `caldera_corrected/correction_report.json` - 수정 내역 보고서

---

## Step 5: 수정된 Abilities를 Caldera 서버로 복사

```bash
# 로컬 → Caldera 서버
scp caldera_corrected/abilities_corrected.yml user@caldera-server:~/caldera_corrected/
```

---

## Step 6: 수정된 Abilities 업로드 및 재실행 (Caldera 서버)

### 6.1 기존 Abilities/Adversary 삭제 (선택사항)

```bash
python delete_from_caldera.py data/processed/20251203_163450/caldera/uploaded_ids.yml
```

### 6.2 수정된 Abilities만 업로드

수정된 abilities를 Caldera에 업로드하려면, `adversaries.yml`도 함께 복사해야 합니다:

```bash
# 로컬에서 adversaries.yml도 복사
cp data/processed/20251203_163450/caldera/adversaries.yml caldera_corrected/

# Caldera 서버로 전송
scp caldera_corrected/adversaries.yml user@caldera-server:~/caldera_corrected/
```

**Caldera 서버에서 업로드:**
```bash
python upload_to_caldera.py --caldera-dir caldera_corrected/
```

### 6.3 새 Operation 실행

Caldera 웹 UI에서 새로운 Operation을 생성하고 실행합니다 (Step 1.2와 동일).

---

## 추가 옵션

### Operation ID 찾기

Caldera API로 최근 Operation ID 조회:

```bash
curl http://localhost:8888/api/v2/operations -H "KEY: ADMIN123" | jq '.[] | {id, name, state}'
```

### 여러 번 반복

실패한 Ability가 다시 발생하면 Step 2~6을 반복합니다:
- 새 Operation 실행 → 로그 수집 → 로컬 수정 → 재업로드 → 재실행

---

## 파일 구조

```
프로젝트/
├── fetch_operation_logs.py              # [Caldera 서버] 로그 수집
├── modules/
│   └── module7_offline_corrector.py     # [로컬] Self-Correcting
├── templates/
│   └── environment_description.md       # 환경 설명 파일
├── data/processed/20251203_163450/
│   └── caldera/
│       ├── abilities.yml                # 원본 Abilities
│       └── adversaries.yml              # 원본 Adversary
├── operation_logs.json                  # [수집] Operation 실행 로그
└── caldera_corrected/                   # [생성] 수정 결과
    ├── abilities_corrected.yml          # 수정된 Abilities
    └── correction_report.json           # 수정 보고서
```

---

## 문제 해결

### Q1: Operation 로그에 실패한 Ability가 없다면?

- Operation이 완전히 성공한 경우입니다
- Self-Correcting이 필요 없습니다

### Q2: LLM 수정이 제대로 안 된다면?

- `templates/environment_description.md`에 더 상세한 정보 추가
- `correction_report.json`에서 어떤 유형의 실패인지 확인
- `UNRECOVERABLE` 타입은 수정 불가능 (도구 미설치 등)

### Q3: Anthropic API 키가 없다면?

- `.env` 파일에 `ANTHROPIC_API_KEY=...` 추가
- [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급

---

## 요약 명령어

```bash
# Caldera 서버
python fetch_operation_logs.py --operation-id <op_id> --output operation_logs.json

# 로컬
python modules/module7_offline_corrector.py \
  --caldera-dir data/processed/20251203_163450/caldera \
  --operation-logs operation_logs.json \
  --env templates/environment_description.md \
  --output caldera_corrected

# Caldera 서버
python upload_to_caldera.py --caldera-dir caldera_corrected/
```
