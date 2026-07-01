import sys
import schedule
import time
import os
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from config import POST_TIMES
from bitcoin_fetcher import get_bitcoin_price
from content_generator import generate_threads_content
from quote_generator import generate_quote_content, get_today_category
from image_fetcher import search_pexels_image
from threads_poster import post_to_threads, check_api_connection


def run_post():
    print("\n" + "="*50)
    print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] ICT 포스팅 시작")
    print("="*50)

    if not check_api_connection():
        print("[중단] 세션 파일 없음")
        return

    btc = get_bitcoin_price()
    if not btc:
        print("[중단] 비트코인 가격 수집 실패")
        return

    content = generate_threads_content(btc)
    success = post_to_threads(text=content["text"])

    if success:
        print("[완료] BTC ICT 포스팅 성공!")
        log_post(btc, content)
    else:
        print("[실패] BTC 포스팅 실패")

    print("="*50 + "\n")


def run_good_words():
    print("\n" + "="*50)
    print("[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] Good Words 포스팅 시작")
    print("="*50)

    if not check_api_connection():
        print("[중단] 세션 파일 없음")
        return

    quote = generate_quote_content()
    text_en = quote.get("text_en", "")
    full_text = quote["text"] + ("\n\n" + text_en if text_en else "")

    # 카테고리에 맞는 Pexels 이미지 검색
    category = get_today_category()
    image_info = search_pexels_image(category)
    image_url = image_info["url"] if image_info else None

    if image_url:
        print(f"[이미지] {category} 카테고리 이미지 준비 완료")
    else:
        print("[이미지] 이미지 없이 텍스트만 포스팅")

    success = post_to_threads(text=full_text, image_url=image_url)

    if success:
        print("[완료] Good Words 포스팅 성공!")
        log_quote(quote)
    else:
        print("[실패] Good Words 포스팅 실패")

    print("="*50 + "\n")


def log_post(btc, content):
    with open("post_log.txt", "a", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write("[" + now + "] BTC $" + str(btc["usd"]) + " (" + str(btc["change_24h"]) + "%)\n")
        f.write(content["text"][:80] + "...\n")
        f.write("-"*40 + "\n")


def log_quote(quote):
    with open("post_log.txt", "a", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write("[" + now + "] Good Words\n")
        f.write(quote["text"][:80] + "...\n")
        f.write("-"*40 + "\n")


def main():
    print("쓰레드 자동 포스팅 시작!")
    print("포스팅 시간: " + str(POST_TIMES))
    check_api_connection()

    for t in POST_TIMES:
        schedule.every().day.at(t).do(run_post)
        print("[스케줄] 매일 " + t + " 예약됨")

    print("\n[대기 중] 종료하려면 Ctrl+C\n")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    if not os.path.exists("threads_session.json"):
        print("[오류] threads_session.json 없음! save_session.py를 먼저 실행하세요.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_post()
    elif len(sys.argv) > 1 and sys.argv[1] == "good_words":
        run_good_words()
    else:
        main()
