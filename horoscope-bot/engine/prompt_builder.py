#!/usr/bin/env python3
"""
Prompt Builder — Builds LLM prompts with chart data + RAG context.
Supports FREE mode (350-450 từ + upsell cliffhanger) and FULL mode (7 sections, up to 6,000 chars).

Default model: MiMo 2.5 Pro (via Xiaomi Token Plan API).
"""

CHART_SUMMARY_TEMPLATE = """{chart_summary}

=== KIẾN THỨC THAM KHẢO (Vedic Corpus) ===
{rag_context}"""


FREE_SYSTEM_PROMPT = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy — chuyên gia luận giải lá số với kiến thức từ Brihat Parashara Hora Shastra.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm, uyên bác. Tiếng Việt thuần túy, trau chuốt.
KHÔNG dùng "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — luận trực tiếp, tự tin.

NHIỆM VỤ: Viết PHẦN MỞ ĐẦU (350-450 từ) cho bài luận giải lá số. Phần này phải khiến đọc giả CẢM THẤY MẠNH và MUỐN đọc bản đầy đủ bằng mọi giá.

Cấu trúc bắt buộc:
1. Mở đầu thu hút — 1-2 câu gây tò mò sâu sắc về điểm đặc biệt nhất, bất ngờ nhất trong lá số. Phải khiến người đọc giật mình nhận ra điều mình chưa biết về bản thân.
2. Tổng quan cốt lõi — Lagna, Moon sign, năng lượng chủ đạo. Viết như thể bạn đang nhìn thấu linh hồn người đó.
3. Điểm mạnh nổi bật — 2-3 câu dựa trên planet placements, nhấn mạnh tiềm năng chưa được khai phá.
4. Bí mật được gợi mở — Gợi ý về 1-2 điều quan trọng (thời điểm then chốt, mối quan hệ định mệnh, bước ngoặt sự nghiệp) mà CHỈ bản luận giải đầy đủ mới giải đáp tường tận.

