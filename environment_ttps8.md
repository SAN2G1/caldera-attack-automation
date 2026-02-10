# ttps8 환경 설명

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
        - sandcat_ttps8.ps1
          - Caldera agent 실행파일

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---

## 거점 서버: 192.168.56.150 (Windows 10)
- 도메인: victimcorp.local (DC: 192.168.56.151)
- 기본 로그인: 로컬 계정 (ttps, Administrators 그룹 소속)

- Windows 기본 동작을 악용한 UAC bypass (fodhelper.exe) 사용하여 관리자 권한으로 sandcat_ttps8.ps1을 실행

- VSS 스냅샷 생성됨 (Volume: C:\)
- LSASS 메모리 덤프 대상

- 유출 대상 파일 위치
    - C:\Users\Public\data\*

- 랜섬노트 생성 위치: C:\Users\Public\data\

---

## Domain Controller: 192.168.56.151 (Windows Server)
- 탈취한 Domain Admin 계정 정보
    - username: VICTIMCORP\Administrator
    - password: P@ssw0rd!2020
- WinRM 활성화
- VSS 스냅샷 생성됨 (Volume: C:\)
- LSASS 메모리 덤프 대상

- 유출 대상 파일 위치
    - C:\Users\Public\data\*

- 랜섬노트 생성 위치: C:\Users\Public\data\

---

## 도메인 클라이언트: 192.168.56.152 (Windows 10)
- 기본 로그인: VICTIMCORP\user1 / User1234!
- WinRM 활성화
- VSS 스냅샷 생성됨 (Volume: C:\)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*

- 랜섬노트 생성 위치: C:\Users\Public\data\
