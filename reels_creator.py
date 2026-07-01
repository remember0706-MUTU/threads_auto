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

    if not tag_lines_raw and body_lines_raw:
        last = body_lines_raw[-1]
        idx = last.find('#')
        if idx != -1:
            before = last[:idx].strip()
            body_lines_raw[-1:] = [before] if before else []
            tag_lines_raw = [last[idx:].strip()]

    # 영어 raw 라인 파싱 (해시태그 제외)
    en_lines_raw = []
    if text_en:
        en_raw = [l.strip() for l in text_en.split('\n')
                  if l.strip() and not l.strip().startswith('#')]
        en_lines_raw = [strip_emoji(l).strip() for l in en_raw if strip_emoji(l).strip()]

    # 줄 수 불일치 방지: min() 기준으로 완전한 쌍만 사용
    n_pairs = min(len(body_lines_raw), len(en_lines_raw)) if (text_en and en_lines_raw) else len(body_lines_raw)
    n_pairs = max(n_pairs, 1)
    if n_pairs <= 5:
        ko_size, en_size = 42, 26
    elif n_pairs <= 7:
        ko_size, en_size = 38, 24
    else:
        ko_size, en_size = 34, 22

    font_body = find_korean_font(ko_size)
    font_tag  = find_korean_font(26)
    font_en   = find_korean_font(en_size) if text_en else None

    # ── 인터리브 쌍 구성: 한글·영어 줄 수가 같은 범위만 쌍으로 묶음 ──
    pairs = []
    pair_count = min(len(body_lines_raw), len(en_lines_raw)) if (text_en and en_lines_raw) else 0
    for i in range(pair_count):
        ko_w = wrap_text(dummy_draw, body_lines_raw[i], font_body, MAX_W)
        en_w = wrap_text(dummy_draw, en_lines_raw[i], font_en, MAX_W) if font_en else []
        if ko_w:
            pairs.append((ko_w, en_w))
    # 영어 없는 경우 한글만 표시
    if not pairs:
        for l in body_lines_raw:
            ko_w = wrap_text(dummy_draw, l, font_body, MAX_W)
            if ko_w:
                pairs.append((ko_w, []))

    # 해시태그 줄바꿈
    tag_lines = []
    for l in tag_lines_raw:
        tag_lines.extend(wrap_text(dummy_draw, l, font_tag, MAX_W))

    print(f"[영상] {len(pairs)}쌍 (한글+영어 인터리브), 해시태그 {len(tag_lines)}줄")

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
    body_lh  = int(size_of(font_body) * 1.5) if font_body else 58
    tag_lh   = int(size_of(font_tag)  * 1.5) if font_tag  else 36
    en_lh    = int(size_of(font_en)   * 1.5) if font_en   else 34
    KO_EN_GAP = 4    # 한글 줄과 그 아래 영어 줄 사이
    PAIR_GAP  = 20   # 쌍(pair)과 다음 쌍 사이

    total_h = 0
    for ko_w, en_w in pairs:
        total_h += len(ko_w) * body_lh
        if en_w:
            total_h += KO_EN_GAP + len(en_w) * en_lh
    total_h += PAIR_GAP * max(0, len(pairs) - 1)
    total_h += (20 + len(tag_lines) * tag_lh) if tag_lines else 0
    y0 = max(PADDING, (H - total_h) // 2)

    # 애니메이션 타이밍용 총 유닛 수
    total_units = sum(len(ko) + len(en) for ko, en in pairs) + len(tag_lines)

    def draw_text_line(draw, line, font, color, y_pos, alpha):
        try:
            tw = int(draw.textlength(line, font=font))
        except:
            tw = len(line) * size_of(font)
        x = max(PADDING, (W - tw) // 2)
        draw.text((x + 2, y_pos + 2), line, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y_pos), line, font=font, fill=(*color, alpha))

    def make_frame(i):
        t = i / (FPS * duration)
        frame = bg.copy().convert('RGBA')
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 155))
        frame = Image.alpha_composite(frame, overlay)
        draw = ImageDraw.Draw(frame)

        y = y0
        unit_idx = 0

        # 인터리브: 한글 → 영어 → 한글 → 영어 ...
        for p_idx, (ko_lines, en_lines) in enumerate(pairs):
            for line in ko_lines:
                reveal_t = (unit_idx / max(total_units, 1)) * 0.4
                alpha = int(max(0.0, min(1.0, (t - reveal_t) / 0.08)) * 255)
                if alpha > 0 and font_body:
                    draw_text_line(draw, line, font_body, (255, 255, 255), y, alpha)
                y += body_lh
                unit_idx += 1

            if en_lines:
                y += KO_EN_GAP
                for line in en_lines:
                    reveal_t = (unit_idx / max(total_units, 1)) * 0.4
                    alpha = int(max(0.0, min(1.0, (t - reveal_t) / 0.08)) * 255)
                    if alpha > 0 and font_en:
                        draw_text_line(draw, line, font_en, (200, 200, 200), y, alpha)
                    y += en_lh
                    unit_idx += 1

            if p_idx < len(pairs) - 1:
                y += PAIR_GAP

        # 해시태그 (연파랑)
        y += 20
        for line in tag_lines:
            reveal_t = (unit_idx / max(total_units, 1)) * 0.4
            alpha = int(max(0.0, min(1.0, (t - reveal_t) / 0.08)) * 255)
            if alpha > 0 and font_tag:
                draw_text_line(draw, line, font_tag, (180, 220, 255), y, alpha)
            y += tag_lh
            unit_idx += 1

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
