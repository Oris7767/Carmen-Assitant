#!/usr/bin/env python3
"""
daily_short.py — La Bàn Số Mệnh YouTube Shorts Pipeline
========================================================
Tự động tạo & upload 1 YouTube Short/ngày về chiêm tinh Vedic (tiếng Việt).

Pipeline:
  1. Thu thập dữ liệu chiêm tinh hôm nay (Swiss Ephemeris sidereal)
  2. Chọn chủ đề dựa trên transit nổi bật
  3. Tạo ảnh nền (gradient cosmic + text overlay qua PIL)
  4. Tạo giọng đọc tiếng Việt (gTTS)
  5. Ghép video 1080×1920 (ffmpeg)
  6. Upload YouTube (youtube_api.js) — public
  7. Log kết quả vào video_log.csv

Requirements:
  - Python 3.10+ with: swisseph, gtts, Pillow, pytz
  - ffmpeg in PATH
  - Node.js for youtube_api.js
  - OAuth credentials at oauth-credentials.json

Usage:
  python3 daily_short.py                    # full pipeline
  python3 daily_short.py --dry-run          # generate but don't upload
  python3 daily_short.py --upload-only FILE # upload existing video only
  python3 daily_short.py --topic "Custom"   # override auto topic

Author: Carmen AI
Created: 2026-05-27
"""

import os
import sys
import io
import json
import time
import shutil
import subprocess
import traceback
import argparse
import textwrap
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
VENV_PYTHON = WORKSPACE / "youtube-ea-venv" / "bin" / "python3"

# Paths
BG_IMAGE = SCRIPT_DIR / "bg_temp.jpg"
FRAME_IMAGE = SCRIPT_DIR / "frame.png"
AUDIO_FILE = SCRIPT_DIR / "narration.mp3"
VIDEO_FILE = SCRIPT_DIR / "output.mp4"
CSV_LOG = SCRIPT_DIR / "video_log.csv"
YOUTUBE_API_JS = SCRIPT_DIR / "youtube_api.js"

# Branding
CHANNEL_NAME = "La Bàn Số Mệnh"
HASHTAGS = "#ChiêmTinh #VedicAstrology #LaBànSốMệnh"

# Colors
BG_COLOR_TOP = (10, 5, 40)       # Dark navy
BG_COLOR_BOTTOM = (40, 10, 60)   # Dark purple
TEXT_COLOR_PRIMARY = (255, 255, 255)
TEXT_COLOR_ACCENT = (255, 215, 0)  # Gold
TEXT_COLOR_DATE = (200, 200, 200)
TEXT_COLOR_BRAND = (150, 150, 150)

# Timing
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
UPLOAD_TIMEOUT = 60  # seconds

# ── Logging ─────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def warn(msg: str):
    log(msg, "WARN")

def error(msg: str):
    log(msg, "ERROR")

def fatal(msg: str, code: int = 1):
    log(msg, "FATAL")
    sys.exit(code)

# ── Gemini Initialization ────────────────────────────────
GEMINI_AVAILABLE = False
gemini_model = None
try:
    import google.generativeai as genai
    env_paths = ["/root/.env", ".env", str(SCRIPT_DIR / ".env")]
    for ep in env_paths:
        if os.path.exists(ep):
            with open(ep) as f:
                for line in f:
                    if "GEMINI_API_KEY" in line and "=" in line:
                        key = line.split("=", 1)[1].strip()
                        if key:
                            genai.configure(api_key=key)
                            gemini_model = genai.GenerativeModel("gemini-2.5-flash-image")
                            GEMINI_AVAILABLE = True
                        break
            if GEMINI_AVAILABLE:
                break
    if GEMINI_AVAILABLE:
        log("✅ Gemini AI image generation ready")
except Exception as e:
    warn(f"Gemini init failed: {e}")

