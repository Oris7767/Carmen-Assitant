#!/usr/bin/env python3
"""Padmini Ekadashi YouTube Short — Custom Script for 2026-05-27"""

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

# Use generated artwork as background
BG_SOURCE = Path("/Users/kimssa/.openclaw/media/tool-image-generation/padmini-ekadashi-2026-05-27---9b95ec49-e40d-4f12-a03d-d467398ee4bd.jpg")
FRAME_IMAGE = ds.FRAME_IMAGE  # Override to same path so combine_video() picks it up

def generate_padmini_background(data: dict) -> Path:
    """Create 1080×1920 frame using Padmini Ekadashi artwork + text overlay."""
    from PIL import Image, ImageDraw, ImageFont
    
    W, H = 1080, 1920
    
    # Open artwork background
    if BG_SOURCE.exists():
        bg = Image.open(BG_SOURCE).convert("RGB")
        bg = bg.resize((W, W), Image.LANCZOS)
        img = Image.new("RGB", (W, H), (5, 2, 20))
        # Center the artwork
        y_offset = 200
        img.paste(bg, (0, y_offset))
    else:
        img = Image.new("RGB", (W, H), (5, 2, 20))
    
    draw = ImageDraw.Draw(img)
    
    # Stars
    import random
    random.seed(108)
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
    
    # Top section - title
    overlay_top = Image.new("RGBA", (W, 300), (0, 0, 0, 100))
    img.paste(overlay_top, (0, 0), overlay_top)
    
    draw_centered(draw, "🪷 PADMINI EKADASHI 🪷", 40, f_title, (255, 215, 0))
    draw_centered(draw, "Adhika Masa — Ekadashi Linh Thiêng Nhất", 110, f_sub, (255, 255, 255))
    draw_centered(draw, f"☉ {data['sun']['sign']} | ☽ {data['moon']['sign']} ({data['nakshatra']}) | ♃ Exalted", 160, f_date, (180, 180, 200))
    
    # Middle overlay (on artwork)
    mid_y = 480
    overlay_mid = Image.new("RGBA", (W, 330), (0, 0, 0, 120))
    img.paste(overlay_mid, (0, mid_y), overlay_mid)
    
    mid_lines = [
        "Chỉ xuất hiện ~3 năm một lần",
        "trong Adhika Masa (tháng nhuận)",
        "",
        "Năng lượng gấp đôi Ekadashi thường",
        "Cánh cổng tâm linh hiếm có",
    ]
    draw_text_block(draw, mid_lines, mid_y + 20, f_body, (255, 255, 255), 40)
    
    # Bottom - date + key planets
    bot_y = 1550
    overlay_bot = Image.new("RGBA", (W, 370), (0, 0, 0, 120))
    img.paste(overlay_bot, (0, bot_y), overlay_bot)
    
    bot_lines = [
        "🌙 Moon tại Thiên Bình (Swati)",
        "🪐 Jupiter Exalted tại Cự Giải",
        "🔥 Mercury Trine Moon (117°)",
        "",
        "Fast • Thiền 15ph • Om Namo Vasudevaya",
        "",
        f"📅 {data['date']}",
    ]
    draw_text_block(draw, bot_lines, bot_y + 15, f_body, (255, 215, 0), 38)
    
    # Brand watermark
    draw_centered(draw, CHANNEL_NAME, H - 50, f_brand, (130, 130, 130))
    
    img.save(FRAME_IMAGE, quality=95)
    log(f"✅ Padmini frame created: {FRAME_IMAGE} ({W}×{H})")
    return FRAME_IMAGE


def main():
    log("🪷 Padmini Ekadashi YouTube Short — Custom Pipeline")
    log(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Astro data
    log("─" * 50)
    log("📡 STEP 1: Collecting astro data...")
    data = get_astro_data()
    log(f"   ☉ Sun: {data['sun']['sign']} {data['sun']['degree']}°")
    log(f"   ☽ Moon: {data['moon']['sign']} {data['moon']['degree']}° → {data['nakshatra']}")
    
    # Step 2: Custom Padmini topic
    topic = {
        "title": "🪷 Padmini Ekadashi — Ekadashi Linh Thiêng",
        "subtitle": "Adhika Masa | Jupiter Exalted | Swati",
        "description": (
            "Hôm nay là Padmini Ekadashi, Ekadashi linh thiêng nhất trong Adhika Masa, "
            "chỉ xuất hiện khoảng ba năm một lần trong lịch Vedic. "
            "Đây là Ekadashi được Vishnu ban phước đặc biệt — người fasting hôm nay "
            "nhận được gấp đôi công đức so với Ekadashi thông thường. "
            "Jupiter đang Exalted tại Cự Giải, Mặt Trăng tại Thiên Bình Swati, "
            "tạo nên cánh cổng tâm linh hiếm có. "
            "Hãy dành ít nhất mười lăm phút thiền định, niệm Om Namo Bhagavate Vasudevaya, "
            "và kết nối với nguồn năng lượng tối cao này. "
            "Theo dõi La Bàn Số Mệnh mỗi ngày để không bỏ lỡ những ngày đặc biệt của vũ trụ."
        ),
    }
    
    # Step 3: Generate background
    log("─" * 50)
    log("🎨 STEP 3: Generating Padmini Ekadashi background...")
    generate_padmini_background(data)
    
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
