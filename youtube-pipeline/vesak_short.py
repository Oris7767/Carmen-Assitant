#!/usr/bin/env python3
"""Vesak / Phật Đản 2026 YouTube Short — Custom Script for 2026-05-31"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Add parent for daily_short imports
sys.path.insert(0, str(SCRIPT_DIR))

import daily_short as ds
from daily_short import (
    get_astro_data, generate_narration, combine_video,
    upload_youtube, log_to_csv, log, warn, error, fatal, CHANNEL_NAME,
    AUDIO_FILE, VIDEO_FILE, CSV_LOG
)

# Use generated Vesak artwork as background
BG_SOURCE = SCRIPT_DIR / "bg_vesak_20260531.jpg"
FRAME_IMAGE = ds.FRAME_IMAGE


def generate_vesak_background(data: dict) -> Path:
    """Create 1080×1920 frame using Vesak artwork + text overlay."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1920

    # Open artwork background
    if BG_SOURCE.exists():
        bg = Image.open(BG_SOURCE).convert("RGB")
        bg = bg.resize((W, W), Image.LANCZOS)
        img = Image.new("RGB", (W, H), (5, 2, 30))
        # Center the artwork
        y_offset = 200
        img.paste(bg, (0, y_offset))
    else:
        img = Image.new("RGB", (W, H), (5, 2, 30))

    draw = ImageDraw.Draw(img)

    # Stars
    import random
    random.seed(2508)
    for _ in range(80):
        sx = random.randint(20, W - 20)
        sy = random.randint(20, H - 20)
        size = random.randint(1, 3)
        b = random.randint(100, 255)
        draw.ellipse([sx-size, sy-size, sx+size, sy+size], fill=(b, b, b))

    # Fonts
    font_dir = "/System/Library/Fonts"
    font_bold = font_normal = font_small = None

    for f in ["Helvetica.ttc", "Supplemental/Arial.ttf"]:
        fp = os.path.join(font_dir, f)
        if os.path.exists(fp):
            font_bold = fp
            font_normal = fp
            font_small = fp
            break

    try:
        f_title = ImageFont.truetype(font_bold or "Helvetica", 58)
        f_sub = ImageFont.truetype(font_normal or "Helvetica", 38)
        f_body = ImageFont.truetype(font_normal or "Helvetica", 28)
        f_date = ImageFont.truetype(font_small or "Helvetica", 26)
        f_brand = ImageFont.truetype(font_small or "Helvetica", 24)
    except:
        f_title = f_sub = f_body = f_date = f_brand = ImageFont.load_default()

    def draw_centered(draw_obj, text, y, font, fill):
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw_obj.text((x, y), text, font=font, fill=fill)

    def draw_text_block(draw_obj, lines, start_y, font, fill, line_spacing=36):
        y = start_y
        for line in lines:
            draw_centered(draw_obj, line, y, font, fill)
            y += line_spacing

    # Top section - title with dark overlay
    overlay_top = Image.new("RGBA", (W, 300), (0, 0, 0, 130))
    img.paste(overlay_top, (0, 0), overlay_top)

    draw_centered(draw, "🪷 VESAK 2026 🪷", 30, f_title, (255, 215, 0))
    draw_centered(draw, "Phật Đản • Thành Đạo • Niết-bàn", 100, f_sub, (255, 255, 255))
    draw_centered(draw, f"☉ {data['sun']['sign']} {data['sun']['degree']}° ⊕ ☽ {data['moon']['sign']} {data['moon']['degree']}° ({data['nakshatra']})", 160, f_date, (200, 180, 220))
    draw_centered(draw, "Trăng Tròn Vesakha — Năng Lượng Giác Ngộ", 200, f_date, (180, 180, 200))

    # Middle overlay (on artwork) - spiritual meaning
    mid_y = 520
    overlay_mid = Image.new("RGBA", (W, 380), (0, 0, 0, 140))
    img.paste(overlay_mid, (0, mid_y), overlay_mid)

    mid_lines = [
        "Ngày thiêng liêng nhất của Phật giáo",
        "Kỷ niệm Đức Phật Đản sinh",
        "Thành đạo dưới cội Bồ Đề",
        "Và Nhập Niết-bàn tại Sala",
        "",
        "Trăng Tròn — Năng Lượng Viên Mãn",
        "Đối đỉnh Kim Ngưu ♉ & Bọ Cạp ♏",
    ]
    draw_text_block(draw, mid_lines, mid_y + 20, f_body, (255, 255, 255), 42)

    # Bottom - astro data + practice
    bot_y = 1480
    overlay_bot = Image.new("RGBA", (W, 440), (0, 0, 0, 140))
    img.paste(overlay_bot, (0, bot_y), overlay_bot)

    bot_lines = [
        "🌙 Mặt Trăng tại Jyeshtha Nakshatra",
        "⭐ Năng Lượng: Trí Tuệ & Giải Thoát",
        "☍ Full Moon 20:45 GMT+7",
        "",
        "🧘 Thiền định • Niệm Phật • Ăn chay",
        "🪷 Om Mani Padme Hum",
        "",
        f"📅 31.05.2026 — {CHANNEL_NAME}",
    ]
    draw_text_block(draw, bot_lines, bot_y + 15, f_body, (255, 215, 0), 38)

    # Brand watermark
    draw_centered(draw, CHANNEL_NAME, H - 50, f_brand, (130, 130, 130))

    img.save(FRAME_IMAGE, quality=95)
    log(f"✅ Vesak frame created: {FRAME_IMAGE} ({W}×{H})")
    return FRAME_IMAGE


