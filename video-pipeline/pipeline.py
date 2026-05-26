#!/usr/bin/env python3
"""
Video Pipeline — Auto Video Generator from Simple Prompts
=========================================================
Flow:
  User Prompt → Gemini (script JSON) → [N scenes]
    → Gemini Imagen (image) → gTTS (voiceover) → ffmpeg (composite)
    → Final MP4 video

Usage:
  python pipeline.py "tạo video người que, triết lý Elon Musk, 10 phân cảnh"
  python pipeline.py "make a stickman video about stoicism, 8 scenes" --lang en
"""

import os
import sys
import json
import time
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types
from gtts import gTTS
from dotenv import load_dotenv

# ─── Config ───────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set. Create .env file or export GEMINI_API_KEY")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

# Project paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"

# Models
SCRIPT_MODEL = "gemini-2.5-flash"         # Fast, high quota, good for structured JSON
IMAGE_MODEL = "gemini-2.5-flash-image"    # Native image generation

# ─── Prompt Templates ──────────────────────────────────────────────────

SCRIPT_SYSTEM_PROMPT = """You are a professional video script writer and storyboard artist.

Given a simple user prompt, generate a complete video production package as JSON.

OUTPUT FORMAT (strict JSON, no markdown wrapping):
{
  "title": "Video title",
  "language": "vi",
  "total_scenes": 10,
  "style_notes": "stick figure style, black on white background, minimalist",
  "scenes": [
    {
      "scene": 1,
      "description": "What happens in this scene",
      "image_prompt": "DETAILED prompt for AI image generation. Include style, composition, colors, mood. Be specific. Must be in English.",
      "narration": "The voiceover text for this scene. Keep each scene 1-3 sentences.",
      "duration_seconds": 6
    }
  ]
}

CRITICAL RULES:
1. image_prompt: ALWAYS write in ENGLISH. Be ultra-specific: describe characters, poses, background, colors, composition, style. Start with "minimalist stick figure drawing, black lines on white background, ..." for stickman style. Include "no text, no words, textless" at the end.
2. narration: Write in the user's requested language. Natural, conversational tone.
3. duration_seconds: Match narration length + 2s buffer. Typically 5-8 seconds per scene.
4. Output ONLY valid JSON. No markdown code blocks, no explanations."""


# ─── Core Functions ────────────────────────────────────────────────────

def generate_script(user_prompt: str, language: str = "vi") -> dict:
    """Step 1: Gemini generates structured script JSON from user prompt."""
    print(f"\n📝 [1/4] Generating script from: '{user_prompt[:80]}...'")

    full_prompt = f"""{SCRIPT_SYSTEM_PROMPT}

USER REQUEST: {user_prompt}
Language: {language}
"""

    response = client.models.generate_content(
        model=SCRIPT_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            top_p=0.95,
            max_output_tokens=8192,
        )
    )

    raw = response.text.strip()
    # Clean markdown wrapping
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.rstrip().endswith("```"):
            raw = raw[: raw.rfind("```")].strip()
    if raw.startswith("json\n"):
        raw = raw[5:]

    try:
        script = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            script = json.loads(raw[start:end])
        else:
            raise ValueError(f"Could not parse Gemini response as JSON:\n{raw[:500]}")

    print(f"   ✅ Script: '{script.get('title', 'Untitled')}' — {len(script['scenes'])} scenes")
    return script


def generate_image(prompt: str, output_path: Path, retries: int = 5) -> Path:
    """Step 2: Gemini Imagen generates image from prompt."""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                )
            )

            # Extract image data from response parts
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.inline_data and part.inline_data.data:
                                mime = part.inline_data.mime_type or "image/png"
                                ext = mime.split("/")[-1]
                                img_path = output_path.with_suffix(f".{ext}")
                                img_path.write_bytes(part.inline_data.data)
                                return img_path

            raise ValueError("No image data in Gemini response")

        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                wait = min((attempt + 1) * 15, 90)  # 15s, 30s, 45s, 60s, 90s max
                print(f"   ⚠️  Rate limited, waiting {wait}s (attempt {attempt+1}/{retries})...")
                time.sleep(wait)
            elif attempt < retries - 1:
                wait = (attempt + 1) * 5
                print(f"   ⚠️  Image gen failed, retrying in {wait}s ({attempt+1}/{retries}): {err[:100]}")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(f"Failed to generate image after {retries} attempts")


def generate_audio(narration: str, output_path: Path, language: str = "vi") -> Path:
    """Step 3: gTTS generates voiceover audio."""
    lang_map = {"vi": "vi", "en": "en", "fr": "fr", "ja": "ja", "ko": "ko"}
    lang_code = lang_map.get(language.lower(), language.lower()[:2])

    tts = gTTS(text=narration, lang=lang_code, slow=False)
    audio_path = output_path.with_suffix(".mp3")
    tts.save(str(audio_path))
    return audio_path


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0


