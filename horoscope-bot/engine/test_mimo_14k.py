#!/usr/bin/env python3
"""Test MiMo with 14k+ char output target."""
import sys, json, time, requests, re, os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "engine"))

from chart_adapter import format_chart_summary, format_rag_context
from embeddings import search_by_chart

# Get API key from openclaw config
def get_mimo_key():
    key = os.environ.get('MIMO_API_KEY', '')
    if key:
        return key
    config_path = Path.home() / '.openclaw' / 'openclaw.json'
    if config_path.exists():
        raw = config_path.read_text()
        m = re.search(r'"xiaomi-token-plan":\s*\{[^}]*"apiKey":\s*"([^"]+)"', raw, re.DOTALL)
        if m:
            return m.group(1)
    return ''

MIMO_URL = 'https://token-plan-sgp.xiaomimimo.com/v1/chat/completions'
MIMO_KEY = get_mimo_key()
print(f"API key: {'found' if MIMO_KEY else 'MISSING'}")

# Load chart
with open(BASE_DIR / 'data' / 'sample_api_response.json') as f:
    chart_data = json.load(f)

rag_results = search_by_chart(chart_data, k=15)
chart_summary = format_chart_summary(chart_data)
rag_context = format_rag_context(rag_results)

PROMPT = """Bạn là nhà chiêm tinh Vệ Đà của Votive Academy — chuyên gia luận giải lá số với kiến thức từ Brihat Parashara Hora Shastra.

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
- CHỈ dùng CHART DATA + KIẾN THỨC THAM KHẢO bên dưới
- KHÔNG bịa thông tin ngoài chart
- Mỗi claim phải có căn cứ từ chart hoặc kiến thức Vedic
- Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄
- Mỗi PHÂN PHẢI PHÂN TÍCH SÂU, có ví dụ cụ thể, KHÔNG được sơ sài
- Mục tiêu: 14,000-18,000 ký tự — đây là yêu cầu BẮT BUỘC

=== CHART DATA ===
{chart_summary}

=== KIẾN THỨC THAM KHẢO ===
{rag_context}

Viết bài luận giải đầy đủ. Mục tiêu 14,000-18,000 ký tự."""

full_prompt = PROMPT.format(chart_summary=chart_summary, rag_context=rag_context)
print(f'Prompt: {len(full_prompt):,} chars')
print('Generating...')

t0 = time.time()
resp = requests.post(MIMO_URL,
    headers={'Authorization': f'Bearer {MIMO_KEY}', 'Content-Type': 'application/json'},
    json={'model': 'mimo-v2.5-pro', 'messages': [{'role': 'user', 'content': full_prompt}], 'max_tokens': 16384, 'temperature': 0.7},
    timeout=600)
elapsed = time.time() - t0

data = resp.json()
text = data['choices'][0]['message']['content']
text = text.replace('**','').replace('*','').replace('__','')
text = re.sub(r'\n{3,}', '\n\n', text).strip()

usage = data.get('usage', {})
print(f'Time: {elapsed:.1f}s')
print(f'Output: {len(text):,} chars')
print(f'Tokens — in: {usage.get("prompt_tokens",0)}, out: {usage.get("completion_tokens",0)}')

Path(BASE_DIR / 'data' / 'test_mimo_full_14k.txt').write_text(text, encoding='utf-8')
print(f'Saved: data/test_mimo_full_14k.txt')