def main():
    log("🪷 Vesak / Phật Đản 2026 YouTube Short — Custom Pipeline")
    log(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Astro data
    log("─" * 50)
    log("📡 STEP 1: Collecting astro data...")
    data = get_astro_data()
    log(f"   ☉ Sun: {data['sun']['sign']} {data['sun']['degree']}°")
    log(f"   ☽ Moon: {data['moon']['sign']} {data['moon']['degree']}° → {data['nakshatra']}")

    # Step 2: Vesak topic
    topic = {
        "title": "🪷 Vesak 2026 — Phật Đản, Thành Đạo, Niết-bàn",
        "subtitle": "Trăng Tròn Vesakha | Jyeshtha Nakshatra",
        "description": (
            "Hôm nay là ngày Vesak, ngày lễ thiêng liêng nhất của Phật giáo, "
            "kỷ niệm ba sự kiện trọng đại trong cuộc đời Đức Phật: Đản sinh, Thành đạo, và Nhập Niết-bàn. "
            "Về mặt chiêm tinh Vedic, đây là ngày Trăng Tròn tháng Vesakha, "
            "Mặt Trời tại Kim Ngưu đối đỉnh Mặt Trăng tại Bọ Cạp, "
            "mang đến năng lượng viên mãn, giác ngộ, và buông bỏ. "
            "Mặt Trăng đi qua Jyeshtha Nakshatra, ngôi sao của trí tuệ và quyền lực tâm linh, "
            "nhắc nhở chúng ta rằng sức mạnh thực sự nằm trong sự tĩnh lặng và từ bi. "
            "Hãy dành ngày hôm nay để thiền định, niệm Phật, ăn chay, "
            "và kết nối với năng lượng giải thoát của Vesak. "
            "Om Mani Padme Hum. "
            "Theo dõi La Bàn Số Mệnh mỗi ngày để không bỏ lỡ những tín hiệu vũ trụ."
        ),
    }

    # Step 3: Generate background
    log("─" * 50)
    log("🎨 STEP 3: Generating Vesak background...")
    generate_vesak_background(data)

    # Step 4: Generate narration
    log("─" * 50)
    log("🎙️  STEP 4: Generating voice narration...")
    generate_narration(topic, data)

    # Step 5: Combine video
    log("─" * 50)
    log("🎬 STEP 5: Combining video...")
    combine_video()

    # Step 6: Upload to YouTube
    log("─" * 50)
    log("📤 STEP 6: Uploading to YouTube...")
    url = upload_youtube(VIDEO_FILE, topic, data, "public")

    # Step 7: Log
    log("─" * 50)
    log("📋 STEP 7: Logging...")
    log_to_csv(url, topic, data, "public")

    # Cleanup temp files
    for f in [AUDIO_FILE, FRAME_IMAGE]:
        if f.exists():
            f.unlink()

    log("─" * 50)
    log(f"🪷 DONE! {url}")
    return url


if __name__ == "__main__":
    main()