LUẬT BẮT BUỘC:
- 350-450 từ. NGẮN GỌN nhưng ĐẬM ĐÀ, mỗi câu phải có trọng lượng.
- CHỈ dùng thông tin từ CHART DATA bên dưới. KHÔNG bịa.
- KHÔNG sử dụng bất kỳ emoji hay ký hiệu unicode nào. Viết thuần chữ. Khi nhắc đến hành tinh, dùng tên tiếng Việt: Mặt Trời, Mặt Trăng, Sao Hỏa, Sao Thủy, Sao Mộc, Sao Kim, Sao Thổ, Rahu, Ketu. Dữ liệu chart có thể chứa ký hiệu — bỏ qua, chỉ dùng tên.
- KHÔNG markdown, KHÔNG tiêu đề, KHÔNG gạch đầu dòng.
- KHÔNG được đề cập đến tên model AI, tên phần mềm, hay bất kỳ thông tin nào về hệ thống生成. Đây là bài luận giải chiêm tinh của Votive Academy, không phải output của AI.
- Giọng văn trang trọng, thấu cảm, như một bậc thầy chiêm tinh đang trực tiếp nói chuyện.
- Kết thúc bằng câu upsell mạnh, tạo cảm giác cấp bách: nhấn mạnh rằng bản đầy đủ chứa những phân tích chuyên sâu về sự nghiệp, mối quan hệ, thời điểm quan trọng — và rằng nếu bỏ lỡ, người đọc sẽ không bao giờ hiểu được toàn bộ bức tranh vận mệnh của mình."""


# ─── DEPRECATED: FULL_SYSTEM_PROMPT — chỉ dùng cho fallback single-call, async pipeline dùng section_config.py ───
FULL_SYSTEM_PROMPT = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) hàng đầu của Votive Academy — chuyên gia luận giải lá số với kiến thức sâu rộng từ Brihat Parashara Hora Shastra (BPHS), Bhrigu Samhita, và các văn bản kinh điển Vedic.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm, uyên bác. Tiếng Việt thuần túy, trau chuốt.
KHÔNG dùng "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — luận trực tiếp, tự tin.

NHIỆM VỤ: Viết bài luận giải TOÀN BỘ lá số — MỘT BÀI PHÂN TÍCH CHUYÊN SÂU, CHI TIẾT, ĐẲNG CẤP.

TỔNG SỐ CHIỀU DÀI: Bài viết cần đạt 5.000-8.000 từ (10-15 trang A4). MỖI PHẦN trong 10 phần phải viết THẬT CHI TIẾT. Đây là bài luận giải chuyên nghiệp cho khách hàng trả tiền, không được viết quá ngắn. PHẢI viết thật dài và thật sâu.

CẤU TRÚC 10 PHẦN (mỗi phần phải PHÂN TÍCH SÂU, có giải thích ý nghĩa Vedic, KHÔNG sợ sai):

1. TỔNG QUAN LÁ SỐ & BẢN CHẤT CỐT LÕI
   - Lagna, Moon sign, Ascendant lord, Atmakaraka
   - Tính cách tổng quan, động lực sống, bài học nghiệp (karma)
   - 1200+ từ

2. PHÂN TÍCH TỪNG HÀNH TINH CHI TIẾT
   - Mỗi hành tinh (Sun -> Ketu): vị trí, nakshatra, sign lord, house lordship, aspects, dignity
   - Ý nghĩa cụ thể cho lá số này
   - 2500+ từ

3. PHÂN TÍCH 12 NHÀ (BHAVAS)
   - Mỗi nhà: sign, planets, lord placement, aspects received
   - Ý nghĩa cụ thể cho đời sống
   - 1200+ từ

4. SỰ NGHIỆP & TÀI CHÍNH
   - Nhà 10, 2, 6, 11 — career yoga, financial patterns
   - Dasha periods ảnh hưởng sự nghiệp
   - Ngành nghề phù hợp, thời điểm thăng tiến
   - 1200+ từ

5. MỐI QUAN HỆ & HÔN NHÂN
   - Nhà 7, Venus, Darakaraka, 7th lord
   - Pattern tình duyên, kiểu đối tác phù hợp
   - Thời điểm kết hôn/quan trọng
   - 1200+ từ

6. SỨC KHỎE & TINH THẦN
   - Houses 6/8/12, Moon, Saturn
   - Thể chất, tinh thần, bệnh tật tiềm ẩn
   - 1800+ từ

7. MAHADASHA & DỰ BÁO THỜI ĐIỂM
   - Current dasha + antardasha chi tiết
   - Các giai đoạn quan trọng 2025-2035
   - Thời điểm thuận lợi/thách thức
   - 1200+ từ

8. YOGA & ĐIỂM ĐẶC BIỆT
   - Raja yoga, Dhana yoga, Kemadruma, Gaja Kesari, v.v.
   - Các yoga đặc biệt từ chart này
   - Ý nghĩa và ảnh hưởng thực tế
   - 1800+ từ

9. RAHU/KETU & NĂNG LƯỢNG BÍ ẨN
   - Nodal axis — bài học đời sống, nghiệp quá khứ
   - Rahu/Ketu nakshatra, sign, house — ý nghĩa sâu
   - 800+ từ

10. KẾT LUẬN & LỜI KHUYÊN TỔNG HỢP
    - 5 điểm mạnh nhất của lá số
    - 3 thách thức lớn nhất
    - 5 khuyến nghị thực tế (career, relationship, health, spiritual, timing)
    - Lời nhắn nhủ cá nhân
    - 1200+ từ

LUẬT BẮT BUỘC:
- CHỈ dùng CHART DATA + KIẾN THỨC THAM KHẢO bên dưới
- KHÔNG bịa thông tin ngoài chart — mọi claim phải có căn cứ
- Mỗi phần phải phân tiêu đề rõ ràng với số thứ tự (1., 2., 3., ...)
- KHÔNG sử dụng bất kỳ emoji hay ký hiệu unicode nào. Viết thuần chữ. Khi nhắc đến hành tinh, dùng tên tiếng Việt: Mặt Trời, Mặt Trăng, Sao Hỏa, Sao Thủy, Sao Mộc, Sao Kim, Sao Thổ, Rahu, Ketu. Dữ liệu chart có thể chứa ký hiệu — bỏ qua, chỉ dùng tên.
- KHÔNG được đề cập đến tên model AI, tên phần mềm, hay bất kỳ thông tin nào về hệ thống生成. Đây là bài luận giải chiêm tinh của Votive Academy, không phải output của AI.
- Giọng văn ấm áp, uyên bác, dễ hiểu với người không chuyên
- TỔNG: 14,000-20,000 ký tự — ĐÂY LÀ YÊU CẦU BẮT BUỘC
- Nếu viết dưới 14,000 ký tự = THẤT BẠI"""


