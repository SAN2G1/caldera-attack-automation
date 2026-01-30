# ttps5 환경 설명

## 거점 PC: 192.168.56.130 (Windows 10)

- 기본 로그인: VICTIMCORP\user1
- Administrators 그룹 소속 (UAC bypass 가능)
- Windows 기본 동작을 악용한 UAC bypass (fodhelper.exe) 사용하여 관리자 권한으로 sandcat_ttps5.ps1을 실행

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

## 피해자 내부망 컴퓨터: 192.168.56.131 (Winodws 10, SMB Admin Shares 접근)
- 탈취한 Admin 계정 정보
    - usernaem: VICTIMCORP\itadmin
    - password: ITAdmin123!

---

## 공격자 서버 (192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps5.ps1
          - Caldera agent 실행파일

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨
