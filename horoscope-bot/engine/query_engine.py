#!/usr/bin/env python3
"""
RAG Query Engine for Horoscope Bot
- Maps chart data → relevant knowledge chunks
- Builds prompt for LLM
- Supports DeepSeek, Gemini, and other providers

Usage:
    python3 query_engine.py --chart '{"dob":"1991-12-24","tob":"03:51","pob":"Saigon"}'
    python3 query_engine.py --chart '{"dob":"1995-06-15","tob":"14:30","pob":"Hanoi"}' --model deepseek
"""

import json
import os
import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHUNKS_DIR = BASE_DIR / "corpus" / "chunks"
EMBED_DIR = BASE_DIR / "corpus" / "embeddings"

# ─── Load all chunks ───

def load_all_chunks():
    """Load all processed chunks into memory."""
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    chunks.append(json.loads(line))
    return chunks


# ─── Retrieval by metadata matching (no embedding needed) ───

def find_chunks_by_metadata(chunks, chart_data):
    """Find relevant chunks based on chart data (keyword matching)."""
    # Parse chart
    planets = chart_data.get("planets", {})
    
    matched = []
    
    for chunk in chunks:
        meta = chunk["metadata"]
        score = 0
        reasons = []
        
        # Match by nakshatra
        if "name" in meta and meta["type"] == "nakshatra":
            for planet, data in planets.items():
                nak = data.get("nakshatra", "")
                if nak and nak.lower() in meta["name"].lower():
                    score += 3
                    reasons.append(f"nakshatra_match:{planet}={nak}")
        
        # Match by planet (karakatvas)
        if "planet" in meta:
            for planet in planets:
                if planet.lower() in meta["planet"].lower():
                    score += 3
                    reasons.append(f"planet_match:{planet}")
        
        # Match by lord
        if "lord" in meta:
            for planet, data in planets.items():
                if planet.lower() in meta["lord"].lower():
                    score += 2
                    reasons.append(f"lord_match:{meta['name']}={planet}")
        
        # Match by sign
        if "sign" in meta:
            for planet, data in planets.items():
                sign = data.get("sign", "")
                if sign and (sign.lower() in meta["sign"].lower() or 
                             meta["sign"].lower() in sign.lower()):
                    score += 2
                    reasons.append(f"sign_match:{planet}={sign}")
        
        # Match by house/karaka topics
        if "type" in meta and meta["type"] == "karaka":
            topics = chart_data.get("topics", [])
            heading = meta.get("heading", "").lower()
            for topic in topics:
                if topic.lower() in heading:
                    score += 1
                    reasons.append(f"topic_match:{topic}")
        
        if score > 0:
            matched.append((score, reasons, chunk))
    
    # Sort by relevance
    matched.sort(key=lambda x: -x[0])
    return matched


# ─── Prompt Builder ───

def build_prompt(chart_data, relevant_chunks, mode="free"):
    """
    Build LLM prompt with chart data + RAG context.
    
    Args:
        chart_data: dict with planets, houses, aspects
        relevant_chunks: top-K matched knowledge chunks
        mode: "free" (200-300 words) or "full" (complete reading)
    """
    
    # Chart summary
    chart_summary = format_chart_summary(chart_data)
    
    # Top chunks as context
    context = format_context(relevant_chunks[:10])
    
    # Build prompt
    if mode == "free":
        prompt = f"""Bạn là một nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy. 
Phong cách: chuyên nghiệp, thấu cảm, chính xác, dùng tiếng Việt.

NHIỆM VỤ: Luận giải MIỄN PHÍ (200-300 từ) cho lá số sau.
CHỈ viết ĐOẠN MỞ ĐẦU: tính cách tổng quan dựa trên Lagna + Moon sign.
Kết thúc bằng một câu gợi mở (cliffhanger) để người đọc muốn xem tiếp.

⚠️ LUẬT LỆ:
- CHỈ dùng thông tin từ CHART DATA và CONTEXT dưới đây
- KHÔNG thêm chi tiết không có trong dữ liệu
- KHÔNG nói "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — cứ luận trực tiếp

=== CHART DATA ===
{chart_summary}

=== KIẾN THỨC THAM KHẢO (RAG Context) ===
{context}

=== YÊU CẦU ===
Viết 200-300 từ, giọng văn ấm áp, chuyên nghiệp, kết thúc bằng "...nhưng điều thú vị nhất sẽ được hé lộ trong phần luận giải đầy đủ."
"""
    else:
        prompt = f"""Bạn là một nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy.
Phong cách: chuyên nghiệp, thấu cảm, chính xác, dùng tiếng Việt.

NHIỆM VỤ: Luận giải TOÀN BỘ lá số sau.

CẤU TRÚC luận giải:
1️⃣ TÍNH CÁCH & BẢN CHẤT (Lagna + Moon sign + Ascendant lord)
2️⃣ SỰ NGHIỆP & TÀI CHÍNH (10th house + Jupiter + 2nd/11th house)
3️⃣ MỐI QUAN HỆ & HÔN NHÂN (7th house + Venus)
4️⃣ SỨC KHỎE & TINH THẦN (6th/8th/12th house)
5️⃣ THỜI ĐIỂM QUAN TRỌNG (transit hiện tại + dasha period)
6️⃣ KẾT LUẬN & LỜI KHUYÊN

⚠️ LUẬT LỆ:
- CHỈ dùng thông tin từ CHART DATA và CONTEXT dưới đây
- KHÔNG thêm chi tiết không có trong dữ liệu
- Mỗi claim PHẢI có căn cứ từ chart hoặc kiến thức Vedic

=== CHART DATA ===
{chart_summary}

=== KIẾN THỨC THAM KHẢO (RAG Context) ===
{context}

=== YÊU CẦU ===
Viết 1500-2500 từ, giọng văn ấm áp nhưng chuyên nghiệp. 
Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ khi nhắc đến hành tinh.
"""
    
    return prompt


