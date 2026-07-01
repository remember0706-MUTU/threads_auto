import anthropic
import os
import random
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

CATEGORIES = [
    "인생격언",
    "힘내는말",
    "좋은말",
    "깨달음",
    "관계와사람",
    "자기사랑",
    "변화와성장",
    "꿈과도전",
    "감사와일상",
    "멘탈관리",
]

STYLES = {
    "인생격언":  "짧고 강렬한 한 줄 명언. 읽자마자 저장하고 싶은 문장.",
    "힘내는말":  "지친 사람의 등을 토닥여주는 따뜻하고 진심 어린 말.",
    "좋은말":    "오늘 하루를 긍정적으로 시작하게 해주는 밝은 에너지의 글.",
    "깨달음":    "살면서 뒤늦게 알게 되는 것들. 솔직하고 담담한 어조.",
    "관계와사람":"사람과의 관계에서 느끼는 진심, 상처, 온기에 대한 통찰.",
    "자기사랑":  "나 자신을 아끼고 존중하는 것의 중요성. 부드럽고 따뜻한 자기 위로.",
    "변화와성장":"불편하지만 꼭 필요한 성장통. 솔직하고 현실적인 어조.",
    "꿈과도전":  "목표를 향한 용기와 실패를 두려워하지 않는 마음. 힘차고 결단력 있는 어조.",
    "감사와일상":"작은 것에서 발견하는 행복과 감사. 잔잔하고 따뜻한 어조.",
    "멘탈관리":  "마음을 단단하게 유지하는 법. 현실적이고 실용적인 조언.",
}

WRITING_FORMATS = [
    {
        "name": "서술형",
        "desc": "감성적인 문장으로 이어지는 일반적인 서술 형식. 자연스럽게 흘러가듯.",
    },
    {
        "name": "질문형",
        "desc": "첫 줄을 독자에게 던지는 질문으로 시작. 읽는 사람이 스스로 생각하게 만드는 형식.",
    },
    {
        "name": "이야기형",
        "desc": "짧은 상황/장면으로 시작해서 교훈이나 감정으로 마무리. 미니 스토리 느낌.",
    },
    {
        "name": "반전형",
        "desc": "처음엔 평범하거나 부정적으로 시작했다가 마지막 줄에서 반전되는 구조.",
    },
    {
        "name": "리스트형",
        "desc": "'-' 또는 숫자 없이 핵심 문장들을 병렬로 나열. 각 줄이 독립적이면서도 하나의 메시지로 수렴.",
    },
]


def get_today_category():
    return CATEGORIES[datetime.now().toordinal() % len(CATEGORIES)]


def generate_quote_content():
    category = get_today_category()
    style = STYLES[category]
    fmt = random.choice(WRITING_FORMATS)

    prompt = (
        "당신은 Threads와 Instagram에서 인생격언과 감성 글로 큰 공감을 얻는 크리에이터입니다.\n\n"
        f"카테고리: {category}\n"
        f"글쓰기 스타일: {style}\n"
        f"글 형식: {fmt['name']} — {fmt['desc']}\n\n"
        "【중요】 한국어 본문을 정확히 6줄로 작성하세요. 줄 수를 절대 바꾸지 마세요.\n\n"
        "한국어 조건:\n"
        "- 정확히 6줄 (빈 줄 없이 연속)\n"
        "- 위에 지정된 '글 형식'을 반드시 따를 것\n"
        "- 이모지 2~3개 자연스럽게 포함\n"
        '- 읽는 사람이 "이거 내 얘기다" 느낄 만큼 공감 가능하게\n'
        "- 마지막 줄은 저장하고 싶게 만드는 한 문장\n"
        "- 광고 느낌 없이 진심 어린 글\n"
        "- 관련 해시태그 4~5개 마지막에 추가\n\n"
        "영어 번역 조건 (text_en):\n"
        "- 한국어 본문과 정확히 같은 6줄 (줄 추가/삭제/합치기 금지)\n"
        "- 1번 줄 → 1번 줄, 2번 줄 → 2번 줄 … 순서 그대로 1:1 번역\n"
        "- 영어 원어민이 쓸 법한 자연스러운 표현\n"
        "- 이모지 동일하게 유지\n"
        "- 해시태그도 영어로 번역 (예: #좋은말 → #goodwords)\n\n"
        "JSON으로 반환:\n"
        '{"text": "6줄 한국어 본문\\n해시태그", "text_en": "정확히 6줄 영어 본문\\n해시태그"}'
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
            print(f"[격언 생성 완료] 카테고리: {category} / 형식: {fmt['name']}")
            return result
        raise ValueError("JSON 파싱 실패")
    except Exception as e:
        print("[격언 생성 오류] " + str(e))
        return {
            "text": "오늘 하루도 수고했어요 ✨\n작은 것에도 감사할 줄 아는 사람이\n결국 가장 행복한 사람입니다.\n\n#좋은말 #오늘의격언 #힘내요 #감성글 #공감",
            "text_en": "You've worked hard today ✨\nThe person who can find gratitude in small things\nis ultimately the happiest.\n\n#goodwords #dailyquote #keepgoing #motivation #empathy"
        }
