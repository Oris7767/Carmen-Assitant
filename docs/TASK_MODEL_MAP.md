# 🪐 Task — Model Assignment Map

> Cập nhật: 2026-05-28 23:35 GMT+7 — Full fallback chain cho tất cả cron jobs

---

## 1. Cron Jobs — Active (11 jobs)

| # | Task | Schedule | Primary | Fallback Chain | Status |
|---|------|----------|---------|----------------|--------|
| 1 | **Patreon Content Generator** | 12:00 CN→Thứ 5 | deepseek-v4-flash | claude → qwen → mimo | ✅ |
| 2 | **Carmen Patreon Post** | 12:05 CN→Thứ 5 | deepseek-v4-flash | claude → qwen → mimo | ✅ |
| 3 | **QuantEA Blog Auto-Publish** | 07:00 Thứ 3+6 | deepseek-v4-flash (thinking=high) | claude → qwen → mimo | ✅ |
| 4 | **Auto Broadcast - Asia** | 07:00 Thứ 2-6 | mimo-v2.5-pro | deepseek → qwen → claude | ✅ |
| 5 | **Auto Broadcast - US** | 19:00 Thứ 2-6 | mimo-v2.5-pro | deepseek → qwen → claude | ✅ |
| 6 | **YouTube Shorts Pipeline** | 09:00 Thứ 2-6 | mimo-v2.5-pro | deepseek → qwen → claude | ✅ |
| 7 | **YouTube KPI Weekly Review** | 09:00 Thứ 2 | deepseek-v4-flash | claude → qwen → mimo | ✅ |
| 8 | **Vedic Weekly #1** | 15:00 Thứ 3 | qwen3.5-plus | deepseek → claude → mimo | ✅ |
| 9 | **Vedic Weekly #2** | 14:00 Thứ 5 | qwen3.5-plus | deepseek → claude → mimo | ⚠️ Timeout |
| 10 | **Vedic Weekly #3** | 16:00 Thứ 7 | qwen3.5-plus | deepseek → claude → mimo | ✅ |
| 11 | **Workspace Cleanup** | 03:00 CN | default (mimo) | deepseek → qwen → claude | ✅ |
| 12 | **Model Performance Report** | 06:00 CN | mimo-v2.5-pro | deepseek → qwen | ✅ |

---

## 2. Cron Jobs — Disabled (3 jobs)

| # | Task | Schedule | Reason Disabled |
|---|------|----------|-----------------|
| D1 | **Nightly Gold Forecast** | 00:30 hàng ngày | Redundant với Patreon Content Generator |
| D2 | **Gold Analysis Asia Session** | 07:00 Thứ 2-6 | Superseded by Auto Broadcast Asia |
| D3 | **Gold Analysis US Session** | 19:00 Thứ 2-6 | Superseded by Auto Broadcast US |

---

## 3. Model Performance Monitoring

### Auto-Logger
- **Script:** `.openclaw/log_model_performance.py` — queries cron run history, generates performance report
- **Cron:** Every Sunday 06:00 GMT+7 (`8fb999a9`) — runs logger + sends summary to Telegram
- **Log file:** `memory/model_performance_log.md` — tracks per-job and cross-job model stats

### Metrics Tracked
| Metric | Purpose |
|--------|---------|
| Success rate | Which models complete tasks reliably |
| Duration | Which models are fastest |
| Token usage | Cost efficiency |
| Fallback usage | How often primary fails |
| Error type | Auth vs timeout vs other |

### Decision Framework
- **3+ failures in 7 days** → investigate/remove model from chain
- **Avg duration > 5min** → consider lighter model or reduce context
- **Auth errors** → fix API key, not model issue
- **Timeouts** → increase timeout or simplify task

---

## 4. Non-Cron Tasks — Manual / Service

| # | Task | Trigger | Model | Ghi chú |
|---|------|---------|-------|---------|
| 13 | **Hand-Post Pipeline** | Kim Ssa gửi bài | `deepseek/deepseek-v4-flash` | Patreon → X → Meta |
| 14 | **Telegram Bot** (Render) | User /command | 🚫 không AI | web.py Flask serve static report |
| 15 | **Historical Correlation Engine** | patreon-db query | 🚫 không AI | SQL matching pattern |
| 16 | **Social Posters** (x_poster.js, meta_post.py) | Script call | 🚫 không AI | Browser automation / API calls |

---

## 4. Fallback Strategy

