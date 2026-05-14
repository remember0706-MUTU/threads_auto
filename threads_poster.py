from playwright.sync_api import sync_playwright
import time, os

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")


def check_api_connection() -> bool:
    if not os.path.exists(SESSION_FILE):
        print("[오류] threads_session.json 없음. save_session.py를 먼저 실행하세요.")
        return False
    print("[확인] 세션 파일 존재. 자동 포스팅 준비 완료.")
    return True


def post_to_threads(text: str, image_url: str = None) -> bool:
    if len(text) > 500:
        text = text[:497] + "..."

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900}
        )
        page = context.new_page()

        try:
            page.goto("https://www.threads.com", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(5)

            if "login" in page.url:
                print("[오류] 세션 만료. save_session.py를 다시 실행하세요.")
                return False

            # 1단계: "What's new?" 버튼 클릭 → 글쓰기 모달 열기
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const btn = btns.find(b => b.textContent.trim() === "What's new?" || b.textContent.trim() === '새로운 소식이 있나요?');
                if (btn) btn.click();
            }""")
            time.sleep(2)

            # 2단계: contenteditable 입력창 대기 및 텍스트 입력
            editable = page.locator('[contenteditable="true"]').first
            editable.wait_for(state="visible", timeout=8000)
            editable.click()
            time.sleep(0.5)
            page.keyboard.type(text, delay=25)
            time.sleep(1.5)

            # 3단계: Post 버튼 JavaScript 클릭
            result = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const btn = btns.find(b => {
                    const t = b.textContent.trim();
                    return t === 'Post' || t === '게시';
                });
                if (btn) {
                    btn.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                    return '성공: ' + btn.textContent.trim();
                }
                return '없음';
            }""")
            print(f"[게시] {result}")
            time.sleep(4)
            print(f"[성공] 포스팅 완료: {text[:40]}...")
            return True

        except Exception as e:
            print(f"[실패] {e}")
            return False
        finally:
            browser.close()