# ── Dependency Check ────────────────────────────────────────
def check_dependencies() -> dict:
    """Check all required tools are available. Returns missing list."""
    missing = []
    
    # Check Python modules
    for mod in ["swisseph", "gtts", "PIL", "pytz"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(f"Python module: {mod}")
    
    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (not in PATH)")
    
    # Check node
    if not shutil.which("node"):
        missing.append("node (not in PATH)")
    
    # Check youtube_api.js
    if not YOUTUBE_API_JS.exists():
        missing.append(f"{YOUTUBE_API_JS} (not found)")
    
    # Check OAuth credentials
    oauth = SCRIPT_DIR / "oauth-credentials.json"
    if not oauth.exists():
        missing.append(f"{oauth} (not found)")
    
    if missing:
        log(f"⚠️  Missing dependencies: {', '.join(missing)}")
    
    return missing


# ── Step 1: Astro Data ─────────────────────────────────────
def get_astro_data() -> dict:
    """Collect today's Vedic/sidereal planetary positions."""
    import swisseph as swe
    import pytz
    
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    tz = pytz.timezone("Asia/Saigon")
    now = datetime.now(tz)
    jd = swe.julday(now.year, now.month, now.day, 
                     now.hour + now.minute / 60.0)
    
    SIGNS_VN = [
        "Bạch Dương", "Kim Ngưu", "Song Tử", "Cự Giải",
        "Sư Tử", "Xử Nữ", "Thiên Bình", "Bọ Cạp",
        "Nhân Mã", "Ma Kết", "Bảo Bình", "Song Ngư"
    ]
    
    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini",
        "Mrigashira", "Ardra", "Punarvasu", "Pushya",
        "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha",
        "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    
    def get_planet(pid: int) -> tuple:
        """Returns (sign_index, degree_in_sign, total_longitude)."""
        lon = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)[0][0]
        sign_idx = int(lon // 30)
        degree = lon % 30
        return sign_idx, degree, lon
    
    sun_sign, sun_deg, sun_lon = get_planet(swe.SUN)
    moon_sign, moon_deg, moon_lon = get_planet(swe.MOON)
    
    nak_num = int(moon_lon * 27 / 360)
    pada = int((moon_lon * 27 / 360 - nak_num) * 4) + 1
    
    planets = {}
    for pid, name in [(2, "Mercury"), (3, "Venus"), (4, "Mars"), 
                       (5, "Jupiter"), (6, "Saturn")]:
        s, d, lon = get_planet(pid)
        planets[name] = {
            "sign": SIGNS_VN[s],
            "degree": round(d, 1),
            "longitude": lon
        }
        
        # Check aspects to Sun
        diff = abs(sun_lon - lon)
        if diff > 180:
            diff = 360 - diff
        if diff <= 5:
            planets[name]["aspect"] = f"Conjunction ({diff:.1f}°)"
        elif abs(diff - 60) <= 4:
            planets[name]["aspect"] = f"Sextile ({diff:.1f}°)"
        elif abs(diff - 90) <= 4:
            planets[name]["aspect"] = f"Square ({diff:.1f}°)"
        elif abs(diff - 120) <= 4:
            planets[name]["aspect"] = f"Trine ({diff:.1f}°)"
        elif abs(diff - 180) <= 5:
            planets[name]["aspect"] = f"Opposition ({diff:.1f}°)"
    
    return {
        "date": now.strftime("%d.%m.%Y"),
        "date_iso": now.strftime("%Y-%m-%d"),
        "sun": {"sign": SIGNS_VN[sun_sign], "degree": round(sun_deg, 1)},
        "moon": {"sign": SIGNS_VN[moon_sign], "degree": round(moon_deg, 1)},
        "nakshatra": NAKSHATRAS[nak_num],
        "nakshatra_pada": pada,
        "planets": planets,
        "signs_vn": SIGNS_VN,
        "nakshatras": NAKSHATRAS,
    }


# ── Step 2: Topic Selection ────────────────────────────────
def select_topic(data: dict) -> dict:
    """Pick a topic based on today's most interesting transit."""
    
    # Priority: conjunction > opposition > square > trine > nakshatra > sign
    conjunctions = []
    for name, info in data["planets"].items():
        if "aspect" in info and "Conjunction" in info["aspect"]:
            conjunctions.append((name, info))
    
    if conjunctions:
        # Best topic: Sun conjunct X
        name, info = conjunctions[0]
        return {
            "title": f"Mặt Trời & Sao {name} Gặp Nhau",
            "subtitle": f"Tại {info['sign']}",
            "description": (
                f"Hôm nay {data['date']}, Mặt Trời và Sao {name} gặp nhau tại {info['sign']} "
                f"— một sự kết hợp hiếm có giữa ý chí và trí tuệ. "
                f"Vũ trụ gửi thông điệp: hãy suy nghĩ thấu đáo trước khi hành động. "
                f"Theo dõi {CHANNEL_NAME} mỗi ngày để không bỏ lỡ bất kỳ tín hiệu vũ trụ nào."
            ),
        }
    
    # Second choice: Sun opposition something
    oppositions = []
    for name, info in data["planets"].items():
        if "aspect" in info and "Opposition" in info["aspect"]:
            oppositions.append((name, info))
    
    if oppositions:
        name, info = oppositions[0]
        return {
            "title": f"Mặt Trời Đối Đỉnh Sao {name}",
            "subtitle": f"Căng Thẳng & Đột Phá",
            "description": (
                f"Hôm nay {data['date']}, Mặt Trời đối đỉnh Sao {name} — "
                f"năng lượng căng thẳng nhưng cũng là cơ hội để đột phá. "
                f"Hãy giữ bình tĩnh và quan sát. "
                f"Theo dõi {CHANNEL_NAME} mỗi ngày để hiểu rõ năng lượng vũ trụ."
            ),
        }
    
    # Third choice: Notable nakshatra
    nakshatra_meanings = {
        "Ashwini": "Khởi Đầu Mới & Tốc Độ",
        "Bharani": "Sức Mạnh Của Sự Kiềm Chế",
        "Krittika": "Ngọn Lửa Thanh Lọc",
        "Rohini": "Sáng Tạo & Dồi Dào",
        "Mrigashira": "Tìm Kiếm & Khám Phá",
        "Ardra": "Ngôi Sao Bão Tố",
        "Punarvasu": "Sự Trở Lại Của Ánh Sáng",
        "Pushya": "Dinh Dưỡng & Bảo Vệ",
        "Ashlesha": "Sức Mạnh Tiềm Ẩn",
        "Magha": "Vương Quyền & Tổ Tiên",
        "Purva Phalguni": "Nghệ Thuật & Đam Mê",
        "Uttara Phalguni": "Hôn Nhân & Cam Kết",
        "Hasta": "Sức Mạnh Của Đôi Bàn Tay",
        "Chitra": "Ngôi Sao Rực Rỡ",
        "Swati": "Tự Do & Độc Lập",
        "Vishakha": "Quyết Tâm & Thành Công",
        "Anuradha": "Tình Bạn & Hợp Tác",
        "Jyeshtha": "Quyền Lực & Trí Tuệ",
        "Mula": "Gốc Rễ & Sự Thật",
        "Purva Ashadha": "Chiến Thắng & Vinh Quang",
        "Uttara Ashadha": "Chiến Thắng Cuối Cùng",
        "Shravana": "Lắng Nghe & Học Hỏi",
        "Dhanishta": "Âm Nhạc & Sự Giàu Có",
        "Shatabhisha": "Người Chữa Lành",
        "Purva Bhadrapada": "Lửa Tâm Linh",
        "Uttara Bhadrapada": "Trí Tuệ Sâu Thẳm",
        "Revati": "Giải Thoát & Hoàn Thành",
    }
    
    nak = data["nakshatra"]
    meaning = nakshatra_meanings.get(nak, "Năng Lượng Đặc Biệt")
    
    return {
        "title": f"{nak} Nakshatra",
        "subtitle": f"{meaning}",
        "description": (
            f"Hôm nay {data['date']}, Mặt Trăng đi qua {nak} Nakshatra tại "
            f"{data['moon']['sign']} — mang theo năng lượng của {meaning.lower()}. "
            f"Đây là thời điểm để bạn kết nối với nguồn năng lượng này. "
            f"Theo dõi {CHANNEL_NAME} mỗi ngày để cập nhật năng lượng vũ trụ."
        ),
    }


# ── Step 3: Generate Background Image ───────────────────────
def generate_background(topic: dict, data: dict) -> Path:
    """Create a 1080×1920 background image with cosmic gradient + text."""
    from PIL import Image, ImageDraw, ImageFont
    import colorsys
    import random as rnd
    
    W, H = 1080, 1920
    
    img = None
    bg_source = "PIL"
    
    # ── Try Gemini first ──
    if GEMINI_AVAILABLE:
        nak = data["nakshatra"]
        nak_vn = topic.get("subtitle", "")
        moon_sign = data["moon"]["sign"]
        date = data["date"]
        
        prompt = (
            f"A cinematic cosmic background for a YouTube Short about {nak} Nakshatra ({nak_vn}) "
            f"in Vedic Astrology. The Moon is in {moon_sign} today ({date}). "
            f"Deep space gradient, stars, subtle sacred geometry mandala, "
            f"golden celestial symbols, glowing cosmic dust, mystical purple-blue dark palette. "
            f"Professional vertical 9:16 aspect ratio for video background. No text. NO text at all."
        )
        log(f"🎨 Gemini generating image...")
        try:
            response = gemini_model.generate_content(
                [prompt, "Generate a mystical cosmic background image. Vertical 1080x1920. NO TEXT."],
                generation_config={"temperature": 1.0},
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    img = Image.open(io.BytesIO(img_data)).convert("RGB")
                    img = img.resize((W, H), Image.LANCZOS)
                    bg_source = "Gemini"
                    log(f"✅ Gemini image generated")
                    break
        except Exception as e:
            warn(f"Gemini image gen failed: {e}")
    
    # ── PIL Fallback ──
    if img is None:
        log(f"📐 Generating PIL background...")
        img = Image.new("RGB", (W, H))
        pixels = img.load()
        
        # Pick colors based on nakshatra for variety
        rnd.seed(ord(data["nakshatra"][0]) * 100 + len(data["nakshatra"]))
        color_variants = [
            ((10, 5, 40), (40, 10, 60)),   # navy-purple (default)
            ((5, 10, 35), (50, 5, 70)),     # deep blue
            ((15, 5, 25), (55, 10, 45)),    # dark crimson
        ]
        top_c, bot_c = color_variants[rnd.randint(0, len(color_variants) - 1)]
        
        for y in range(H):
            ratio = y / H
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * ratio)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * ratio)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * ratio)
            for x in range(W):
                pixels[x, y] = (r, g, b)
        
        draw = ImageDraw.Draw(img)
        cx, cy = W // 2, 960
        
        for i, radius in enumerate([400, 350, 280, 200, 120]):
            alpha = max(10, 30 - i * 3)
            color = (255, 215, 0, alpha) if i % 2 == 0 else (200, 220, 255, alpha)
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                outline=color, width=max(1, 3 - i // 2)
            )
        
        rnd.seed(None)
        for _ in range(80):
            sx = rnd.randint(20, W - 20)
            sy = rnd.randint(20, H - 20)
            size = rnd.randint(1, 4)
            b = rnd.randint(100, 255)
            draw.ellipse([sx - size, sy - size, sx + size, sy + size],
                         fill=(b, b, b))
        
        bg_source = "PIL"
        log(f"✅ PIL background created")
    
    # ── Text Overlay (applied on either Gemini or PIL image) ──
    # Convert to RGBA for overlay
    img = img.convert("RGBA")
    
    # Find available fonts
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    font_title = font_sub = font_date = font_brand = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_title = ImageFont.truetype(fp, 56)
                font_sub = ImageFont.truetype(fp, 42)
                font_date = ImageFont.truetype(fp, 30)
                font_brand = ImageFont.truetype(fp, 26)
                break
            except:
                pass
    if not font_title:
        font_title = font_sub = font_date = font_brand = ImageFont.load_default()
    
    def draw_centered(draw_obj, text, y, font, fill):
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw_obj.text((x, y), text, font=font, fill=fill)
    
    # Semi-transparent overlays
    overlay = Image.new("RGBA", (W, 450), (0, 0, 0, 160))
    img.paste(overlay, (0, 130), overlay)
    overlay_bot = Image.new("RGBA", (W, 130), (0, 0, 0, 160))
    img.paste(overlay_bot, (0, H - 140), overlay_bot)
    
    # Draw text
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt)
    
    draw_centered(draw, topic["title"], 190, font_title, (255, 255, 255, 255))
    draw_centered(draw, topic["subtitle"], 260, font_sub, (255, 215, 0, 255))
    draw_centered(draw, data["date"], 320, font_date, (200, 200, 200, 255))
    
    planet_text = (
        f"☉ {data['sun']['sign']} {data['sun']['degree']}°  "
        f"☽ {data['moon']['sign']} {data['moon']['degree']}°  "
        f"✦ {data['nakshatra']}"
    )
    draw_centered(draw, planet_text, H - 100, font_date, (180, 180, 180, 255))
    draw_centered(draw, CHANNEL_NAME, H - 60, font_brand, (150, 150, 150, 255))
    
    img = Image.alpha_composite(img, txt)
    img = img.convert("RGB")
    img.save(FRAME_IMAGE, quality=95)
    log(f"✅ Background created ({bg_source}): {FRAME_IMAGE} ({W}×{H})")
    return FRAME_IMAGE


