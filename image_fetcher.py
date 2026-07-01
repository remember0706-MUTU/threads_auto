import requests
import random
import json
import os
from datetime import date

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

USED_PHOTOS_FILE = "used_photos.json"

KEYWORD_MAP = {
    # 라이프스타일
    "라이프스타일": ["lifestyle morning", "daily life peaceful"],
    "건강":         ["healthy lifestyle nature", "fresh air exercise"],
    "웰빙":         ["wellness spa calm", "mindful living"],
    "일상":         ["everyday life cozy", "daily routine morning"],
    "힐링":         ["relaxation nature peaceful", "healing calm water"],
    "운동":         ["workout fitness energy", "running motivation"],
    "식단":         ["healthy food fresh", "nutritious meal colorful"],
    "카페":         ["cafe coffee warm", "coffee shop cozy morning"],
    "자연":         ["nature landscape serene", "forest light peaceful"],
    "명상":         ["meditation calm sunset", "mindfulness quiet"],
    "요가":         ["yoga sunrise nature", "yoga pose peaceful"],
    "아침루틴":     ["morning routine sunrise", "morning light coffee"],
    "월요일동기부여": ["motivation sunrise energy", "new week fresh start"],
    "주말일상":     ["weekend lifestyle relax", "weekend morning cozy"],
    "AI":           ["technology futuristic minimal", "digital abstract light"],
    "챗GPT":        ["ai technology abstract", "digital innovation"],
    "스마트폰":     ["smartphone technology minimal", "mobile digital life"],
    "일상공감":     ["everyday life relatable", "ordinary moment beautiful"],

    # 명언 카테고리 — 날짜 기반으로 매일 다른 배경 키워드 선택
    "인생격언":  [
        "mountain peak clouds dramatic",
        "city lights night reflection",
        "open road horizon freedom",
        "starry sky milky way",
        "forest path light rays",
    ],
    "힘내는말":  [
        "sunrise ocean hope",
        "person running track motivation",
        "green field sunlight energy",
        "warm window light morning",
        "rainy day cozy window coffee",
    ],
    "좋은말":    [
        "morning golden light peaceful",
        "peaceful lake reflection",
        "autumn leaves warm colors",
        "summer beach calm water",
        "colorful sunset sky dramatic",
    ],
    "깨달음":    [
        "misty forest mysterious",
        "desert dunes silence",
        "snowy mountain solitude",
        "calm river reflection",
        "stone garden zen peaceful",
    ],
    "관계와사람": [
        "two silhouettes sunset",
        "hands together warmth",
        "friends laughing together",
        "people connection city",
        "couple walking nature",
    ],
    "자기사랑":  [
        "woman alone nature peaceful",
        "self care morning routine",
        "solo hike mountain",
        "mirror reflection light",
        "bath candles relaxation",
    ],
    "변화와성장": [
        "butterfly flower nature",
        "seedling growing sunlight",
        "new beginning sunrise",
        "road ahead horizon",
        "caterpillar transformation",
    ],
    "꿈과도전":  [
        "athlete stadium determination",
        "climber rock mountain",
        "airplane sky freedom",
        "finish line achievement",
        "night study lamp ambition",
    ],
    "감사와일상": [
        "kitchen morning coffee warm",
        "family dinner table warm light",
        "dog owner park happiness",
        "simple meal sunlight",
        "book window rain cozy",
    ],
    "멘탈관리":  [
        "meditation yoga calm sunset",
        "deep breath nature peaceful",
        "journal writing morning",
        "calm water reflection",
        "night sky stars solitude",
    ],
}

DEFAULT_QUERIES = [
    "minimalist peaceful nature",
    "morning light calm",
    "sunset reflection",
    "person alone thinking nature",
    "path road forest",
]


def load_used_photos():
    if os.path.exists(USED_PHOTOS_FILE):
        with open(USED_PHOTOS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_used_photo(photo_id):
    used = load_used_photos()
    used.add(str(photo_id))
    used_list = list(used)[-200:]
    with open(USED_PHOTOS_FILE, "w") as f:
        json.dump(used_list, f)


def search_pexels_image(keyword: str) -> dict:
    if not PEXELS_API_KEY:
        print("[이미지] PEXELS_API_KEY 없음 — 스킵")
        return None

    headers = {"Authorization": PEXELS_API_KEY}

    raw = KEYWORD_MAP.get(keyword)
    if isinstance(raw, list):
        en_keyword = raw[date.today().toordinal() % len(raw)]
    elif isinstance(raw, str):
        en_keyword = raw
    else:
        en_keyword = random.choice(DEFAULT_QUERIES)

    params = {
        "query":       en_keyword,
        "orientation": "portrait",
        "size":        "large",
        "per_page":    80,
    }

    try:
        resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        photos = resp.json().get("photos", [])

        if not photos:
            params["query"] = random.choice(DEFAULT_QUERIES)
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
            photos = resp.json().get("photos", [])

        # 이미 사용한 사진 제외
        used = load_used_photos()
        fresh = [p for p in photos if str(p["id"]) not in used]
        pool = fresh if fresh else photos

        if pool:
            photo = random.choice(pool)
            save_used_photo(photo["id"])
            print(f"[이미지 검색] '{keyword}' → '{en_keyword}' (ID {photo['id']}, 풀 {len(pool)}장)")
            return {
                "id":           photo["id"],
                "url":          photo["src"]["large2x"],
                "photographer": photo["photographer"],
            }
        return None

    except Exception as e:
        print(f"[이미지 검색 오류] {e}")
        return None
