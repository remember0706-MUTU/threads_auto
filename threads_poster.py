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
            print("[스크린샷] screenshot_1_loaded.png 저장")

            if "login" in page.url or "accounts" in page.url:
                print("[오류] 세션 만료 - 로그인 페이지로 리디렉션됨")
                return False

            # 초기 contenteditable 수 기록 (피드에 있는 것들)
            initial_editable_count = page.locator('[contenteditable="true"]').count()
            print(f"[디버그] 초기 contenteditable 수: {initial_editable_count}")

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
            print("[스크린샷] screenshot_2_after_click.png 저장")

            after_click_count = page.locator('[contenteditable="true"]').count()
            print(f"[디버그] 클릭 후 contenteditable 수: {after_click_count}")

            # 모달이 열렸다면 새로 추가된 contenteditable이 있을 것
            # last()로 가장 최근에 추가된 것 사용
            editable = page.locator('[contenteditable="true"]').last
            editable.wait_for(state="visible", timeout=8000)
            editable.click()
            time.sleep(0.5)

            # press_sequentially: Playwright가 keydown/keypress/keyup/input 이벤트 모두 발화
            editable.press_sequentially(text, delay=30)
            time.sleep(1.5)

            page.screenshot(path="screenshot_3_typed.png", full_page=False)
            print("[스크린샷] screenshot_3_typed.png 저장")

            # Post 버튼 찾기 및 클릭
            post_btn = page.locator('[role="button"]:has-text("Post"), [role="button"]:has-text("게시")').last
            post_btn.wait_for(state="visible", timeout=5000)
            time.sleep(0.5)
            post_btn.click(force=True)
            print("[게시] 클릭 완료")
            time.sleep(5)

            page.screenshot(path="screenshot_4_posted.png", full_page=False)
            print("[스크린샷] screenshot_4_posted.png 저장")

            # 성공 검증: compose 창이 닫혔는지 (contenteditable 수가 줄었는지)
            after_post_count = page.locator('[contenteditable="true"]').count()
            print(f"[디버그] 게시 후 contenteditable 수: {after_post_count}")

            if after_post_count >= after_click_count:
                print("[경고] compose 창이 아직 열려있음 - Ctrl+Enter 재시도")
                # Ctrl+Enter 재시도
                page.keyboard.press("Control+Enter")
                time.sleep(3)
                page.screenshot(path="screenshot_5_retry.png", full_page=False)
                print("[스크린샷] screenshot_5_retry.png 저장")
                retry_count = page.locator('[contenteditable="true"]').count()
                print(f"[디버그] 재시도 후 contenteditable 수: {retry_count}")
                if retry_count >= after_click_count:
                    print("[실패] 게시 실패 확인")
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
