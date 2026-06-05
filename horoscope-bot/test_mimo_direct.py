#!/usr/bin/env python3
"""Direct MiMo test — no engine imports, just API call."""
import requests, re, json, time
from pathlib import Path

# Get API key
config_path = Path.home() / '.openclaw' / 'openclaw.json'
raw = config_path.read_text()
m = re.search(r'"xiaomi-token-plan":\s*\{[^}]*"apiKey":\s*"([^"]+)"', raw, re.DOTALL)
key = m.group(1) if m else ''
print(f"API key: {'found' if key else 'MISSING'}")

# Load chart data
with open('data/sample_api_response.json') as f:
    chart = json.load(f)

# Build chart summary
meta = chart['metadata']
asc = chart['ascendant']
planets = chart['planets']
houses = chart['houses']
dashas = chart['dashas']

lines = []
lines.append(f"CHART: {meta['date']} {meta['time']} {meta['timezone']}")
lines.append(f"Location: {meta['latitude']}, {meta['longitude']}")
asc_deg = asc['sign'].get('degree', asc['sign'].get('longitude', 0))
lines.append(f"Ascendant: {asc['sign']['name']} {asc_deg}°{asc['sign']['minutes']}' - Nakshatra: {asc['nakshatra']['name']} (Lord: {asc['nakshatra']['lord']}, Pada: {asc['nakshatra']['pada']})")
lines.append("")
lines.append("PLANETS:")
for p in planets:
    retro = " (R)" if p['isRetrograde'] else ""
    aspects_str = ", ".join([f"{a['planet']} {a['aspect']}({a['orb']}°)" for a in p.get('aspects', [])])
    lines.append(f"  {p['planet']}: {p['sign']['name']} {p['sign']['longitude']}°{p['sign']['minutes']}' (House {p['house']['number']}) - Nak: {p['nakshatra']['name']} (Lord: {p['nakshatra']['lord']}){retro}")
    if aspects_str:
        lines.append(f"    Aspects: {aspects_str}")

lines.append("")
lines.append("HOUSES:")
for h in houses:
    planets_str = ", ".join(h['planets']) if h['planets'] else "empty"
    lines.append(f"  House {h['number']}: {h['sign']} — {planets_str}")

lines.append("")
lines.append(f"CURRENT DASHA: {dashas['current']['planet']} (until {dashas['current']['endDate'][:10]})")
lines.append("DASHA SEQUENCE:")
for d in dashas['sequence']:
    lines.append(f"  {d['planet']}: {d['startDate'][:10]} → {d['endDate'][:10]} ({d['duration']}y)")

chart_summary = "\n".join(lines)

# Prompt
PROMPT = f"""Bạn là nhà chiêm tinh Vệ Đà của Votive Academy — chuyên gia luận giải lá số với kiến thức từ Brihat Parashara Hora Shastra.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm. Tiếng Việt thuần túy. Luận trực tiếp, KHÔNG nói "dựa trên dữ liệu".

NHIỆM VỤ: Luận giải TOÀN BỘ lá số. 8 phần, TỔNG 14,000-18,000 ký tự:

1️⃣ TỔNG QUAN LÁ SỐ — Lagna, Moon sign, Ascendant lord, tính cách tổng quan (500+ từ)
2️⃣ PHÂN TÍCH HÀNH TINH CHI TIẾT — Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu/Ketu: vị trí, nakshatra, aspects, ý nghĩa chi tiết (1000+ từ)
3️⃣ SỰ NGHIỆP & TÀI CHÍNH — Nhà 10, career yoga, financial patterns (500+ từ)
4️⃣ MỐI QUAN HỆ & HÔN NHÂN — Nhà 7, Venus, relationship yoga (500+ từ)
5️⃣ SỨC KHỎE & TINH THẦN — Houses 6/8/12, health indicators (400+ từ)
6️⃣ MAHADASHA & THỜI ĐIỂM — Current dasha, transits, key periods 2025-2030 (500+ từ)
7️⃣ YOGA & ĐIỂM ĐẶC BIỆT — Raja yoga, Dhana yoga, các yoga đặc biệt từ chart (400+ từ)
8️⃣ KẾT LUẬN & LỜI KHUYÊN — 5 điểm mạnh nhất, 3 khuyến nghị thực tế (400+ từ)

⚠️ BẮT BUỘC:
- CHỈ dùng CHART DATA bên dưới — KHÔNG bịa thông tin
- Mỗi claim phải có căn cứ từ chart hoặc kiến thức Vedic
- Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄
- Mỗi PHẦN phải phân tích SÂU, có ví dụ cụ thể, KHÔNG sơ sài
- Mục tiêu: 14,000-18,000 ký tự — BẮT BUỘC

=== CHART DATA ===
{chart_summary}

Viết bài luận giải đầy đủ. Mục tiêu 14,000-18,000 ký tự."""

print(f"Prompt: {len(PROMPT):,} chars")
print("Generating 14k+ FULL reading...")

t0 = time.time()
resp = requests.post('https://token-plan-sgp.xiaomimimo.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={'model': 'mimo-v2.5-pro', 'messages': [{'role': 'user', 'content': PROMPT}], 'max_tokens': 16384, 'temperature': 0.7},
    timeout=600)
elapsed = time.time() - t0

data = resp.json()
text = data['choices'][0]['message']['content']
text = text.replace('**','').replace('*','').replace('__','')
text = re.sub(r'\n{3,}', '\n\n', text).strip()

usage = data.get('usage', {})
print(f"\n{'='*60}")
print(f"Time: {elapsed:.1f}s")
print(f"Output: {len(text):,} chars")
print(f"Tokens — in: {usage.get('prompt_tokens',0)}, out: {usage.get('completion_tokens',0)}")

Path('data/test_mimo_full_14k.txt').write_text(text, encoding='utf-8')
print(f"Saved: data/test_mimo_full_14k.txt")
print(f"{'='*60}")
print("\nFirst 500 chars:")
print(text[:500])
