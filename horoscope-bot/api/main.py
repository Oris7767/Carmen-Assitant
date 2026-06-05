#!/usr/bin/env python3
"""
Votive Academy — Horoscope Reading API

Endpoints:
  POST /reading/free → FREE preview (~60s)
  POST /reading/full → FULL reading (3-5 min)
  Frontend calls FREE first, then FULL separately.

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
import threading
import uuid

from api.schemas import ChartRequest, HealthResponse, TaskStatusResponse
from engine.chart_adapter import format_chart_summary, format_rag_context, generate_rag_queries
from engine.prompt_builder import build_free_prompt, build_full_prompt, call_llm
from engine.embeddings import load_all_chunks
from engine.diacritic_repair import _estimate_no_diacritic_ratio

# ─── Raw Response Logging ───
RAW_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw_logs")
os.makedirs(RAW_LOG_DIR, exist_ok=True)


def _save_raw_log(task_id: str, section_idx: int, raw_text: str, model: str):
    """Save raw LLM response for diacritic debugging."""
    from datetime import datetime
    import re
    
    # Auto-detect diacritics: count Vietnamese tone marks
    vn_tones = r'[ắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵđ]'
    tone_count = len(re.findall(vn_tones, raw_text, re.IGNORECASE))
    total_words = len(raw_text.split())
    has_diacritics = tone_count > 0
    
    raw = raw_text if raw_text else "(EMPTY)"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_lines = [
        f"# Raw Response Log — Section {section_idx}",
        f"# Timestamp: {ts}",
        f"# Task ID: {task_id}",
        f"# Model: {model}",
        f"# Raw chars: {len(raw)}",
        f"# Words: {total_words}",
        f"# Vietnamese tone marks: {tone_count}",
        f"# Has diacritics: {has_diacritics}",
        "" if has_diacritics else "# ⚠️ NO DIACRITICS!⚠️ ",
        "═" * 60,
        raw,
        "",
        "═" * 60,
        f"# END — {ts}",
    ]
    
    log_path = os.path.join(RAW_LOG_DIR, f"{task_id}_section_{section_idx}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    
    print(f"   📝 RAW LOG SAVED: {log_path}", flush=True)
from engine.pdf_generator import generate_pdf, save_pdf
from engine.supabase_client import update_order_status, get_order
from utils.error_sanitizer import sanitize_exception
import json


# ─── Text Post-Processing ───

# ─── Notifications ───
NOTIF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notifications")
os.makedirs(NOTIF_DIR, exist_ok=True)

TELEGRAM_ADMIN_ID = "1336718742"
TELEGRAM_BOT_TOKEN = ""

def _load_bot_token_static():
    global TELEGRAM_BOT_TOKEN
    if TELEGRAM_BOT_TOKEN:
        return TELEGRAM_BOT_TOKEN
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("BOT_TOKEN") and "=" in line:
                TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                return TELEGRAM_BOT_TOKEN
    return ""

def send_notification(order_id, task_id, pdf_path, chart_data=None):
    """Notify Kim Ssa when PDF is ready."""
    meta = (chart_data or {}).get('metadata', {}) or {}
    name = (chart_data or {}).get('name', 'Không rõ')
    
    basename = os.path.basename(pdf_path)
    msg = (
        f"📄 PDF MOI DA SAN SANG\n\n"
        f"👤 Khach: {name}\n"
        f"📅 Ngay sinh: {meta.get('date', '?')}\n"
        f"⏰ Gio sinh: {meta.get('time', '?')}\n"
        f"🆔 Order: {order_id}\n"
        f"📎 File: {basename}\n\n"
        f"🔗 Download: http://horoscope.vedicvn.sbs/reading/pdf/{task_id}"
    )
    
    # File notification (backup)
    os.makedirs(NOTIF_DIR, exist_ok=True)
    notif_file = os.path.join(NOTIF_DIR, f"{order_id}.json")
    with open(notif_file, 'w', encoding='utf-8') as f:
        json.dump({
            "order_id": order_id,
            "task_id": task_id,
            "pdf_path": pdf_path,
            "message": msg,
            "notified": False,
        }, f, ensure_ascii=False, indent=2)
    
    # Telegram
    token = _load_bot_token_static()
    if token and TELEGRAM_ADMIN_ID:
        try:
            import requests
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": TELEGRAM_ADMIN_ID,
                "text": msg,
                "parse_mode": "Markdown",
            }, timeout=10)
            if resp.status_code == 200:
                print(f"✅ Telegram sent for order {order_id}")
                d = json.load(open(notif_file))
                d["notified"] = True
                d["telegram_sent"] = True
                json.dump(d, open(notif_file, 'w'), ensure_ascii=False, indent=2)
            else:
                print(f"⚠️ Telegram HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"⚠️ Telegram error: {e}")
    else:
        print(f"⚠️ No Telegram token (token={'set' if token else 'empty'}, admin={'set' if TELEGRAM_ADMIN_ID else 'empty'})")
    
    print(f"📄 Notification: {notif_file}")


def clean_text(text: str) -> str:
    """
    Clean LLM output for display:
    - Strip * characters (markdown bold/italic artifacts)
    - Normalize whitespace
    """
    if not text:
        return ""
    # Remove standalone * and ** used for markdown formatting
    text = text.replace('**', '').replace('*', '')
    # Remove __ used for markdown bold
    text = text.replace('__', '')
    # Normalize multiple blank lines
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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
    """Get preferred LLM model from env. Default: mimo (MiMo 2.5 Pro)."""
    return os.environ.get("READING_MODEL", "mimo")


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

# ── Fix double slash ──
import re as _re
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.datastructures import URL

class DoubleSlashMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http",) and scope["path"].startswith("//"):
            scope["path"] = _re.sub(r'/+', '/', scope["path"])
            scope["raw_path"] = scope["path"].encode()
        await self.app(scope, receive, send)

app.add_middleware(DoubleSlashMiddleware)


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
            "/reading/free": "⭐ FREE preview reading — gọi trước (~60s)",
            "/reading/full": "⭐ FULL reading — gọi sau (3-5 min)",
            "/reading": "Redirect → hướng dẫn flow 2 bước (POST)",
            "/reading/full/async": "⚡ FULL async — MiMo → PDF (POST)",
            "/reading/status/{task_id}": "⚡ Check task status (GET)",
            "/reading/pdf/{task_id}": "⚡ Download PDF (GET)", 
            "/debug/config": "Debug config (GET)",
        }
    }


@app.get("/debug/config")
def debug_config():
    """Debug endpoint — check env vars and API key status."""
    import sys
    reading_model = os.environ.get("READING_MODEL", "mimo")
    
    # Check API keys using same logic as call_llm()
    def _find_key(env_name, alt_name=None):
        key = os.environ.get(env_name, "")
        if not key and alt_name:
            key = os.environ.get(alt_name, "")
        if not key:
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                for line in env_file.read_text().split('\n'):
                    line = line.strip()
                    if (env_name in line or (alt_name and alt_name in line)) and not line.startswith('#'):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        return key
    
    mimo_key = _find_key("MIMO_API_KEY", "XIAOMI_API_KEY")
    gemini_key = _find_key("GEMINI_API_KEY")
    deepseek_key = _find_key("DEEPSEEK_API_KEY")
    env_file_exists = (BASE_DIR / ".env").exists()
    
    # Test MiMo API connectivity
    mimo_status = "unknown"
    mimo_error = None
    if mimo_key:
        try:
            import requests as req_debug
            r = req_debug.post(
                "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {mimo_key}", "Content-Type": "application/json"},
                json={"model": "mimo-v2.5-pro", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
                timeout=10,
            )
            mimo_status = f"HTTP {r.status_code}"
        except Exception as e:
            mimo_status = "error"
            mimo_error = str(e)[:200]
    else:
        mimo_status = "no_key"
    
    return {
        "python_version": sys.version,
        "reading_model": reading_model,
        "mimo_key_set": bool(mimo_key),
        "mimo_key_prefix": mimo_key[:12] + "..." if mimo_key else None,
        "mimo_key_length": len(mimo_key) if mimo_key else 0,
        "mimo_api_status": mimo_status,
        "mimo_api_error": mimo_error,
        "gemini_key_set": bool(gemini_key),
        "deepseek_key_set": bool(deepseek_key),
        "env_file_exists": env_file_exists,
    }


@app.post("/reading")
def reading_redirect(chart: ChartRequest):
    """
    ⚠️ DEPRECATED: Use /reading/free + /reading/full separately.
    
    Frontend flow:
      1. POST /reading/free → hiện FREE ngay (~60s)
      2. POST /reading/full → loading spinner → hiện FULL (3-5 min)
    """
    return {
        "message": "Vui lòng gọi 2 endpoint riêng biệt",
        "flow": {
            "step1": {"method": "POST", "endpoint": "/reading/free", "description": "FREE preview (~60s)"},
            "step2": {"method": "POST", "endpoint": "/reading/full/async", "description": "⚡ FULL async — MiMo → PDF (background)"},
            "poll": {"method": "GET", "endpoint": "/reading/status/{task_id}", "description": "Poll cho tới khi status=done"},
        }
    }


@app.post("/reading/free")
def free_reading(chart: ChartRequest, model: str = None):
    """
    Generate ONLY the FREE preview reading (nhanh hơn, rẻ hơn).
    Dùng khi web chỉ cần show preview trước paywall.
    """
    try:
        chart_data = chart.model_dump(exclude_none=True)
        chosen_model = model or get_model_name()
        
        chart_summary = format_chart_summary(chart_data)
        prompt = build_free_prompt(chart_summary, "(Không có dữ liệu tham khảo)")
        
        print(f"📝 FREE reading ({chosen_model}) — prompt: {len(prompt)} chars")
        text = call_llm(prompt, chosen_model)
        text = clean_text(text or "")
        
        return {"free": text}
    except Exception as e:
        safe_msg = sanitize_exception(e, context="FreeReading")
        raise HTTPException(status_code=500, detail=safe_msg)


@app.post("/reading/full")
def full_reading(chart: ChartRequest, model: str = None):
    """
    Generate FULL reading only.
    Dùng sau khi user đã trả phí 19k.
    """
    try:
        chart_data = chart.model_dump(exclude_none=True)
        chosen_model = model or get_model_name()
        
        # RAG: query with full context
        rag_results = query_rag(chart_data, k=15)
        
        chart_summary = format_chart_summary(chart_data)
        rag_context = format_rag_context(rag_results) if rag_results else "(Không có dữ liệu tham khảo)"
        
        prompt = build_full_prompt(chart_summary, rag_context)
        
        print(f"📝 FULL reading ({chosen_model}) — prompt: {len(prompt)} chars")
        text = call_llm(prompt, chosen_model)
        text = clean_text(text or "")
        
        return {"full": text}
    except Exception as e:
        safe_msg = sanitize_exception(e, context="FullReading")
        raise HTTPException(status_code=500, detail=safe_msg)



# ─── Async Task Store ───
# ─── Task Store (persists across restarts) ───
TASK_STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "task_store.json")

def _save_tasks():
    import json
    clean = {}
    for k, v in _tasks.items():
        clean[k] = {sk: sv for sk, sv in v.items() if sk != 'lock'}
    with open(TASK_STORE, 'w') as f:
        json.dump(clean, f, indent=2)


def _load_tasks():
    import json
    if os.path.exists(TASK_STORE):
        try:
            with open(TASK_STORE) as f:
                return json.load(f)
        except:
            pass
    return {}

_tasks = _load_tasks()
_tasks_lock = threading.Lock()

def _run_full_reading(task_id: str, chart_data: dict, chosen_model: str, order_id: str = None):
    """Background task: 6 sequential MiMo calls → concatenate → PDF"""
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from engine.chart_adapter import format_chart_summary, format_rag_context
        from engine.embeddings import search_by_chart, keyword_search
        from engine.prompt_builder import build_full_prompt, call_llm
        from engine.section_config import SECTIONS_CONFIG
        from engine.pdf_generator import save_pdf
        
        total_sections = len(SECTIONS_CONFIG)
        
        with _tasks_lock:
            _tasks[task_id] = {"status": "rag", "section": 0, "total": total_sections}
            _save_tasks()
        
        # Update Supabase
        if order_id:
            try:
                update_order_status(order_id, "processing")
            except Exception as se:
                print(f"⚠️ Supabase start update: {se}", flush=True)
        
        # RAG (shared across all sections)
        chart_summary = format_chart_summary(chart_data)
        rag_chunks_local = load_all_chunks()
        from engine.embeddings import search_by_chart
        try:
            results = search_by_chart(chart_data, k=15)
        except:
            results = []
        rag_context = format_rag_context(results) if results else "(Không có dữ liệu tham khảo)"
        
        print(f"🔍 RAG: {len(results) if results else 0} results, context: {len(rag_context)} chars", flush=True)
        
        # ─── 6 SEQUENTIAL SECTION CALLS ───
        sections_text = []
        
        # Self-healing: max attempts per section (1 original + 2 retries)
        # max_tokens removed — letting MiMo use full model capacity for Vietnamese diacritics
        MAX_RETRIES = 3
        
        for idx, (sid, title, wc, instruction) in enumerate(SECTIONS_CONFIG, 1):
            with _tasks_lock:
                _tasks[task_id] = {
                    "status": "generating",
                    "section": idx,
                    "section_title": title,
                    "total": total_sections,
                }
                _save_tasks()
            
            print(f"\n{'='*50}", flush=True)
            print(f"📝 Section {idx}/{total_sections}: {title}", flush=True)
            print(f"   Target: {wc} chars | max_tokens: unlimited", flush=True)
            
            # Build section-specific prompt (includes system persona)
            section_prompt = build_full_prompt(chart_summary, rag_context, section=idx)
            print(f"   Prompt: {len(section_prompt)} chars", flush=True)
            
            # Self-healing loop: retry on short/empty OR no diacritics
            section_text = ""
            section_attempts = 0
            while section_attempts < MAX_RETRIES:
                section_attempts += 1
                try:
                    if section_attempts > 1:
                        print(f"   🔄 Retry #{section_attempts}/{MAX_RETRIES}...", flush=True)
                    # No max_tokens limit — let API use full model capacity for diacritics
                    section_text = call_llm(section_prompt, chosen_model)
                    
                    # Save raw LLM response (attempt suffix for retries)
                    suffix = f"_attempt{section_attempts}"
                    _save_raw_log(f"{task_id}{suffix}", idx, section_text or "", chosen_model)
                    
                    if section_text and len(section_text.strip()) > 50:
                        # ─── Self-Healing: Diacritic Check ───
                        # Retry if LLM response lacks Vietnamese diacritics
                        bad_ratio = _estimate_no_diacritic_ratio(section_text)
                        
                        if bad_ratio > 0.3:
                            print(f"   ⚠️ Attempt {section_attempts}: NO DIACRITICS (ratio={bad_ratio:.0%}), retrying...", flush=True)
                            if section_attempts >= MAX_RETRIES:
                                print(f"   Max retries reached — using raw output as-is", flush=True)
                                sections_text.append(f"## {idx}. {title}\n\n{section_text.strip()}")
                                print(f"   ✅ Done (raw): {len(section_text)} chars", flush=True)
                            continue  # retry (don't append yet)
                        else:
                            # Diacritics OK — use raw output directly
                            sections_text.append(f"## {idx}. {title}\n\n{section_text.strip()}")
                            print(f"   ✅ Done: {len(section_text)} chars" + (f" (after retry)" if section_attempts > 1 else ""), flush=True)
                            break
                    else:
                        print(f"   ⚠️ Attempt {section_attempts}: Short/empty ({len(section_text or '')} chars), retrying...", flush=True)
                        if section_attempts >= MAX_RETRIES:
                            sections_text.append(f"## {idx}. {title}\n\n(Không có dữ liệu cho phần này — vui lòng thử lại)\n")
                except Exception as section_err:
                    safe_err = sanitize_exception(section_err, context=f"Section{idx}")
                    print(f"   ❌ Attempt {section_attempts} failed: {safe_err}", flush=True)
                    if section_attempts >= MAX_RETRIES:
                        sections_text.append(f"## {idx}. {title}\n\n(Lỗi khi tạo phần này. Vui lòng liên hệ Votive Academy để được hỗ trợ. Mã lỗi: {task_id}-S{idx})\n")
        
        # ─── Concatenate ───
        full_text = "\n\n".join(sections_text)
        total_chars = len(full_text)
        print(f"\n📊 Concatenated: {total_chars:,} chars from {len(sections_text)} sections", flush=True)
        
        if total_chars < 500:
            raise RuntimeError(f"Noi dung qua ngan ({total_chars} chars) — tat ca sections that bai")
        
        # ─── PDF ───
        with _tasks_lock:
            _tasks[task_id] = {"status": "pdf", "section": total_sections, "total": total_sections}
            _save_tasks()
        
        pdf_path = save_pdf(full_text, chart_data)
        
        with _tasks_lock:
            _tasks[task_id] = {
                "status": "done",
                "pdf_path": pdf_path,
                "chars": total_chars,
                "sections": len(sections_text),
            }
            _save_tasks()
        print(f"✅ PDF ready: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)", flush=True)
        
        # Supabase
        if order_id:
            try:
                bp = os.path.basename(pdf_path)
                update_order_status(order_id, "done", pdf_url=f"/reading/pdf/{task_id}", notes=f"PDF: {bp}, chars: {total_chars}, sections: {len(sections_text)}/{total_sections}")
                print(f"✅ Supabase updated for order {order_id}", flush=True)
            except Exception as se:
                print(f"⚠️ Supabase update failed: {se}", flush=True)
        
        # Notify
        try:
            send_notification(order_id, task_id, pdf_path, chart_data)
        except Exception as ne:
            print(f"⚠️ Notification failed: {ne}", flush=True)
        
    except Exception as e:
        safe = sanitize_exception(e, context="FullReadingAsync")
        print(f"❌ Async task {task_id} failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        with _tasks_lock:
            _tasks[task_id] = {"status": "error", "error": safe}
            _save_tasks()
        if order_id:
            try:
                update_order_status(order_id, "error", notes=str(e)[:200])
            except:
                pass


@app.post("/reading/full/async")
def full_reading_async(chart: ChartRequest, model: str = None, order_id: str = None):
    """
    Start FULL reading asynchronously.
    Accepts optional order_id to update Supabase when done.
    """
    try:
        chart_data = chart.model_dump(exclude_none=True)
        chosen_model = model or get_model_name()
        
        task_id = str(uuid.uuid4())[:8]
        with _tasks_lock:
            _tasks[task_id] = {"status": "queued"}
            _save_tasks()
        
        # Start background thread
        t = threading.Thread(
            target=_run_full_reading,
            args=(task_id, chart_data, chosen_model, order_id),
            daemon=True,
        )
        t.start()
        
        from engine.section_config import SECTIONS_CONFIG as _sections_config
        return {"task_id": task_id, "status": "queued", "order_id": order_id, "total_sections": len(_sections_config)}
    except Exception as e:
        safe_msg = sanitize_exception(e, context="AsyncFullReading")
        raise HTTPException(status_code=500, detail=safe_msg)


@app.get("/reading/status/{task_id}")
def reading_status(task_id: str):
    """Check async FULL reading status with section progress."""
    with _tasks_lock:
        task = _tasks.get(task_id)
    
    if task is None:
        return {"status": "not_found"}
    
    result = {
        "status": task["status"],
    }
    
    # Section progress (for "generating" status)
    if task["status"] == "generating":
        result["section"] = task.get("section", 0)
        result["total"] = task.get("total", 7)
        result["section_title"] = task.get("section_title", "")
    
    if task["status"] == "done":
        result["chars"] = task.get("chars", 0)
        result["sections"] = task.get("sections", 0)
        pdf_path = task.get("pdf_path", "")
        result["pdf_url"] = f"/reading/pdf/{task_id}" if pdf_path else None
    elif task["status"] == "error":
        result["error"] = task.get("error", "Lỗi không xác định")
    
    return result


@app.get("/reading/pdf/{task_id}")
def reading_pdf(task_id: str):
    """Download generated PDF."""
    with _tasks_lock:
        task = _tasks.get(task_id)
    
    if task is None or task["status"] != "done":
        raise HTTPException(status_code=404, detail="PDF chưa sẵn sàng")
    
    pdf_path = task.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="File PDF không tồn tại")
    
    from fastapi.responses import FileResponse
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=os.path.basename(pdf_path))


@app.on_event("startup")
def startup():
    """Load RAG engine on startup. Clean stale tasks."""
    print("🔮 Votive Academy Horoscope API starting...", flush=True)
    try:
        get_rag_engine()
        print("✅ RAG engine ready", flush=True)
    except Exception as e:
        print(f"⚠️ RAG engine init: {e}", flush=True)
    
    # Mark any in-flight tasks as error (service restart = lost threads)
    try:
        with _tasks_lock:
            stale = [tid for tid, t in _tasks.items() if t.get("status") in ("generating", "rag", "pdf", "queued")]
            for tid in stale:
                _tasks[tid] = {"status": "error", "error": "Service restarted — vui lòng thử lại"}
            if stale:
                _save_tasks()
                print(f"🧹 Cleaned {len(stale)} stale tasks: {stale}", flush=True)
    except Exception as e:
        print(f"⚠️ Task cleanup: {e}", flush=True)
    
    print("🚀 API ready!", flush=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("api.main:app", host=host, port=port, reload=False)
