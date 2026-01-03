# ttps3 환경 설명

## 네트워크 구성

- 피해자 컴퓨터: 192.168.56.115 (Windows 10, IIS)

- 공격자 서버(192.168.56.1:34444)
  - api 설명
    - GET /agents/*
      - 필요한 스크립트 파일을 * 에 입력하여 파일을 다운받을 수 있음

    - POST /upload
      - 피해자 PC에서 수집한 데이터를 HTTP POST 요청을 통해 공격자 서버로 유출하기 위한 엔드포인트
      - multipart/form-data 및 raw binary 업로드를 모두 지원하도록 구성됨

---

## 악성 코드 실행
- Unquoted 서비스가 실행됨
- C:\Program Files\Vuln App\service.exe
- C:\에 Everyone 쓰기 권한이 부여되어있다.
- 1분마다 재시작 되도록 스케줄 되어있다.
- 공격자 서버에서 Program.exe를 다운받아 Unquoted 서비스를 이용하여 실행될 수 있도록 작업해야한다.

---

## 지속성 유지
- 시작 프로그램에 등록하여 자동실행 될 수 있도록 한다.

---

## 권한 상승

- 유효한 계정 정보를 활용해 관리자 권한으로 Program.exe을 실행한다.
- Username: administrator
- Password: P@ssw0rd123
- Start-Process with Credential을 시도한다.

---

## 계정 정보 접근

- 공격자 서버에서 Keylogger.ps1 을 다운받아 실행한다.

---

## 탐색

- 정보 수집시 너무 큰 범위를 탐색하지 않도록 한다.

- 유출 대상 파일 위치
    - C:\Users\Public\data\*
    - 유출 행위 시뮬레이션 목적의 더미 데이터가 존재함


---

## 시스템 내부 이동

- 이동식 매체를 이용한 시스템 내부 이동을 시뮬레이션한다.
- 공격자 서버에서 SimulatedUSB.ps1을 다운받아 실행한다.

---

## 정보 수집

- 공격자 서버에서 Keylogger.ps1 을 다운받아 실행한다.

---

## 데이터 유출

- 유출 대상 파일들을 압축해 공격자 서버로 전송한다.
- 암호화를 통한 유출도 시도한다.