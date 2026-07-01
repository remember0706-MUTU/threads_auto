"""
로컬에서 실행: Instagram 세션을 저장합니다.
실행 후 instagram_session.json을 GitHub Secret에 추가하세요.
"""
from playwright.sync_api import sync_playwright
import json, os

SESSION_FILE = "instagram_session.json"

print("Instagram 세션 저장 도구")
print("="*40)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto("https://www.instagram.com/accounts/login/")
    print("브라우저가 열렸습니다. Instagram에 로그인하세요.")
    print("로그인 완료 후 이 터미널에서 Enter를 누르세요...")
    input()
    context.storage_state(path=SESSION_FILE)
    print(f"\n[완료] 세션 저장됨: {SESSION_FILE}")
    print("\n다음 단계:")
    print("1. GitHub 레포 → Settings → Secrets → New repository secret")
    print("2. Name: INSTAGRAM_SESSION")
    print(f"3. Value: {SESSION_FILE} 파일 내용 전체 복사+붙여넣기")
    browser.close()
