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
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def render_frame(bg, lines, progress, W=1080, H=1920):
    frame = bg.copy().convert('RGBA')
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 150))
    frame = Image.alpha_composite(frame, overlay)
    draw = ImageDraw.Draw(frame)

    font_lg = find_font(58)
    font_sm = find_font(34)
    LINE_H = 82
    total_h = len(lines) * LINE_H
    y0 = (H - total_h) // 2 - 30

    for i, line in enumerate(lines):
        # Staggered fade-in: each line appears at its own time
        reveal_at = i / max(len(lines), 1)
        alpha = int(max(0, min(1, (progress - reveal_at) / (1.0 / max(len(lines), 1)) * 2)) * 255)
        if alpha <= 0:
            continue
        is_tag = line.strip().startswith('#')
        font = font_sm if is_tag else font_lg
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except:
            tw = len(line) * (28 if is_tag else 42)
        x = max(40, (W - tw) // 2)
        y = y0 + i * LINE_H
        draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, alpha // 2))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, alpha))

    return np.array(frame.convert('RGB'))

def create_reels_video(text: str, image_path: str = None,
                       output_path: str = "reels_output.mp4",
                       bgm_path: str = None, duration: int = 18) -> str:
    from moviepy.editor import ImageSequenceClip, AudioFileClip

    W, H, FPS = 1080, 1920, 24
    total = FPS * duration

    if image_path and os.path.exists(image_path):
        bg = Image.open(image_path).convert('RGB')
        iw, ih = bg.size
        scale = max(W / iw, H / ih)
        bg = bg.resize((int(iw*scale), int(ih*scale)), Image.LANCZOS)
        left = (bg.width - W) // 2
        top = (bg.height - H) // 2
        bg = bg.crop((left, top, left+W, top+H))
    else:
        bg = create_gradient_bg(W, H)

    lines = [l for l in text.split('\n') if l.strip()]
    frames = []
    for i in range(total):
        progress = min(i / (total * 0.75), 1.0)  # fully shown at 75% of duration
        frames.append(render_frame(bg, lines, progress, W, H))

    clip = ImageSequenceClip(frames, fps=FPS)
    if bgm_path and os.path.exists(bgm_path):
        audio = AudioFileClip(bgm_path).subclip(0, duration).volumex(0.25)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, fps=FPS, codec='libx264',
                         audio_codec='aac', logger=None)
    print(f"[영상] 생성 완료: {output_path}")
    return output_path
