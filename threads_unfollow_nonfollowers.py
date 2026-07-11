import os
import sys
import time
import json
import random
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright

# 콘솔에서 한글이 깨지지 않도록 표준 출력 UTF-8 재설정
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --------------------------------------------------------------------------- #
# 스레드(Threads) "맞팔 아님" 언팔로우 스크립트
#
# 내가 팔로우하는 사람 중, 나를 맞팔하지 않는 계정을 찾아 언팔로우합니다.
# 스레드는 인스타그램과 동일한 Barcelona 백엔드를 사용하므로
# 내부 REST 친구관계 API(/api/v1/friendships/...)를 재사용합니다.
#
# 인증: threads_session.json (playwright storage_state)
#   -> save_session.py 로 로그인 세션을 먼저 저장해야 합니다.
# --------------------------------------------------------------------------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "threads_session.json")
LOG_PATH = os.path.join(BASE_DIR, "threads_unfollow_log.json")
WHITELIST_DEFAULT = os.path.join(BASE_DIR, "threads_unfollow_whitelist.txt")

HOME_URL = "https://www.threads.com/"
# 스레드 웹앱이 사용하는 App ID (Barcelona)
THREADS_APP_ID = "238260118697367"


# --------------------------------------------------------------------------- #
# 상태 로그 / 화이트리스트
# --------------------------------------------------------------------------- #
def load_log():
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_log(log):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def load_whitelist(path):
    names = set()
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip().lstrip("@").lower()
                if name and not name.startswith("#"):
                    names.add(name)
    return names


# --------------------------------------------------------------------------- #
# 쿠키 헬퍼
# --------------------------------------------------------------------------- #
def get_cookie(context, name):
    for c in context.cookies():
        if c.get("name") == name:
            return c.get("value")
    return None


# --------------------------------------------------------------------------- #
# 내부 API 호출 (브라우저 컨텍스트 안에서 fetch 실행 -> 쿠키/세션 자동 적용)
# --------------------------------------------------------------------------- #
def api_get(page, path):
    return page.evaluate(
        """async ({path, appId}) => {
            try {
                const r = await fetch(path, { headers: { 'X-IG-App-ID': appId } });
                const text = await r.text();
                let body = null;
                try { body = JSON.parse(text); } catch (e) { body = text.slice(0, 300); }
                return { ok: r.ok, status: r.status, body };
            } catch (e) { return { ok: false, error: String(e) }; }
        }""",
        {"path": path, "appId": THREADS_APP_ID},
    )


def collect_list(page, uid, kind, cap, max_pages=300):
    """friendships/{uid}/{kind} 를 페이지네이션으로 수집.
    kind: 'following' | 'followers'. -> [{'username','pk'}]"""
    ordered, seen, next_max_id, pages = [], set(), None, 0

    while len(ordered) < cap and pages < max_pages:
        pages += 1
        path = f"/api/v1/friendships/{uid}/{kind}/?count=100"
        if next_max_id:
            path += f"&max_id={next_max_id}"
        res = api_get(page, path)

        if not res or not res.get("ok"):
            print(f"[경고] {kind} API 오류: status={res.get('status') if res else '無응답'} "
                  f"body={str(res.get('body') if res else '')[:150]}")
            break

        data = res.get("body") or {}
        if not isinstance(data, dict):
            print(f"[경고] {kind} 응답 형식이 JSON이 아닙니다: {str(data)[:150]}")
            break

        users = data.get("users") or []
        for u in users:
            name = (u.get("username") or "").lower()
            pk = str(u.get("pk") or u.get("id") or "")
            if name and name not in seen:
                seen.add(name)
                ordered.append({"username": name, "pk": pk})

        next_max_id = data.get("next_max_id")
        if not next_max_id or not users:
            break
        time.sleep(random.uniform(0.8, 1.5))

    return ordered[:cap]


