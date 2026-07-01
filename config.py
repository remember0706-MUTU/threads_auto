import os

# Claude API 키 (GitHub Secret: CLAUDE_API_KEY / 로컬: 환경변수로 설정)
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

# Pexels API 키 (GitHub Secret: PEXELS_API_KEY)
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# 포스팅 시간
POST_TIMES = ["09:00", "13:00", "17:00", "21:00"]
