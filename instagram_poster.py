from playwright.sync_api import sync_playwright
import time, os

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_session.json")

def check_session() -> bool:
    if not os.path.exists(SESSION_FILE):
        print("[오류] instagram_session.json 없음.")
        return False
    return True

def post_reel(video_path: str, caption: str) -> bool:
    if not check_session():
        return False
    if not os.path.exists(video_path):
        print(f"[오류] 영상 없음: {video_path}")
        return False

    abs_video = os.path.abspath(video_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://www.instagram.com/", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(4)
            page.screenshot(path="ig_1_loaded.png")

            if "login" in page.url or "accounts" in page.url:
                print("[오류] 세션 만료")
                return False

            # "+" New post 버튼 클릭 (SVG aria-label 기반)
            result = page.evaluate("""() => {
                const svgs = document.querySelectorAll('svg[aria-label]');
                for (const svg of svgs) {
                    const label = svg.getAttribute('aria-label');
                    if (label === 'New post' || label === '새 게시물') {
                        const btn = svg.closest('a') || svg.closest('[role="button"]') || svg.parentElement;
                        if (btn) { btn.click(); return 'CLICKED:' + label; }
                    }
                }
                const links = document.querySelectorAll('a[href="/create/"]');
                if (links.length) { links[0].click(); return 'CLICKED:link'; }
                return 'NOT_FOUND';
            }""")
            print(f"[생성 버튼] {result}")
            time.sleep(3)
            page.screenshot(path="ig_2_menu.png")

            # 버튼 목록 로깅
            btns_debug = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"], [role="menuitem"], button, a'));
                return btns.map(b => b.textContent?.trim()).filter(t => t && t.length < 60).slice(0, 30);
            }""")
            print(f"[페이지 버튼 목록] {btns_debug}")

            # "Post" 타입 선택 — Instagram은 아이콘 label + 텍스트가 합쳐져 'PostPost' 형태로 나옴
            type_clicked = page.evaluate("""() => {
                const candidates = [
                    'Post', 'PostPost', '게시물', '게시물게시물',
                    'Reel', 'ReelReel', '릴스', '릴스릴스'
                ];
                const btns = Array.from(document.querySelectorAll('[role="menuitem"], [role="button"], a, li'));
                for (const btn of btns) {
                    const t = (btn.textContent?.trim() || '');
                    if (candidates.includes(t)) {
                        btn.click();
                        return 'CLICKED:' + t;
                    }
                }
                return 'NOT_FOUND';
            }""")
            print(f"[타입 선택] {type_clicked}")
            time.sleep(3)
            page.screenshot(path="ig_2b_after_type.png")

            # 타입 선택 후 버튼 목록
            btns_debug2 = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"], button'));
                return btns.map(b => b.textContent?.trim()).filter(t => t && t.length < 80).slice(0, 20);
            }""")
            print(f"[타입 선택 후 버튼] {btns_debug2}")

            # "Select from computer" 버튼 클릭 → file chooser 인터셉트
            print("[파일 업로드] Select from computer 클릭 시도...")
            try:
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    clicked = page.evaluate("""() => {
                        const candidates = [
                            'Select from computer', '컴퓨터에서 선택',
                            'Select From Computer', 'Select from Computer'
                        ];
                        const btns = Array.from(document.querySelectorAll('[role="button"], button, div, span'));
                        for (const btn of btns) {
                            const t = (btn.textContent?.trim() || '');
                            if (candidates.includes(t) || t.toLowerCase().includes('from computer') || t.includes('컴퓨터에서')) {
                                btn.click();
                                return 'CLICKED:' + t;
                            }
                        }
                        return 'NOT_FOUND';
                    }""")
                    print(f"[Select from computer] {clicked}")
                file_chooser = fc_info.value
                file_chooser.set_files(abs_video)
                print(f"[업로드] 파일 설정 완료: {abs_video}")
            except Exception as fe:
                print(f"[파일 chooser 실패] {fe}")
                page.screenshot(path="ig_error_upload.png")
                # fallback: hidden input 노출 시도
                page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    inputs.forEach(inp => {
                        inp.style.display = 'block';
                        inp.style.opacity = '1';
                        inp.style.position = 'static';
                        inp.removeAttribute('hidden');
                    });
                }""")
                time.sleep(0.5)
                file_input = page.locator('input[type="file"]').first
                if file_input.count() > 0:
                    file_input.set_input_files(abs_video)
                    print("[업로드] fallback hidden input 성공")
                else:
                    print("[오류] file input 없음 — 포기")
                    return False

            time.sleep(6)
            page.screenshot(path="ig_3_uploaded.png")

            # 비율 조정 팝업 OK
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                for (const btn of btns) {
                    const t = btn.textContent?.trim();
                    if (t === 'OK' || t === '확인') { btn.click(); return; }
                }
            }""")
            time.sleep(1)

            # Next / 다음 최대 3번
            for step in range(3):
                nexted = page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('[role="button"]'));
                    for (const btn of btns) {
                        const t = btn.textContent?.trim();
                        if (t === 'Next' || t === '다음') { btn.click(); return 'CLICKED'; }
                    }
                    return 'NOT_FOUND';
                }""")
                print(f"[다음 {step+1}] {nexted}")
                time.sleep(2)
                page.screenshot(path=f"ig_next{step+1}.png")
                if nexted == 'NOT_FOUND':
                    break

            # 캡션 입력
            cap_written = page.evaluate("""(caption) => {
                const areas = document.querySelectorAll('[aria-label*="caption"], [aria-label*="Write"], textarea, [contenteditable="true"]');
                for (const el of areas) {
                    const label = (el.getAttribute('aria-label') || '').toLowerCase();
                    const tag = el.tagName.toLowerCase();
                    if (label.includes('caption') || label.includes('write') || tag === 'textarea') {
                        el.focus();
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, caption);
                        return 'WRITTEN';
                    }
                }
                return 'NOT_FOUND';
            }""", caption)
            print(f"[캡션] {cap_written}")
            time.sleep(1)
            page.screenshot(path="ig_4_caption.png")

            # Share / 공유
            shared = page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('[role="button"]'));
                const shareBtns = btns.filter(b => {
                    const t = b.textContent?.trim();
                    return t === 'Share' || t === '공유';
                });
                if (!shareBtns.length) return 'NOT_FOUND';
                shareBtns[shareBtns.length - 1].click();
                return 'CLICKED:' + shareBtns.length;
            }""")
            print(f"[공유] {shared}")
            if shared == 'NOT_FOUND':
                print("[오류] Share 버튼 없음")
                return False

            # 업로드 완료 대기 (최대 60초 — 영상 서버 업로드 시간)
            print("[대기] 업로드 완료 대기 중...")
            for i in range(12):
                time.sleep(5)
                # "Sharing" 스피너가 사라지면 완료
                still_sharing = page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('[role="button"]'));
                    return btns.some(b => b.textContent?.trim() === 'Share' || b.textContent?.trim() === '공유');
                }""")
                page.screenshot(path=f"ig_5_sharing_{i}.png")
                if not still_sharing:
                    print(f"[완료] {(i+1)*5}초 후 업로드 완료 감지!")
                    break
                print(f"[대기] {(i+1)*5}초 경과... (Share 버튼 {'있음' if still_sharing else '없음'})")

            print("[완료] Instagram 릴스 게시 성공!")
            return True

        except Exception as e:
            print(f"[실패] {e}")
            try: page.screenshot(path="ig_error.png")
            except: pass
            return False
        finally:
            browser.close()
