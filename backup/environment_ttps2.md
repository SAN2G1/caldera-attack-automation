# ttps2 환경 설명

## 네트워크 구성

- 웹 서버(DMZ): 192.168.56.120 (Windows 10, IIS)
- 내부망: 192.168.56.120 (Windows 10)

- 공격자 서버: 192.168.56.1:34444

---

## 피해자 서버(192.168.56.120)

- 웹 서버 구성
    - index.html
      - 기업 포털 메인 페이지, 직원 안내 페이지 및 업무 관련 자료 링크 포함
    - staff.html
      - 직원 이름, 부서, 직급, 이메일 패턴: firstname.lastname@victimcorp.com
    - security.html
      - 비밀번호 정책
      - MFA 적용 기준
      - OWA(Outlook Web Access) 사용 여부 등

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함

---

## 공격자 서버(192.168.56.1:34444)

- api 설명
  - GET /login?user=xxxx
    - 피싱 링크 클릭 이벤트 기록
    - 피싱 링크 클릭 또는 악성 문서 실행을 논리적으로 대체하는 트리거
    - 접근 시점, 사용자 식별 정보 로그 기록
  - GET /agents/sandcat_ttps2.ps1
    - Caldera sandcat_ttps2.ps1 에이전트 스크립트 다운로드
    - 피해자 PC가 직접 요청하여 저장
  - POST /upload
    - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
    - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---

## 에이전트 설치 및 권한 상승 흐름

### 에이전트 다운로드 (일반 사용자 권한)

- 피해자는 피싱 링크 클릭 후 공격자 서버에 접속했다고 가정
- sandcat_ttps2.ps1을 로컬에 다운로드

예시 동작:
- C:\Users\Public\sandcat_ttps2.ps1 에 저장

---

### UAC Bypass 환경 및 조건

- Windows 기본 UAC 설정 유지
- 사용자는 Administrators 그룹 소속
- UAC 프롬프트 우회 가능 환경

- 본 시나리오에서는:
  - 취약점 exploit이 아닌
  - Windows 기본 동작을 악용한 UAC bypass(fodhelper.exe) 사용

---

### 관리자 권한 sandcat 에이전트 실행

- UAC bypass 트리거 후
- High Integrity Level PowerShell 컨텍스트 확보

- sandcat_ttps2.ps1을 관리자 권한으로 실행

- 이후 실행되는 ability들은 관리자 권한을 전제로 동작하며, 서비스 등록, 보호된 경로 접근, 시스템 수준 정찰을 시뮬레이션한다.

---

## 공격 흐름 요약

1. 피해자가 내부 웹 서버 접속
2. 직원 정보 페이지를 통해 이메일 패턴 확인
3. 보안 정책 페이지를 통해 MFA 적용 여부 확인
4. 공격자가 피싱 메일을 발송했다고 가정
5. 피해자가 피싱 링크 클릭 → 공격자 서버 접속
6. sandcat_ttps2.ps1 다운로드
7. UAC bypass를 통해 관리자 권한 확보
8. 관리자 권한 sandcat 에이전트 설치
9. 시스템 및 내부 파일 위치 정찰
10. 유출 대상 더미 데이터 수집 및 압축
11. 공격자 서버로 데이터 업로드
