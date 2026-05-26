#!/usr/bin/env python3
"""
Votive Academy — Horoscope Reading API
FastAPI endpoint: POST /reading → { free, full }

Usage:
    uvicorn api.main:app --reload --port 8080
"""

import sys
import os
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ChartRequest, ReadingResponse, HealthResponse
from engine.chart_adapter import format_chart_summary, format_rag_context, generate_rag_queries
from engine.prompt_builder import build_free_prompt, build_full_prompt, call_llm
from engine.embeddings import load_all_chunks

# ─── RAG Engine (lazy-loaded) ───

rag_engine = None
rag_chunks = None
rag_index_loaded = False


def get_rag_engine():
    global rag_engine, rag_chunks, rag_index_loaded
    
    if rag_engine is not None:
        return rag_engine, rag_chunks
    
    from engine.embeddings import search_by_chart, keyword_search
    
    # Try semantic search first
    try:
        rag_engine = search_by_chart
        print("✅ Semantic RAG engine loaded")
        rag_index_loaded = True
    except Exception as e:
        print(f"⚠️ Semantic engine failed: {e}")
        rag_index_loaded = False
        rag_chunks = load_all_chunks()
        rag_engine = lambda chart, k: [
            {"chunk": m[2], "metadata": m[2]["metadata"], "score": m[0]}
            for m in keyword_search(chart, rag_chunks)[:k]
        ]
        print(f"✅ Keyword RAG engine loaded ({len(rag_chunks)} chunks)")
    
    return rag_engine, rag_chunks


def query_rag(chart_data, k=15):
    """Query RAG: merge semantic + keyword results for best coverage."""
    from engine.embeddings import keyword_search
    
    # 1. Semantic search (broad context from clean texts)
    semantic_results = []
    engine_fn, _ = get_rag_engine()
    try:
        semantic_results = engine_fn(chart_data, k=k*2)  # get more for merging
    except Exception as e:
        print(f"⚠️ Semantic search: {e}")
    
    # 2. Keyword search (specific nakshatra/karaka matches)
    local_chunks = load_all_chunks()
    keyword_matched = keyword_search(chart_data, local_chunks)
    keyword_results = [
        {"chunk": m[2], "metadata": m[2]["metadata"], "score": m[0]}
        for m in keyword_matched[:k]
    ]
    
    # 3. Merge: deduplicate by chunk id, prioritize higher score
    merged = {}
    for r in semantic_results:
        cid = r.get("chunk", {}).get("id", "") or r.get("metadata", {}).get("name", "")
        if cid:
            if cid not in merged:
                merged[cid] = r
    for r in keyword_results:
        cid = r.get("chunk", {}).get("id", "") or r.get("metadata", {}).get("name", "")
        if cid:
            if cid not in merged or r["score"] > merged[cid].get("score", 0):
                merged[cid] = r
    
    # 4. Sort: keyword first (specific), then semantic (broad)
    final = sorted(merged.values(), key=lambda x: -x.get("score", 0))
    
    return final[:k]


def get_model_name():
    """Get preferred LLM model from env."""
    return os.environ.get("READING_MODEL", "gemini")


# ─── App ───

app = FastAPI(
    title="Votive Academy — Horoscope Reading API",
    description="RAG-powered Vedic astrology chart interpretation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ───

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check for UptimeRobot / Render."""
    engine, chunks = get_rag_engine()
    all_chunks = load_all_chunks()
    return HealthResponse(
        status="ok",
        chunks_count=len(all_chunks),
        index_loaded=rag_index_loaded,
    )


@app.get("/")
def root():
    return {
        "service": "Votive Academy Horoscope API",
        "endpoints": {
            "/health": "Health check (GET)",
            "/reading": "Full chart reading (POST)",
            "/reading/free": "Free preview reading (POST)",
            "/reading/full": "Full reading only (POST)",
        }
    }


@app.post("/reading", response_model=ReadingResponse)
def full_reading(chart: ChartRequest, model: str = None):
    """
    Generate both FREE and FULL readings from chart data.
    
    - FREE: ~300 từ giới thiệu + cliffhanger (không có RAG)
    - FULL: 1500-3000 từ, 6 sections, có RAG context
    
    Web gọi endpoint này → lưu cả 2 phần.
    Paywall 19k → chỉ show FULL sau khi user trả tiền.
    """
    chart_data = chart.model_dump(exclude_none=True)
    chosen_model = model or get_model_name()
    
    # RAG: query relevant knowledge
    rag_results = query_rag(chart_data, k=12)
    
    # Build chart summary + RAG context
    chart_summary = format_chart_summary(chart_data)
    rag_context = format_rag_context(rag_results) if rag_results else "(Không có dữ liệu tham khảo)"
    
    # Build prompts
    free_prompt = build_free_prompt(chart_summary, rag_context)
    full_prompt = build_full_prompt(chart_summary, rag_context)
    
    try:
        # Generate FREE reading
        print(f"📝 Generating FREE reading ({chosen_model})...")
        free_text = call_llm(free_prompt, chosen_model)
        
        # Generate FULL reading
        print(f"📝 Generating FULL reading ({chosen_model})...")
        full_text = call_llm(full_prompt, chosen_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
    
    return ReadingResponse(
        free=free_text or "",
        full=full_text or "",
        model=chosen_model,
        char_count_free=len(free_text or ""),
        char_count_full=len(full_text or ""),
        rag_chunks_used=len(rag_results),
    )


@app.post("/reading/free")
def free_reading(chart: ChartRequest, model: str = None):
    """
    Generate ONLY the FREE preview reading (nhanh hơn, rẻ hơn).
    Dùng khi web chỉ cần show preview trước paywall.
    """
    chart_data = chart.model_dump(exclude_none=True)
    chosen_model = model or get_model_name()
    
    chart_summary = format_chart_summary(chart_data)
    prompt = build_free_prompt(chart_summary, "(Không có dữ liệu tham khảo)")
    
    text = call_llm(prompt, chosen_model)
    
    return {"free": text, "model": chosen_model, "char_count": len(text or "")}


@app.post("/reading/full")
def full_reading(chart: ChartRequest, model: str = None):
    """
    Generate FULL reading only.
    Dùng sau khi user đã trả phí 19k.
    """
    chart_data = chart.model_dump(exclude_none=True)
    chosen_model = model or get_model_name()
    
    # RAG: query with full context
    rag_results = query_rag(chart_data, k=15)
    
    chart_summary = format_chart_summary(chart_data)
    rag_context = format_rag_context(rag_results) if rag_results else "(Không có dữ liệu tham khảo)"
    
    prompt = build_full_prompt(chart_summary, rag_context)
    
    text = call_llm(prompt, chosen_model)
    
    return {
        "full": text,
        "model": chosen_model,
        "char_count": len(text or ""),
        "rag_chunks_used": len(rag_results),
    }


@app.on_event("startup")
def startup():
    """Load RAG engine on startup."""
    print("🔮 Votive Academy Horoscope API starting...")
    try:
        get_rag_engine()
        print("✅ RAG engine ready")
    except Exception as e:
        print(f"⚠️ RAG engine init: {e}")
    print("🚀 API ready!")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=port, reload=False)
