#!/usr/bin/env python3
"""
Test MiMo vs Gemini — So sánh chất lượng horoscope reading.
Dùng cùng chart data + prompts, output 2 file để Kim Ssa comparison.
"""

import sys, json, os, time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "engine"))

from prompt_builder import build_free_prompt, build_full_prompt
from chart_adapter import format_chart_summary, format_rag_context
from embeddings import search_by_chart, keyword_search, load_all_chunks

# ── Config ──
MIMO_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
MIMO_API_KEY = "tp-s6uadpifeol3rlg4yyqrcpb3y6l3imbv6wzcgz5a77jpfflx"
MIMO_MODEL = "mimo-v2.5-pro"

CHART_FILE = BASE_DIR / "data" / "sample_api_response.json"
OUTPUT_DIR = BASE_DIR / "data"


def call_mimo(prompt: str, max_tokens: int = 4096) -> str:
    """Call MiMo API (OpenAI-compatible)."""
    import requests
    
    resp = requests.post(
        f"{MIMO_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MIMO_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_gemini(prompt: str) -> str:
    """Call Gemini API."""
    from google import genai
    
    api_key = ""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().split('\n'):
            line = line.strip()
            if 'GEMINI_API_KEY' in line:
                api_key = line.split('=', 1)[1].strip()
    
    if not api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY")
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="models/gemini-2.5-pro",
        contents=prompt,
    )
    return response.text


def clean_text(text: str) -> str:
    """Strip markdown artifacts."""
    if not text:
        return ""
    text = text.replace('**', '').replace('*', '').replace('__', '')
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def main():
    print("🔮 MiMo vs Gemini — Horoscope Quality Test")
    print("=" * 60)
    
    # 1. Load chart data
    print("\n📊 Loading chart data...")
    with open(CHART_FILE) as f:
        chart_data = json.load(f)
    
    date = chart_data.get("metadata", {}).get("date", "unknown")
    print(f"   Chart: {date}")
    
    # 2. Query RAG
    print("\n🔍 Querying RAG corpus...")
    try:
        rag_results = search_by_chart(chart_data, k=12)
        print(f"   Semantic search: {len(rag_results)} results")
    except Exception as e:
        print(f"   ⚠️ Semantic failed: {e}")
        chunks = load_all_chunks()
        matched = keyword_search(chart_data, chunks)
        rag_results = [{"chunk": m[2], "metadata": m[2]["metadata"], "score": m[0]} for m in matched[:12]]
        print(f"   Keyword fallback: {len(rag_results)} results")
    
    # 3. Build prompts
    chart_summary = format_chart_summary(chart_data)
    rag_context = format_rag_context(rag_results) if rag_results else "(Không có dữ liệu tham khảo)"
    
    free_prompt = build_free_prompt(chart_summary, rag_context)
    full_prompt = build_full_prompt(chart_summary, rag_context)
    
    print(f"\n📝 FREE prompt: {len(free_prompt):,} chars")
    print(f"📝 FULL prompt: {len(full_prompt):,} chars")
    
    # 4. Generate readings
    results = {}
    
    for model_name, call_fn in [("mimo", call_mimo), ("gemini", call_gemini)]:
        print(f"\n{'='*60}")
        print(f"🤖 Generating with {model_name.upper()}...")
        print(f"{'='*60}")
        
        t0 = time.time()
        try:
            free_text = clean_text(call_fn(free_prompt))
            free_time = time.time() - t0
            print(f"   ✅ FREE: {len(free_text)} chars ({free_time:.1f}s)")
        except Exception as e:
            free_text = f"❌ ERROR: {e}"
            free_time = 0
            print(f"   ❌ FREE failed: {e}")
        
        t0 = time.time()
        try:
            full_text = clean_text(call_fn(full_prompt))
            full_time = time.time() - t0
            print(f"   ✅ FULL: {len(full_text)} chars ({full_time:.1f}s)")
        except Exception as e:
            full_text = f"❌ ERROR: {e}"
            full_time = 0
            print(f"   ❌ FULL failed: {e}")
        
        results[model_name] = {
            "free": free_text,
            "full": full_text,
            "free_time": free_time,
            "full_time": full_time,
        }
    
    # 5. Save comparison files
    print(f"\n{'='*60}")
    print("💾 Saving comparison files...")
    
    for model_name, data in results.items():
        # FREE reading
        free_path = OUTPUT_DIR / f"test_{model_name}_free.txt"
        free_path.write_text(data["free"], encoding="utf-8")
        print(f"   📄 {free_path.name} ({len(data['free'])} chars, {data['free_time']:.1f}s)")
        
        # FULL reading
        full_path = OUTPUT_DIR / f"test_{model_name}_full.txt"
        full_path.write_text(data["full"], encoding="utf-8")
        print(f"   📄 {full_path.name} ({len(data['full'])} chars, {data['full_time']:.1f}s)")
    
    # 6. Side-by-side comparison file
    comparison_path = OUTPUT_DIR / "comparison_mimo_vs_gemini.md"
    with open(comparison_path, "w", encoding="utf-8") as f:
        f.write(f"# 🔮 MiMo vs Gemini — Horoscope Comparison\n\n")
        f.write(f"**Chart:** {date} | **Generated:** {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        
        f.write(f"## ⏱️ Performance\n\n")
        f.write(f"| | MiMo ({MIMO_MODEL}) | Gemini 2.5 Pro |\n")
        f.write(f"|---|---|---|\n")
        f.write(f"| FREE time | {results['mimo']['free_time']:.1f}s | {results['gemini']['free_time']:.1f}s |\n")
        f.write(f"| FULL time | {results['mimo']['full_time']:.1f}s | {results['gemini']['full_time']:.1f}s |\n")
        f.write(f"| FREE chars | {len(results['mimo']['free'])} | {len(results['gemini']['free'])} |\n")
        f.write(f"| FULL chars | {len(results['mimo']['full'])} | {len(results['gemini']['full'])} |\n\n")
        
        f.write(f"## 📖 FREE Reading — MiMo\n\n{results['mimo']['free']}\n\n---\n\n")
        f.write(f"## 📖 FREE Reading — Gemini\n\n{results['gemini']['free']}\n\n---\n\n")
        f.write(f"## 📖 FULL Reading — MiMo\n\n{results['mimo']['full']}\n\n---\n\n")
        f.write(f"## 📖 FULL Reading — Gemini\n\n{results['gemini']['full']}\n\n")
    
    print(f"   📄 comparison_mimo_vs_gemini.md")
    
    print(f"\n{'='*60}")
    print("✅ Done! So sánh 4 file:")
    print(f"   data/test_mimo_free.txt")
    print(f"   data/test_mimo_full.txt")
    print(f"   data/test_gemini_free.txt")
    print(f"   data/test_gemini_full.txt")
    print(f"   data/comparison_mimo_vs_gemini.md")


if __name__ == "__main__":
    main()
