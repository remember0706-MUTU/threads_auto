# =============================================
# Threads API 토큰 발급 확인 스크립트
# config.py에 토큰/ID 입력 후 실행
# =============================================

import requests
import sys

def verify_token(access_token: str, user_id: str):
    """토큰과 User ID가 올바른지 확인"""
    url = f"https://graph.threads.net/v1.0/{user_id}"
    params = {
        "fields": "id,username,threads_profile_picture_url,threads_biography",
        "access_token": access_token
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if "error" in data:
        print(f"[오류] {data['error']['message']}")
        return False
    print(f"[성공] @{data.get('username')} (ID: {data.get('id')})")
    print(f"  소개: {data.get('threads_biography', '없음')}")
    return True


def get_threads_user_id(access_token: str):
    """access_token으로 Threads User ID 자동 조회"""
    url = "https://graph.threads.net/v1.0/me"
    params = {
        "fields": "id,username",
        "access_token": access_token
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if "id" in data:
        print(f"[Threads User ID] {data['id']}  (@{data.get('username')})")
        return data["id"]
    else:
        print(f"[실패] {data}")
        return None


if __name__ == "__main__":
    token = input("Threads Access Token을 붙여넣으세요: ").strip()
    user_id = get_threads_user_id(token)
    if user_id:
        print(f"\nconfig.py에 아래 값을 입력하세요:")
        print(f'  THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "{token[:30]}...")')
        print(f'  THREADS_USER_ID = os.environ.get("THREADS_USER_ID", "{user_id}")')
