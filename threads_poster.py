from playwright.sync_api import sync_playwright
import time, os, base64

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

            # 스크린샷 저장 (디버깅용)
            page.screenshot(path="screenshot_1_loaded.png", full_page=False)
            print("[스크린샷] screenshot_1_loaded.png 저장")

            # 로그인 체크
            if "login" in page.url or "accounts" in page.url:
                print("[오류] 세션 만료 - 로그인 페이지로 리디렉션됨")
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

            # 스크린샷2
            page.screenshot(path="screenshot_2_after_click.png", full_page=False)
            print("[스크린샷] screenshot_2_after_click.png 저장")

            # contenteditable 대기 및 입력
            editable = page.locator('[contenteditable="true"]').first
            editable.wait_for(state="visible", timeout=8000)
            editable.click()
            time.sleep(0.5)
            page.keyboard.type(text, delay=25)
            time.sleep(1.5)

            # 스크린샷3
            page.screenshot(path="screenshot_3_typed.png", full_page=False)
            print("[스크린샷] screenshot_3_typed.png 저장")

            # Post 버튼 Playwright 네이티브 클릭 (force=True로 오버레이 무시)
            post_btn = page.locator('[role="button"]:has-text("Post"), [role="button"]:has-text("게시")').first
            post_btn.wait_for(state="visible", timeout=5000)
            post_btn.click(force=True)
            print(f"[게시] 네이티브 클릭 완료")
            time.sleep(4)

            # 스크린샷4
            page.screenshot(path="screenshot_4_posted.png", full_page=False)
            print("[스크린샷] screenshot_4_posted.png 저장")
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