# ── Step 4: Generate Voice Narration ────────────────────────
def generate_narration(topic: dict, data: dict) -> Path:
    """Generate Vietnamese TTS narration using gTTS."""
    from gtts import gTTS
    
    description = topic["description"]
    
    log(f"📝 Narration text ({len(description)} chars): {description[:80]}...")
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            tts = gTTS(text=description, lang="vi", slow=False)
            tts.save(str(AUDIO_FILE))
            
            # Verify file
            size = AUDIO_FILE.stat().st_size
            if size < 1000:
                raise RuntimeError(f"Audio file too small: {size} bytes")
            
            log(f"✅ Narration generated: {AUDIO_FILE} ({size/1024:.0f} KB)")
            return AUDIO_FILE
            
        except Exception as e:
            if attempt < MAX_RETRIES:
                warn(f"gTTS attempt {attempt}/{MAX_RETRIES} failed: {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                fatal(f"gTTS failed after {MAX_RETRIES} attempts: {e}")


# ── Step 5: Combine Video ──────────────────────────────────
def combine_video() -> Path:
    """Combine frame image + audio narration into 1080×1920 MP4."""
    
    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(AUDIO_FILE)],
        capture_output=True, text=True, timeout=10
    )
    
    try:
        duration = float(result.stdout.strip())
    except ValueError:
        fatal(f"Cannot determine audio duration: {result.stdout}")
    
    log(f"🎬 Combining: {FRAME_IMAGE} + {AUDIO_FILE} ({duration:.1f}s)")
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(FRAME_IMAGE),
        "-i", str(AUDIO_FILE),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-t", str(duration),
        str(VIDEO_FILE)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
    except subprocess.TimeoutExpired:
        fatal("ffmpeg timed out after 60s")
    except subprocess.CalledProcessError as e:
        fatal(f"ffmpeg failed: {e.stderr[-500:]}")
    
    size_mb = VIDEO_FILE.stat().st_size / (1024 * 1024)
    log(f"✅ Video created: {VIDEO_FILE} ({size_mb:.1f} MB, {duration:.1f}s)")
    return VIDEO_FILE


