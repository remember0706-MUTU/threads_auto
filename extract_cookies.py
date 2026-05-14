import rookiepy, json, os

print("Chrome에서 threads.net 쿠키 추출 중...")
try:
    cookies = rookiepy.chrome(["threads.net"])
    print(f"쿠키 {len(cookies)}개 발견")

    if len(cookies) == 0:
        print("[실패] threads.net 쿠키 없음 - Chrome에서 Threads 로그인이 필요합니다")
        exit(1)

    # Playwright storage_state 형식으로 변환
    playwright_cookies = []
    for c in cookies:
        playwright_cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["host"] if "host" in c else ".threads.net",
            "path": c.get("path", "/"),
            "expires": c.get("expires", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True),
            "sameSite": "None"
        })

    session = {
        "cookies": playwright_cookies,
        "origins": []
    }

    out = os.path.join(os.path.dirname(__file__), "threads_session.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)

    print(f"[완료] 세션 저장: {out}")
    print(f"저장된 쿠키: {[c['name'] for c in playwright_cookies[:5]]}")

except Exception as e:
    print(f"[오류] {e}")
    exit(1)
