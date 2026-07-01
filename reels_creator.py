from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import re
import glob as _glob

def strip_emoji(text):
    """이모지 제거 — NanumGothicBold가 지원하지 않는 이모지 제거. 한글은 보존."""
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"   # 현대 이모지 (얼굴, 동물, 음식, 심볼 등)
        "\U0001FA00-\U0001FAFF"   # 확장 이모지 (체스, 새 심볼)
        "\U00002600-\U000027BF"   # 기타 심볼(☀♠) + Dingbats — 한글은 U+AC00+로 이 범위 밖
        "\U0000FE00-\U0000FE0F"   # Variation Selectors (이모지 색상 지정자)
        "\U0000200D"              # Zero Width Joiner (합성 이모지 연결자)
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()

def find_korean_font(size):
    """한국어 지원 폰트를 찾아 반환. 없으면 None."""
    candidates = [
        '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf',
        '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/malgun.ttf',
        '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    ]
    # glob으로 Nanum 폰트 추가 탐색
    candidates += _glob.glob('/usr/share/fonts/**/*Nanum*Bold*.ttf', recursive=True)
    candidates += _glob.glob('/usr/share/fonts/**/*Nanum*.ttf', recursive=True)
    candidates += _glob.glob('/usr/share/fonts/**/*nanum*.ttf', recursive=True)

    for p in candidates:
        if p and os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                print(f"[폰트] 로드 성공: {p} (size={size})")
                return font
            except Exception as e:
                print(f"[폰트] 실패: {p} → {e}")
    print(f"[폰트 경고] 한국어 폰트 없음! size={size}")
    return None

def wrap_text(draw, text, font, max_w):
    """텍스트를 max_w 픽셀 이내로 줄바꿈. 폰트 없으면 그냥 반환."""
    if font is None:
        return [text]
    result, cur = [], ""
    for ch in text:
        test = cur + ch
        try:
            w = draw.textlength(test, font=font)
        except:
            try:
                bb = draw.textbbox((0, 0), test, font=font)
                w = bb[2] - bb[0]
            except:
                w = len(test) * size_of(font)
        if w > max_w and cur:
            result.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        result.append(cur)
    return result or [text]

def size_of(font):
    try:
        return font.size
    except:
        return 20

def create_gradient_bg(width=1080, height=1920, c1=(15, 15, 35), c2=(50, 20, 80)):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / height
        arr[y] = [int(c1[i]*(1-t) + c2[i]*t) for i in range(3)]
    return Image.fromarray(arr)

def create_reels_video(text: str, image_path: str = None,
                       output_path: str = "reels_output.mp4",
                       bgm_path: str = None, duration: int = 18,
                       text_en: str = "") -> str:
    from moviepy.editor import ImageSequenceClip, AudioFileClip

    W, H, FPS = 1080, 1920, 24
    PADDING = 70
    MAX_W = W - PADDING * 2

    # ── 폰트 탐색 (영어 있으면 한글 폰트 약간 축소해서 공간 확보) ──
    ko_size = 44 if text_en else 52
    font_body = find_korean_font(ko_size)
    font_tag  = find_korean_font(28)
    font_en   = find_korean_font(26) if text_en else None

    # ── 텍스트 파싱 ──
    dummy_img  = Image.new('RGB', (W, H))
    dummy_draw = ImageDraw.Draw(dummy_img)

    raw_lines = [l.strip() for l in text.split('\n') if l.strip()]

    body_lines_raw, tag_lines_raw = [], []
    for line in raw_lines:
        if line.startswith('#'):
            tag_lines_raw.append(strip_emoji(line).strip())
        else:
            cleaned = strip_emoji(line).strip()
            if cleaned:
                body_lines_raw.append(cleaned)

    # 해시태그가 별도 줄 없으면 마지막 본문에서 분리
    if not tag_lines_raw and body_lines_raw:
        last = body_lines_raw[-1]
        idx = last.find('#')
        if idx != -1:
            before = last[:idx].strip()
            body_lines_raw[-1:] = [before] if before else []
            tag_lines_raw = [last[idx:].strip()]

    # 줄바꿈 적용
    body_lines = []
    for l in body_lines_raw:
        body_lines.extend(wrap_text(dummy_draw, l, font_body, MAX_W))
    tag_lines = []
    for l in tag_lines_raw:
        tag_lines.extend(wrap_text(dummy_draw, l, font_tag, MAX_W))

    # 줄 수가 너무 많으면 폰트 줄임
    if len(body_lines) > 9 and font_body:
        font_body = find_korean_font(36)
        body_lines = []
        for l in body_lines_raw:
            body_lines.extend(wrap_text(dummy_draw, l, font_body, MAX_W))
    elif len(body_lines) > 6 and font_body:
        font_body = find_korean_font(40)
        body_lines = []
        for l in body_lines_raw:
            body_lines.extend(wrap_text(dummy_draw, l, font_body, MAX_W))

    # ── 영어 파싱 (해시태그 제외, 이모지 제거) ──
    en_lines = []
    if text_en and font_en:
        en_raw = [l.strip() for l in text_en.split('\n')
                  if l.strip() and not l.strip().startswith('#')]
        en_lines_raw = [strip_emoji(l).strip() for l in en_raw if strip_emoji(l).strip()]
        for l in en_lines_raw:
            en_lines.extend(wrap_text(dummy_draw, l, font_en, MAX_W))

    print(f"[영상] 한글 {len(body_lines)}줄, 영어 {len(en_lines)}줄, 해시태그 {len(tag_lines)}줄")

    # ── 배경 ──
    if image_path and os.path.exists(image_path):
        bg = Image.open(image_path).convert('RGB')
        iw, ih = bg.size
        scale = max(W / iw, H / ih)
        bg = bg.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
        left = (bg.width - W) // 2
        top  = (bg.height - H) // 2
        bg = bg.crop((left, top, left + W, top + H))
    else:
        bg = create_gradient_bg(W, H)

    # ── 레이아웃 계산 ──
    body_lh = int(size_of(font_body) * 1.5) if font_body else 60
    tag_lh  = int(size_of(font_tag)  * 1.5) if font_tag  else 40
    en_lh   = int(size_of(font_en)   * 1.5) if font_en   else 38
    en_gap  = 28 if en_lines else 0   # 한글-영어 구분 여백

    total_h = (len(body_lines) * body_lh
               + en_gap + len(en_lines) * en_lh
               + (20 if tag_lines else 0) + len(tag_lines) * tag_lh)
    y0 = max(PADDING, (H - total_h) // 2)

    total_lines = len(body_lines) + len(en_lines) + len(tag_lines)

    def make_frame(i):
        t = i / (FPS * duration)  # 0.0 → 1.0
        frame = bg.copy().convert('RGBA')
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 155))
        frame = Image.alpha_composite(frame, overlay)
        draw = ImageDraw.Draw(frame)

        y = y0

        # 한글 본문 (흰색)
        for j, line in enumerate(body_lines):
            reveal_t = (j / max(total_lines, 1)) * 0.4
            raw_a = (t - reveal_t) / 0.08
            alpha = int(max(0.0, min(1.0, raw_a)) * 255)
            if alpha > 0 and font_body:
                try:
                    tw = int(draw.textlength(line, font=font_body))
                except:
                    tw = len(line) * size_of(font_body)
                x = max(PADDING, (W - tw) // 2)
                draw.text((x + 2, y + 2), line, font=font_body, fill=(0, 0, 0, alpha // 2))
                draw.text((x, y), line, font=font_body, fill=(255, 255, 255, alpha))
            y += body_lh

        # 영어 번역 (구분 여백 + 연한 회백색)
        y += en_gap
        for j, line in enumerate(en_lines):
            k = len(body_lines) + j
            reveal_t = (k / max(total_lines, 1)) * 0.4
            raw_a = (t - reveal_t) / 0.08
            alpha = int(max(0.0, min(1.0, raw_a)) * 255)
            if alpha > 0 and font_en:
                try:
                    tw = int(draw.textlength(line, font=font_en))
                except:
                    tw = len(line) * size_of(font_en)
                x = max(PADDING, (W - tw) // 2)
                draw.text((x + 1, y + 1), line, font=font_en, fill=(0, 0, 0, alpha // 3))
                draw.text((x, y), line, font=font_en, fill=(200, 200, 200, alpha))
            y += en_lh

        # 해시태그 (연파랑)
        y += 20
        for j, line in enumerate(tag_lines):
            k = len(body_lines) + len(en_lines) + j
            reveal_t = (k / max(total_lines, 1)) * 0.4
            raw_a = (t - reveal_t) / 0.08
            alpha = int(max(0.0, min(1.0, raw_a)) * 255)
            if alpha > 0 and font_tag:
                try:
                    tw = int(draw.textlength(line, font=font_tag))
                except:
                    tw = len(line) * size_of(font_tag)
                x = max(PADDING, (W - tw) // 2)
                draw.text((x + 2, y + 2), line, font=font_tag, fill=(0, 0, 0, alpha // 2))
                draw.text((x, y), line, font=font_tag, fill=(180, 220, 255, alpha))
            y += tag_lh

        return np.array(frame.convert('RGB'))

    frames = [make_frame(i) for i in range(FPS * duration)]

    clip = ImageSequenceClip(frames, fps=FPS)
    if bgm_path and os.path.exists(bgm_path):
        audio = AudioFileClip(bgm_path).subclip(0, duration).volumex(0.25)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, fps=FPS, codec='libx264',
                         audio_codec='aac', logger=None)
    print(f"[영상] 생성 완료: {output_path}")
    return output_path
