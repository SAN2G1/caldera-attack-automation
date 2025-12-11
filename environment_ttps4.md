# ttps4 환경 설명

## 네트워크 구성

- 웹 서버(DMZ): 192.168.56.110 (Windows 10, IIS)
- 내부망: 192.168.56.110 (Windows 10, SMB 활성화)
- Caldera server: 192.168.56.1:34444 (파일 유출시)

---

## 피해자 서버

- 웹 서버 구성
    - index.html
      - 내부 포털 메인 페이지. 직원 디렉터리 및 보안정책 페이지로 이동.
    - staff.html
      - 직원 이름, 부서, 직급, 이메일 패턴: firstname.lastname@victimcorp.com
    - security.html
      - 비밀번호 정책
      - MFA 적용 기준
      - OWA(Outlook Web Access) 사용 여부 등

- 유출 대상 파일 위치
    - C:\Users\Public\data\*

---

## 공격자 서버

- api 설명
    - GET /login?user=xxxx
      - 피싱 링크 클릭 이벤트 기록
    - GET /agents/<file>
      - Caldera sandcat.ps1 에이전트 파일 제공
    - POST /upload
      - 피해자 PC가 유출한 파일을 공격자 서버로 업로드하는 엔드포인트
---

## 에이전트 설치
- powershell -ExecutionPolicy Bypass -File sandcat.ps1

---

## 공격 흐름

피해자 서버에 접속 -> 이메일 확인 -> MFA 확인 -> 피싱메일을 보냈다고 가정 -> 피해자가 공격자 서버에 로그인 -> sandcat.ps1 다운로드 링크를 통해 다운 -> Caldera agent를 설치 -> 피해자 컴퓨터에서 정보 수집 -> 더미데이터 확인 -> 더미데이터 압축 -> 공격자 서버로 파일 유출
