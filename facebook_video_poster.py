import os
import requests


def post_video_to_facebook(video_path: str, caption: str) -> bool:
    page_id = os.environ["FB_PAGE_ID"]
    access_token = os.environ["FB_PAGE_ACCESS_TOKEN"]

    url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"

    with open(video_path, "rb") as f:
        files = {"source": f}
        data = {
            "description": caption,
            "access_token": access_token,
        }
        resp = requests.post(url, data=data, files=files, timeout=120)

    if resp.status_code == 200:
        result = resp.json()
        print(f"[Facebook] 영상 게시 성공: {result.get('id')}")
        return True
    else:
        print(f"[Facebook] 영상 게시 실패: {resp.status_code} {resp.text}")
        return False
