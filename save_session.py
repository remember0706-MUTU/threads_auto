from playwright.sync_api import sync_playwright
import os

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")

print("브라우저를 열겠습니다...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.threads.net/login")
    print("Threads 로그인 창이 열렸습니다. 로그인해주세요.")
    print("로그인 완료를 자동으로 감지합니다 (최대 5분)...")

    # 피드 요소가 나타날 때까지 대기 (로그인 완료 감지)
    try:
        page.wait_for_url(
            lambda url: ("threads.net" in url or "threads.com" in url) and "/login" not in url,
            timeout=300000
        )
        import time; time.sleep(3)
        context.storage_state(path=SESSION_FILE)
        print(f"\n[완료] 세션 저장됨: {SESSION_FILE}")
    except Exception as e:
        print(f"[오류] {e}")

    input("Enter 키로 창을 닫습니다...")
    browser.close()