# ── Step 6: Upload to YouTube ───────────────────────────────
def upload_youtube(video_path: Path, topic: dict, data: dict, privacy: str = "public") -> str:
    """Upload video to YouTube via youtube_api.js."""
    
    title = f"{topic['title']} | {data['date']}"
    description = f"{topic['description']}\n\n{HASHTAGS}"
    
    cmd = [
        "node", str(YOUTUBE_API_JS),
        str(video_path),
        title,
        description,
        privacy
    ]
    
    log(f"📤 Uploading: {title}")
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=UPLOAD_TIMEOUT, cwd=str(SCRIPT_DIR)
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode != 0:
                raise RuntimeError(f"Upload failed (code {result.returncode}): {output[-500:]}")
            
            # Extract URL from output
            for line in output.split("\n"):
                if "youtube.com/shorts/" in line:
                    video_id = line.split("youtube.com/shorts/")[-1].strip()
                    url = f"https://youtube.com/shorts/{video_id}"
                    log(f"✅ Uploaded: {url}")
                    return url
            
            raise RuntimeError(f"No URL found in output: {output[-300:]}")
            
        except subprocess.TimeoutExpired:
            if attempt < MAX_RETRIES:
                warn(f"Upload timeout (attempt {attempt}/{MAX_RETRIES}). Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                fatal(f"YouTube upload timed out after {MAX_RETRIES} attempts")
        except Exception as e:
            if attempt < MAX_RETRIES:
                warn(f"Upload failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                fatal(f"YouTube upload failed after {MAX_RETRIES} attempts: {e}")


# ── Step 7: Log to CSV ──────────────────────────────────────
def log_to_csv(url: str, topic: dict, data: dict, privacy: str):
    """Append entry to video_log.csv."""
    now = datetime.now()
    line = (
        f'{data["date_iso"]},'
        f'{now.strftime("%H:%M:%S")},'
        f'"{topic["title"]} | {data["date"]}",'
        f'{url},'
        f'short,'
        f'"published via daily_short.py ({privacy})"'
        '\n'
    )
    
    with open(CSV_LOG, "a") as f:
        f.write(line)
    
    log(f"📋 Logged to {CSV_LOG.name}")


# ── Cleanup ─────────────────────────────────────────────────
def cleanup():
    """Remove temporary files."""
    for f in [BG_IMAGE, FRAME_IMAGE, AUDIO_FILE]:
        if f.exists():
            f.unlink()
            log(f"🧹 Cleaned: {f.name}")


# ── Main ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="La Bàn Số Mệnh — Daily YouTube Short Pipeline"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate video but don't upload")
    parser.add_argument("--upload-only", type=str, metavar="FILE",
                        help="Upload an existing video file only")
    parser.add_argument("--topic", type=str, default=None,
                        help="Custom topic title (overrides auto-detection)")
    parser.add_argument("--privacy", type=str, default="public",
                        choices=["public", "unlisted", "private"],
                        help="YouTube privacy setting (default: public)")
    parser.add_argument("--keep-temp", action="store_true",
                        help="Keep temporary files after completion")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Skip dependency check")
    
    args = parser.parse_args()
    
    log("🚀 La Bàn Số Mệnh — Daily Short Pipeline")
    log(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # ── Upload-only mode ──
    if args.upload_only:
        video_path = Path(args.upload_only)
        if not video_path.exists():
            fatal(f"Video not found: {video_path}")
        
        # Minimal data for upload
        data = get_astro_data()
        topic = select_topic(data)
        if args.topic:
            topic["title"] = args.topic
        
        url = upload_youtube(video_path, topic, data, args.privacy)
        log_to_csv(url, topic, data, args.privacy)
        log(f"🎉 Done! {url}")
        return
    
    # ── Check dependencies ──
    if not args.skip_deps:
        missing = check_dependencies()
        if missing:
            log("❌ Missing dependencies. Install with:")
            log("   pip3 install swisseph gtts Pillow pytz --break-system-packages")
            log("   brew install ffmpeg node")
            fatal("Cannot continue without dependencies.")
    
    # ── Full pipeline ──
    try:
        # Step 1: Astro data
        log("─" * 50)
        log("📡 STEP 1: Collecting astro data...")
        data = get_astro_data()
        log(f"   ☉ Sun: {data['sun']['sign']} {data['sun']['degree']}°")
        log(f"   ☽ Moon: {data['moon']['sign']} {data['moon']['degree']}° → "
            f"{data['nakshatra']} pada {data['nakshatra_pada']}")
        
        for name, info in data["planets"].items():
            aspect_str = f" [{info.get('aspect', '')}]" if "aspect" in info else ""
            log(f"   {name}: {info['sign']} {info['degree']}°{aspect_str}")
        
        # Step 2: Select topic
        log("─" * 50)
        log("🧠 STEP 2: Selecting topic...")
        topic = select_topic(data)
        if args.topic:
            topic["title"] = args.topic
        log(f"   Title: {topic['title']}")
        log(f"   Subtitle: {topic['subtitle']}")
        
        # Step 3: Generate background
        log("─" * 50)
        log("🎨 STEP 3: Generating background image...")
        generate_background(topic, data)
        
        # Step 4: Generate narration
        log("─" * 50)
        log("🎙️  STEP 4: Generating voice narration (gTTS)...")
        generate_narration(topic, data)
        
        # Step 5: Combine video
        log("─" * 50)
        log("🎬 STEP 5: Combining video...")
        combine_video()
        
        # Step 6: Upload (or skip if dry-run)
        if args.dry_run:
            log("─" * 50)
            log("🏁 DRY RUN — Skipping upload.")
            log(f"   Video saved at: {VIDEO_FILE}")
            log(f"   Size: {VIDEO_FILE.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            log("─" * 50)
            log("📤 STEP 6: Uploading to YouTube...")
            url = upload_youtube(VIDEO_FILE, topic, data, args.privacy)
            
            # Step 7: Log
            log("─" * 50)
            log("📋 STEP 7: Logging result...")
            log_to_csv(url, topic, data, args.privacy)
            
            log("─" * 50)
            log(f"🎉 ALL DONE! {url}")
        
        # Cleanup
        if not args.keep_temp:
            cleanup()
            # Keep the video file for reference
            if not args.dry_run:
                log(f"📁 Final video: {VIDEO_FILE}")
        
        return 0
        
    except SystemExit:
        raise
    except Exception as e:
        error(f"Pipeline failed: {e}")
        traceback.print_exc()
        log("💡 Check dependencies and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
