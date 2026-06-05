#!/usr/bin/env python3
"""
A/B Test: MiMo 2.5 Pro vs Qwen 3.5 Plus
Generate FREE + FULL horoscope readings, compare quality.
Target: FULL ≥ 14k chars, FREE has strong hook + upsell.
"""
import sys, json, time, requests, re, os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "engine"))

from chart_adapter import format_chart_summary, format_rag_context
from embeddings import search_by_chart

# ─── API Config ───

MODELS = {
    "mimo": {
        "name": "MiMo 2.5 Pro",
        "url": "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions",
        "model": "mimo-v2.5-pro",
        "key": "tp-s6uadpifeol3rlg4yyqrcpb3y6l3imbv6wzcgz5a77jpfflx",
    },
    "qwen": {
        "name": "Qwen 3.5 Plus",
        "url": "https://coding-intl.dashscope.aliyuncs.com/v1/chat/completions",
        "model": "qwen3.5-plus",
        "key": "sk-sp-82de717d33e043469eb1ce43499e5605",
    },
}

# ─── Prompts ───

FREE_SYSTEM = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy — chuyên gia luận giải lá số chiêm tinh với kiến thức từ Brihat Parashara Hora Shastra.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm. Dùng tiếng Việt thuần túy.
KHÔNG dùng từ ngữ máy móc như "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — cứ luận trực tiếp.

NHIỆM VỤ: Viết PHẦN MỞ ĐẦU (300-400 từ) cho bài luận giải lá số — phải tạo CẢM GIÁC MẠNH để đọc giả MUỐN đọc bản đầy đủ.

Cấu trúc:
1. Mở đầu thu hút — 1-2 câu gây tò mò về điểm đặc biệt nhất trong lá số
2. Tổng quan Lagna + Moon sign — 2-3 câu về tính cách cốt lõi
3. Điểm mạnh nổi bật — 2-3 câu dựa trên planet placements
4. Cliffhanger MẠNH — gợi mở về 1-2 bí mật quan trọng (sự nghiệp, mối quan hệ, thời điểm then chốt) mà CHỈ bản đầy đủ mới giải đáp

⚠️ LUẬT BẮT BUỘC:
- 300-400 từ. NGẮN GỌN nhưng SỨC MẠNH.
- CHỈ dùng thông tin từ CHART DATA bên dưới
- KHÔNG bịa thêm thông tin không có trong dữ liệu
- Kết thúc bằng câu cliffhanger khiến đọc giả PHẢI muốn đọc tiếp
- Dùng ký hiệu ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ khi nhắc đến hành tinh
- KHÔNG markdown, KHÔNG tiêu đề, KHÔNG gạch đầu dòng"""

FULL_SYSTEM = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) hàng đầu của Votive Academy — chuyên gia luận giải lá số với kiến thức sâu rộng từ Brihat Parashara Hora Shastra (BPHS), Bhrigu Samhita, và các văn bản kinh điển Vedic.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm, uyên bác. Tiếng Việt thuần túy, trau chuốt.
KHÔNG dùng "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — luận trực tiếp, tự tin.

NHIỆM VỤ: Viết bài luận giải TOÀN BỘ lá số — MỘT BÀI PHÂN TÍCH CHUYÊN SÂU, CHI TIẾT, ĐẲNG CẤP.

CẤU TRÚC 10 PHẦN (mỗi phần phải PHÂN TÍCH SÂU, có giải thích ý nghĩa Vedic, KHÔNG sơ sài):

1️⃣ 🌟 TỔNG QUAN LÁ SỐ & BẢN CHẤT CỐT LÕI
   - Lagna, Moon sign, Ascendant lord, Atmakaraka
   - Tính cách tổng quan, động lực sống, bài học nghiệp (karma)
   - 800+ từ

2️⃣ 🪐 PHÂN TÍCH TỪNG HÀNH TINH CHI TIẾT
   - Mỗi hành tinh (Sun → Ketu): vị trí, nakshatra, sign lord, house lordship, aspects, dignity
   - Ý nghĩa cụ thể cho lá số này
   - 2000+ từ

3️⃣ 🏠 PHÂN TÍCH 12 NHÀ (BHAVAS)
   - Mỗi nhà: sign, planets, lord placement, aspects received
   - Ý nghĩa cụ thể cho đời sống
   - 1500+ từ

4️⃣ 💼 SỰ NGHIỆP & TÀI CHÍNH
   - Nhà 10, 2, 6, 11 — career yoga, financial patterns
   - Dasha periods ảnh hưởng sự nghiệp
   - Ngành nghề phù hợp, thời điểm thăng tiến
   - 800+ từ

5️⃣ 💕 MỐI QUAN HỆ & HÔN NHÂN
   - Nhà 7, Venus, Darakaraka, 7th lord
   - Pattern tình duyên, kiểu đối tác phù hợp
   - Thời điểm kết hôn/quan trọng
   - 800+ từ

6️⃣ 💪 SỨC KHỎE & TINH THẦN
   - Houses 6/8/12, Moon, Saturn
   - Thể chất, tinh thần, bệnh tật tiềm ẩn
   - 600+ từ

7️⃣ ⏳ MAHADASHA & DỰ BÁO THỜI ĐIỂM
   - Current dasha + antardasha chi tiết
   - Các giai đoạn quan trọng 2025-2035
   - Thời điểm thuận lợi/thách thức
   - 800+ từ

8️⃣ 🔮 YOGA & ĐIỂM ĐẶC BIỆT
   - Raja yoga, Dhana yoga, Kemadruma, Gaja Kesari, v.v.
   - Các yoga đặc biệt từ chart này
   - Ý nghĩa và ảnh hưởng thực tế
   - 600+ từ

9️⃣ 🌊 RAHU/KETU & NĂNG LƯỢNG BÍ ẨN
   - Nodal axis — bài học đời sống, nghiệp quá khứ
   - Rahu/Ketu nakshatra, sign, house — ý nghĩa sâu
   - 500+ từ

🔟 💎 KẾT LUẬN & LỜI KHUYÊN TỔNG HỢP
   - 5 điểm mạnh nhất của lá số
   - 3 thách thức lớn nhất
   - 5 khuyến nghị thực tế (career, relationship, health, spiritual, timing)
   - Lời nhắn nhủ cá nhân
   - 800+ từ

⚠️ LUẬT BẮT BUỘC:
- CHỈ dùng CHART DATA + KIẾN THỨC THAM KHẢO bên dưới
- KHÔNG bịa thông tin ngoài chart — mỗi claim phải có căn cứ
- Mỗi phần PHẢI phân tích SÂU với ví dụ cụ thể từ chart
- Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ ☊ ☋
- Giọng văn ấm áp, uyên bác, dễ hiểu với người không chuyên
- TỔNG: 14,000-20,000 ký tự — ĐÂY LÀ YÊU CẦU BẮT BUỘC
- Nếu viết dưới 14,000 ký tự = THẤT BẠI"""