def format_chart_summary(chart_data):
    """Format chart data for LLM context."""
    parts = []
    parts.append(f"Ngày sinh: {chart_data.get('dob', '?')}")
    parts.append(f"Giờ sinh: {chart_data.get('tob', '?')}")
    parts.append(f"Nơi sinh: {chart_data.get('pob', '?')}")
    
    planets = chart_data.get("planets", {})
    if planets:
        parts.append("\nVị trí các hành tinh:")
        for name, data in planets.items():
            line = f"  {name}: {data.get('sign','')} {data.get('degree','')}°"
            if data.get("nakshatra"):
                line += f" | Nakshatra: {data['nakshatra']}"
            if data.get("house"):
                line += f" | Nhà {data['house']}"
            parts.append(line)
    
    lagna = chart_data.get("lagna", {})
    if lagna:
        parts.append(f"\nLagna (Ascendant): {lagna.get('sign','')} {lagna.get('degree','')}°")
    
    aspects = chart_data.get("aspects", [])
    if aspects:
        parts.append(f"\nGóc chiếu chính:")
        aspect_symbols = {'conjunction': '☌', 'sextile': '⚺', 'square': '□', 'trine': '⚹', 'opposition': '☍'}
        for asp in aspects[:8]:
            p1 = asp.get('planet1', '')
            p2 = asp.get('planet2', '')
            atype = asp.get('type', '').lower()
            sym = aspect_symbols.get(atype, '?')
            orb = asp.get('orb', '')
            parts.append(f"  {p1} {sym} {p2} (orb: {orb}°)")
    
    return '\n'.join(parts)


def format_context(chunks_with_scores):
    """Format top chunks as LLM context."""
    parts = []
    for score, reasons, chunk in chunks_with_scores:
        meta = chunk["metadata"]
        source = meta.get("source", meta.get("type", "unknown"))
        name = meta.get("name", meta.get("heading", meta.get("planet", "general")))
        parts.append(f"[{source}/{name}] (relevance: {score})")
        parts.append(chunk["text"][:600])
        parts.append("")
    return '\n'.join(parts)


# ─── Main ───

def run(chart_json, mode="free"):
    """Main entry point."""
    chunks = load_all_chunks()
    print(f"📚 Loaded {len(chunks)} knowledge chunks")
    
    chart_data = json.loads(chart_json) if isinstance(chart_json, str) else chart_json
    
    # Find relevant chunks
    matched = find_chunks_by_metadata(chunks, chart_data)
    print(f"🔍 Found {len(matched)} relevant chunks\n")
    
    # Build prompt
    prompt = build_prompt(chart_data, matched[:10], mode)
    
    print("=" * 60)
    print(f"📝 {'FREE' if mode=='free' else 'FULL'} READING PROMPT ({len(prompt):,} chars)")
    print("=" * 60)
    print(prompt[:3000])
    if len(prompt) > 3000:
        print(f"\n... [truncated, {len(prompt)} chars total]")
    
    # Save for reference
    out_dir = BASE_DIR / "data"
    out_dir.mkdir(exist_ok=True)
    fname = f"prompt_{chart_data.get('dob','unknown')}_{mode}.txt"
    with open(out_dir / fname, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"\n💾 Saved to data/{fname}")
    
    return prompt, matched[:10]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", required=True, help='JSON chart data')
    parser.add_argument("--mode", choices=["free", "full"], default="free")
    args = parser.parse_args()
    run(args.chart, args.mode)
