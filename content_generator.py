# =============================================
# Claude API - 비트코인 ICT 분석 콘텐츠 생성
# =============================================

import anthropic
import json
import re
import time
from config import CLAUDE_API_KEY

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def generate_threads_content(btc_data: dict) -> dict:
    """
    비트코인 현재 가격 데이터를 바탕으로
    ICT 관점 분석 + 쓰레드 포스팅 텍스트 생성
    """
    usd = btc_data["usd"]
    krw = btc_data["krw"]
    change = btc_data["change_24h"]
    trend = btc_data["trend"]
    emoji = btc_data["emoji"]

    prompt = f"""당신은 ICT(Inner Circle Trader) 방법론 전문가이자 비트코인 차트 분석가입니다.

현재 비트코인 데이터:
- 현재가: ${usd:,.0f} (₩{krw//10000:,.0f}만원)
- 24h 변동: {change:+.2f}% ({trend})

아래 조건으로 Threads 포스팅을 작성하세요:

1. 첫 줄: 현재가 + 변동률 요약 (이모지 포함)
2. ICT 관점 브리핑 2~3줄:
   - 현재 가격대의 의미 (주요 레벨, 유동성 구간 등)
   - 단기 시나리오 (bullish/bearish 관점)
   - 주의할 구간 또는 킬존
3. 마지막: 해시태그 4~5개

규칙:
- 총 450자 이내 (공백 포함)
- 투자 권유 절대 금지 ("개인 판단" 문구 포함)
- 전문적이지만 읽기 쉬운 말투
- 이모지 3~5개

JSON으로 반환:
{{"text": "전체 포스팅 내용"}}"""

    for attempt in range(4):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                result["text"] = result["text"].rstrip() + "\n\nhttps://blog.naver.com/remember0706"
                print(f"[콘텐츠 생성 완료] {len(result['text'])}자")
                return result
            raise ValueError("JSON 파싱 실패")

        except anthropic.OverloadedError:
            if attempt < 3:
                wait = 30 * (2 ** attempt)
                print(f"[API 과부하] {wait}초 후 재시도... ({attempt+1}/3)")
                time.sleep(wait)
                continue
            print("[API 과부하] 재시도 횟수 초과 → 기본 콘텐츠 사용")
            break
        except Exception as e:
            print(f"[콘텐츠 생성 오류] {e} → 기본 콘텐츠 사용")
            break

    direction = "▲" if change > 0 else "▼"
    return {
        "text": (
            f"{emoji} BTC ${usd:,.0f} | ₩{krw//10000:,.0f}만\n"
            f"{direction} 24h {change:+.2f}%\n\n"
            f"📊 ICT 관점: 현재 가격대는 주요 유동성 구간 근처입니다.\n"
            f"킬존(뉴욕/런던) 전후 움직임을 주시하세요.\n"
            f"※ 개인 판단 하에 참고용으로만 활용하세요.\n\n"
            f"#비트코인 #BTC #ICT #차트분석 #암호화폐\n\n"
            f"https://blog.naver.com/remember0706"
        )
    }
