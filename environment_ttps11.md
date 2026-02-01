# ttps11 환경 설명

## 공격자 서버 (192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps11.ps1
          - Caldera agent 실행파일
          - 웹쉘로 칼데라 에이전트를 실행한 뒤에는 웹쉘을 이용하지 않음
          - 측면 이동시에도 sandcat_ttps11.ps1을 이용
        - upload-webshell.ps1
          - webshell.asp를 공격자 서버에서 다운로드하여 192.168.56.210/upload.asp로 업로드하는 스크립트
          - multipart/form-data 형식으로 자동 업로드
        - webshell.asp
          - webshell.asp?c={명령} 로 실행 가능
        - PrintSpoofer64.exe
          - Print Spoofer 실행파일
        - vcruntime140.dll
          - Print Spoofer 실행파일에 필요한 라이브러리
        - screen_capture.ps1
          - 정보 수집을 위한 화면 캡처 스크립트, 정보 수집 후 C:\Users\Public\data\screenshot_*.png 에 저장

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---
## 중앙집중형 솔루션 관리 PC (192.168.56.210)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
    - 추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.

- 공격자가 발견한 취약한 API
    - POST /upload.asp
      - multipart/form-data 형식 필수
      - 파일 필드명: "file"
      - Content-Disposition 헤더에 filename 포함 필요
      - boundary 구분자 필수
      - 업로드 위치: `C:\inetpub\wwwroot\uploads\{파일명}`
    
    - GET /api.asp?action=createuser&user={사용자명}&pass={비밀번호}
      - 관리자 계정 생성
      - 인증 없음
      - 취약점: IIS 권한 제약으로 파일 쓰기 실패 가능 (권한 상승 필요)
    
    - POST /deploy.asp
      - filename 파라미터로 파일명 전달
      - uploads 폴더의 파일을 deploy 폴더로 복사
      - 하위 클라이언트(192.168.56.211:8081)에 HTTP 요청으로 배포
      - 인증 없음

---
## 중앙집중형 솔루션 하위 클라이언트 PC (192.168.56.211:8081)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
    추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.