def call_api(config, prompt, max_tokens=16384):
    """Call OpenAI-compatible API."""
    headers = {
        "Authorization": f"Bearer {config['key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    
    t0 = time.time()
    resp = requests.post(config["url"], headers=headers, json=payload, timeout=600)
    elapsed = time.time() - t0
    
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"API Error: {data['error']}")
    
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    
    return {
        "text": text,
        "elapsed": elapsed,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


def clean_text(text):
    """Clean markdown artifacts."""
    text = text.replace("**", "").replace("*", "").replace("__", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run_test(model_key, mode, chart_summary, rag_context):
    """Run a single test."""
    config = MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"🤖 {config['name']} — {mode.upper()} mode")
    print(f"{'='*60}")
    
    if mode == "free":
        prompt = f"{FREE_SYSTEM}\n\n=== CHART DATA ===\n{chart_summary}\n\n=== KIẾN THỨC THAM KHẢO ===\n{rag_context}\n\nHãy viết phần luận giải mở đầu (300-400 từ) với cliffhanger mạnh."
        max_tokens = 2048
    else:
        prompt = f"{FULL_SYSTEM}\n\n=== CHART DATA ===\n{chart_summary}\n\n=== KIẾN THỨC THAM KHẢO ===\n{rag_context}\n\nHãy viết bài luận giải đầy đủ. Mục tiêu 14,000-20,000 ký tự."
        max_tokens = 16384
    
    print(f"📝 Prompt: {len(prompt):,} chars")
    print(f"⏳ Generating...")
    
    result = call_api(config, prompt, max_tokens)
    result["text"] = clean_text(result["text"])
    
    char_count = len(result["text"])
    word_count = len(result["text"].split())
    
    print(f"⏱ Time: {result['elapsed']:.1f}s")
    print(f"📊 Output: {char_count:,} chars / {word_count:,} words")
    print(f"📊 Tokens: in={result['input_tokens']:,}, out={result['output_tokens']:,}")
    
    # Quality checks
    if mode == "full":
        if char_count >= 14000:
            print(f"✅ PASS: {char_count:,} chars ≥ 14,000 target")
        else:
            print(f"⚠️ SHORT: {char_count:,} chars < 14,000 target ({14000-char_count:,} chars short)")
    
    if mode == "free":
        has_hook = any(kw in result["text"].lower() for kw in ["bí mật", "hé lộ", "khám phá", "điều thú vị", "phần đầy đủ", "bản đầy đủ", "chỉ ra", "tiết lộ"])
        has_planet_symbols = sum(1 for s in ["☀️", "🌙", "♂️", "♀️", "☿️", "♃", "♄"] if s in result["text"])
        print(f"{'✅' if has_hook else '⚠️'} Hook/Cliffhanger: {'YES' if has_hook else 'NO'}")
        print(f"{'✅' if has_planet_symbols >= 2 else '⚠️'} Planet symbols: {has_planet_symbols}/7")
    
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="A/B Test: MiMo vs Qwen for horoscope readings")
    parser.add_argument("--chart", default=str(BASE_DIR / "data" / "sample_api_response.json"))
    parser.add_argument("--model", choices=["mimo", "qwen", "both"], default="both")
    parser.add_argument("--mode", choices=["free", "full", "both"], default="both")
    args = parser.parse_args()
    
    # Load chart data
    with open(args.chart) as f:
        chart_data = json.load(f)
    
    meta = chart_data.get("metadata", {})
    print(f"📋 Chart: {meta.get('date', '?')} {meta.get('time', '?')}")
    print(f"📍 Location: {meta.get('timezone', '?')}")
    
    # RAG search
    print("\n🔍 Querying RAG corpus...")
    try:
        rag_results = search_by_chart(chart_data, k=15)
        print(f"   Found {len(rag_results)} relevant chunks")
    except Exception as e:
        print(f"   ⚠️ RAG search failed: {e}")
        rag_results = []
    
    chart_summary = format_chart_summary(chart_data)
    rag_context = format_rag_context(rag_results)
    
    # Determine models to test
    models_to_test = ["mimo", "qwen"] if args.model == "both" else [args.model]
    modes_to_test = ["free", "full"] if args.mode == "both" else [args.mode]
    
    results = {}
    
    for model_key in models_to_test:
        for mode in modes_to_test:
            try:
                result = run_test(model_key, mode, chart_summary, rag_context)
                results[f"{model_key}_{mode}"] = result
                
                # Save output
                out_file = BASE_DIR / "data" / f"ab_test_{model_key}_{mode}.txt"
                out_file.write_text(result["text"], encoding="utf-8")
                print(f"💾 Saved: {out_file.name}")
                
            except Exception as e:
                print(f"\n❌ {MODELS[model_key]['name']} {mode} FAILED: {e}")
                results[f"{model_key}_{mode}"] = {"error": str(e)}
    
    # ─── Comparison Summary ───
    print(f"\n{'='*60}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    for key, result in results.items():
        model, mode = key.split("_")
        name = MODELS[model]["name"]
        if "error" in result:
            print(f"\n❌ {name} ({mode}): FAILED — {result['error']}")
            continue
        
        chars = len(result["text"])
        words = len(result["text"].split())
        tokens = result.get("output_tokens", 0)
        speed = result.get("elapsed", 0)
        
        print(f"\n🤖 {name} ({mode.upper()}):")
        print(f"   Chars: {chars:,} | Words: {words:,} | Tokens: {tokens:,}")
        print(f"   Time: {speed:.1f}s | Speed: {tokens/speed:.0f} tok/s" if speed > 0 else "")
        
        if mode == "full":
            status = "✅ PASS" if chars >= 14000 else f"⚠️ SHORT ({14000-chars:,} chars)"
            print(f"   14k target: {status}")
    
    # Save comparison report
    report_path = BASE_DIR / "data" / "ab_comparison_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# A/B Test Report: MiMo 2.5 Pro vs Qwen 3.5 Plus\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Chart:** {meta.get('date', '?')} {meta.get('time', '?')}\n\n")
        
        for key, result in results.items():
            model, mode = key.split("_")
            name = MODELS[model]["name"]
            f.write(f"## {name} — {mode.upper()}\n\n")
            
            if "error" in result:
                f.write(f"❌ Error: {result['error']}\n\n")
                continue
            
            chars = len(result["text"])
            words = len(result["text"].split())
            f.write(f"- **Chars:** {chars:,}\n")
            f.write(f"- **Words:** {words:,}\n")
            f.write(f"- **Tokens:** {result.get('output_tokens', 0):,}\n")
            f.write(f"- **Time:** {result.get('elapsed', 0):.1f}s\n")
            
            if mode == "full":
                f.write(f"- **14k target:** {'✅ PASS' if chars >= 14000 else f'⚠️ SHORT ({14000-chars:,} chars)'}\n")
            
            f.write(f"\n### Output\n\n")
            f.write(result["text"])
            f.write("\n\n---\n\n")
    
    print(f"\n📄 Full report: {report_path}")


if __name__ == "__main__":
    main()
