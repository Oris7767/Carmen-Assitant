# Horoscope Bot — Kiến trúc & Luồng Chi Tiết

> **Last updated:** 2026-05-30 17:47 GMT+7  
> **Bot:** Votive VedicVN Horoscope (votive-astrologybot)  
> **Domain:** https://horoscope.vedicvn.sbs  
> **VPS:** 160.22.106.46 (4 vCPU, 4GB RAM, 40GB SSD, Ubuntu 24.04)

---

## 1. Tổng quan Hạ tầng

```
┌──────────────────────────────────────────────────────────────┐
│                     FRONTEND (Netlify)                        │
│            deploy-preview-35--vedicvn.netlify.app             │
│                                                               │
│  Flow: Nhập chart → Sepay thanh toán 19k → Order created     │
│       → POST /reading/full/async → Poll status → Download PDF │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS
                           ▼
┌──────────────────────────────────────────────────────────────┐
│              NGINX (horoscope.vedicvn.sbs)                    │
│              Let's Encrypt SSL → proxy_pass :8000              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│        VOTIVE-ASTROLOGYBOT (systemd, uvicorn :8000)           │
│                                                               │
│  /health               → Health check (UptimeRobot)          │
│  /reading/free         → FREE preview (sync, ~60s)           │
│  /reading/full/async   → FULL async (POST, returns task_id)  │
│  /reading/status/{id}  → Poll progress (GET)                  │
│  /reading/pdf/{id}     → Download PDF (GET)                   │
│  /debug/config         → Debug API key status                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌──────────┐  ┌───────────┐
         │  MiMo   │  │ Supabase │  │ Telegram  │
         │ 2.5 Pro │  │ (orders) │  │ (notify)  │
         └────────┘  └──────────┘  └───────────┘
```

---

## 2. Cấu trúc thư mục

```
/root/horoscope-bot/                    # VPS production
~/workspace/horoscope-bot/             # Local dev (sync qua scp)

├── api/
│   ├── main.py          ← FastAPI app, endpoints, async pipeline
│   └── schemas.py       ← Pydantic models (ChartRequest, TaskStatusResponse)
├── engine/
│   ├── section_config.py    ← 6 section prompts + shared persona
│   ├── prompt_builder.py    ← build_free_prompt(), build_full_prompt(), call_llm()
│   ├── chart_adapter.py     ← format_chart_summary(), format_rag_context()
│   ├── embeddings.py        ← FAISS semantic search + keyword search
│   ├── pdf_generator.py     ← WeasyPrint PDF generation
│   └── supabase_client.py   ← get_supabase(), update_order_status()
├── data/
│   ├── pdf_template.html    ← PDF layout (A4, DejaVu Sans, gold theme)
│   └── pdfs/                ← Generated PDF output
├── notifications/           ← JSON backup of Telegram notifications
├── task_store.json          ← Persisted task states
├── .env                     ← MIMO_API_KEY, BOT_TOKEN
└── .supabase_creds.json     ← Supabase URL + anon key
```

---

## 3. Luồng FULL Reading (Async Pipeline)

### 3.1 Trigger

```
Frontend → POST /reading/full/async?order_id=VEDIC2XXXXXX
  Body: ChartRequest (ascendant, planets, houses, dashas, metadata)
  
  → Response ngay: {"task_id": "a1b2c3d4", "status": "queued", "total_sections": 7}
  → Background thread bắt đầu
```