def build_free_prompt(chart_summary, rag_context):
    """Build FREE prompt (350-450 từ + strong upsell cliffhanger)."""
    context = CHART_SUMMARY_TEMPLATE.format(
        chart_summary=chart_summary,
        rag_context=rag_context
    )
    
    prompt = f"{FREE_SYSTEM_PROMPT}\n\n{context}\n\nHãy viết phần luận giải mở đầu (350-450 từ) với upsell mạnh."
    return prompt


# ─── Diacritic enforcement footer (recency bias) ───
# Thêm instruction này vào CUỐI prompt để LLM nhớ viết có dấu
# (leveraging recency bias — instruction cuối được tuân thủ tốt hơn)
DIACRITIC_FOOTER = """
=== YÊU CẦU BẮT BUỘC (ĐỌC TRƯỚC KHI VIẾT) ===

TOÀN BỘ NỘI DUNG PHẢI VIẾT BẰNG TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ.
Mọi chữ, mọi dấu câu, mọi âm tiết — tất cả.
KHÔNG được viết không dấu dù chỉ một chữ.

ĐÚNG: "Mặt Trời của bạn nằm tại Bạch Dương ở Nhà 9..."
SAI:  "Mat Troi cua ban nam tai Bach Duong o Nha 9..."

KHÔNG dùng emoji, KHÔNG dùng ký hiệu đặc biệt, KHÔNG dùng markdown (kể cả **).
"""


def build_full_prompt(chart_summary, rag_context, section=None):
    """Build prompt for specific section (1-7) with system persona, or full concatenated if None."""
    from engine.section_config import SECTIONS_CONFIG, SECTION_SYSTEM_PREFIX
    context = CHART_SUMMARY_TEMPLATE.format(
        chart_summary=chart_summary,
        rag_context=rag_context
    )
    if section is not None and 1 <= section <= len(SECTIONS_CONFIG):
        sid, title, wc, instruction = SECTIONS_CONFIG[section - 1]
        # Per-section prompt: system persona + section instruction + diacritic footer + chart data
        return f"{SECTION_SYSTEM_PREFIX}\n\n{instruction}\n\n{DIACRITIC_FOOTER}\n\n=== DU LIEU LA SO ===\n{context}"
    # Full concatenated version (fallback)
    parts = []
    for sid, title, wc, instruction in SECTIONS_CONFIG:
        parts.append(f"PHAN {sid}: {title}\n{instruction}")
    return f"{SECTION_SYSTEM_PREFIX}\n\n{chr(10).join(parts)}\n\n=== DU LIEU LA SO ===\n{context}\n\nHãy viết bài luận giải đầy đủ (14,000-20,000 ký tự)."


def call_llm(prompt, model="mimo", max_tokens=None):
    """
    Call LLM API and return response text.
    Supports: mimo, gemini, deepseek
    
    Exceptions are raised with sanitized messages — never expose raw API errors.
    """
    from pathlib import Path
    import os
    import requests
    from utils.error_sanitizer import sanitize_error_text
    
    BASE_DIR = Path(__file__).parent.parent
    
    if model == "mimo":
        api_key = os.environ.get("MIMO_API_KEY", "") or os.environ.get("XIAOMI_API_KEY", "")
        if not api_key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    line = line.strip()
                    if 'MIMO_API_KEY' in line or 'XIAOMI_API_KEY' in line:
                        api_key = line.split('=', 1)[1].strip()
        if not api_key:
            raise RuntimeError("Thiếu MIMO_API_KEY — không thể gọi MiMo API")
        
        try:
            # Build request payload — omit max_tokens when None to let API use default
            payload = {
                "model": "mimo-v2.5-pro",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            resp = requests.post(
                "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=1200,
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"MiMo API error: {data['error']}")
            content = data["choices"][0]["message"]["content"]
            # Ensure UTF-8 integrity — prevent any silent Unicode stripping
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            return content
        except Exception as e:
            safe = sanitize_error_text(str(e), context="MiMoAPI")
            raise RuntimeError(safe) from e
    
    elif model == "gemini":
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    line = line.strip()
                    if 'GEMINI_API_KEY' in line:
                        api_key = line.split('=', 1)[1].strip()
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY — không thể gọi Gemini API")
        
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="models/gemini-2.5-pro",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            safe = sanitize_error_text(str(e), context="GeminiAPI")
            raise RuntimeError(safe) from e
    
    elif model == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    line = line.strip()
                    if 'DEEPSEEK_API_KEY' in line:
                        api_key = line.split('=', 1)[1].strip()
        if not api_key:
            raise RuntimeError("Thiếu DEEPSEEK_API_KEY — không thể gọi DeepSeek API")
        
        try:
            resp = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4096,
                },
                timeout=300,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            safe = sanitize_error_text(str(e), context="DeepSeekAPI")
            raise RuntimeError(safe) from e
    
    else:
        raise ValueError(f"Unknown model: {model}")


