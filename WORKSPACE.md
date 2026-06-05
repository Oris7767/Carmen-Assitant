# 🗺️ Workspace Map — Cấu Trúc & Brand Rules

> Cập nhật: 2026-06-05
> Mục đích: Cho bất kỳ session nào cũng hiểu được cấu trúc workspace.

---

## 🏗️ Kiến Trúc Tổng Thể

```
WORKSPACE ROOT ─── Core files (AGENTS, SOUL, MEMORY, TOOLS, USER...)
     │
     ├── 📁 patreon-db/           Aether Astro-Quant Engine (GOLD)
     ├── 📁 votive-virtual-assistant/   Votive Academy (chiêm tinh)
     ├── 📁 social-pipelines/           Social posting scripts
     ├── 📁 horoscope-bot/              Horoscope reading bot
     ├── 📁 youtube-pipeline/           La Bàn Số Mệnh (YouTube)
     ├── 📁 website-pipeline/           Quant EA Labs web
     ├── 📁 blog-pipeline/              VedicVN blog
     ├── 📁 docs/                       General references
     └── ... (other auxiliary folders)
```

---

## 1. 📁 `patreon-db/` — Aether / Patreon (GOLD TRADING)

**Brand:** Aether Astro-Quant Engine
**Content:** Gold (XAUUSD) quant analysis, Gann, Fibonacci, Vedic astrology for trading
**Post destinations:** Patreon + X (Aether account)
**🔴 TUYỆT ĐỐI KHÔNG post sang Votive, YouTube, hay Quant EA Labs**

### Key files
| File | Purpose |
|------|---------|
| `carmen_analyst.py` | Core analysis engine (dual backend: Gemini + DeepSeek) |
| `run_bot.py` | Bot orchestrator, data fetching, report generation |
| `historical_correlation.py` | Historical pattern correlation for Patreon posts |
| `backtest_patterns.py` | Pattern backtesting |
| `strict_backtest*.py` | Strict backtest engines (v1, v2, v3) |
| `patreon_post_gen_v2.py` | Patreon post content generation |
| `patreon_poster.js` | Patreon browser posting |
| `patreon_publish.js` | Patreon publish via browser |
| `social_poster.js` | X + Instagram API posting |
| `x_poster.js` | X browser automation |
| `x_post.js` / `x_post.py` | X posting scripts |
| `collect.py` / `collect_v2.py` | Data collection (Gold OHLC, astro, macro) |
| `analyze_v2.py` / `analyze_yearly.py` | Data analysis & reporting |
| `build_scorer_v2.py` | Scoring engine builder |
| `backfill*.py` | Historical data backfill |
| `ASTRO_QUANT_FRAMEWORK*.md` | Framework documentation |
| `SUPER_CYCLE_FRAMEWORK.md` | Super cycle theory docs |
| `SCHEMA.md` | Database schema |
| `reports/` | Analysis reports (ANALYSIS_REPORT_*.md) |
| `data/` | 18 years of CSV price data (529MB) |
| `research/` | Research scripts |
| `BOT_TRADING_SPEC.md` | Bot trading specification |
| `.env` | X API credentials for Aether |

---

## 2. 📁 `votive-virtual-assistant/` — Votive Academy (CHIÊM TINH)

**Brand:** Votive Academy
**Content:** Chiêm tinh Vệ Đà, khóa học, dịch vụ tư vấn
**Post destinations:** Facebook, Instagram, X (Votive accounts)
**🚫 Không dùng từ:** "bot", "AI" — dùng "trợ lý số Votive"

### Key files
| File | Purpose |
|------|---------|
| `api/server.py` | FastAPI server (endpoints: /chat, /health, /booking) |
| `bot/engine.py` | Chat engine logic |
| `bot/intent_router.py` | Intent classification & routing |
| `bot/session.py` | Session management |
| `bot/system_prompt.py` | System prompt (persona: Carmen) |
| `rag/search.py` | RAG search engine |
| `rag/knowledge_base.py` | Knowledge base management |
| `data/services.md` | Service descriptions (courses, pricing) |
| `data/ethics.md` | Ethics rules for responses |
| `data/faiss_index/` | FAISS vector index for RAG |
| `docs/` | QA reports, SEO audits, UX reports |
| `.env` | API keys (Supabase, DeepSeek, Telegram) |

---

## 3. 📁 `social-pipelines/` — Social Media Posting