### 3.2 Pipeline chi tiết

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: RAG Search (trạng thái: "rag")                         │
│                                                                 │
│ format_chart_summary() → search_by_chart(k=15)                  │
│   ├─ FAISS semantic search (634 chunks từ BPHS, Nakshatras,     │
│   │   Karakatvas, Bhrigu Samhita, giáo trình Việt)             │
│   └─ Keyword search fallback nếu semantic fail                 │
│                                                                 │
│ → rag_context: ~7,000 chars                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: 7 Sequential MiMo Calls (trạng thái: "generating")     │
│                                                                 │
│ FOR section 1..7:                                               │
│   build_full_prompt(summary, rag, section=N)                    │
│     ├─ SECTION_SYSTEM_PREFIX (902 chars persona)                │
│     ├─ Section instruction (có dấu, ~400-600 chars)             │
│     └─ Chart data + RAG context                                 │
│                                                                 │
│   → Prompt: ~12,500-12,800 chars mỗi section                   │
│                                                                 │
│   call_llm(prompt, "mimo", max_tokens=N)                        │
│     → POST https://token-plan-sgp.xiaomimimo.com/v1/chat/...    │
│     → model: mimo-v2.5-pro, timeout: 1200s                      │
│                                                                 │
│   Kết quả được wrap: "## {N}. {TITLE}\n\n{content}"            │
│                                                                 │
│   Token map:                                                     │
│     Section 1 (Tổng quan,   1000c): 3500 tokens                 │
│     Section 2 (Hành tinh,   1500c): 5000 tokens                 │
│     Section 3 (12 nhà,      1500c): 5000 tokens                 │
│     Section 4 (Sự nghiệp,    500c): 2000 tokens                 │
│     Section 5 (Quan hệ,      500c): 2000 tokens                 │
│     Section 6 (Sức khỏe,     500c): 2000 tokens                 │
│     Section 7 (Dasha,        500c): 2000 tokens                 │
│     ─────────────────────────────────────────                   │
│     TOTAL: 6,000 chars target, 21,500 tokens max                │
│                                                                 │
│   Progress được update vào _tasks sau mỗi section              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Concatenate                                             │
│                                                                 │
│ full_text = "\n\n".join(all_6_sections)                         │
│ Minimum: 500 chars (nếu < 500 → error)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: PDF Generation (trạng thái: "pdf")                     │
│                                                                 │
│ pdf_generator.py::save_pdf(full_text, chart_data)               │
│   ├─ _build_sections(): Parse headers → HTML                    │
│   │   └─ Regex: "## N. Title" hoặc "N. TITLE" → <h2>           │
│   ├─ Merge with pdf_template.html (DejaVu Sans, A4, gold theme) │
│   └─ WeasyPrint → /data/pdfs/reading_YYYYMMDD_HHMMSS.pdf       │
│                                                                 │
│ → Task status: "done"                                          │
│ → Task persisted to task_store.json                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Post-processing (song song)                             │
│                                                                 │
│ 📦 Supabase:                                                    │
│   update_order_status(order_id, "done",                        │
│     pdf_url="/reading/pdf/{task_id}",                           │
│     notes="PDF: file.pdf, chars: 8500, sections: 6/6")         │
│                                                                 │
│ 📱 Telegram:                                                    │
│   send_notification() → Kim Ssa (chat_id: 1336718742)          │
│   Message: "📄 PDF MOI DA SAN SANG\n👤 Khach: ...\n🔗 ..."     │
│   Backup: /notifications/{order_id}.json                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Endpoints

### 4.1 FREE Reading (Sync)

```
POST /reading/free
  Body: ChartRequest
  → build_free_prompt() → call_llm(mimo) → clean_text()
  → Response: {"free": "nội dung..."}
  
  Time: ~60s
  Prompt: ~6,000 chars
  Output: 350-450 từ + upsell cliffhanger
```

### 4.2 FULL Reading (Async)

```
POST /reading/full/async?order_id=VEDIC2XXXXXX
  Body: ChartRequest
  → Tạo task_id → Start daemon thread → Return ngay
  → Response: {"task_id": "abc123", "status": "queued", "total_sections": 6}

GET /reading/status/{task_id}
  → Polling response:
    - {"status": "rag"}                          ← đang search
    - {"status": "generating", "section": 3, "total": 6, "section_title": "..."}
    - {"status": "pdf"}                          ← đang tạo PDF
    - {"status": "done", "pdf_url": "/reading/pdf/abc123", "chars": 8500}
    - {"status": "error", "error": "..."}

GET /reading/pdf/{task_id}
  → FileResponse (application/pdf)
  → 404 nếu chưa done
```

### 4.3 Legacy (Deprecated)

```
POST /reading  → redirect guide (dùng flow mới)
POST /reading/full  → sync 1-call (không dùng async)
```

---

## 5. Section Configuration

| # | Section | Target Chars | max_tokens | Nội dung |
|---|---------|-------------|------------|----------|
| 1 | Tổng quan lá số | 1,000 | 3,500 | Lagna, Moon sign, Atmakaraka, Asc lord |
| 2 | Phân tích hành tinh | 1,500 | 5,000 | 9 hành tinh: sign, nakshatra, house, aspects |
| 3 | Phân tích 12 nhà | 1,500 | 5,000 | 12 nhà: sign, planets, lord, ý nghĩa |
| 4 | Sự nghiệp & Tài chính | 500 | 2,000 | Nhà 10, 2, 6, 11 |
| 5 | Mối quan hệ & Hôn nhân | 500 | 2,000 | Nhà 7, Venus, Darakaraka |
| 6 | Sức khỏe & Tinh thần | 500 | 2,000 | Nhà 6, 8, 12, Moon, Saturn |
| 7 | Phân tích Dasha & Thời điểm then chốt | 500 | 2,000 | Mahadasha hiện tại, Antardasha, upsell gói tư vấn cá nhân |

