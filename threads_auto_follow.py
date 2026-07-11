import os
import time
from playwright.sync_api import sync_playwright

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")
JS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../threads_follow_script.js")

def main():
    if not os.path.exists(SESSION_FILE):
        print("\n[오류] threads_session.json 세션 파일이 존재하지 않습니다.")
        print("작업을 시작하기 전에 로그인 세션을 먼저 저장해야 합니다.")
        print("같은 폴더의 'save_session.bat' 파일을 더블 클릭하여 실행하거나,")
        print("터미널에서 'python save_session.py'를 실행하여 로그인을 완료해주세요.\n")
        return

    if not os.path.exists(JS_FILE):
        print(f"\n[오류] 자바스크립트 파일({JS_FILE})을 찾을 수 없습니다.\n")
        return

    # 주입할 JS 코드 로드
    with open(JS_FILE, "r", encoding="utf-8") as f:
        js_code = f.read()

    print("\n==================================================")
    print("스레드(Threads) 자동 '스하리' 댓글 & 팔로우 봇")
    print("==================================================")
    print("[준비] 세션 파일 로드 완료.")
    print("[준비] 브라우저(Chrome)를 실행하는 중...")
    
    with sync_playwright() as p:
        # 사용자가 실시간 동작을 볼 수 있도록 headless=False로 실행
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 브라우저 콘솔 출력을 파이썬 터미널에 연동하여 출력 (인코딩 오류 방지)
        import sys
        def safe_print(msg):
            try:
                enc = sys.stdout.encoding or 'utf-8'
                safe_text = msg.text.encode(enc, errors='replace').decode(enc)
                print(f"[브라우저 로그] {safe_text}")
            except Exception:
                pass
        page.on("console", safe_print)

        # 스레드 홈 피드(추천)로 이동
        home_url = "https://www.threads.net/"
        print(f"[이동] 스레드 홈 피드(추천)로 이동합니다: {home_url}")
        page.goto(home_url, timeout=60000)
        
        # 페이지 로딩 및 레이아웃 렌더링 대기
        time.sleep(6)

        # 로그인 만료 체크
        if "login" in page.url or "accounts" in page.url:
            print("\n[오류] 로그인 세션이 만료되었습니다.")
            print("다시 'save_session.bat'을 실행하여 로그인을 갱신해주세요.\n")
            browser.close()
            return

        # 디버깅용 스크린샷 캡처
        page.screenshot(path="debug_home.png")
        print("[디버그] 현재 화면 스크린샷을 'debug_home.png'에 저장했습니다.")

        # 피드 요소가 렌더링될 때까지 명시적 대기 (최대 15초)
        try:
            print("[대기] 피드 콘텐츠(article) 로딩을 대기 중...")
            page.wait_for_selector('article, [role="article"]', timeout=15000)
            print("[확인] 피드 콘텐츠 로딩 완료.")
        except Exception:
            print("[알림] 명시적 대기 타임아웃. 요소가 없거나 렌더링이 지연되고 있습니다.")

        # 임시 DOM 분석
        try:
            print("[디버그] DOM 구조를 분석합니다...")
            dom_analysis = page.evaluate("""() => {
                const links = document.querySelectorAll('a[href^="/@"]');
                let result = "링크 개수: " + links.length;
                if (links.length > 0) {
                    const firstLink = links[0];
                    let parent = firstLink;
                    let path = [];
                    for (let i = 0; i < 7; i++) {
                        if (!parent) break;
                        path.push(parent.tagName + "." + [...parent.classList].join('.'));
                        parent = parent.parentElement;
                    }
                    result += "\\n부모 경로: " + path.join(" <- ");
                }
                return result;
            }""")
            print(f"[디버그] DOM 분석 결과:\n{dom_analysis}")
        except Exception as e:
            print(f"[디버그] DOM 분석 실패: {e}")

        print("[실행] 자바스크립트 스크립트를 주입하여 작업을 시작합니다...")
        
        # JS 코드 주입
        page.evaluate(js_code)

        print("[대기] 작업이 시작되었습니다. 브라우저 창을 닫지 마세요. (종료: Ctrl + C)\n")
        
        try:
            # 브라우저에서 JS가 완료되거나 중단할 때까지 상태 모니터링
            while True:
                # 실시간 모니터링용 스크린샷 갱신
                try:
                    page.screenshot(path="debug_loop.png")
                except Exception:
                    pass

                # 브라우저 내의 전역 변수 _threadsAuto 상태 조회
                status = page.evaluate("window._threadsAuto ? {count: window._threadsAuto.count, target: window._threadsAuto.target, stop: window._threadsAuto.stop} : null")
                
                if status:
                    if status["stop"]:
                        print("[중단] 스크립트가 사용자에 의해 중단되었습니다.")
                        break
                    if status["count"] >= status["target"]:
                        print(f"\n[완료] 목표 팔로우 수({status['target']}명)를 달성하여 봇을 안전하게 종료합니다.")
                        break
                else:
                    # 주입된 스크립트 객체가 사라지거나 페이지가 리로드된 경우 에러 방지
                    print("[알림] 자동화 스크립트 상태를 감지할 수 없습니다. 재주입을 시도하거나 대기합니다.")
                    time.sleep(3)
                    
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n[중단] 파이썬 터미널에서 강제 종료를 감지했습니다.")
        except Exception as e:
            print(f"\n[오류] 봇 실행 중 예외 발생: {e}")
        finally:
            print("[종료] 브라우저를 닫고 프로그램을 종료합니다.\n")
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
