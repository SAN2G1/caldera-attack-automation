# KISA TTP → Caldera Adversary Automation Pipeline

KISA 위협 인텔리전스 보고서(PDF)를 자동으로 분석하여 MITRE Caldera 공격 시뮬레이션용 Adversary Profile을 생성하는 파이프라인

## 개요

이 프로젝트는 KISA의 TTP(Tactics, Techniques, and Procedures) 보고서를 입력으로 받아 다음을 자동 생성합니다:

- **Abstract Attack Flow**: 환경 독립적인 추상 공격 흐름
- **Concrete Attack Flow**: 환경별 구체화된 공격 시나리오
- **MITRE ATT&CK Technique Mapping**: 각 단계에 대한 technique 자동 매핑
- **Caldera Abilities**: 실행 가능한 PowerShell 명령어
- **Caldera Adversary Profile**: 전체 공격 시나리오 통합 프로필
- **시각화**: 실행 순서, 의존성, Kill Chain 그래프

## 주요 기능

- ✅ **완전 자동화**: PDF → Caldera Adversary 전 과정 자동화
- ✅ **AI 기반 분석**: Claude Sonnet 4.5를 사용한 지능형 TTP 추출
- ✅ **MITRE ATT&CK 통합**: mitreattack-python 라이브러리 기반 technique 매핑
- ✅ **환경 맞춤형**: 특정 환경 설정에 맞춘 구체적 명령어 생성
- ✅ **Caldera 네이티브**: Caldera API 호환 YAML 형식 출력
- ✅ **시각화 지원**: Graphviz 기반 3종 시각화 + ATT&CK Navigator 연동

## 시스템 아키텍처

```
┌─────────────────────┐
│  KISA PDF Report    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 0           │  PDF → 텍스트 추출 (pypdf)
│  PDF Processing     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 1           │  환경 독립적 추상 flow 추출
│  Abstract Flow      │  - Attack goals
│  Extraction         │  - MITRE tactics
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 2           │  환경별 구체화 + 명령어 생성
│  Concrete Flow      │  - 환경 설명(MD) 결합
│  Generation         │  - PowerShell 명령어 생성
│                     │  - Top 3 technique 후보 추출
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 3           │  최종 technique 선택
│  Technique          │  - Top 3 → 최종 1개 선택
│  Selection          │  - 누락 명령어 일괄 생성
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 4           │  Caldera ability 생성
│  Ability Generator  │  - YAML 형식 변환
│                     │  - Payload/cleanup 추출
│                     │  - Adversary profile 생성
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Module 5           │  시각화
│  Visualization      │  - Execution order graph
│                     │  - Dependency graph
│                     │  - Tactic flow graph
└─────────────────────┘
```

## 모듈 상세

### Module 0: PDF Processing
**입력**: KISA TTP 보고서 (PDF)
**출력**: `step0_parsed.yml`

- pypdf 기반 텍스트 추출
- 페이지별 텍스트 구조화
- YAML 형식 저장

**실행**:
```bash
python modules/module0_pdf_processing.py data/raw/report.pdf data/processed/step0_parsed.yml
```

---

### Module 1: Abstract Flow Extraction
**입력**: `step0_parsed.yml`
**출력**: `step1_abstract_flow.yml`

- 2단계 추출 (Overview → Detailed Flow)
- 환경 독립적 attack goal 추출
- MITRE ATT&CK tactic 자동 매핑
- Kill chain 논리적 순서 재정렬

**주요 특징**:
- Chunk 기반 대용량 PDF 처리 (8K characters/chunk)
- 의존성 기반 goal 재정렬
- Command & Control tactic 제외 (Caldera가 제공)

**실행**:
```bash
python modules/module1_abstract_flow.py data/processed/step0_parsed.yml data/processed/step1_abstract_flow.yml
```

---

### Module 2: Concrete Flow Generation
**입력**: `step1_abstract_flow.yml`, `templates/environment_description.md`
**출력**: `step2_concrete_flow.yml`

- Abstract flow + 환경 설명 결합
- 환경별 구체적 공격 단계 생성
- **단일 라인 PowerShell 명령어 생성**
- MITRE ATT&CK technique 후보 3개 추출 (mitreattack-python)

**환경 설명 파일 (environment_description.md)**:
- 네트워크 구성 (IP, 포트, 서비스)
- 취약점 정보
- Caldera payload 파일 목록
- 인증 정보 (테스트 계정)

