## 1️⃣ 전체 설계 방향 (tts2 단순화 원칙)

### 원본 ttps2의 특징

* 실제 악성코드 중심
* HWP, IE exploit, DLL injection, 서비스 등록 등 **불안정 요소 많음**
* 권한상승이 후반부 핵심 역할

### 단순화 목표

* **공격 논리만 유지**
* “성공 여부가 명확히 판별되는 지점”만 남김
* 실제 exploit 대신:

  * 정적 웹
  * API 호출
  * UAC bypass **단일 성공 이벤트**

---

## 2️⃣ 공격자 서버 (Attacker Server)

👉 **기본 구조는 ttps4와 동일하게 사용 가능**, 기능만 확장

### 기본 역할 (유지)

* Flask 기반 API 서버
* Caldera C2는 그대로 Caldera가 담당

### 유지할 엔드포인트

* `GET /login`

  * 피싱 클릭 / 방문 트리거
* `GET /agents/<file>`

  * sandcat.ps1 또는 dropper 전달
* `POST /upload`

  * 유출 데이터 수신

### ttps2에서 추가하면 좋은 기능 (선택)

* `GET /wateringhole`

  * “악성 웹사이트 방문” 시나리오용
  * 실제 exploit ❌, 방문 로그만 기록
* `POST /uac_result`

  * fodhelper 기반 UAC bypass **성공 여부 보고용**
  * 예: `{ "result": "success", "method": "fodhelper" }`

> ⚠️ 실제 IE exploit, HWP exploit은 **절대 구현하지 않음**

---

## 3️⃣ 피해자 환경 – 웹 서버 (IIS, 정적)

### 목적

* “정찰 → 타겟 선정 → 공격 유도” 논리를 설명하기 위한 **정보 노출 지점**

---

### 📄 필수 페이지 구성 (권장)

#### 1️⃣ `index.html`

* 내부 포털 메인
* 링크:

  * 직원 디렉터리
  * 보안 정책
  * 외부 협력사 링크 (watering hole 설명용)

---

#### 2️⃣ `staff.html`

* 직원 이름 / 부서
* **이메일 패턴 명시**

  * `firstname.lastname@victimcorp.com`
* → **Recon → Phishing 타겟 선정 논리 충족**

---

#### 3️⃣ `security.html`

* 보안 정책 요약

  * MFA 적용 여부
  * 외부 메일 경고 문구
* “MFA 있음 → UAC bypass 필요” 논리 연결

---

#### 4️⃣ `partners.html` (선택)

* 외부 사이트 링크
* watering hole 시나리오 설명용
* 실제 악성 없음

---

## 4️⃣ 피해자 시스템 환경 (Windows)

### 기본 조건

* Windows 10
* 일반 사용자 계정 + 로컬 Administrators 소속
* UAC **기본 활성화 상태**

### 반드시 준비할 것

* fodhelper.exe UAC bypass **가능한 빌드**
* Caldera agent 자동 실행 설정
* 더미 유출 파일:

  ```
  C:\Users\Public\data\
  ```

---

## 5️⃣ ttps2 단순화 시나리오 골격 (권장)

### 🔹 핵심 분기 포인트

> **“UAC bypass 성공 여부”**

---

### 전체 흐름 (논리 중심)

1. 웹 서버 접근 (정찰)
2. 직원 / 이메일 패턴 확인
3. 보안 정책 확인 (MFA 존재 인식)
4. 공격자 서버(피싱 or watering hole) 접속
5. sandcat / dropper 다운로드
6. **UAC bypass 시도**
7. ✔ 성공 → 관리자 권한 획득
8. 관리자 권한 기반 정찰 수행
9. 더미 데이터 수집
10. 공격자 서버로 업로드

---

## 6️⃣ 권한상승(UAC bypass)을 이렇게 녹이면 좋다

### 구현 방식 (훈련용)

* fodhelper.exe 레지스트리 hijack
* 실제 exploit ❌
* **성공 여부만 판별**

### 판별 기준

* `whoami /groups` 결과
* `High Mandatory Level` 확인
* 결과를 공격자 서버로 POST

---