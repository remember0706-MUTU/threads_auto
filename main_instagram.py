import sys, os, requests, tempfile
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from quote_generator import generate_quote_content, get_today_category
from image_fetcher import search_pexels_image
from reels_creator import create_reels_video
from instagram_poster import post_reel


def run_instagram_reels() -> bool:
    print("\n" + "="*50)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Instagram Reels 시작")
    print("="*50)

    quote = generate_quote_content()
    korean_text = quote["text"]
    english_text = quote.get("text_en", "")
    category = get_today_category()
    print(f"[콘텐츠] 카테고리: {category}")

    # Pexels 이미지
    image_path = None
    image_info = search_pexels_image(category)
    if image_info:
        try:
            resp = requests.get(image_info["url"], timeout=15)
            resp.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(resp.content)
            tmp.close()
            image_path = tmp.name
            print(f"[이미지] 다운로드 완료 ({len(resp.content)//1024}KB)")
        except Exception as e:
            print(f"[이미지] 실패: {e}")

    # 릴스 영상 생성
    video_path = "reels_output.mp4"
    bgm_path = "bgm.mp3" if os.path.exists("bgm.mp3") else None
    print("[영상] 생성 중... (30~60초 소요)")
    create_reels_video(korean_text, image_path, video_path, bgm_path, duration=18, text_en=english_text)

    # 인스타그램 게시
    success = post_reel(video_path, korean_text)

    # 정리
    for f in [image_path, video_path]:
        if f and os.path.exists(f):
            os.unlink(f)

    if success:
        print("[완료] Instagram Reels 게시 성공!")
    else:
        print("[실패] Instagram Reels 게시 실패")
    print("="*50)
    return success


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "session":
        import subprocess
        subprocess.run([sys.executable, "save_instagram_session.py"])
    else:
        ok = run_instagram_reels()
        if not ok:
            sys.exit(1)
