#!/usr/bin/env python3
"""A/B Test: MiMo 2.5 Pro vs Qwen 3.5 Plus — No RAG, direct chart data."""
import sys, json, time, requests, re
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "engine"))
from chart_adapter import format_chart_summary

MODELS = {
    "mimo": {"name": "MiMo 2.5 Pro", "url": "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions", "model": "mimo-v2.5-pro", "key": "tp-s6uadpifeol3rlg4yyqrcpb3y6l3imbv6wzcgz5a77jpfflx"},
    "qwen": {"name": "Qwen 3.5 Plus", "url": "https://coding-intl.dashscope.aliyuncs.com/v1/chat/completions", "model": "qwen3.5-plus", "key": "sk-sp-82de717d33e043469eb1ce43499e5605"},
}

FREE_PROMPT = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy — chuyên gia luận giải lá số chiêm tinh với kiến thức từ Brihat Parashara Hora Shastra.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm. Tiếng Việt thuần túy. Luận trực tiếp, KHÔNG nói "dựa trên dữ liệu".

NHIỆM VỤ: Viết PHẦN MỞ ĐẦU (300-400 từ) cho bài luận giải lá số.

YÊU CẦU:
1. Mở đầu THU HÚT — 1-2 câu gây tò mò về điểm ĐẶC BIỆT nhất trong lá số
2. Tổng quan Lagna + Moon sign — 2-3 câu về tính cách cốt lõi
3. Điểm mạnh nổi bật — 2-3 câu dựa trên planet placements
4. Cliffhanger MẠNH — gợi mở về bí mật quan trọng mà CHỈ bản đầy đủ mới giải đáp

LUẬT:
- 300-400 từ, NGẮN GỌN nhưng SỨC MẠNH
- CHỈ dùng CHART DATA bên dưới, KHÔNG bịa
- Kết thúc bằng cliffhanger khiến đọc giả PHẢI muốn đọc tiếp
- Dùng ký hiệu ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄
- KHÔNG markdown, KHÔNG tiêu đề

=== CHART DATA ===
{chart}

Viết phần luận giải mở đầu."""

FULL_PROMPT = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) hàng đầu của Votive Academy — chuyên gia luận giải lá số với kiến thức sâu rộng từ Brihat Parashara Hora Shastra (BPHS).

PHONG CÁCH: Chuyên nghiệp, sâu sắc, uyên bác. Tiếng Việt thuần túy, trau chuốt. Luận trực tiếp, tự tin.

NHIỆM VỤ: Viết bài luận giải TOÀN BỘ lá số — CHI TIẾT, CHUYÊN SÂU, ĐẲNG CẤP.

CẤU TRÚC 10 PHẦN (mỗi phần PHÂN TÍCH SÂU, KHÔNG sơ sài):

1️⃣ 🌟 TỔNG QUAN LÁ SỐ & BẢN CHẤT CỐT LÕI — Lagna, Moon, Ascendant lord, Atmakaraka, động lực sống, bài học nghiệp (800+ từ)
2️⃣ 🪐 PHÂN TÍCH TỪNG HÀNH TINH CHI TIẾT — Sun→Ketu: vị trí, nakshatra, sign lord, house lordship, aspects, dignity, ý nghĩa cụ thể (2000+ từ)
3️⃣ 🏠 PHÂN TÍCH 12 NHÀ (BHAVAS) — Mỗi nhà: sign, planets, lord placement, aspects, ý nghĩa đời sống (1500+ từ)
4️⃣ 💼 SỰ NGHIỆP & TÀI CHÍNH — Nhà 10/2/6/11, career yoga, financial patterns, ngành nghề phù hợp (800+ từ)
5️⃣ 💕 MỐI QUAN HỆ & HÔN NHÂN — Nhà 7, Venus, Darakaraka, pattern tình duyên, kiểu đối tác (800+ từ)
6️⃣ 💪 SỨC KHỎE & TINH THẦN — Houses 6/8/12, Moon, Saturn, thể chất & tinh thần (600+ từ)
7️⃣ ⏳ MAHADASHA & DỰ BÁO — Current dasha + antardasha, giai đoạn 2025-2035 (800+ từ)
8️⃣ 🔮 YOGA & ĐIỂM ĐẶC BIỆT — Raja/Dhana/Kemadruma/Gaja Kesari yoga, ý nghĩa (600+ từ)
9️⃣ 🌊 RAHU/KETU & NĂNG LƯỢNG BÍ ẨN — Nodal axis, bài học nghiệp, Rahu/Ketu nakshatra (500+ từ)
🔟 💎 KẾT LUẬN & LỜI KHUYÊN — 5 điểm mạnh, 3 thách thức, 5 khuyến nghị thực tế (800+ từ)

LUẬT BẮT BUỘC:
- CHỈ dùng CHART DATA bên dưới, KHÔNG bịa
- Mỗi claim phải có căn cứ từ chart
- Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ ☊ ☋
- TỔNG: 14,000-20,000 ký tự — BẮT BUỘC
- Viết dưới 14,000 ký tự = THẤT BẠI

=== CHART DATA ===
{chart}

Viết bài luận giải đầy đủ. Mục tiêu 14,000-20,000 ký tự."""

