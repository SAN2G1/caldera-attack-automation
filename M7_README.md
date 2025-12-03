# M7: Self-Correcting Module

KISA TTPs → Caldera Adversary 파이프라인의 Self-Correcting 모듈

## 개요

M7 모듈은 Caldera에서 실행된 공격 시나리오의 실패한 Ability를 자동으로 감지하고 수정하여 재실행하는 시스템입니다.

### 목표

- **초기 성공률**: 76% (현재)
- **최종 성공률**: 85%+ (목표)
- **최대 재시도**: 3회/Ability
- **평균 수정 시간**: 30초/Ability 이내

## 모듈 구조

```
modules/
├── m7_models.py                      # 데이터 모델 (FailureType, ExecutionReport 등)
├── module7_1_caldera_executor.py     # Caldera API 실행 및 결과 수집
├── module7_2_failure_classifier.py   # 실패 유형 자동 분류
├── module7_3_env_collector.py        # Agent 환경 정보 수집
├── module7_4_ability_fixer.py        # LLM 기반 자동 수정
└── module7_self_correcting.py        # 전체 오케스트레이터

config/
└── classification_rules.yml          # 실패 분류 규칙

run_self_correcting.py                # 실행 스크립트
```

## 설치

필수 패키지가 이미 requirements.txt에 포함되어 있습니다:

```bash
pip install -r requirements.txt
```

추가 요구사항:
- Caldera 서버 실행 중
- Caldera Agent 배포 완료
- Anthropic API Key 설정 (.env 파일)

## 사용 방법

### 1. 기본 실행

```bash
python run_self_correcting.py \
  --caldera-dir data/processed/20251203_142900/caldera \
  --env templates/environment_description.md \
  --agent-paw <your-agent-paw>
```

### 2. 전체 옵션

```bash
python run_self_correcting.py \
  --caldera-dir data/processed/20251203_142900/caldera \
  --env templates/environment_description.md \
  --agent-paw <your-agent-paw> \
  --caldera-url http://localhost:8888 \
  --caldera-key ADMIN123 \
  --max-retries 3 \
  --output report.json
```

### 옵션 설명

| 옵션 | 필수 | 설명 | 기본값 |
|------|------|------|--------|
| `--caldera-dir` | O | Caldera 출력 디렉토리 (abilities.yml, adversaries.yml 포함) | - |
| `--env` | O | 환경 설명 파일 (*.md) | - |
| `--agent-paw` | O | Caldera Agent PAW (식별자) | - |
| `--caldera-url` | X | Caldera 서버 URL | http://localhost:8888 |
| `--caldera-key` | X | Caldera API 키 | ADMIN123 |
| `--max-retries` | X | Ability당 최대 재시도 횟수 | 3 |
| `--output` | X | 결과 보고서 JSON 파일 경로 | - |

## 실행 프로세스

1. **초기 실행**: Caldera에서 Adversary 실행
2. **결과 수집**: 실행 결과 분석
3. **실패 감지**: 실패한 Ability 식별
4. **실패 분류**: 5가지 유형으로 분류
   - SYNTAX_ERROR: 명령어 문법 오류
   - MISSING_ENV: 환경 정보 누락
   - CALDERA_CONSTRAINT: Caldera 제약사항
   - DEPENDENCY_ERROR: 권한 부족
   - UNRECOVERABLE: 복구 불가능
5. **환경 정보 수집**: Agent 정보 및 진단 명령어 실행
6. **LLM 수정**: Claude API로 Ability 자동 수정
7. **재실행**: 수정된 Ability 실행 (최대 3회)
8. **통계 생성**: 최종 보고서 작성

## 출력 예시

### 콘솔 출력

```
======================================================================
M7: Self-Correcting Engine
======================================================================

[Loaded] 36 abilities from data/processed/.../caldera/abilities.yml
[Loaded] Adversary: KISA TTP Adversary

[Initial Execution]
  ...

[Initial Results]
  Total: 36
  Success: 27
  Failed: 9
  Success Rate: 75.0%

[Correction Phase]
  Failed Abilities: 9

======================================================================
[Correcting] Web Login
======================================================================
  Failure Type: missing_env
  [Attempt 1/3]
    [OK] Ability fixed
    New Command: $url = "http://192.168.1.10/login"...
    [SUCCESS] Ability fixed and executed successfully

...

======================================================================
[Final Results]
  Initial Success Rate: 75.0%
  Final Success Rate: 88.9%
  Improvement: +13.9%
======================================================================
```

