# ttps1 환경 설명

## 공격자 서버(192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps1.ps1
          - Caldera agent 실행파일
          - 웹쉘로 칼데라 에이전트를 실행한 뒤에는 웹쉘을 이용하지 않음
          - 측면 이동시에도 sandcat_ttps1.ps1을 이용
        - cmd.asp
          - cmd.asp?cmd={명령} 로 실행 가능
        - PrintSpoofer64.exe
          - Print Spoofer 실행파일
        - vcruntime140.dll
          - Print Spoofer 실행파일에 필요한 라이브러리

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---
## 웹 애플리케이션(192.168.56.105)

- 로그인: http://192.168.56.105/login_process.asp
  - 방식: POST 요청, Body 파라미터 `userid`, `password`
  - 계정: admin / P@ssw0rd!2020

- 파일 업로드: http://192.168.56.105/upload_handler.asp
  - 방식: POST 요청, multipart/form-data
  - 폼 필드 이름: `file`
  - 업로드 경로: /uploads/

## 피해자 서버(192.168.56.105)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
    - 추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.

---

## 내부망 SMB Admin Shares 접근 (192.168.56.106)
   - 계정: admin / P@ssw0rd!2020
   - C$ 공유 접근 가능