def composite_scene(image_path: Path, audio_path: Path, output_path: Path,
                    duration: float = None) -> Path:
    """Step 4: ffmpeg composites image + audio into video clip."""
    if duration is None:
        duration = get_audio_duration(audio_path)
    duration += 0.3  # small buffer

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white",
        "-shortest",
        str(output_path)
    ]

    subprocess.run(cmd, capture_output=True, check=True, timeout=60)
    return output_path


def concat_videos(video_paths: list[Path], output_path: Path) -> Path:
    """Concatenate multiple video clips into final video."""
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w") as f:
        for vp in video_paths:
            f.write(f"file '{vp.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path)
    ]

    subprocess.run(cmd, capture_output=True, check=True, timeout=120)
    concat_file.unlink()
    return output_path


# ─── Main Pipeline ─────────────────────────────────────────────────────

def run_pipeline(user_prompt: str, language: str = "vi") -> Path:
    """Run the full video generation pipeline."""
    start_time = time.time()

    # Create timestamped output folder
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_hash = hashlib.md5(user_prompt.encode()).hexdigest()[:8]
    run_dir = OUTPUT_DIR / f"{ts}_{prompt_hash}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"🎬 VIDEO PIPELINE")
    print(f"   Output: {run_dir}")
    print(f"{'='*60}")

    # ── Step 1: Generate Script ──
    script = generate_script(user_prompt, language)
    script_path = run_dir / "script.json"
    script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"   💾 Script saved: {script_path}")

    # ── Step 2 & 3 & 4: Generate Images + Audio + Composite per scene ──
    scenes = script["scenes"]
    total = len(scenes)
    scene_videos = []

    for i, scene in enumerate(scenes):
        scene_num = scene["scene"]
        desc = scene.get("description", "")[:60]
        print(f"\n🎨 [{scene_num}/{total}] Scene {scene_num}: {desc}")

        # Generate image
        img_path = run_dir / f"scene_{scene_num:02d}_image"
        print(f"   🖼️  Generating image...")
        img_path = generate_image(scene["image_prompt"], img_path)
        print(f"   ✅ Image: {img_path.name}")

        # Generate audio
        audio_path = run_dir / f"scene_{scene_num:02d}_audio"
        narration = scene["narration"]
        print(f"   🎙️  Generating voiceover ({len(narration)} chars)...")
        audio_path = generate_audio(narration, audio_path, script.get("language", language))
        print(f"   ✅ Audio: {audio_path.name}")

        # Composite video clip
        video_path = run_dir / f"scene_{scene_num:02d}.mp4"
        duration = scene.get("duration_seconds")
        print(f"   🎞️  Compositing video...")
        composite_scene(img_path, audio_path, video_path, duration)
        scene_videos.append(video_path)
        print(f"   ✅ Video clip: {video_path.name}")

    # ── Step 5: Concat all scenes ──
    print(f"\n🔗 Concatenating {len(scene_videos)} scenes...")
    safe_title = script.get("title", "output").replace(" ", "_").replace("/", "_")
    final_video = run_dir / f"{safe_title}.mp4"
    concat_videos(scene_videos, final_video)

    elapsed = time.time() - start_time
    file_size_mb = final_video.stat().st_size / (1024 * 1024)

    print(f"\n{'='*60}")
    print(f"✅ DONE! Final video: {final_video}")
    print(f"   Scenes: {total} | "
          f"Duration: ~{sum(s.get('duration_seconds', 5) for s in scenes)}s")
    print(f"   File size: {file_size_mb:.1f} MB | Time: {elapsed:.0f}s")
    print(f"{'='*60}")

    return final_video


# ─── CLI ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Examples:")
        print('  python pipeline.py "tạo video người que, triết lý Elon Musk, 10 phân cảnh"')
        print('  python pipeline.py "make a stickman video about stoicism, 8 scenes" --lang en')
        sys.exit(1)

    user_prompt = sys.argv[1]

    # Parse optional --lang flag
    language = "vi"
    args = sys.argv[2:]
    for i, arg in enumerate(args):
        if arg == "--lang" and i + 1 < len(args):
            language = args[i + 1]

    # Auto-detect language if prompt is mostly English
    if "--lang" not in " ".join(args):
        english_chars = sum(1 for c in user_prompt if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in user_prompt if c.isalpha())
        if total_chars > 0 and english_chars / total_chars > 0.8:
            language = "en"

    try:
        final_video = run_pipeline(user_prompt, language)
        print(f"\n📁 {final_video}")
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
