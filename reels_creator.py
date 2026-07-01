from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

def create_gradient_bg(width=1080, height=1920, c1=(15, 15, 35), c2=(50, 20, 80)):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / height
        arr[y] = [int(c1[i]*(1-t) + c2[i]*t) for i in range(3)]
    return Image.fromarray(arr)

def find_font(size):
    paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/malgun.ttf',
        '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def measure_text(draw, text, font):
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    except:
        return len(text) * (font.size if hasattr(font, 'size') else 20)

def wrap_line(draw, text, font, max_width):
    """한 줄 텍스트를 max_width 픽셀 이내로 자동 줄바꿈."""
    if measure_text(draw, text, font) <= max_width:
        return [text]
    result = []
    current = ""
    for char in text:
        test = current + char
        if measure_text(draw, test, font) > max_width:
            if current:
                result.append(current)
            current = char
        else:
            current = test
    if current:
        result.append(current)
    return result

def prepare_lines(draw, text, max_width, body_font, tag_font):
    """텍스트를 본문줄과 해시태그줄로 분리 후 각각 줄바꿈."""
    raw_lines = [l for l in text.split('\n') if l.strip()]
    body_lines = []
    tag_lines = []
    for line in raw_lines:
        if line.strip().startswith('#'):
            tag_lines.extend(wrap_line(draw, line.strip(), tag_font, max_width))
        else:
            body_lines.extend(wrap_line(draw, line.strip(), body_font, max_width))

    # 해시태그가 없으면 마지막 줄에서 # 찾아 분리
    if not tag_lines and body_lines:
        last = body_lines[-1]
        if '#' in last:
            idx = last.index('#')
            before = last[:idx].strip()
            tags = last[idx:].strip()
            body_lines[-1:] = ([before] if before else [])
            tag_lines.extend(wrap_line(draw, tags, tag_font, max_width))

    return body_lines, tag_lines

def render_frame(bg, body_lines, tag_lines, progress, W=1080, H=1920):
    frame = bg.copy().convert('RGBA')
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 160))
    frame = Image.alpha_composite(frame, overlay)
    draw = ImageDraw.Draw(frame)

    PADDING = 60          # 좌우 여백
    max_width = W - PADDING * 2

    # 폰트 크기: 본문 줄 수에 따라 동적 조정
    body_count = len(body_lines)
    if body_count <= 4:
        body_size, body_lh = 56, 80
    elif body_count <= 6:
        body_size, body_lh = 48, 70
    elif body_count <= 8:
        body_size, body_lh = 42, 62
    else:
        body_size, body_lh = 36, 54

    tag_size, tag_lh = 30, 46

    font_body = find_font(body_size)
    font_tag  = find_font(tag_size)

    # 본문/태그가 아직 기본 폰트 사이즈로 측정된 거라면 재측정 후 재래핑
    body_lines_final = []
    for l in body_lines:
        body_lines_final.extend(wrap_line(draw, l, font_body, max_width))
    tag_lines_final = []
    for l in tag_lines:
        tag_lines_final.extend(wrap_line(draw, l, font_tag, max_width))

    # 전체 높이 계산해서 수직 중앙 배치
    total_h = (len(body_lines_final) * body_lh
               + (20 if tag_lines_final else 0)
               + len(tag_lines_final) * tag_lh)
    y0 = max(80, (H - total_h) // 2 - 40)
    all_count = len(body_lines_final) + len(tag_lines_final)

    def draw_line(text, x, y, font, alpha, color=(255, 255, 255)):
        a = int(alpha)
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, a // 2))
        draw.text((x, y), text, font=font, fill=(*color, a))

    idx = 0
    y = y0

    # 본문 줄
    for i, line in enumerate(body_lines_final):
        reveal_at = i / max(all_count, 1)
        raw_alpha = (progress - reveal_at) / (1.0 / max(all_count, 1)) * 2
        alpha = int(max(0, min(1, raw_alpha)) * 255)
        if alpha > 0:
            tw = measure_text(draw, line, font_body)
            x = max(PADDING, (W - tw) // 2)
            draw_line(line, x, y, font_body, alpha)
        y += body_lh
        idx += 1

    y += 20  # 본문-해시태그 간격

    # 해시태그 줄
    for i, line in enumerate(tag_lines_final):
        j = len(body_lines_final) + i
        reveal_at = j / max(all_count, 1)
        raw_alpha = (progress - reveal_at) / (1.0 / max(all_count, 1)) * 2
        alpha = int(max(0, min(1, raw_alpha)) * 255)
        if alpha > 0:
            tw = measure_text(draw, line, font_tag)
            x = max(PADDING, (W - tw) // 2)
            draw_line(line, x, y, font_tag, alpha, color=(200, 230, 255))
        y += tag_lh
        idx += 1

    return np.array(frame.convert('RGB'))

def create_reels_video(text: str, image_path: str = None,
                       output_path: str = "reels_output.mp4",
                       bgm_path: str = None, duration: int = 18) -> str:
    from moviepy.editor import ImageSequenceClip, AudioFileClip

    W, H, FPS = 1080, 1920, 24
    total = FPS * duration

    # 배경 이미지
    if image_path and os.path.exists(image_path):
        bg = Image.open(image_path).convert('RGB')
        iw, ih = bg.size
        scale = max(W / iw, H / ih)
        bg = bg.resize((int(iw*scale), int(ih*scale)), Image.LANCZOS)
        left = (bg.width - W) // 2
        top  = (bg.height - H) // 2
        bg = bg.crop((left, top, left+W, top+H))
    else:
        bg = create_gradient_bg(W, H)

    # 텍스트 미리 파싱 (dummy draw로 측정)
    dummy_img  = Image.new('RGB', (W, H))
    dummy_draw = ImageDraw.Draw(dummy_img)
    font_body_tmp = find_font(56)
    font_tag_tmp  = find_font(30)
    body_lines, tag_lines = prepare_lines(
        dummy_draw, text, W - 120, font_body_tmp, font_tag_tmp
    )

    frames = []
    for i in range(total):
        progress = min(i / (total * 0.75), 1.0)
        frames.append(render_frame(bg, body_lines, tag_lines, progress, W, H))

    clip = ImageSequenceClip(frames, fps=FPS)
    if bgm_path and os.path.exists(bgm_path):
        audio = AudioFileClip(bgm_path).subclip(0, duration).volumex(0.25)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, fps=FPS, codec='libx264',
                         audio_codec='aac', logger=None)
    print(f"[영상] 생성 완료: {output_path}")
    return output_path
