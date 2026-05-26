#!/usr/bin/env python3
"""
ElevenLabs TTS for YouTube Shorts — Vietnamese female voice
Usage: python3 elevenlabs_tts.py "text to speak" output.mp3

Voice: Vietnamese female, warm and authoritative
"""

import requests
import sys
import os
from pathlib import Path

KEY_FILE = Path(__file__).parent / "elevenlabs_key.txt"
# Free tier working voices: Bella, Adam, Antoni, Arnold
# Bella = female, Adam/Antoni/Arnold = male
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Bella — female voice

# Upgraded plan alternatives (currently 402 on free tier):
# "21m00Tcm4TlvDq8ikWAM" — Rachel (warm, authoritative)
# "JBFqnCBsd6RMkjVDRZzb" — multilingual v2 (best for Vietnamese)

def get_key():
    if not KEY_FILE.exists():
        print("❌ elevenlabs_key.txt not found")
        sys.exit(1)
    return KEY_FILE.read_text().strip()

def speak(text, output_path, voice_id=VOICE_ID):
    key = get_key()
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    resp = requests.post(url, json=data, headers=headers)
    
    if resp.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        size_kb = len(resp.content) / 1024
        print(f"✅ Generated: {output_path} ({size_kb:.0f} KB)")
        return output_path
    else:
        print(f"❌ ElevenLabs error {resp.status_code}: {resp.text[:200]}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 elevenlabs_tts.py '<text>' <output.mp3>")
        sys.exit(1)
    
    text = sys.argv[1]
    output = sys.argv[2]
    speak(text, output)
