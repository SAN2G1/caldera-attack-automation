# ttps11 환경 설명

## 중앙집중형 솔루션 관리 PC (192.168.56.210:8080)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함

- 공격자가 웹서버 코드를 탈취하여 다음 API를 발견함
    - POST /uploads/{파일명}
      - 업로드 위치: `C:\CentralManagement\uploads\{파일명}`
    - GET /uploads/{파일명}?cmd={명령}
      - 업로드된 웹셸 실행
      - `.aspx` 파일에 대해 `cmd` 파라미터로 시스템 명령 실행 가능
    - GET /api/createuser?user={사용자명}&pass={비밀번호}
      - 취약점: 인증 없이 관리자 계정 생성 가능
    - GET /api/login?user={사용자명}&pass={비밀번호}
      - 사용자 로그인 검증
    - GET /api/deploy/{파일명}
      - 하위 클라이언트(VM2)에 배포

---
## 중앙집중형 솔루션 하위 클라이언트 PC (192.168.56.211:8081)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
- 에이전트 전파 필요

---
## 공격자 서버 (192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps11.ps1
          - Caldera agent 실행파일
          - 칼데라 에이전트 실행
        - webshell.aspx
          - 웹셸 실행파일
        - PrintSpoofer64.exe
          - Print Spoofer 실행파일
        - vcruntime140.dll
          - Print Spoofer 실행파일에 필요한 라이브러리
        - screen_capture.ps1
          - 정보 수집을 위한 화면 캡처 스크립트, 정보 수집 후 C:\Users\Public\data\screenshot_*.png 에 저장

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨
      - 더미데이터를 유출해야함