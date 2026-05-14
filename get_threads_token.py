# =============================================
# Threads OAuth 자동 토큰 발급 스크립트
# =============================================

import http.server
import threading
import webbrowser
import requests
import urllib.parse
import json
import sys

THREADS_APP_ID = "1957706824830623"
THREADS_APP_SECRET = "958b5c191c8175fe6e9166f3789709af"
REDIRECT_URI = "http://localhost:8080/"
SCOPE = "threads_basic,threads_content_publish"

auth_code = None

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>✅ 인증 완료! 이 창을 닫아도 됩니다.</h2>".encode("utf-8"))
            print(f"\n[인증 코드 수신] {auth_code[:20]}...")
        elif "error" in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Error: {params}".encode())
            print(f"[오류] {params}")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Waiting for OAuth callback...")

    def log_message(self, format, *args):
        pass  # 로그 출력 억제


def exchange_code_for_token(code):
    """단기 토큰 발급"""
    print("[토큰 교환 중...]")
    resp = requests.post(
        "https://graph.threads.net/oauth/access_token",
        data={
            "client_id": THREADS_APP_ID,
            "client_secret": THREADS_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=15
    )
    data = resp.json()
    if "access_token" in data:
        return data["access_token"], data.get("user_id")
    else:
        print(f"[단기 토큰 오류] {data}")
        return None, None


def get_long_lived_token(short_token):
    """장기 토큰으로 교환 (60일)"""
    print("[장기 토큰 교환 중...]")
    resp = requests.get(
        "https://graph.threads.net/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": THREADS_APP_SECRET,
            "access_token": short_token,
        },
        timeout=15
    )
    data = resp.json()
    if "access_token" in data:
        return data["access_token"]
    else:
        print(f"[장기 토큰 오류] {data}")
        return short_token


def save_to_config(token, user_id):
    """config.py에 토큰 자동 저장"""
    config_path = "config.py"
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        'THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")',
        f'THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "{token}")'
    )
    content = content.replace(
        'THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "")',
        f'THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "{user_id}")'
    )

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[저장 완료] config.py 업데이트됨")
    print(f"  User ID: {user_id}")
    print(f"  Token: {token[:30]}...")


def main():
    global auth_code

    # 1. 로컬 서버 시작
    server = http.server.HTTPServer(("localhost", 8080), OAuthHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print("[서버 시작] localhost:8080 대기 중...")

    # 2. OAuth 인증 URL 열기
    auth_url = (
        f"https://www.threads.net/oauth/authorize"
        f"?client_id={THREADS_APP_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={SCOPE}"
        f"&response_type=code"
    )
    print(f"[브라우저 열기] Threads 인증 페이지로 이동합니다...")
    webbrowser.open(auth_url)

    # 3. 코드 수신 대기 (최대 120초)
    print("[대기 중] 브라우저에서 Threads 계정으로 승인해주세요...")
    import time
    for _ in range(120):
        if auth_code:
            break
        time.sleep(1)

    server.shutdown()

    if not auth_code:
        print("[오류] 인증 코드를 받지 못했습니다.")
        sys.exit(1)

    # 4. 토큰 교환
    short_token, user_id = exchange_code_for_token(auth_code)
    if not short_token:
        sys.exit(1)

    # 5. 장기 토큰 교환
    long_token = get_long_lived_token(short_token)

    # 6. config.py 저장
    save_to_config(long_token, user_id)
    print("\n✅ 완료! 이제 test_post.bat으로 테스트하세요.")


if __name__ == "__main__":
    main()
