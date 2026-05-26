#!/usr/bin/env python3
"""
Prompt Builder — Builds LLM prompts with chart data + RAG context.
Supports FREE mode (300 từ + cliffhanger) and FULL mode (complete reading).
"""

CHART_SUMMARY_TEMPLATE = """{chart_summary}

=== KIẾN THỨC THAM KHẢO (Vedic Corpus) ===
{rag_context}"""


FREE_SYSTEM_PROMPT = """Bạn là một nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy — chuyên gia luận giải lá số chiêm tinh với kiến thức từ Brihat Parashara Hora Shastra.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm. Dùng tiếng Việt thuần túy.
KHÔNG dùng từ ngữ máy móc như "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — cứ luận trực tiếp.

NHIỆM VỤ: Viết PHẦN MỞ ĐẦU NGẮN (ĐÚNG 200-300 từ) cho một bài luận giải lá số.

Nội dung:
1. 1-2 câu giới thiệu Lagna (Cung Mọc) và tính cách tổng quan
2. 2-3 câu về điểm mạnh tính cách dựa trên Moon sign + Lagna lord
3. 1-2 câu gợi mở về sự nghiệp hoặc mối quan hệ (cliffhanger)

⚠️ LUẬT BẮT BUỘC:
- ĐÚNG 200-300 từ. KHÔNG dài dòng. Viết ngắn gọn, súc tích.
- CHỈ dùng thông tin từ CHART DATA bên dưới
- KHÔNG bịa thêm thông tin không có trong dữ liệu
- Kết thúc bằng: "...nhưng điều thú vị nhất sẽ được hé lộ trong phần luận giải đầy đủ."
- Dùng ký hiệu ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ khi nhắc đến hành tinh
- KHÔNG có tiêu đề, KHÔNG có gạch đầu dòng, KHÔNG có dấu hiệu markdown"""


FULL_SYSTEM_PROMPT = """Bạn là nhà chiêm tinh Vệ Đà (Vedic astrologer) của Votive Academy — chuyên gia luận giải lá số với kiến thức từ Brihat Parashara Hora Shastra (BPHS) và các văn bản kinh điển Vedic.

PHONG CÁCH: Chuyên nghiệp, sâu sắc, thấu cảm. Dùng tiếng Việt thuần túy.
KHÔNG dùng "dựa trên dữ liệu", "theo chiêm tinh Vệ Đà" — luận trực tiếp.

NHIỆM VỤ: Luận giải TOÀN BỘ lá số. Cấu trúc gồm 6 phần:

1️⃣ 🎭 TÍNH CÁCH & BẢN CHẤT (Lagna + Moon sign + Lagna lord)
2️⃣ 💼 SỰ NGHIỆP & TÀI CHÍNH (Nhà 10 + ♃ Sao Mộc)  
3️⃣ 💕 MỐI QUAN HỆ & HÔN NHÂN (Nhà 7 + ♀️ Sao Kim)
4️⃣ 💪 SỨC KHỎE & TINH THẦN (Nhà 6/8/12 + ♄ Sao Thổ)
5️⃣ ⏳ THỜI ĐIỂM QUAN TRỌNG (Dasha hiện tại + dự báo)
6️⃣ 💎 KẾT LUẬN & LỜI KHUYÊN — tổng kết 3 điểm mạnh nhất, 2 khuyến nghị

⚠️ LUẬT BẮT BUỘC:
- CHỈ dùng thông tin từ CHART DATA và KIẾN THỨC THAM KHẢO
- KHÔNG bịa thêm chi tiết không có trong dữ liệu
- Mỗi claim PHẢI có căn cứ từ chart hoặc kiến thức Vedic trong tham khảo
- Dùng ký hiệu 🪐 ☀️ 🌙 ♂️ ♀️ ☿️ ♃ ♄ 
- Độ dài: 1500-3000 từ
- Giọng văn ấm áp, chuyên nghiệp, dễ hiểu với người không chuyên"""


def build_free_prompt(chart_summary, rag_context):
    """Build FREE prompt (300 từ + cliffhanger)."""
    context = CHART_SUMMARY_TEMPLATE.format(
        chart_summary=chart_summary,
        rag_context=rag_context
    )
    
    prompt = f"{FREE_SYSTEM_PROMPT}\n\n{context}\n\nHãy viết phần luận giải mở đầu."
    return prompt


def build_full_prompt(chart_summary, rag_context):
    """Build FULL prompt (1500-3000 từ, 6 sections)."""
    context = CHART_SUMMARY_TEMPLATE.format(
        chart_summary=chart_summary,
        rag_context=rag_context
    )
    
    prompt = f"{FULL_SYSTEM_PROMPT}\n\n{context}\n\nHãy viết bài luận giải đầy đủ."
    return prompt


def call_llm(prompt, model="gemini"):
    """
    Call LLM API and return response text.
    Supports: gemini, deepseek
    """
    from pathlib import Path
    import os
    
    BASE_DIR = Path(__file__).parent.parent
    
    if model == "gemini":
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
            return "❌ Không tìm thấy GEMINI_API_KEY"
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="models/gemini-2.5-pro",
            contents=prompt,
        )
        return response.text
    
    elif model == "deepseek":
        # DeepSeek API call
        import requests
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    line = line.strip()
                    if 'DEEPSEEK_API_KEY' in line:
                        api_key = line.split('=', 1)[1].strip()
        if not api_key:
            return "❌ Không tìm thấy DEEPSEEK_API_KEY"
        
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    
    else:
        return f"❌ Unknown model: {model}"


def generate_reading(chart_data, rag_results, model="gemini", mode="free"):
    """
    Generate complete reading using chart data + RAG context.
    
    Args:
        chart_data: dict from web API
        rag_results: list of RAG search results
        model: "gemini" or "deepseek"
        mode: "free" or "full"
    
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
    parser.add_argument("--model", choices=["gemini", "deepseek", "both"], default="gemini")
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
