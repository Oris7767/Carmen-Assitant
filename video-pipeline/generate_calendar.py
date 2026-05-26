#!/usr/bin/env python3
"""
Generate 30-day IG Reels Content Calendar JSON
Output: image prompts + video prompts per Reel | No voiceover | Pure ASMR
"""
from google import genai
from google.genai import types
import os, json
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = """You are an Instagram content strategist for a Slow Living ASMR channel.

The channel features an AI influencer named "Mai" — a young Asian woman with long dark hair, wearing neutral-toned linen dresses (beige, cream, olive). All content is POV (first-person perspective) or shows Mai from behind/side — never direct face-on. Pure visual + natural ASMR sounds. NO TALKING. NO VOICEOVER.

Generate a 14-day content calendar. Each day = 1 Reel (30-60 seconds).

Content Pillars (rotate through these):
1. Morning Ritual — tea/coffee, morning light, steam
2. Nature POV — walking in forest, stream, garden, rain
3. Cooking ASMR — vegetarian, fresh ingredients, cast iron, wooden tools
4. Slow Moments — reading, writing, flower arranging, folding clothes
5. Seasonal/Weather — rain on leaves, morning dew, golden hour, wind

Aesthetic: minimalist, wabi-sabi, neutral tones, natural light, linen textures, ceramics, wood, botanicals.
Colors: beige, cream, olive green, warm brown, soft white.

OUTPUT FORMAT — STRICT JSON, NO MARKDOWN:
{
  "channel": "Mai - Slow Living ASMR",
  "persona": "Young Asian woman, long dark hair, neutral linen dresses, never shows face directly",
  "total_reels": 14,
  "content_calendar": [
    {
      "day": 1,
      "pillar": "Morning Ritual",
      "title": "Vietnamese title here",
      "description": "English description of the scene",
      "image_prompt": "ULTRA-DETAILED English prompt for AI image generation. Describe exact composition, lighting, colors, camera angle, what is visible. POV shot or behind-view. Include: 'young Asian woman, long dark hair, neutral linen dress, photorealistic, cinematic lighting, 9:16 vertical aspect ratio, no text, no words'",
      "video_prompt": "English prompt for AI video generation FROM this image. Describe gentle camera movement, what animates: steam rising, leaves swaying, light shifting. Smooth, slow motion. 5-8 seconds of described motion.",
      "duration_seconds": 35,
      "sound_design": "List specific ASMR sounds: e.g. water pouring, gentle ceramic clink, morning birds distant, soft lo-fi background at 20% volume",
      "hashtags": ["#slowliving", "#morningritual", "#asmr", "#slowlivingvietnam"],
      "best_post_time": "06:30 GMT+7"
    }
  ]
}

CRITICAL RULES:
- image_prompt: MUST be in English. Ultra-detailed. Include "9:16 vertical aspect ratio, photorealistic, cinematic lighting, no text, no words" at the end. 50-100 words.
- video_prompt: MUST be in English. Describe exactly what MOVES. Gentle, slow movements only. 20-40 words.
- title: Vietnamese (for Vietnamese audience)
- description: English (for internal reference)
- sound_design: List 3-5 specific ASMR sounds
- hashtags: 5-7 relevant hashtags, mix of broad + niche
- best_post_time: Rotate between 06:30, 07:00, 20:00, 20:30, 21:00 GMT+7
- DUMP ALL 14 REELS. Do not truncate. Do not use "...". Complete every field for every reel.
- OUTPUT ONLY VALID JSON. NO MARKDOWN FENCES. NO EXPLANATIONS."""

print("📝 Generating 14-day content calendar...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=PROMPT,
    config=types.GenerateContentConfig(temperature=0.95, max_output_tokens=16384)
)

raw = response.text.strip()
if raw.startswith("```"):
    raw = raw.split("\n", 1)[1]
    if raw.rstrip().endswith("```"):
        raw = raw[: raw.rfind("```")].strip()
if raw.startswith("json\n"):
    raw = raw[5:]

script = json.loads(raw)
output_path = "/Users/kimssa/.openclaw/workspace/video-pipeline/content_calendar.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(script, f, ensure_ascii=False, indent=2)

print(f"✅ Saved: {output_path}")
print(f"   Channel: {script['channel']}")
print(f"   Total Reels: {len(script['content_calendar'])}")
print(f"\n📋 Quick overview:")
for reel in script["content_calendar"]:
    print(f"  Day {reel['day']:2d} | {reel['pillar']:<20s} | {reel['title'][:50]}")
