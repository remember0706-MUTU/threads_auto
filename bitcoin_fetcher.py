# =============================================
# 비트코인 실시간 가격 수집 (CoinGecko 무료 API)
# =============================================

import requests

def get_bitcoin_price() -> dict:
    """비트코인 현재가 + 24h 변동률 가져오기"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd,krw",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()["bitcoin"]

        usd = data["usd"]
        krw = data["krw"]
        change_24h = data.get("usd_24h_change", 0)

        print(f"[BTC] ${usd:,.0f} / ₩{krw:,.0f} | 24h: {change_24h:+.2f}%")
        return {
            "usd": usd,
            "krw": krw,
            "change_24h": round(change_24h, 2),
            "trend": "상승" if change_24h > 0 else "하락",
            "emoji": "🟢" if change_24h > 0 else "🔴",
        }
    except Exception as e:
        print(f"[BTC 가격 오류] {e}")
        return None
