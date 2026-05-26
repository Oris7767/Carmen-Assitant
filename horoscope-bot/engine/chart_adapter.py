#!/usr/bin/env python3
"""
Chart Adapter — Converts web API JSON → structured chart summary for LLM.
Also queries RAG corpus for relevant knowledge chunks.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Vedic planet symbols
PLANET_SYMBOLS = {
    "SUN": "☀️ Mặt Trời",
    "MOON": "🌙 Mặt Trăng",
    "MARS": "♂️ Sao Hỏa",
    "MERCURY": "☿️ Sao Thủy",
    "JUPITER": "♃ Sao Mộc",
    "VENUS": "♀️ Sao Kim",
    "SATURN": "♄ Sao Thổ",
    "RAHU": "☊ Rahu",
    "KETU": "☋ Ketu",
    "URANUS": "⛢ Sao Thiên Vương",
    "NEPTUNE": "♆ Sao Hải Vương",
    "PLUTO": "♇ Sao Diêm Vương",
}

PLANET_ORDER = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU", "URANUS", "NEPTUNE", "PLUTO"]

HOUSE_LABELS = {
    1: "Bản thân, tính cách, ngoại hình",
    2: "Tài chính, gia đình, lời nói",
    3: "Dũng cảm, anh chị em, giao tiếp",
    4: "Nhà cửa, mẹ, học vấn, tài sản",
    5: "Con cái, sáng tạo, đầu cơ, trí tuệ",
    6: "Sức khỏe, bệnh tật, kẻ thù, nợ nần",
    7: "Hôn nhân, đối tác, kinh doanh",
    8: "Tuổi thọ, huyền bí, biến cố, thừa kế",
    9: "May mắn, đạo đức, cha, triết học",
    10: "Sự nghiệp, danh vọng, quyền lực",
    11: "Lợi nhuận, thu nhập, mạng lưới",
    12: "Mất mát, chi tiêu, nước ngoài, tâm linh",
}

ASPECT_SYMBOLS = {
    "Conjunction": "☌ Giao hội",
    "Sextile": "⚺ Lục hợp",
    "Square": "□ Góc vuông",
    "Trine": "⚹ Tam hợp",
    "Opposition": "☍ Đối đỉnh",
}


def format_chart_summary(chart_data):
    """
    Convert web API JSON → structured Vietnamese text for LLM context.
    Returns a formatted string summarizing the entire chart.
    """
    lines = []
    lines.append("📋 THÔNG TIN LÁ SỐ")
    lines.append("=" * 60)
    
    meta = chart_data.get("metadata", {})
    lines.append(f"Ngày sinh: {meta.get('date', '?')}")
    lines.append(f"Giờ sinh: {meta.get('time', '?')}")
    lines.append(f"Nơi sinh: {meta.get('timezone', '?')}")
    lines.append("")
    
    # 1. LAGNA (Ascendant)
    asc = chart_data.get("ascendant", {})
    asc_sign = asc.get("sign", {})
    asc_nak = asc.get("nakshatra", {})
    lines.append(f"🔼 LAGNA (Cung Mọc)")
    lines.append(f"  {asc_sign.get('name', '?')} {asc_sign.get('degree', 0)}°{asc_sign.get('minutes', 0)}'")
    lines.append(f"  Nakshatra: {asc_nak.get('name', '?')} - Chủ: {asc_nak.get('lord', '?')} - Pada {asc_nak.get('pada', '?')}")
    lines.append("")
    
    # 2. HOUSES
    lines.append("🏠 CÁC NHÀ (Houses)")
    for h in chart_data.get("houses", []):
        hnum = h.get("number", "?")
        hsign = h.get("sign", "?")
        hplanets = h.get("planets", [])
        label = HOUSE_LABELS.get(hnum, "")
        
        planet_str = ", ".join(PLANET_SYMBOLS.get(p, p) for p in hplanets) if hplanets else "trống"
        lines.append(f"  Nhà {hnum} ({hsign}): {planet_str}")
        lines.append(f"    → {label}")
    lines.append("")
    
    # 3. PLANETS
    lines.append("🪐 VỊ TRÍ CÁC HÀNH TINH")
    
    # Sort planets by house number for logical flow
    for pdata in chart_data.get("planets", []):
        pname = pdata.get("planet", "")
        psym = PLANET_SYMBOLS.get(pname, pname)
        psign = pdata.get("sign", {})
        phouse = pdata.get("house", {})
        pnak = pdata.get("nakshatra", {})
        retro = " (Nghịch hành 🔄)" if pdata.get("isRetrograde") else ""
        
        lines.append(f"  {psym}: {psign.get('name','?')} {psign.get('longitude',0)}°{retro}")
        lines.append(f"    Nhà {phouse.get('number','?')} ({phouse.get('sign','?')})")
        lines.append(f"    Nakshatra: {pnak.get('name','?')} - Chủ: {pnak.get('lord','?')} - Pada {pnak.get('pada','?')}")
        
        # Aspects
        aspects = pdata.get("aspects", [])
        if aspects:
            asp_strs = []
            for asp in aspects[:4]:
                asp_sym = ASPECT_SYMBOLS.get(asp["aspect"], asp["aspect"])
                asp_target = PLANET_SYMBOLS.get(asp["planet"], asp["planet"])
                asp_strs.append(f"{asp_sym} {asp_target} (orb: {asp['orb']:.1f}°)")
            lines.append(f"    Góc chiếu: {'; '.join(asp_strs)}")
        lines.append("")
    
    # 4. DASHA (current)
    dashas = chart_data.get("dashas", {})
    current = dashas.get("current", {})
    if current:
        lines.append("⏳ DASHA HIỆN TẠI")
        cp = current.get("planet", "?")
        cs = PLANET_SYMBOLS.get(cp, cp)
        cd_start = current.get("startDate", "?")[:10]
        cd_end = current.get("endDate", "?")[:10]
        lines.append(f"  {cs} Mahadasha: {cd_start} → {cd_end}")
        
        seq = dashas.get("sequence", [])
        if seq:
            lines.append("  Chuỗi Dasha:")
            for s in seq:
                sp = PLANET_SYMBOLS.get(s["planet"], s["planet"])
                ss = s.get("startDate", "?")[:10]
                se = s.get("endDate", "?")[:10]
                sd = s.get("duration", "?")
                lines.append(f"    {sp}: {ss} → {se} ({sd} năm)")
        lines.append("")
    
    # 5. RETROGRADE PLANETS
    retros = [p for p in chart_data.get("planets", []) if p.get("isRetrograde")]
    if retros:
        lines.append("🔄 HÀNH TINH NGHỊCH HÀNH")
        for r in retros:
            lines.append(f"  {PLANET_SYMBOLS.get(r['planet'], r['planet'])}")
        lines.append("")
    
    return "\n".join(lines)


def extract_key_facts(chart_data):
    """Extract key astrological facts for RAG querying."""
    facts = []
    
    # Lagna sign + nakshatra
    asc = chart_data.get("ascendant", {})
    asc_nak = asc.get("nakshatra", {})
    if asc_nak:
        facts.append(f"Lagna Nakshatra: {asc_nak['name']}")
        facts.append(f"Lagna Lord: {asc_nak['lord']}")
    
    # Planet nakshatras
    for p in chart_data.get("planets", []):
        pnak = p.get("nakshatra", {})
        if pnak:
            facts.append(f"{p['planet']} Nakshatra: {pnak['name']}")
            facts.append(f"{p['planet']} Nakshatra Lord: {pnak['lord']}")
    
    # House placements
    for p in chart_data.get("planets", []):
        phouse = p.get("house", {})
        if phouse:
            facts.append(f"{p['planet']} House: {phouse['number']}")
    
    # Retrograde planets
    for p in chart_data.get("planets", []):
        if p.get("isRetrograde"):
            facts.append(f"{p['planet']} Retrograde")
    
    # Current dasha
    current = chart_data.get("dashas", {}).get("current", {})
    if current:
        facts.append(f"Current Dasha: {current['planet']}")
    
    return list(set(facts))  # deduplicate


def generate_rag_queries(chart_data):
    """Generate search queries from chart data for RAG retrieval."""
    queries = []
    
    # 1. Lagna nakshatra query
    asc = chart_data.get("ascendant", {})
    asc_nak = asc.get("nakshatra", {})
    if asc_nak:
        queries.append(f"{asc_nak['name']} nakshatra characteristics personality lord {asc_nak['lord']}")
    
    # 2. Planet nakshatra queries
    for p in chart_data.get("planets", []):
        pname = p.get("planet", "")
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue
        pnak = p.get("nakshatra", {})
        if pnak:
            queries.append(f"{pnak['name']} nakshatra {pname} planet characteristics")
    
    # 3. Planet in house queries
    for p in chart_data.get("planets", []):
        pname = p.get("planet", "")
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue
        phouse = p.get("house", {}).get("number", "")
        psign = p.get("sign", {}).get("name", "")
        if phouse and psign:
            queries.append(f"{pname} in {psign} house {phouse} effects karakatva significations")
    
    # 4. Karaka queries for planets in houses
    house_planets = {}
    for h in chart_data.get("houses", []):
        for p in h.get("planets", []):
            if p not in house_planets:
                house_planets[p] = []
            house_planets[p].append(str(h["number"]))
    
    for pname, hnums in house_planets.items():
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue
        queries.append(f"{pname} karakatva significations houses {','.join(hnums)}")
    
    # 5. Retrograde queries
    for p in chart_data.get("planets", []):
        if p.get("isRetrograde") and p["planet"] not in ("URANUS", "NEPTUNE", "PLUTO"):
            queries.append(f"{p['planet']} retrograde effects vedic astrology")
    
    # 6. Aspect queries (important ones)
    for p in chart_data.get("planets", []):
        pname = p.get("planet", "")
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue
        for asp in p.get("aspects", []):
            if asp["planet"] not in ("URANUS", "NEPTUNE", "PLUTO"):
                queries.append(f"{pname} {asp['aspect']} {asp['planet']} aspect effects")
    
    # 7. Current dasha
    current = chart_data.get("dashas", {}).get("current", {})
    if current:
        queries.append(f"{current['planet']} mahadasha effects characteristics")
    
    # Deduplicate, max 25 queries
    seen = set()
    unique = []
    for q in queries:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    
    return unique[:25]


def format_rag_context(rag_results):
    """Format RAG search results as LLM context string."""
    if not rag_results:
        return "(Không có dữ liệu tham khảo)"
    
    parts = []
    for r in rag_results[:12]:
        meta = r.get("metadata", r.get("chunk", {}).get("metadata", {}))
        text = r.get("text", r.get("chunk", {}).get("text", ""))
        score = r.get("score", 0)
        
        source = meta.get("source", meta.get("type", "unknown"))
        name = meta.get("name", meta.get("heading", meta.get("planet", "general")))
        
        parts.append(f"[{source}/{name}] (độ phù hợp: {score:.2f})")
        parts.append(text[:600])
        parts.append("")
    
    return "\n".join(parts)


if __name__ == "__main__":
    import sys
    sample = BASE_DIR / "data" / "sample_api_response.json"
    if sample.exists():
        data = json.loads(sample.read_text())
        print(format_chart_summary(data))
        print("\n\n=== KEY FACTS ===")
        for f in extract_key_facts(data):
            print(f"  • {f}")
    else:
        print("❌ sample_api_response.json not found")
