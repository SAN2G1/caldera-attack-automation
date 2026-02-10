# ttps2 환경 설명

## 공통 환경 정보
- OS: Windows 10
- Shell: Windows PowerShell 5.1 (powershell.exe)
  - Invoke-WebRequest 사용 시 반드시 -UseBasicParsing 옵션 필요

## 공격자 서버(192.168.56.1:34444)

- api 설명
  - GET /mail?user=xxxx
    - 공격자가 획득한 이메일 주소로 피싱 메일을 보냄
  - GET /login?user=xxxx
    - 피싱 링크 클릭 이벤트 기록
    - 이후 공격자 서버에서 피해자 서버로 에이전트를 받고 실행
  - GET /agents/*
    - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
    - 초기 다운로드 위치는 C:\Users\Public\data\*
    - 목록
      - sandcat_ttps2.ps1
        - Caldera agent 실행파일
  - POST /upload
    - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
    - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---
## 피해자 서버(192.168.56.120)

- 웹 서버 구성
    - index.html
      - 기업 포털 메인 페이지
    - staff.html
      - 직원 이름, 부서, 직급
      - 알게된 이메일 주소
        - 홍길동: hong.gil.dong@victimcorp.com
        - 이영희: lee.young.hee@victimcorp.com
        - 김철수: kim.chul.su@victimcorp.com

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
    - 추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.

- Windows 기본 동작을 악용한 UAC bypass (fodhelper.exe) 사용하여 관리자 권한으로 sandcat_ttps2.ps1을 실행한다.