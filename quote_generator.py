import anthropic
import os
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

CATEGORIES = ["인생격언", "힘내는말", "좋은말", "깨달음"]

STYLES = {
    "인생격언": "짧고 강렬한 한 줄 명언. 읽자마자 저장하고 싶은 문장.",
    "힘내는말": "지친 사람의 등을 토닥여주는 따뜻하고 진심 어린 말.",
    "좋은말":   "오늘 하루를 긍정적으로 시작하게 해주는 밝은 에너지의 글.",
    "깨달음":   "살면서 뒤늦게 알게 되는 것들. 솔직하고 담담한 어조.",
}


def get_today_category():
    return CATEGORIES[datetime.now().weekday() % len(CATEGORIES)]


def generate_quote_content():
    category = get_today_category()
    style = STYLES[category]

    prompt = (
        "당신은 Threads에서 인생격언과 감성 글로 큰 공감을 얻는 크리에이터입니다.\n\n"
        "카테고리: " + category + "\n"
        "글쓰기 스타일: " + style + "\n\n"
        "조건:\n"
        "- 한국어, 총 5~7줄\n"
        "- 이모지 2~3개 자연스럽게 포함\n"
        '- 읽는 사람이 "이거 내 얘기다" 느낄 만큼 공감 가능하게\n'
        "- 마지막 줄은 저장하고 싶게 만드는 한 문장\n"
        "- 광고 느낌 없이 진심 어린 글\n"
        "- 관련 해시태그 4~5개 마지막에 추가\n"
        "- 총 450자 이내\n\n"
        "그리고 위 한국어 내용 전체를 영어로도 작성해주세요 (text_en):\n"
        "- 한국어 원문과 줄 수, 구성, 흐름이 동일하게\n"
        "- 한 줄도 빠짐없이 전부 영어로 번역\n"
        "- 직역 말고 영어 원어민이 쓸 법한 자연스러운 표현으로\n"
        "- 이모지는 동일하게 유지\n"
        "- 해시태그도 영어로 번역 (예: #좋은말 → #goodwords)\n"
        "- 한국어와 동일한 분량\n\n"
        "JSON으로 반환:\n"
        '{"text": "전체 내용 (해시태그 포함)", "text_en": "Full English version (same length as Korean, all lines translated)"}'
    )

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        import json, re
        text = message.content[0].text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            result = json.loads(match.group())
            print("[격언 생성 완료] 카테고리: " + category)
            return result
        raise ValueError("JSON 파싱 실패")
    except Exception as e:
        print("[격언 생성 오류] " + str(e))
        return {
            "text": "오늘 하루도 수고했어요 ✨\n작은 것에도 감사할 줄 아는 사람이\n결국 가장 행복한 사람입니다.\n\n#좋은말 #오늘의격언 #힘내요 #감성글 #공감",
            "text_en": "You've worked hard today ✨\nThe person who can find gratitude in small things\nis ultimately the happiest.\n\n#goodwords #dailyquote #keepgoing #motivation #empathy"
        }