def friendship_show(page, pk):
    res = api_get(page, f"/api/v1/friendships/show/{pk}/")
    if res and res.get("ok") and isinstance(res.get("body"), dict):
        return res["body"]
    return {"error": res.get("status") if res else "none"}


def unfollow_api(page, pk, csrf):
    return page.evaluate(
        """async ({pk, csrf, appId}) => {
            try {
                const r = await fetch(`/api/v1/friendships/destroy/${pk}/`, {
                    method: 'POST',
                    headers: {
                        'X-IG-App-ID': appId,
                        'X-CSRFToken': csrf,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: ''
                });
                const j = await r.json().catch(() => ({}));
                return { ok: r.ok, status: r.status, body: j };
            } catch (e) { return { ok: false, error: String(e) }; }
        }""",
        {"pk": pk, "csrf": csrf, "appId": THREADS_APP_ID},
    )


# --------------------------------------------------------------------------- #
# 메인
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="스레드 맞팔 아님 언팔로우")
    parser.add_argument("--daily-limit", type=int, default=40, help="이번 실행 최대 언팔 수")
    parser.add_argument("--max-scan", type=int, default=300, help="검사할 팔로잉 최대 수")
    parser.add_argument("--max-followers-scan", type=int, default=5000, help="수집할 팔로워 최대 수")
    parser.add_argument("--min-delay", type=float, default=15, help="언팔 간 최소 대기(초)")
    parser.add_argument("--max-delay", type=float, default=30, help="언팔 간 최대 대기(초)")
    parser.add_argument("--whitelist", type=str, default=WHITELIST_DEFAULT, help="보호 계정 목록 파일")
    parser.add_argument("--dry-run", action="store_true", help="실제 언팔 없이 대상만 출력")
    parser.add_argument("--probe", action="store_true", help="API 동작만 점검하고 종료")
    args = parser.parse_args()

    if not os.path.exists(SESSION_FILE):
        print(f"[오류] 세션 파일이 없습니다: {SESSION_FILE}")
        print("먼저 save_session.py 로 로그인 세션을 저장하세요.")
        return

    whitelist = load_whitelist(args.whitelist)

    print("=" * 52)
    print("스레드(Threads) 맞팔 아님 언팔로우")
    print("=" * 52)
    print(f"[설정] 일일 한도   : {args.daily_limit}명")
    print(f"[설정] 팔로잉 스캔 : {args.max_scan}명")
    print(f"[설정] 대기 시간   : {args.min_delay:.0f}-{args.max_delay:.0f}초")
    print(f"[설정] 화이트리스트: {len(whitelist)}개 보호 계정")
    print(f"[설정] Dry run    : {args.dry_run}")
    print("=" * 52)

    log = load_log()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        )
        page = context.new_page()

        print(f"[이동] {HOME_URL}")
        page.goto(HOME_URL, timeout=60000)
        time.sleep(5)

        if "login" in page.url or "accounts" in page.url:
            print("[오류] 로그인 세션이 만료되었습니다. save_session.py 로 다시 저장하세요.")
            browser.close()
            return

        uid = get_cookie(context, "ds_user_id")
        csrf = get_cookie(context, "csrftoken")
        if not uid:
            print("[오류] ds_user_id 쿠키를 읽지 못했습니다.")
            browser.close()
            return
        if not csrf:
            print("[오류] csrftoken 쿠키를 읽지 못했습니다.")
            browser.close()
            return
        print(f"[정보] 내 user id: {uid}")

        # --- API 점검 모드 ---
        if args.probe:
            print("\n[점검] following API 1페이지 호출...")
            res = api_get(page, f"/api/v1/friendships/{uid}/following/?count=5")
            print(f"  status={res.get('status')} ok={res.get('ok')}")
            body = res.get("body")
            if isinstance(body, dict):
                users = body.get("users") or []
                print(f"  users 수: {len(users)}")
                for u in users[:5]:
                    print(f"    - @{u.get('username')} (pk={u.get('pk')})")
            else:
                print(f"  body(비JSON): {str(body)[:250]}")
            print("\n[점검] 완료. 5초 후 종료합니다.")
            time.sleep(5)
            browser.close()
            return

        print("[수집] 팔로잉 목록 API 호출 중...")
        following = collect_list(page, uid, "following", args.max_scan)
        print(f"[정보] 팔로잉 수집: {len(following)}")

        print("[수집] 팔로워 목록 API 호출 중...")
        followers = {u["username"] for u in collect_list(page, uid, "followers", args.max_followers_scan)}
        print(f"[정보] 팔로워 수집: {len(followers)}")

        if not following:
            print("[종료] 팔로잉을 가져오지 못했습니다. --probe 로 API를 먼저 점검하세요.")
            browser.close()
            return

        targets = [u for u in following if u["username"] not in followers]
        print(f"[정보] 맞팔 아님 대상: {len(targets)}명")
        if not targets:
            print("[종료] 모두 맞팔 상태입니다. 언팔 대상 없음.")
            browser.close()
            return

        unfollowed = kept = gone = skipped = 0

        for entry in targets:
            name, pk = entry["username"], entry["pk"]

            if unfollowed >= args.daily_limit:
                print(f"\n[중단] 일일 한도 {args.daily_limit}명 도달.")
                break
            if name in whitelist:
                print(f"[보호] @{name} 화이트리스트, 건너뜀.")
                skipped += 1
                continue
            if log.get(name, {}).get("status") == "unfollowed":
                continue
            if not pk:
                print(f"[건너뜀] @{name}: user id 없음.")
                gone += 1
                continue

            print(f"\n--- 언팔 {unfollowed}/{args.daily_limit} | 확인: @{name} ---")

            # 계정별 최종 재확인 (팔로워 목록 누락 대비)
            rel = friendship_show(page, pk)
            if not rel or rel.get("error"):
                print(f"[건너뜀] 관계 확인 실패 (err={rel.get('error') if rel else 'none'}).")
                gone += 1
                time.sleep(random.uniform(1.5, 3))
                continue
            if rel.get("followed_by"):
                print("[유지] 맞팔 상태입니다. 유지.")
                log[name] = {"status": "kept", "checked_at": datetime.now().isoformat(timespec="seconds")}
                save_log(log)
                kept += 1
                time.sleep(random.uniform(1, 2))
                continue
            if not rel.get("following"):
                print("[건너뜀] 이미 팔로우하고 있지 않습니다.")
                gone += 1
                time.sleep(random.uniform(1, 2))
                continue

            if args.dry_run:
                print("[모의] 언팔 대상 (맞팔 아님).")
                unfollowed += 1
                time.sleep(random.uniform(0.5, 1.2))
                continue

            res = unfollow_api(page, pk, csrf)
            if res and res.get("ok") and (res.get("body", {}).get("status") == "ok"):
                unfollowed += 1
                log[name] = {
                    "status": "unfollowed",
                    "pk": pk,
                    "unfollowed_at": datetime.now().isoformat(timespec="seconds"),
                }
                save_log(log)
                print(f"[완료] @{name} 언팔. (누적: {unfollowed})")
                delay = random.uniform(args.min_delay, args.max_delay)
                print(f"[대기] 안전 대기: {delay:.1f}초...")
                time.sleep(delay)
            else:
                status = res.get("status") if res else "무응답"
                body = res.get("body") if res else {}
                if status in (429, 400) or (isinstance(body, dict) and body.get("message") == "feedback_required"):
                    print(f"[경고] 액션 차단/속도 제한 (status={status}). 계정 보호를 위해 중단합니다.")
                    break
                print(f"[오류] @{name} 언팔 실패 (status={status}). 건너뜀.")
                time.sleep(random.uniform(3, 6))

        print("\n" + "=" * 52)
        print(f"[종료] 언팔:{unfollowed} | 맞팔유지:{kept} | 건너뜀/이탈:{gone} | 보호:{skipped}")
        print("=" * 52)
        time.sleep(3)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
