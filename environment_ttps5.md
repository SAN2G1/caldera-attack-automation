# ttps5 환경 설명

## 공통 환경 정보
- OS: Windows 10
- Shell: Windows PowerShell 5.1 (powershell.exe)
  - Invoke-WebRequest 사용 시 반드시 -UseBasicParsing 옵션 필요

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

---

## 거점 PC: 192.168.56.130 (Windows 10)
- 도메인: victimcorp.local (DC: 192.168.56.140)
- 기본 로그인: VICTIMCORP\user1 (로컬 Administrators 그룹 소속)

- Windows 기본 동작을 악용한 UAC bypass (fodhelper.exe) 사용하여 관리자 권한으로 sandcat_ttps5.ps1을 실행

- 유출 대상 파일 위치
    - C:\Users\Public\data\*

- 추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.

---

## 피해자 내부망 컴퓨터: 192.168.56.131 (Winodws 10, SMB Admin Shares 접근)
- 탈취한 Admin 계정 정보
    - username: VICTIMCORP\itadmin
    - password: ITAdmin123!
