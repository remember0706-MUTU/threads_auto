# =============================================
# 쓰레드 자동 포스팅 - 비트코인 ICT 브리핑
# =============================================

import sys
import schedule
import time
import os
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

from config import POST_TIMES
from bitcoin_fetcher import get_bitcoin_price
from content_generator import generate_threads_content
from threads_poster import post_to_threads, check_api_connection


def run_post():
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 포스팅 시작")
    print(f"{'='*50}")

    if not check_api_connection():
        print("[중단] 세션 파일 없음")
        return

    # 1. 비트코인 가격 수집
    btc = get_bitcoin_price()
    if not btc:
        print("[중단] 비트코인 가격 수집 실패")
        return

    # 2. ICT 분석 콘텐츠 생성
    content = generate_threads_content(btc)

    # 3. 포스팅
    success = post_to_threads(text=content["text"])

    if success:
        print(f"[완료] 포스팅 성공!")
        log_post(btc, content)
    else:
        print("[실패] 포스팅 실패")

    print(f"{'='*50}\n")


def log_post(btc, content):
    with open("post_log.txt", "a", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now}] BTC ${btc['usd']:,.0f} ({btc['change_24h']:+.2f}%)\n")
        f.write(f"{content['text'][:80]}...\n")
        f.write("-" * 40 + "\n")


def main():
    print("쓰레드 비트코인 ICT 브리핑 자동화 시작!")
    print(f"포스팅 시간: {POST_TIMES}")
    check_api_connection()

    for t in POST_TIMES:
        schedule.every().day.at(t).do(run_post)
        print(f"[스케줄] 매일 {t} 예약됨")

    print("\n[대기 중] 종료하려면 Ctrl+C\n")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    if not os.path.exists("threads_session.json"):
        print("[오류] threads_session.json 없음! save_session.py를 먼저 실행하세요.")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("[테스트] 즉시 실행...")
        run_post()
    else:
        main()