**명령어 생성 원칙**:
1. **Caldera payload 우선**: 환경 설명에 명시된 파일 사용
2. **네이티브 도구 활용**: PowerShell, cmd.exe 등 OS 기본 도구
3. **시뮬레이션 stub**: 도구 없을 시 echo 기반 시뮬레이션

**실행**:
```bash
python modules/module2_concrete_flow.py \
  data/processed/step1_abstract_flow.yml \
  templates/environment_description.md \
  data/processed/step2_concrete_flow.yml
```

---

### Module 3: Technique Selection
**입력**: `step2_concrete_flow.yml`
**출력**: `step3_technique_selected.yml`

- Top 3 technique 후보 → 최종 1개 선택
- 환경별 context 기반 AI 선택
- 누락된 명령어 일괄 생성 (fallback)

**선택 전략**:
1. **자동 선택**: 단일 후보 또는 점수 차이 50%+ 시
2. **AI 선택**: 환경 context 기반 최적 technique 선택
3. **Fallback**: 오류 시 top candidate 사용

**명령어 정리**:
- 탭 → 공백 변환
- 줄바꿈 제거
- 연속 공백 축소
- 단일 라인 보장

**실행**:
```bash
python modules/module3_technique_selection.py \
  data/processed/step2_concrete_flow.yml \
  data/processed/step3_technique_selected.yml
```

---

### Module 4: Caldera Ability Generator
**입력**: `step3_technique_selected.yml`
**출력**: `abilities.yml`, `adversaries.yml`

- Caldera YAML 형식 변환
- Payload 파일 자동 추출 및 매핑
- Adversary profile 생성 (atomic_ordering)
- UUID 기반 deterministic ID 생성

**생성 항목**:
- **abilities.yml**: 개별 ability 정의 (38개)
- **adversaries.yml**: Adversary profile (실행 순서 포함)

**Ability 구조**:
```yaml
- ability_id: UUID
  name: 공격 단계 이름
  description: 설명
  tactic: MITRE tactic
  technique_id: MITRE technique ID
  technique_name: Technique 이름
  singleton: true
  executors:
  - name: psh
    platform: windows
    command: PowerShell 명령어 (단일 라인)
    timeout: 20
    payloads:
    - payload_file.exe
    uploads: []
    cleanup: []
```

**실행**:
```bash
python modules/module4_ability_generator.py \
  data/processed/step3_technique_selected.yml \
  data/processed/caldera
```

---

### Module 5: Visualization
**입력**: `abilities.yml`, `adversaries.yml`
**출력**: 3종 시각화 (SVG/PNG)

**생성 그래프**:

#### 1. Execution Order Graph
- 전체 38개 ability 실행 순서
- Tactic별 색상 구분
- Technique ID 표시
- 범례 포함

#### 2. Dependency Graph
- Payload 파일 의존성 (노란색 노트)
- Cleanup 명령 관계 (점선)
- Ability 간 연결

#### 3. Tactic Flow Graph
- Kill chain 단순화 흐름
- Tactic 전환 표시
- 각 tactic의 ability 개수

**Tactic 색상 매핑**:
- Initial Access: 주황색
- Execution: 연한 주황색
- Privilege Escalation: 보라색
- Discovery: 파란색
- Lateral Movement: 밝은 파란색
- Collection: 청록색
- Exfiltration: 녹색

**실행**:
```bash
python modules/module5_visualization.py \
  data/processed/caldera/abilities.yml \
  data/processed/caldera/adversaries.yml \
  data/visualizations
```

**출력 파일**:
- `execution_order.svg/png`
- `dependencies.svg/png`
- `tactic_flow.svg/png`

---

### Module 5 (Alternative): ATT&CK Navigator
**입력**: `abilities.yml`, `adversaries.yml`
**출력**: `attack_navigator.json`

- MITRE ATT&CK Navigator 레이어 생성
- Technique coverage heatmap
- Ability 상세 정보 포함 (comment)

**사용 방법**:
```bash
python modules/module5_attack_navigator.py \
  data/processed/caldera/abilities.yml \
  data/processed/caldera/adversaries.yml \
  data/processed/caldera/attack_navigator.json
```

**시각화**:
1. https://mitre-attack.github.io/attack-navigator/ 접속
2. "Open Existing Layer" → "Upload from local"
3. `attack_navigator.json` 업로드
4. Technique coverage 확인

---

## 설치

### 1. Python 환경 설정
```bash
# Python 3.8+ 필요
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
anthropic>=0.18.0
pypdf>=3.0.0
pyyaml>=6.0
mitreattack-python==3.0.6
graphviz>=0.20.0
```

