import requests
import random
from config import PEXELS_API_KEY
from datetime import date

KEYWORD_MAP = {
    # 라이프스타일
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
    # 명언 카테고리 — 날짜 기반으로 매일 다른 배경 키워드 선택
    "인생격언":  ["mountain peak", "city lights night", "open road", "starry sky", "forest path"],
    "힘내는말":  ["sunrise ocean", "running track", "green field", "warm light window", "rainy day coffee"],
    "좋은말":    ["morning light", "peaceful lake", "autumn leaves", "summer beach", "colorful sky sunset"],
    "깨달음":    ["misty forest", "desert dunes", "snowy mountain", "calm river", "stone path garden"],
    "관계와사람": ["two people silhouette", "hands together", "friends laughing", "crowd city", "couple walking"],
    "자기사랑":  ["mirror reflection", "woman alone nature", "self care morning", "solo hike", "bath candles"],
    "변화와성장": ["butterfly nature", "seedling growing", "caterpillar leaf", "new beginning sunrise", "construction building"],
    "꿈과도전":  ["athlete stadium", "climber rock", "airplane sky", "finish line race", "night study lamp"],
    "감사와일상": ["kitchen morning coffee", "family dinner table", "dog owner park", "simple meal sunlight", "book window rain"],
    "멘탈관리":  ["meditation yoga sunset", "deep breath nature", "journal writing", "calm water reflection", "night sky stars"],
}


def search_pexels_image(keyword: str) -> dict:
    """
    Pexels에서 키워드로 이미지 검색 후 URL 반환
    """
    if not PEXELS_API_KEY:
        print("[이미지] PEXELS_API_KEY 없음 — 스킵")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    raw = KEYWORD_MAP.get(keyword, keyword)
    if isinstance(raw, list):
        # 날짜 기반으로 매일 다른 키워드 선택 (같은 날은 동일)
        en_keyword = raw[date.today().toordinal() % len(raw)]
    else:
        en_keyword = raw

    params = {
        "query": en_keyword,
        "orientation": "landscape",
        "size": "large",
        "per_page": 15,
    }

    try:
        resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        photos = resp.json().get("photos", [])

        if not photos:
            params["query"] = "nature landscape"
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            photos = resp.json().get("photos", [])

        if photos:
            photo = random.choice(photos)
            print(f"[이미지 검색] '{keyword}' → '{en_keyword}' (ID {photo['id']})")
            return {
                "id": photo["id"],
                "url": photo["src"]["large2x"],
                "photographer": photo["photographer"],
            }
        return None

    except Exception as e:
        print(f"[이미지 검색 오류] {e}")
        return None
