#!/usr/bin/env python3
"""Create YouTube Short video — pipe frames directly to ffmpeg."""

from PIL import Image, ImageDraw, ImageFont
import subprocess
import os

BG_PATH = os.path.join(os.path.dirname(__file__), "bg.jpg")
OUTPUT = os.path.join(os.path.dirname(__file__), "output_001.mp4")
FPS = 15
DURATION = 16
W, H = 1080, 1920

font_paths = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]

def load_font(size):
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()

bg_orig = Image.open(BG_PATH).convert("RGB")
bg = bg_orig.resize((W, H), Image.LANCZOS)

segments = [
    (0, 4, [
        (50, (255, 215, 0), "Mặt Trăng gặp Ketu"),
        (50, (255, 215, 0), "tại Magha ♌"),
    ]),
    (4, 8, [
        (40, (255, 255, 255), "23.05.2026"),
        (38, (220, 220, 220), "Ngày của sự tĩnh lặng"),
    ]),
    (8, 12, [
        (40, (255, 215, 0), "Ketu tách rời cảm xúc"),
        (40, (255, 215, 0), "khỏi bản ngã"),
        (24, (0,0,0), ""),
        (32, (255, 255, 255), "Magha — Nakshatra của"),
        (32, (255, 255, 255), "tổ tiên & vương quyền"),
    ]),
    (12, 16, [
        (36, (255, 215, 0), "Carmen AI"),
        (36, (255, 255, 255), "Vedic Astrology Daily"),
        (22, (0,0,0), ""),
        (26, (170, 170, 170), "vedicvn.com"),
    ]),
]

def make_frame(t):
    """Generate a single frame at time t seconds."""
    # Find active segment
    current_lines = segments[-1][2]
    seg_start = 0
    seg_end = DURATION
    for s, e, lines in segments:
        if s <= t < e:
            current_lines = lines
            seg_start, seg_end = s, e
            break
    
    # Calculate fade
    alpha = 1.0
    fade_dur = 0.5
    if t - seg_start < fade_dur:
        alpha = (t - seg_start) / fade_dur
    elif seg_end - t < fade_dur:
        alpha = (seg_end - t) / fade_dur
    alpha = max(0, min(1, alpha))
    
    # Draw background with text box
    frame = bg.copy()
    draw = ImageDraw.Draw(frame)
    
    # Calculate total text block height
    line_hs = []
    for size, color, text in current_lines:
        if not text:
            line_hs.append(24)
            continue
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        line_hs.append(bbox[3] - bbox[1])
    
    spacing = 8
    total_h = sum(line_hs) + spacing * (len(current_lines) - 1)
    
    # Find max width
    max_w = 0
    for (size, color, text), lh in zip(current_lines, line_hs):
        if not text:
            continue
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        max_w = max(max_w, bbox[2] - bbox[0])
    
    pad = 24
    box_x = (W - max_w) // 2 - pad
    box_y = (H - total_h) // 2 - pad
    box_w = max_w + pad * 2
    box_h = total_h + pad * 2
    
    # Dark overlay
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    alpha_int = int(100 * alpha)
    od.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h], radius=16, fill=(0, 0, 0, alpha_int))
    frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(frame)
    
    # Draw text
    y = box_y + pad
    for (size, color, text), lh in zip(current_lines, line_hs):
        if not text:
            y += lh + spacing
            continue
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        r, g, b = color
        draw.text((x, y), text, fill=(r, g, b, int(255*alpha)) if len(color) == 3 else color, font=font)
        y += lh + spacing
    
    return frame

print(f"Piping {DURATION * FPS} frames to ffmpeg...")

# Start ffmpeg process
cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{W}x{H}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "ultrafast",
    "-crf", "23",
    OUTPUT
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

total = DURATION * FPS
for i in range(total):
    t = i / FPS
    frame = make_frame(t)
    proc.stdin.write(frame.tobytes())
    if i % 60 == 0:
        print(f"  Frame {i}/{total}")

proc.stdin.close()
proc.wait()

print(f"✅ Video: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f} KB)")