### Nguyên tắc
- **3 models trong chain** — nếu model chính fail (rate limit / timeout / error) → tự động thử model tiếp theo
- **Loop qua đến khi success** — không bỏ qua task
- **Không rate limit hoặc timeout thì bỏ** — luôn thử đến khi thành công

### Chain theo nhóm task

| Nhóm | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|------|---------|-----------|-----------|-----------|
| **Reasoning-heavy** (Patreon, Blog, KPI) | deepseek-v4-flash | gwai/claude-sonnet-4-6 | qwen/qwen3.5-plus | xiaomi/mimo-v2.5-pro |
| **Light task** (Broadcast, Cleanup, YouTube) | mimo-v2.5-pro | deepseek/deepseek-v4-flash | qwen/qwen3.5-plus | gwai/claude-sonnet-4-6 |
| **VN Content** (Vedic Weekly) | qwen/qwen3.5-plus | deepseek/deepseek-v4-flash | gwai/claude-sonnet-4-6 | xiaomi/mimo-v2.5-pro |

### Model Pool

| Model | Provider | Vai trò |
|-------|----------|---------|
| **deepseek-v4-flash** 🟢 | DeepSeek | Strong reasoning, orchestrate pipeline, viết article dài |
| **claude-sonnet-4-6** 🟠 | Anthropic (gwai) | Premium fallback — best reasoning khi deepseek/qwen fail |
| **qwen3.5-plus** 🟣 | Alibaba | VN content, X + Meta posting |
| **mimo-v2.5-pro** 🔵 | Xiaomi | Light tasks (curl, cleanup), final fallback |
| **Gemini Imagen** 🎨 | Google | Image generation (luôn res 1K, aspect 16:9 hoặc 9:16) |
| **gTTS** 🎙️ | Google | Text-to-Speech cho YouTube Shorts |
| **Swiss Ephemeris** 📐 | Local | Tính toán chiêm tinh, không AI |

---

## 5. Architecture Flow

```
                              ┌─────────────────┐
                              │  Telegram Bot    │
                              │  (Render/web.py) │
                              │  🚫 no AI        │
                              └────────┬────────┘
                                       │
     ┌──────────────────────────────────┼──────────────────────────────────┐
     │                                  │                                  │
     ▼                                  ▼                                  ▼
┌────────────┐                   ┌──────────────┐                 ┌──────────────┐
│  Patreon   │                   │   YouTube    │                 │  Social (X   │
│  Pipeline  │                   │   Pipeline   │                 │  + Meta)     │
│  deepseek  │                   │   mimo       │                 │  qwen        │
│  ↘ claude  │                   │  ↘ deepseek  │                 │  ↘ claude    │
│  ↘ qwen    │                   │  ↘ qwen      │                 │  ↘ deepseek  │
│  ↘ mimo    │                   │  ↘ claude    │                 │  ↘ mimo      │
│  🎨 Gemini │                   │  🎨 Gemini   │                 │  🎨 Gemini   │
│  1K        │                   │  🎙️ gTTS     │                 │  1K          │
└────────────┘                   └──────────────┘                 └──────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  QuantEA Labs │
                              │  deepseek     │
                              │  thinking=high│
                              │  ↘ claude     │
                              │  ↘ qwen       │
                              │  ↘ mimo       │
                              └──────────────┘
```

---

## 6. Cron Job IDs (reference)

| Job | ID (prefix) |
|-----|------------|
| Patreon Content Generator | `9176ff92` |
| Carmen Patreon Post | `5865f446` |
| QuantEA Blog Auto-Publish | `d3660f02` |
| Auto Broadcast Asia | `f1058514` |
| Auto Broadcast US | `13e60c97` |
| YouTube Shorts | `7986dafd` |
| YouTube KPI Review | `4dd6b3cc` |
| Vedic Weekly #1 | `16db7a7b` |
| Vedic Weekly #2 | `8f3400ac` |
| Vedic Weekly #3 | `ae987ff8` |
| Workspace Cleanup | `d8f3c033` |
| Model Performance Report | `8fb999a9` |

---

## 7. ⚠️ Known Issues

| Job | Issue | Action |
|-----|-------|--------|
| Vedic Weekly #2 (#9) | Timeout 300s (2026-05-28) | Fallback chain đã add — lần tới sẽ thử deepseek nếu qwen timeout. Cân nhắc tăng timeout lên 450s nếu vẫn fail. |
| Anthropic auth errors | Multiple jobs failing | Old fallback chains included `anthropic/claude-haiku` with invalid key. Updated chains now use correct models. |
