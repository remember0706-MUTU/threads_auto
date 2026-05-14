# =============================================
# 네이버 DataLab 핫키워드 수집 모듈 (쓰레드용)
# =============================================

import requests
import json
from datetime import datetime, timedelta
import os

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")


def get_trending_keywords(category="라이프스타일", top_n=5):
    """네이버 DataLab에서 오늘의 핫 키워드 수집"""
    today = datetime.now()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    keyword_map = {
        "라이프스타일": ["라이프스타일", "일상", "데일리", "인테리어", "취미"],
        "건강": ["건강", "헬스", "운동", "다이어트", "웰빙", "영양"],
        "IT·기술": ["AI", "챗GPT", "스마트폰", "앱추천", "유튜브"],
        "일상·공감": ["공감", "일상", "오늘", "소소한행복", "힐링"],
    }

    keywords = keyword_map.get(category, ["라이프스타일"])
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "Content-Type": "application/json",
    }
    keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in keywords]
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": keyword_groups,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        keyword_scores = []
        for result in results:
            name = result["title"]
            recent_data = result["data"][-3:] if len(result["data"]) >= 3 else result["data"]
            avg_ratio = sum(d["ratio"] for d in recent_data) / len(recent_data)
            keyword_scores.append((name, avg_ratio))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [k[0] for k in keyword_scores[:top_n]]
        print(f"[키워드 수집] TOP {top_n}: {top_keywords}")
        return top_keywords
    except Exception as e:
        print(f"[키워드 수집 오류] {e} → fallback 사용")
        return get_fallback_keywords()


def get_fallback_keywords():
    """네이버 API 없을 때 사용할 기본 키워드"""
    weekday = datetime.now().weekday()
    weekday_keywords = {
        0: ["월요일동기부여", "한주시작", "건강습관"],
        1: ["화요일", "건강식단", "운동루틴"],
        2: ["수요일", "미드위크", "힐링"],
        3: ["목요일", "웰빙라이프", "일상공감"],
        4: ["금요일", "주말준비", "라이프스타일"],
        5: ["토요일", "주말일상", "카페투어"],
        6: ["일요일", "주말마무리", "한주준비"],
    }
    return weekday_keywords.get(weekday, ["라이프스타일", "건강", "웰빙"])