### 3. Graphviz 설치 (시각화용)
- **Windows**: https://graphviz.org/download/ 에서 설치 후 PATH 추가
- **Linux**: `sudo apt-get install graphviz`
- **macOS**: `brew install graphviz`

### 4. API Key 설정
```bash
# .env 파일 생성
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

또는 `modules/config.py`에서 직접 설정:
```python
ANTHROPIC_API_KEY = "your_api_key_here"
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
```

---

## 사용 방법

### 전체 파이프라인 실행

**1단계별 실행**:
```bash
# Step 0: PDF 파싱
python modules/module0_pdf_processing.py \
  data/raw/kisa_report.pdf \
  data/processed/step0_parsed.yml

# Step 1: Abstract flow 추출
python modules/module1_abstract_flow.py \
  data/processed/step0_parsed.yml \
  data/processed/step1_abstract_flow.yml

# Step 2: Concrete flow 생성
python modules/module2_concrete_flow.py \
  data/processed/step1_abstract_flow.yml \
  templates/environment_description.md \
  data/processed/step2_concrete_flow.yml

# Step 3: Technique 선택
python modules/module3_technique_selection.py \
  data/processed/step2_concrete_flow.yml \
  data/processed/step3_technique_selected.yml

# Step 4: Caldera ability 생성
python modules/module4_ability_generator.py \
  data/processed/step3_technique_selected.yml \
  data/processed/caldera

# Step 5: 시각화
python modules/module5_visualization.py \
  data/processed/caldera/abilities.yml \
  data/processed/caldera/adversaries.yml \
  data/visualizations
```

**2. 자동화 스크립트 (선택)**:
```bash
# scripts/run_pipeline.sh 생성 후 실행
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh data/raw/report.pdf
```

---

## 프로젝트 구조

```
.
├── README.md                      # 본 문서
├── requirements.txt               # Python 의존성
├── modules/
│   ├── config.py                  # API key 설정
│   ├── module0_pdf_processing.py
│   ├── module1_abstract_flow.py
│   ├── module2_concrete_flow.py
│   ├── module3_technique_selection.py
│   ├── module4_ability_generator.py
│   └── module5_visualization.py
├── templates/
│   └── environment_description.md # 환경 설정 템플릿
├── data/
│   ├── raw/                       # 원본 PDF 파일
│   ├── processed/                 # 중간 산출물 (YAML)
│   │   └── caldera/               # Caldera 최종 출력
│   └── visualizations/            # 시각화 출력 (SVG/PNG)
├── scripts/
│   ├── upload_to_caldera.py       # Caldera API 업로드
│   └── delete_from_caldera.py     # Caldera API 삭제
└── docs/
    └── midterm_report.md          # 중간 보고서
```

---

## 환경 설정 가이드

### environment_description.md 작성 예시

```markdown
# ttps1 환경 설명

## 네트워크 구성

- 웹 서버(DMZ): 192.168.56.105 (Windows 10, IIS)
- 내부망: 192.168.56.106 (Windows 10, SMB 활성화)
- Caldera server: 192.168.56.1:8888

## 웹 애플리케이션

- 로그인: http://192.168.56.105/login_process.asp
  - 방식: POST 요청, Body 파라미터 `userid`, `password`
  - 계정: admin / P@ssw0rd!2020

- 파일 업로드: http://192.168.56.105/upload_handler.asp
  - 방식: POST 요청, multipart/form-data
  - 폼 필드 이름: `file`
  - 업로드 경로: /uploads/

## 취약점 및 Exploit

1. **ASP 파일 업로드 취약점**
   - 확장자 검증 없음
   - 업로드 후 실행 가능

2. **PrintSpoofer 권한 상승**
   - SeImpersonatePrivilege 권한 활용
   - 필요 파일: PrintSpoofer64.exe + vcruntime140.dll

3. **SMB Admin Shares 접근**
   - C$ 공유 접근 가능
   - 계정은 웹 애플리케이션과 동일

## Caldera Payload

- cmd.asp (웹셸)
- PrintSpoofer64.exe
- vcruntime140.dll
- deploy.ps1 (Caldera agent 배포 스크립트)

## 데이터 유출

- Caldera server 업로드 경로: /file/upload
- 방식: POST 요청, -InFile 파라미터 사용
```

---

## Caldera 통합

### Abilities 업로드
```bash
python scripts/upload_to_caldera.py \
  --server http://localhost:8888 \
  --apikey YOUR_API_KEY \
  --abilities data/processed/caldera/abilities.yml
```

### Adversary 업로드
```bash
python scripts/upload_to_caldera.py \
  --server http://localhost:8888 \
  --apikey YOUR_API_KEY \
  --adversary data/processed/caldera/adversaries.yml
