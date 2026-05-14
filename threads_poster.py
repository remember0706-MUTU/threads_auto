from playwright.sync_api import sync_playwright
import time, os

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")


def check_api_connection() -> bool:
    if not os.path.exists(SESSION_FILE):
        print("[오류] threads_session.json 없음.")
        return False
    print("[확인] 세션 파일 존재.")
    return True


def post_to_threads(text: str, image_url: str = None) -> bool:
    if len(text) > 500:
        text = text[:497] + "..."

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://www.threads.com", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(5)

            print(f"[URL] {page.url}")

            page.screenshot(path="screenshot_1_loaded.png", full_page=False)

            if "login" in page.url or "accounts" in page.url:
                print("[오류] 세션 만료")
                return False

            # "What's new?" 버튼 클릭
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const btn = btns.find(b =>
                    b.textContent.trim() === "What's new?" ||
                    b.textContent.trim() === '새로운 소식이 있나요?'
                );
                if (btn) btn.click();
            }""")
            time.sleep(2)

            page.screenshot(path="screenshot_2_after_click.png", full_page=False)

            editable = page.locator('[contenteditable="true"]').last
            editable.wait_for(state="visible", timeout=8000)
            editable.click()
            time.sleep(0.5)

            # 텍스트 입력
            editable.press_sequentially(text, delay=30)
            time.sleep(1.5)

            page.screenshot(path="screenshot_3_typed.png", full_page=False)

            # JavaScript로 정확히 "Post"/"게시" 버튼 찾아 클릭 (Post Options 등 제외)
            clicked = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const postBtns = btns.filter(b => {
                    const t = b.textContent.trim();
                    return t === 'Post' || t === '게시';
                });
                if (postBtns.length === 0) return 'NOT_FOUND';
                // 마지막 버튼 = compose 모달의 게시 버튼
                postBtns[postBtns.length - 1].click();
                return 'CLICKED:' + postBtns.length;
            }""")
            print(f"[게시] JS 클릭 결과: {clicked}")
            print("[게시] 클릭 완료")
            time.sleep(5)

            page.screenshot(path="screenshot_4_posted.png", full_page=False)

            after_post_count = page.locator('[contenteditable="true"]').count()
            if after_post_count > 0:
                print(f"[실패] compose 창 아직 열림 ({after_post_count}개)")
                return False

            print(f"[성공] {text[:50]}...")
            return True

        except Exception as e:
            print(f"[실패] {e}")
            try:
                page.screenshot(path="screenshot_error.png", full_page=False)
            except:
                pass
            return False
        finally:
            browser.close()
