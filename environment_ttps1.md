# ttps1 환경 설명

## 공통 환경 정보
- OS: Windows 10
- Shell: Windows PowerShell 5.1 (powershell.exe)
  - Invoke-WebRequest 사용 시 반드시 -UseBasicParsing 옵션 필요
  - executionpolicy : Bypass 필요

## 공격자 서버(192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps1.ps1
          - Caldera agent 실행파일
          - 초기 권한 상승용(PrintSpoofer)으로만 웹쉘을 거친 후, 이후 웹쉘 없이 새 에이전트 환경에서 직접 실행함
          - 측면 이동시에도 sandcat_ttps1.ps1을 이용
        - cmd.asp
          - 공격자 서버에서 다운로드해 웹 애플리케이션에 업로드하여 사용
          - cmd.asp?cmd={명령} 로 실행 가능
        - PrintSpoofer64.exe
          - Print Spoofer 실행파일
          - IIS AppPool\DefaultAppPool 권한으로 실행해야함
          - -c 옵션 뒤에 공백이 포함된 명령어를 넣을 때는 반드시 큰따옴표로 전체를 묶어야 함
        - vcruntime140.dll
          - Print Spoofer 실행파일에 필요한 라이브러리

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---
## IIS 웹 애플리케이션(192.168.56.105)

- 로그인: http://192.168.56.105/login_process.asp
  - 방식: POST 요청, Body 파라미터 `userid`, `password`
  - 계정: admin / P@ssw0rd!2020

- 파일 업로드: http://192.168.56.105/upload_handler.asp
  - 방식: POST 요청, RFC 2388 표준 multipart/form-data
  - 폼 필드 이름: `file`
  - 업로드 경로: /uploads/
  - PowerShell에서는 `System.Net.WebClient.UploadFile()` 사용 권장

## 피해자 서버(192.168.56.105)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함
    - 추가적인 정보 수집시 Users 폴더 하위만 탐색후 C:\Users\Public\data\* 에 저장한다.

---

## 내부망 SMB Admin Shares 접근 (192.168.56.106)
   - 계정: admin / P@ssw0rd!2020
   - C$ 공유 접근 가능