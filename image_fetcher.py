# =============================================
# Pexels 이미지 검색 모듈 (쓰레드용 - URL만 반환)
# =============================================

import requests
import random
from config import PEXELS_API_KEY

KEYWORD_MAP = {
    "라이프스타일": "lifestyle",
    "건강": "healthy lifestyle",
    "웰빙": "wellness",
    "일상": "daily life",
    "힐링": "relaxation healing",
    "운동": "workout fitness",
    "식단": "healthy food",
    "카페": "cafe coffee",
    "자연": "nature",
    "명상": "meditation",
    "요가": "yoga",
    "아침루틴": "morning routine",
    "월요일동기부여": "motivation monday",
    "주말일상": "weekend lifestyle",
    "AI": "artificial intelligence technology",
    "챗GPT": "ai chatbot technology",
    "스마트폰": "smartphone technology",
    "일상공감": "everyday life",
}


def search_pexels_image(keyword: str) -> dict:
    """
    Pexels에서 키워드로 이미지 검색 후 URL 반환
    쓰레드는 landscape(가로) 비율이 더 자연스러움
    """
    headers = {"Authorization": PEXELS_API_KEY}
    en_keyword = KEYWORD_MAP.get(keyword, keyword)

    params = {
        "query": en_keyword,
        "orientation": "landscape",
        "size": "large",
        "per_page": 10,
    }

    try:
        resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        photos = resp.json().get("photos", [])

        if not photos:
            params["query"] = "lifestyle"
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            photos = resp.json().get("photos", [])

        if photos:
            photo = random.choice(photos)
            print(f"[이미지 검색] {keyword} → ID {photo['id']}")
            return {
                "id": photo["id"],
                "url": photo["src"]["large2x"],
                "photographer": photo["photographer"],
            }
        return None

    except Exception as e:
        print(f"[이미지 검색 오류] {e}")
        return None