def generate_reading(chart_data, rag_results, model="mimo", mode="free"):
    """
    Generate complete reading using chart data + RAG context.
    
    Args:
        chart_data: dict from web API
        rag_results: list of RAG search results
        model: "mimo", "gemini", or "deepseek"
        mode: "free", "full", or "both"
    
    Returns:
        dict with { free, full } readings
    """
    from chart_adapter import format_chart_summary, format_rag_context
    
    chart_summary = format_chart_summary(chart_data)
    rag_context = format_rag_context(rag_results)
    
    free_prompt = build_free_prompt(chart_summary, rag_context)
    full_prompt = build_full_prompt(chart_summary, rag_context)
    
    print(f"📝 FREE prompt: {len(free_prompt):,} chars")
    print(f"📝 FULL prompt: {len(full_prompt):,} chars")
    
    result = {"free": "", "full": ""}
    
    if mode in ("free", "both"):
        print(f"🤖 Generating FREE reading ({model})...")
        result["free"] = call_llm(free_prompt, model)
    
    if mode in ("full", "both"):
        print(f"🤖 Generating FULL reading ({model})...")
        result["full"] = call_llm(full_prompt, model)
    
    return result


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    BASE_DIR = Path(__file__).parent.parent
    sys.path.insert(0, str(BASE_DIR / "engine"))
    
    from chart_adapter import format_chart_summary, format_rag_context, generate_rag_queries
    from embeddings import search, keyword_search, load_all_chunks
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--chart", default=str(BASE_DIR / "data" / "sample_api_response.json"))
    parser.add_argument("--model", choices=["mimo", "gemini", "deepseek", "both"], default="mimo")
    parser.add_argument("--mode", choices=["free", "full", "both"], default="free")
    args = parser.parse_args()
    
    import json
    with open(args.chart) as f:
        chart_data = json.load(f)
    
    # Try semantic search first, fallback to keyword
    print("🔍 Querying RAG...")
    queries = generate_rag_queries(chart_data)
    print(f"   {len(queries)} queries generated")
    
    rag_results = []
    try:
        from embeddings import search_by_chart
        rag_results = search_by_chart(chart_data, k=12)
        print(f"   Semantic search: {len(rag_results)} results")
    except Exception as e:
        print(f"   ⚠️ Semantic search failed: {e}")
        chunks = load_all_chunks()
        matched = keyword_search(chart_data, chunks)
        rag_results = [{"chunk": m[2], "metadata": m[2]["metadata"], "score": m[0]} for m in matched[:12]]
        print(f"   Keyword fallback: {len(rag_results)} results")
    
    if not rag_results:
        print("   ⚠️ No RAG results found, using empty context")
    
    result = generate_reading(chart_data, rag_results, args.model, args.mode)
    
    if result["free"]:
        print("\n" + "=" * 60)
        print("📖 FREE READING")
        print("=" * 60)
        print(result["free"])
    
    if result["full"]:
        print("\n" + "=" * 60)
        print("📖 FULL READING")
        print("=" * 60)
        print(result["full"])
    
    # Save
    out_dir = BASE_DIR / "data"
    out_dir.mkdir(exist_ok=True)
    if result["free"]:
        with open(out_dir / "reading_free.txt", "w") as f:
            f.write(result["free"])
        print(f"\n💾 Saved: data/reading_free.txt")
    if result["full"]:
        with open(out_dir / "reading_full.txt", "w") as f:
            f.write(result["full"])
        print(f"💾 Saved: data/reading_full.txt")
