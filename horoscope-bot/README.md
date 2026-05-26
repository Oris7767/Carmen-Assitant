# Votive Academy — Horoscope Bot

## 🪐 What It Does

Nhận chart JSON từ web (đã có chart engine), query RAG corpus → LLM → luận giải chiêm tinh Vệ Đà.

Kiến trúc:

```
Web (tính chart)               Bot LLM (chúng ta)
      │                                │
      │  POST JSON (houses, dashas,    │
      │   aspects, nakshatras... )     │
      ├──────────────────────────────► │
      │                                 ├─ Parse chart
      │                                 ├─ RAG: query 431 chunks
      │                                 ├─ Build prompt
      │                                 ├─ LLM → FREE + FULL
      │  { free: "...", full: "..." }   │
      │◄──────────────────────────────┤
      │  Web: FREE hiển thị trước       │
      │  Paywall 19k → FULL             │
```

## Current State (24/05/2026) ✅

| Component | Status | Detail |
|-----------|--------|--------|
| RAG Corpus | ✅ | 431 chunks (nakshatras 104 + karakatvas 327) |
| FAISS Index | ✅ | 3072-dim, Gemini embedding-2 |
| Semantic Search | ✅ | Multi-query from chart data |
| Keyword Fallback | ✅ | Metadata matching |
| Prompt Builder | ✅ | FREE (~300 từ) + FULL (6 sections) |
| LLM Integration | ✅ | Gemini 2.5 Pro + DeepSeek |
| API (FastAPI) | ✅ | POST /reading, /reading/free, /reading/full |
| Chart Adapter | ✅ | Parse web JSON → LLM-friendly format |

## API Endpoints

### POST /reading
Full reading: FREE + FULL trong 1 call.

### POST /reading/free
FREE preview nhanh (không RAG). Dùng trước paywall.

### POST /reading/full
FULL reading với RAG context. Dùng sau paywall 19k.

### GET /health
Health check cho UptimeRobot/Render.

## Input Format (từ web API)

```json
{
  "metadata": { "date": "1998-04-16", "time": "02:36", "timezone": "Asia/Ho_Chi_Minh" },
  "ascendant": { "sign": { "name": "Aquarius" }, "nakshatra": { "name": "Dhanishta", "lord": "Mars" } },
  "planets": [ { "planet": "SUN", "sign": {...}, "house": {...}, "nakshatra": {...}, "aspects": [...] }, ... ],
  "houses": [ { "number": 1, "sign": "Aquarius", "planets": [...] }, ... ],
  "dashas": { "current": { "planet": "Venus", ... }, "sequence": [...] }
}
```

## Output

```json
{
  "free": "~300 từ giới thiệu + cliffhanger",
  "full": "1500-3000 từ, 6 sections",
  "model": "gemini",
  "rag_chunks_used": 12,
  "char_count_free": 1901,
  "char_count_full": 15628
}
```

## Deployment

```bash
# Dev
python api/main.py

# Production (Render)
uvicorn api.main:app --host 0.0.0.0 --port $PORT

# Environment
GEMINI_API_KEY=xxx         # Required
DEEPSEEK_API_KEY=xxx       # Optional
READING_MODEL=gemini       # gemini | deepseek
PORT=8080                  # Render auto-set
```

## Project Structure

```
horoscope-bot/
├── api/
│   ├── main.py         → FastAPI app (endpoints)
│   └── schemas.py      → Pydantic models
├── corpus/
│   ├── raw/            → PDFs & documents gốc
│   ├── chunks/         → 431 processed chunks
│   └── embeddings/     → FAISS index + metadata
├── engine/
│   ├── chart_adapter.py → Parse web JSON → structured text
│   ├── embeddings.py    → FAISS build + search (Gemini API)
│   ├── prompt_builder.py → Prompt + LLM call
│   ├── pipeline.py      → Corpus processing
│   └── query_engine.py  → Legacy: keyword matching
├── data/
│   ├── sample_api_response.json
│   └── test_chart.json
└── README.md
```

## Key Design Decisions

1. **Web handles chart calc** → No house/dasha engine needed in bot
2. **Gemini Embedding API** → No local ML deps (sentence-transformers, torch)
3. **FAISS for vector search** → Fast, small index (540KB for 431 chunks)
4. **FREE + FULL split** → FREE: preview + cliffhanger. FULL: paywall 19k
5. **Dual search** → Semantic (karakatva chunks) + Keyword (nakshatra chunks with OCR noise)

## Dependencies

- `fastapi`, `uvicorn` — API server
- `google-genai` — Gemini LLM + embedding API
- `faiss-cpu` — Vector search
- `numpy` — Embedding math
- `pydantic` — Schema validation
