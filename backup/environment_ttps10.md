# ttps10 환경 설명

## 피해자 PC (192.168.56.200)

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함

- 피해자가 뉴스 사이트를 클릭하여 악성 스크립트 다운로드 및 실행하는 것을 시뮬레이션 해야함
    - http://192.168.56.1:34444/news/article/1
    - 악성 PowerShell 스크립트 반환
    - IEX를 통해 메모리상에서 직접 실행해야함.

- Windows 기본 동작을 악용한 UAC bypass (fodhelper.exe) 사용하여 관리자 권한으로 sandcat_ttps10.ps1을 실행한다.

---
## 피해자 내부망 PC (192.168.56.201)

- PowerShell Invoke-Command를 사용하여 피해자 내부망 PC로 전파
- 탈취한 계정 정보
    - username: Administrator
    - password: P@ssw0rd!2020

---

## 공격자 서버 (192.168.56.1:34444)

- api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 공격자 서버에서 파일을 다운받을 수 있음
      - 초기 다운로드 위치는 C:\Users\Public\data\*
      - 목록
        - sandcat_ttps10.ps1
          - Caldera agent 실행파일
        - ttps10_malware.dll
          - LSA 프로세스에 주입되어 악성 행위를 수행하는 DLL 파일
        - Keylogger.ps1
          - 키로거 스크립트, 정보 수집 후 C:\Users\Public\data\keylog.txt 에 저장
        - screen_capture.ps1
          - 정보 수집을 위한 화면 캡처 스크립트, 정보 수집 후 C:\Users\Public\data\screenshot_*.png 에 저장

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨
      - 더미데이터를 유출해야함