**Tổng:** 6,000 chars target / 21,500 tokens / ~5-9 phút

---

## 6. PDF Generation

- **Engine:** WeasyPrint (HTML → PDF)
- **Font:** DejaVu Sans (Unicode, hỗ trợ tiếng Việt)
- **Layout:** A4, 2cm margins, gold (#d4a017) accent
- **Pagination:** Tự động qua CSS `@page` counter
- **Output:** `/data/pdfs/reading_YYYYMMDD_HHMMSS.pdf`

### Section parsing (`_build_sections`):

3 regex patterns để detect headers:
1. `## [number]. Title` — format từ code
2. `Number. TITLE TEXT` — LLM output format (1 ≤ number ≤ 12)
3. `## Generic Title` — fallback

→ Mỗi section → `<h2>{title}</h2>` + paragraphs/ul

---

## 7. Task Persistence

- **File:** `task_store.json`
- **Lock:** `threading.Lock()` → `_tasks_lock`
- **Startup cleanup:** Mark queued/generating/rag/pdf tasks as "error" (lost threads)
- **Task object:**
  ```json
  {
    "abc123": {
      "status": "done",
      "pdf_path": "/root/horoscope-bot/data/pdfs/reading_20260530_161801.pdf",
      "chars": 8613,
      "sections": 6
    }
  }
  ```

---

## 8. Error Handling

| Layer | Mechanism |
|-------|-----------|
| Section call fail | Fallback message: `"(Khong co du lieu...)"` — không block section khác |
| All sections fail | `total_chars < 500` → raise RuntimeError |
| MiMo API error | `sanitize_error_text()` → user-friendly Vietnamese message |
| Telegram fail | Log warning, JSON backup vẫn lưu |
| Supabase fail | Log warning, PDF vẫn tạo |
| Service restart | Auto-clean stale tasks → mark "error" |

---

## 9. RAG Corpus (634 chunks)

| Source | Chunks | Nội dung |
|--------|--------|----------|
| BPHS Vol 1 | Chapters | Brihat Parashara Hora Shastra |
| Nakshatras | 27 × subsections | Book of Nakshatras |
| Karakatvas | Chapters | Planetary significations |
| Bhrigu Samhita | Sections | Bhrigu Samhita |
| Choudhry Lagna | Signs | Impact of ascending signs |
| Giáo trình Việt | Sections | Vietnamese teaching materials |
| Client readings | Samples | Real client chart interpretations |

**Search:** FAISS (all-MiniLM-L6-v2) + keyword fallback

---

## 10. Deployment

```bash
# Sync code từ local → VPS
scp api/main.py root@160.22.106.46:/root/horoscope-bot/api/main.py
scp engine/section_config.py root@160.22.106.46:/root/horoscope-bot/engine/section_config.py
scp engine/prompt_builder.py root@160.22.106.46:/root/horoscope-bot/engine/prompt_builder.py

# Restart
ssh root@160.22.106.46 'systemctl restart votive-astrologybot.service'

# Check logs
ssh root@160.22.106.46 'journalctl -u votive-astrologybot.service -f'
```

---

## 11. Cấu hình Môi trường

```bash
# .env
MIMO_API_KEY=sk-...            # Xiaomi Token Plan API
BOT_TOKEN=854240…oH2s          # Telegram bot token
READING_MODEL=mimo             # default model

# .supabase_creds.json
{
  "url": "https://qzyyiqzekduduoscdwjc.supabase.co",
  "anon_key": "eyJh..."
}
```

---

## 12. Điểm cần lưu ý

- **Section 2 rủi ro nhất:** 1500 chars target cho 9 hành tinh là tight. Nếu MiMo trả về 0 chars (đã xảy ra 1 lần), có thể do max_tokens quá cao. Giảm từ 9000 → 5000.
- **Tiếng Việt có dấu:** Prompt phải dùng tiếng Việt có dấu trong instruction để LLM bắt chước. Cũ "VIẾT TIẾNG VIỆT CÓ DẤU" thay vì "VIET TIENG VIET KHONG DAU".
- **Deploy path:** `scp` với full path, không dùng `rsync` vì dễ miss subdirectory.
- **Timeout MiMo:** 1200s (20 phút) — đủ cho cả 6 sections sequential.
- **Stale tasks:** Startup tự động cleanup — không cần thủ công.
