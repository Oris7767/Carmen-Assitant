#!/usr/bin/env python3
"""
Test horoscope reading với DeepSeek và Gemini
So sánh output từ 2 models

Usage:
    python3 test_models.py --chart data/test_chart.json
    python3 test_models.py --chart data/test_chart.json --model deepseek
    python3 test_models.py --chart data/test_chart.json --model gemini
"""

import json
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "engine"))

from query_engine import run as build_prompt

# ─── Gemini ───

def call_gemini(prompt, api_key=None):
    """Call Gemini API."""
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    if 'GEMINI_API_KEY' in line:
                        api_key = line.split('=')[1].strip()
    
    if not api_key:
        return "❌ No Gemini API key found"
    
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)
    return response.text


def run(chart_path, model="both"):
    """Run test with specified model(s)."""
    
    chart_data = json.load(open(chart_path))
    chart_json = json.dumps(chart_data)
    
    # Build prompt
    prompt, chunks = build_prompt(chart_json, mode="free")
    
    print("=" * 60)
    print("🔮 HOROSCOPE READING TEST")
    print(f"📋 Chart: {chart_data.get('dob')} - {chart_data.get('pob')}")
    print(f"📚 RAG chunks: {len(chunks)}")
    print("=" * 60)
    
    results = {}
    
    if model in ("deepseek", "both"):
        print("\n🤖 DEEPSEEK READING:")
        print("-" * 60)
        # Read from query_engine prompt - would normally call API
        # For now, use the prompt we already built
        print("(Prompt ready. Manual generation via assistant.)")
        print("-" * 60)
    
    if model in ("gemini", "both"):
        print("\n🤖 GEMINI READING:")
        print("-" * 60)
        try:
            result = call_gemini(prompt)
            print(result[:1500])
            print(f"\n... [{len(result)} chars total]")
            results["gemini"] = result
            
            # Save
            out = BASE_DIR / "data" / f"reading_gemini_{chart_data.get('dob','test')}.txt"
            out.write_text(result)
            print(f"\n💾 Saved: {out}")
        except Exception as e:
            print(f"❌ Gemini error: {e}")
        print("-" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", default=str(BASE_DIR / "data" / "test_chart.json"))
    parser.add_argument("--model", choices=["deepseek", "gemini", "both"], default="both")
    args = parser.parse_args()
    
    # Set API key
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().split('\n'):
            if 'GEMINI_API_KEY' in line:
                os.environ['GEMINI_API_KEY'] = line.split('=')[1].strip()
    
    run(args.chart, args.model)