Central folder for ALL social posting scripts, organized by brand.

```
social-pipelines/
├── README.md          ← Brand map + architecture + rules
├── votive/            ← 🪐 Votive Academy (FB, IG, X)
│   ├── scripts/
│   │   ├── meta_post.py   ← FB + IG via Graph API
│   │   ├── x_poster.js    ← X browser automation
│   │   └── .token         ← Meta Graph API token
│   ├── posts/             ← Post content templates
│   └── images/            ← Generated images
└── patreon/           ← 🔴 Aether (Patreon, X)
    └── scripts/            ← Posting scripts + .env
```

**⛔ Rule:** Mỗi brand post riêng. KHÔNG lẫn content.

---

## 4. 📁 `horoscope-bot/` — Horoscope Reading Bot

**Brand:** Votive Academy (backend)
**Stack:** FastAPI + MiMo 2.5 Pro + WeasyPrint + FAISS + Supabase
**Domain:** https://horoscope.vedicvn.sbs
**VPS:** Port 8000, systemd: `votive-astrologybot.service`

### Key files
| File | Purpose |
|------|---------|
| `api/main.py` | FastAPI server (async reading pipeline) |
| `api/pdf_generator.py` | PDF report generation |
| `engine/section_config.py` | 7-section reading config |
| `engine/prompt_builder.py` | Dynamic prompt builder |
| `engine/pipeline.py` | Reading pipeline orchestrator |
| `engine/chart_adapter.py` | Chart data adapter (diacritic fix) |
| `engine/diacritic_repair.py` | Vietnamese diacritic handling |
| `corpus/` | RAG corpus (FAISS index + chunks) |

---

## 5. 📁 `youtube-pipeline/` — La Bàn Số Mệnh

**Brand:** La Bàn Số Mệnh
**Content:** Video chiêm tinh, shorts, storytelling
**Pipeline:** `daily_short.py`, `elevenlabs_tts.py`, `create_video.py`

---

## 6. 📁 `website-pipeline/` — Quant EA Labs

**Content:** Blog articles, website content

---

## 7. 📁 `blog-pipeline/` — VedicVN Blog

**Pipeline:** `publish.py` — blog publishing

---

## 8. 📁 `docs/` — General References

| File | Purpose |
|------|---------|
| `VPS_REFERENCE.md` | VPS 160.22.106.46 (IP, services, ports) |
| `TASK_MODEL_MAP.md` | Task-to-model assignment for all crons |

---

## 🔥 Brand Independence Rules

```
Votive Content  → FB, IG, X     (social-pipelines/votive/)
Aether Content  → Patreon, X    (social-pipelines/patreon/) — ĐỘC LẬP
La Bàn Số Mệnh  → YouTube       (youtube-pipeline/) — RIÊNG
Quant EA Labs   → Web            (website-pipeline/) — RIÊNG
```

**Thư viện DÙNG CHUNG** (code, data có thể dùng nhiều brand):
| Library | Used by |
|---------|---------|
| RAG Gold (`patreon-db/data/`) | Bot trade, Aether post, Quant EA Labs |
| RAG Chiêm tinh (`horoscope-bot/corpus/`) | Horoscope bot, Votive VA, Cron, YouTube |
| Swiss Ephemeris (`pyswisseph`) | ALL Votive projects (horoscope, VA, bot trade, YouTube) |

---

## 🔐 VPS Access

| VPS | IP | OS | Purpose |
|-----|----|----|---------|
| **Linux** | `160.22.106.46` | Ubuntu 24.04 | OpenClaw Gateway, Horoscope bot, Votive VA |
| **Windows** | `138.252.133.45` | Win Server 2012 R2 | MT5 trading bot |

---

## 🆘 Quick Reference

```bash
# Deploy Votive VA
cd /Users/kimssa/.openclaw/workspace/social-pipelines/votive/scripts
python3 meta_post.py fb "message" "/path/to/image.jpg"

# Deploy horoscope bot
scp engine/section_config.py root@160.22.106.46:/root/horoscope-bot/engine/
ssh root@160.22.106.46 'systemctl restart votive-astrologybot.service'

# Deploy Aether X post
cd social-pipelines/patreon/scripts
node x_poster.js --content ./post.md --image ./image.jpg

# Check logs
ssh root@160.22.106.46 'journalctl -u votive-va -n 30'
ssh root@160.22.106.46 'journalctl -u votive-astrologybot -n 30'
```
