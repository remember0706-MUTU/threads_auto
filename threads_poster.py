from playwright.sync_api import sync_playwright
import time, os, requests, tempfile

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")


def check_api_connection() -> bool:
    if not os.path.exists(SESSION_FILE):
        print("[오류] threads_session.json 없음.")
        return False
    print("[확인] 세션 파일 존재.")
    return True


def download_image(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(resp.content)
        tmp.close()
        print(f"[이미지 다운로드] {tmp.name} ({len(resp.content)//1024}KB)")
        return tmp.name
    except Exception as e:
        print(f"[이미지 다운로드 오류] {e}")
        return None


def post_to_threads(text: str, image_url: str = None, reply_text: str = None) -> bool:
    if len(text) > 500:
        text = text[:497] + "..."
    if reply_text and len(reply_text) > 500:
        reply_text = reply_text[:497] + "..."

    image_path = None
    if image_url:
        image_path = download_image(image_url)

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

            # 로그인된 사용자명 추출 (프로필 링크에서)
            username = page.evaluate("""() => {
                const links = document.querySelectorAll('a[href^="/@"]');
                for (const link of links) {
                    const href = link.getAttribute('href');
                    if (href && /^\\/@[\\w.]+$/.test(href)) {
                        return href.slice(2);
                    }
                }
                return null;
            }""")
            print(f"[사용자] {username or '추출 실패'}")

            # "새로운 소식이 있나요?" 버튼 클릭
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

            # 텍스트 입력
            editable = page.locator('[contenteditable="true"]').last
            editable.wait_for(state="visible", timeout=8000)
            editable.click()
            time.sleep(0.5)
            editable.press_sequentially(text, delay=30)
            time.sleep(1.5)

            page.screenshot(path="screenshot_3_typed.png", full_page=False)

            # 이미지 첨부
            if image_path and os.path.exists(image_path):
                print("[이미지] 첨부 시도...")
                page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    inputs.forEach(i => { i.style.display = 'block'; i.style.opacity = '1'; });
                }""")
                time.sleep(0.5)

                file_input = page.locator('input[type="file"]').first
                if file_input.count() > 0:
                    file_input.set_input_files(image_path)
                    print("[이미지] 파일 설정 완료")
                    time.sleep(4)
                else:
                    page.evaluate("""() => {
                        const svgs = document.querySelectorAll('svg');
                        for (const svg of svgs) {
                            const label = svg.getAttribute('aria-label') || '';
                            if (label.includes('이미지') || label.includes('사진') || label.includes('Photo') || label.includes('Image')) {
                                const btn = svg.closest('[role="button"]') || svg.parentElement;
                                if (btn) { btn.click(); return; }
                            }
                        }
                    }""")
                    time.sleep(1)
                    file_input2 = page.locator('input[type="file"]').first
                    if file_input2.count() > 0:
                        file_input2.set_input_files(image_path)
                        print("[이미지] 아이콘 클릭 후 파일 설정 완료")
                        time.sleep(4)

                page.screenshot(path="screenshot_3b_image_attached.png", full_page=False)

            # 게시 버튼 클릭
            clicked = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const postBtns = btns.filter(b => {
                    const t = b.textContent.trim();
                    return t === 'Post' || t === '게시';
                });
                if (postBtns.length === 0) return 'NOT_FOUND';
                postBtns[postBtns.length - 1].click();
                return 'CLICKED:' + postBtns.length;
            }""")
            print(f"[게시] JS 클릭 결과: {clicked}")
            time.sleep(5)

            page.screenshot(path="screenshot_4_posted.png", full_page=False)

            after_post_count = page.locator('[contenteditable="true"]').count()
            if after_post_count > 0:
                print(f"[실패] compose 창 아직 열림 ({after_post_count}개)")
                return False

            print(f"[성공] {text[:50]}...")

            # 영어 답글 달기
            if reply_text:
                print("[답글] 영어 답글 시작...")
                time.sleep(3)

                # 내 프로필 페이지로 이동 — 첫 번째 포스트가 방금 올린 글
                profile_url = f"https://www.threads.com/@{username}" if username else "https://www.threads.com"
                print(f"[답글] 이동: {profile_url}")
                page.goto(profile_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                time.sleep(4)

                page.screenshot(path="screenshot_5_reply_page.png", full_page=False)

                # 첫 번째 포스트의 Reply 버튼 클릭
                replied = page.evaluate("""() => {
                    const svgs = document.querySelectorAll('svg[aria-label]');
                    for (const svg of svgs) {
                        const label = svg.getAttribute('aria-label');
                        if (label === 'Reply' || label === '답글' || label === '댓글' || label === 'Comment') {
                            const btn = svg.closest('[role="button"]') || svg.parentElement;
                            if (btn) {
                                btn.click();
                                return 'CLICKED:' + label;
                            }
                        }
                    }
                    return 'NOT_FOUND';
                }""")
                print(f"[답글] 버튼 클릭: {replied}")
                time.sleep(2)

                page.screenshot(path="screenshot_5b_reply_open.png", full_page=False)

                if 'NOT_FOUND' not in replied:
                    try:
                        reply_editor = page.locator('[contenteditable="true"]').last
                        reply_editor.wait_for(state="visible", timeout=8000)
                        reply_editor.click()
                        time.sleep(0.5)
                        # execCommand 방식 — 긴 텍스트도 누락 없이 한 번에 삽입
                        page.evaluate("""(text) => {
                            const editors = document.querySelectorAll('[contenteditable="true"]');
                            const editor = editors[editors.length - 1];
                            if (!editor) return;
                            editor.focus();
                            document.execCommand('selectAll', false, null);
                            document.execCommand('insertText', false, text);
                        }""", reply_text)
                        time.sleep(1.5)

                        page.screenshot(path="screenshot_5c_reply_typed.png", full_page=False)

                        reply_clicked = page.evaluate("""() => {
                            const btns = Array.from(document.querySelectorAll('[role="button"]'));
                            const postBtns = btns.filter(b => {
                                const t = b.textContent.trim();
                                return t === 'Post' || t === '게시' || t === 'Reply' || t === '답글';
                            });
                            if (postBtns.length === 0) return 'NOT_FOUND';
                            postBtns[postBtns.length - 1].click();
                            return 'CLICKED:' + postBtns.length;
                        }""")
                        print(f"[답글] 게시 클릭: {reply_clicked}")
                        time.sleep(4)

                        page.screenshot(path="screenshot_6_reply_posted.png", full_page=False)
                        print(f"[답글 완료] {reply_text[:50]}...")
                    except Exception as re:
                        print(f"[답글 오류] {re} (본문 포스팅은 성공)")
                else:
                    print("[답글 경고] 답글 버튼을 찾지 못했습니다 (본문 포스팅은 성공)")

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
            if image_path and os.path.exists(image_path):
                os.unlink(image_path)
                print("[이미지] 임시 파일 삭제 완료")