def call_api(config, prompt, max_tokens):
    t0 = time.time()
    resp = requests.post(
        config["url"],
        headers={"Authorization": f"Bearer {config['key']}", "Content-Type": "application/json"},
        json={"model": config["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0.7},
        timeout=600,
    )
    elapsed = time.time() - t0
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"API Error: {data['error']}")
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return text, elapsed, usage

def clean(t):
    t = t.replace("**","").replace("*","").replace("__","")
    return re.sub(r"\n{3,}", "\n\n", t).strip()

# Load chart
with open(BASE / "data" / "sample_api_response.json") as f:
    chart_data = json.load(f)
chart = format_chart_summary(chart_data)
meta = chart_data.get("metadata", {})
print(f"📋 Chart: {meta.get('date')} {meta.get('time')} | {len(chart)} chars\n")

results = {}

for mk in ["mimo", "qwen"]:
    c = MODELS[mk]
    for mode in ["free", "full"]:
        print(f"{'='*60}")
        print(f"🤖 {c['name']} — {mode.upper()}")
        print(f"{'='*60}")
        
        if mode == "free":
            prompt = FREE_PROMPT.format(chart=chart)
            max_tok = 2048
        else:
            prompt = FULL_PROMPT.format(chart=chart)
            max_tok = 16384
        
        print(f"Prompt: {len(prompt):,} chars | max_tokens: {max_tok}")
        sys.stdout.flush()
        
        try:
            text, elapsed, usage = call_api(c, prompt, max_tok)
            text = clean(text)
            chars = len(text)
            words = len(text.split())
            out_tok = usage.get("completion_tokens", 0)
            
            print(f"Time: {elapsed:.1f}s | Output: {chars:,} chars / {words:,} words | Tokens: {out_tok:,}")
            
            if mode == "full":
                status = "✅ PASS" if chars >= 14000 else f"⚠️ SHORT ({14000-chars:,} missing)"
                print(f"14k target: {status}")
            
            if mode == "free":
                hooks = [h for h in ["bí mật","hé lộ","khám phá","điều thú vị","phần đầy đủ","bản đầy đủ","tiết lộ","chỉ ra","bạn chưa biết"] if h in text.lower()]
                syms = sum(1 for s in ["☀️","🌙","♂️","♀️","☿️","♃","♄"] if s in text)
                print(f"Hooks: {hooks or 'NONE'} | Symbols: {syms}/7")
            
            out = BASE / "data" / f"ab_{mk}_{mode}.txt"
            out.write_text(text, encoding="utf-8")
            print(f"Saved: {out.name}\n")
            
            results[f"{mk}_{mode}"] = {"chars": chars, "words": words, "time": elapsed, "tokens": out_tok, "text": text}
            
        except Exception as e:
            print(f"❌ FAILED: {e}\n")
            results[f"{mk}_{mode}"] = {"error": str(e)}
        sys.stdout.flush()

# Final table
print(f"\n{'='*60}")
print("📊 FINAL COMPARISON")
print(f"{'='*60}")
print(f"{'Model':<18} {'Mode':<6} {'Chars':>8} {'Words':>8} {'Time':>6} {'Tokens':>8} {'Status'}")
print("-" * 70)
for key in ["mimo_free","mimo_full","qwen_free","qwen_full"]:
    r = results.get(key, {})
    mk, mode = key.split("_")
    name = MODELS[mk]["name"][:16]
    if "error" in r:
        print(f"{name:<18} {mode:<6} {'FAIL':>8} — {r['error'][:35]}")
    else:
        ch = r["chars"]
        ok = "✅" if (mode=="free" and ch>=300) or (mode=="full" and ch>=14000) else "⚠️"
        print(f"{name:<18} {mode:<6} {ch:>8,} {r['words']:>8,} {r['time']:>5.1f}s {r['tokens']:>8,} {ok}")
