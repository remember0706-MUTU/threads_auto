"""로컬 디버깅용 - headless=False로 브라우저 화면 직접 확인"""
from playwright.sync_api import sync_playwright
import time, os

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")
TEXT = "테스트 포스팅입니다. #디버그"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(
        storage_state=SESSION_FILE,
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    print("1. threads.com 접속 중...")
    page.goto("https://www.threads.com", timeout=30000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    time.sleep(5)
    print(f"   URL: {page.url}")

    if "login" in page.url:
        print("   [오류] 세션 만료!")
        browser.close()
        exit()

    # contenteditable 초기 수
    cnt = page.locator('[contenteditable="true"]').count()
    print(f"2. 초기 contenteditable 수: {cnt}")

    # What's new? 클릭
    print("3. 'What's new?' 버튼 클릭...")
    page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('[role="button"]'));
        const btn = btns.find(b =>
            b.textContent.trim() === "What's new?" ||
            b.textContent.trim() === '새로운 소식이 있나요?'
        );
        if (btn) { console.log('버튼 찾음:', btn.textContent); btn.click(); }
        else console.log('버튼 못찾음');
    }""")
    time.sleep(3)

    cnt2 = page.locator('[contenteditable="true"]').count()
    print(f"4. 클릭 후 contenteditable 수: {cnt2}")

    # 텍스트 입력
    print("5. 텍스트 입력 중...")
    editable = page.locator('[contenteditable="true"]').last
    editable.wait_for(state="visible", timeout=8000)
    editable.click()
    time.sleep(0.5)
    editable.press_sequentially(TEXT, delay=50)
    time.sleep(2)

    # Post 버튼 상태 확인
    print("6. Post 버튼 찾기...")
    btns = page.locator('[role="button"]:has-text("Post"), [role="button"]:has-text("게시")')
    btn_count = btns.count()
    print(f"   Post 버튼 수: {btn_count}")
    for i in range(btn_count):
        b = btns.nth(i)
        print(f"   버튼[{i}]: visible={b.is_visible()}, enabled={b.is_enabled()}, text={b.inner_text()[:30]}")

    input("\n>>> 브라우저 화면 확인 후 Enter를 눌러 Post 클릭 시도...")

    # 마지막 Post 버튼 클릭
    post_btn = btns.last
    post_btn.click(force=True)
    print("7. Post 클릭 완료")
    time.sleep(5)

    cnt3 = page.locator('[contenteditable="true"]').count()
    print(f"8. 클릭 후 contenteditable 수: {cnt3} (줄었으면 성공)")

    input("\n>>> 최종 상태 확인 후 Enter를 눌러 종료...")
    browser.close()