```

### 삭제
```bash
python scripts/delete_from_caldera.py \
  --server http://localhost:8888 \
  --apikey YOUR_API_KEY \
  --adversary "KISA TTP Adversary"
```

---

## 출력 예시

### Tactic 분포 (Step 4 출력)
```
Tactic 분포:
  - collection: 4개
  - credential-access: 1개
  - defense-evasion: 4개
  - discovery: 14개
  - exfiltration: 3개
  - initial-access: 3개
  - lateral-movement: 3개
  - persistence: 2개
  - privilege-escalation: 4개
```

### Ability 예시
```yaml
- ability_id: bce5dfd5-f459-5b57-bf7a-0f5737f7daf4
  name: Web Application Login
  description: Authenticate to web application using compromised credentials
  tactic: initial-access
  technique_id: T1133
  technique_name: External Remote Services
  singleton: true
  executors:
  - name: psh
    platform: windows
    command: $body = @{userid='admin'; password='P@ssw0rd!2020'}; ...
    timeout: 20
    payloads: []
```

---

## 제약사항 및 주의사항

### PowerShell 제약
- **PowerShell 5.1 호환**: `-Form`, `-SkipCertificateCheck` 사용 불가
- **단일 라인 명령어**: 줄바꿈 없이 세미콜론으로 체인
- **변수 공유 불가**: 각 ability는 독립적으로 실행

### Caldera Payload
- 환경 설명에 명시된 파일만 자동 매핑
- Payload는 Caldera가 자동으로 agent 작업 디렉토리에 배치
- 다운로드 URL 불필요 (Caldera 자동 처리)

### API 제한
- Claude API rate limit 주의 (대용량 PDF 처리 시)
- Token 사용량: Step 2/3에서 집중 소모

---

## 트러블슈팅

### 1. "MITRE ATT&CK data not available"
**원인**: mitreattack-python 미설치 또는 데이터 파일 누락
**해결**:
```bash
pip install mitreattack-python==3.0.6
# enterprise-attack.json 다운로드
wget https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json
```

### 2. Graphviz 렌더링 오류
**원인**: Graphviz 실행 파일이 PATH에 없음
**해결**:
- Windows: 환경변수 PATH에 `C:\Program Files\Graphviz\bin` 추가
- Linux/macOS: `which dot` 확인 후 재설치

### 3. API Key 오류
**원인**: ANTHROPIC_API_KEY 미설정
**해결**:
```bash
export ANTHROPIC_API_KEY="your_key_here"
# 또는 .env 파일 생성
```

### 4. "No commands found in Step 3"
**원인**: Module 2에서 명령어 생성 실패
**해결**:
- `environment_description.md`에 충분한 정보 제공
- Module 3의 fallback 메커니즘이 자동으로 재생성

### 5. Tactic이 모두 'execution'으로 표시
**원인**: Module 4의 tactic 매핑 버그 (이미 수정됨)
**해결**: 최신 코드 사용 (`node.get('tactic')` 사용)

---

## 성능 최적화

### Token 사용량 절감
- Module 1: Chunk size 조정 (기본 8K)
- Module 2: 프롬프트 간소화
- Module 3: Auto-selection 활용 (점수 차이 50%+)

### 처리 속도
- **평균 실행 시간**:
  - Module 0: ~10초 (10페이지 PDF 기준)
  - Module 1: ~2분 (chunk 기반)
  - Module 2: ~3분 (노드 수에 비례)
  - Module 3: ~1분 (후보 선택)
  - Module 4: ~5초 (변환만)
  - Module 5: ~3초 (시각화)

---

## 향후 개선 사항

- [ ] 다국어 보고서 지원 (영문 KISA 보고서)
- [ ] Linux/macOS 명령어 생성 (현재 Windows/PowerShell만)
- [ ] Cleanup 명령어 자동 생성
- [ ] Technique sub-technique 지원
- [ ] Batch 처리 (여러 보고서 동시 처리)
- [ ] Web UI 개발

---

## 라이선스

MIT License

---

## 기여

이슈 및 Pull Request 환영합니다.

---

## 참고 자료

- [MITRE Caldera](https://github.com/mitre/caldera)
- [MITRE ATT&CK](https://attack.mitre.org/)
- [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
- [mitreattack-python](https://github.com/mitre-attack/mitreattack-python)
- [Claude API](https://docs.anthropic.com/)

---

## 연락처

프로젝트 관련 문의: [이슈 생성](https://github.com/YOUR_REPO/issues)
