# ttps4 환경 설명

## 네트워크 구성

- 웹 서버(DMZ): 192.168.56.110 (Windows 10, IIS)
- 내부망: 192.168.56.110 (Windows 10)

- 공격자 서버: 192.168.56.1:34444

---

## 피해자 서버(192.168.56.110)

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

## 공격자 서버(192.168.56.1:34444)

- api 설명
    - GET /login?user=xxxx
      - 피싱 링크 클릭 이벤트 기록
    - GET /agents/sandcat.ps1
      - Caldera sandcat.ps1 에이전트 파일 다운로드
    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨
---

## 에이전트 설치
- Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File C:\Windows\Temp\sandcat.ps1' -WindowStyle Hidden; Write-Output "Sandcat started"
- 공격자 서버를 통해 다운 후 백그라운드에서 설치
---

## 공격 흐름

1. 피해자가 기업 웹 서버에 접속
2. 직원 디렉터리를 통해 이메일 주소 패턴 확인
3. 보안 정책 페이지를 통해 MFA 적용 여부 확인
4. 공격자가 피싱 메일을 발송했다고 가정
5. 피해자가 피싱 링크를 클릭하여 공격자 서버에 접속
6. sandcat.ps1 에이전트 다운로드
7. Caldera 에이전트 설치 및 실행
8. 피해자 PC에서 내부 정보 및 파일 위치 정찰
9. 유출 대상 더미 데이터 확인 및 압축
10. 공격자 서버로 데이터 유출