### JSON 보고서 (report.json)

```json
{
  "initial_stats": {
    "total_abilities": 36,
    "success": 27,
    "failed": 9,
    "success_rate": 0.75
  },
  "final_stats": {
    "total_abilities": 36,
    "success": 32,
    "failed": 4,
    "success_rate": 0.889
  },
  "correction_summary": {
    "total_corrections_attempted": 9,
    "successful_corrections": 5,
    "failed_corrections": 4,
    "avg_retries": 1.8,
    "correction_success_rate": 0.556
  },
  "corrections": [
    {
      "ability_id": "uuid-xxx",
      "ability_name": "Web Login",
      "failure_type": "missing_env",
      "attempts": 1,
      "success": true,
      "fixed_command": "$url = \"http://192.168.1.10/login\"...",
      "reason": ""
    }
  ]
}
```

## 설정 파일

### classification_rules.yml

실패 유형별 키워드 및 패턴 정의:

```yaml
syntax_error:
  keywords:
    - "syntax error"
    - "ParserError"
  patterns:
    - "line \\d+:"

missing_env:
  keywords:
    - "cannot find path"
    - "invalid URI"
  extractors:
    ip_address: "\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}"
    url: "https?://[\\w\\.\\-:]+"
```

## 주요 기능

### 1. 실패 유형 자동 분류

Rule-based 키워드 매칭으로 5가지 유형 분류:

- **SYNTAX_ERROR**: PowerShell 문법 오류
- **MISSING_ENV**: IP, URL, 경로 등 누락
- **CALDERA_CONSTRAINT**: 변수 공유 불가 등
- **DEPENDENCY_ERROR**: 권한 부족
- **UNRECOVERABLE**: 도구 미설치 등

### 2. 환경 정보 수집

Caldera API를 통한 Agent 정보 조회:

- Platform, Executors, Privilege
- Host, Username
- 진단 명령어 실행 (whoami, ipconfig 등)

### 3. LLM 기반 자동 수정

Claude Sonnet 4.5를 사용한 지능형 수정:

- 유형별 맞춤 Prompt
- 이전 실패 이력 학습
- Caldera 제약사항 준수
- PowerShell 5.1 호환

### 4. 재시도 로직

- 최대 3회 재시도
- 실패 이력 누적
- 성공 시 즉시 종료

## 제약사항

### PowerShell 제약

- PowerShell 5.1 호환 필수
- 단일 라인 명령어
- 변수 공유 불가

### Caldera 제약

- 각 Ability는 독립 프로세스
- 이전 Ability 변수 참조 불가
- Payload는 Caldera가 자동 배포

### API 제한

- Anthropic API rate limit
- 대용량 재시도 시 주의

## 트러블슈팅

### 1. Agent PAW를 모르는 경우

Caldera 웹 UI에서 확인:
1. Agents 탭 열기
2. Agent 선택
3. PAW 복사

또는 Caldera API:
```bash
curl http://localhost:8888/api/v2/agents -H "KEY: ADMIN123"
```

### 2. 환경 설명 파일 작성

`templates/environment_description.md` 참고:

```markdown
# 환경 설명

## 네트워크
- Target IP: 192.168.1.10
- Web URL: http://192.168.1.10/login

## 계정
- Username: admin
- Password: pass123

## Payload
- cmd.asp
- exploit.exe
```

### 3. Classification Rules 수정

`config/classification_rules.yml` 편집:

- 키워드 추가/제거
- 패턴 정규식 수정
- Extractor 추가

## 성능 최적화

### Token 사용량 절감

- Prompt 간소화
- 진단 명령어 최소화
- 재시도 횟수 조정

### 처리 속도

- **평균 실행 시간** (36 abilities 기준):
  - 초기 실행: ~5분
  - 수정 및 재시도: ~3분 (9개 실패)
  - 전체: ~8분

## 향후 개선 사항

- [ ] Linux/macOS 지원
- [ ] Batch 처리 (여러 Agent 동시)
- [ ] 수정 이력 DB 저장
- [ ] 웹 UI 대시보드
- [ ] 실시간 모니터링

## 라이선스

MIT License

## 관련 문서

- [M1-M6 파이프라인 README](README.md)
- [Caldera API 문서](https://caldera.readthedocs.io/)
- [Anthropic API 문서](https://docs.anthropic.com/)
