"""Threads 페이지 구조 분석 및 포스팅 시도"""
from playwright.sync_api import sync_playwright
import time, os, json

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threads_session.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_result.txt")
TEXT = "테스트 포스팅입니다 🌿\n매일 조금씩 성장하는 중!\n\n#테스트 #일상"

log = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=SESSION_FILE, viewport={"width": 1280, "height": 900})
    page = context.new_page()

    page.goto("https://www.threads.net")
    page.wait_for_load_state("networkidle", timeout=20000)
    time.sleep(3)

    log.append(f"URL: {page.url}")

    # 페이지 구조 분석
    info = page.evaluate("""() => {
        const result = {};
        // placeholder 목록
        result.placeholders = Array.from(document.querySelectorAll('[placeholder]')).map(e => e.placeholder);
        // contenteditable
        result.editables = document.querySelectorAll('[contenteditable]').length;
        // role=button 텍스트
        result.buttons = Array.from(document.querySelectorAll('[role="button"]'))
            .map(b => b.textContent.trim())
            .filter(t => t && t.length < 30);
        // compose 링크
        result.composeLinks = Array.from(document.querySelectorAll('a'))
            .map(a => a.href)
            .filter(h => h.includes('compose') || h.includes('new'));
        return result;
    }""")

    log.append(f"Placeholders: {info['placeholders']}")
    log.append(f"Editables: {info['editables']}")
    log.append(f"Buttons: {info['buttons'][:15]}")
    log.append(f"Compose links: {info['composeLinks'][:5]}")

    # contenteditable 클릭 시도
    try:
        el = page.locator('[contenteditable="true"]').first
        el.click(timeout=5000)
        time.sleep(1.5)
        page.keyboard.type(TEXT, delay=20)
        time.sleep(1)
        log.append("텍스트 입력 완료")

        # 게시 버튼 JavaScript 클릭
        posted = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('[role="button"]'));
            const btn = btns.find(b => {
                const t = b.textContent.trim();
                return t === '게시' || t === 'Post';
            });
            if (btn) {
                btn.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}));
                return '게시 클릭 성공: ' + btn.textContent.trim();
            }
            return '게시 버튼 없음. 버튼들: ' + btns.map(b=>b.textContent.trim()).filter(t=>t).join(', ');
        }""")
        log.append(f"게시: {posted}")
        time.sleep(4)
        log.append(f"최종 URL: {page.url}")

    except Exception as e:
        log.append(f"오류: {e}")

    browser.close()

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(log))

print("완료. debug_result.txt 확인하세요.")
