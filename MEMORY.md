# MEMORY.md - Curated Trading & Astrological Knowledge

## Aether — Quant Data Brand
**Aether** là tên thương hiệu cho toàn bộ hệ thống Quant Data của Kim Ssa, bao gồm:
- **Database:** 18 năm dữ liệu giá vàng (2008-2026), 2,511+ trading days
- **Frameworks:** Astro-Quant Engine v2.0, Super Cycle Framework, Gann/Fibonacci engines
- **Modules:** collect, analyze, scorer, report generator, patreon post gen
- **Khi nào dùng "Aether":** Bất kỳ khi nào nói về quant data, framework, database, hoặc build/modify bot trading liên quan đến hệ thống này.
- **Ví dụ:** "Dùng Aether để build bot", "Chỉnh sửa Aether framework", "Aether database có data từ 2008"
- **Published as:** Aether Astro-Quant Engine từ Hệ thống Cosmic Data Labs

---

## Technical Analysis (Kim Ssa's Rules)
- **Fibonacci Levels:** 0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874.
- **Gann Fan:** Primary angle is 45 degrees (1x1 angle) connecting major High/Low.

## Core Astrological Rulerships (Financial)
- **Sun (Mặt Trời):** Rules Gold (XAUUSD). Confident, decisive.
- **Jupiter (Sao Mộc):** Broad market, liquidity, expansion, FOMO.
- **Mercury (Sao Thủy):** Short-term volatility, news, trading efficiency.
- **Venus (Sao Kim):** Market valuation, extreme greed/fear (Morning/Evening star phases).
- **Saturn (Sao Thổ):** Resistance, karma, low liquidity, pressure.
- **Mars (Sao Hỏa):** Sudden volatility, trend reversals, sharp dumps/pumps.

## Astrological Orbs & Aspects (Combust, Conjunction, Aspects)
- **Combust (Bốc cháy - Khoảng cách tới Mặt Trời):**
  - **Sao Hỏa, Sao Thổ, Sao Mộc:** Bốc cháy khi cách Mặt Trời trong vòng **8°**.
  - **Sao Kim:** Bốc cháy khi cách Mặt Trời trong vòng **4°**.
  - **Sao Thủy:** Bốc cháy khi cách Mặt Trời trong vòng **2°**.
- **Aspects (Góc chiếu - Trine 120°, Square 90°, Opposition 180°, Conjunction 0°):**
  -Phạm vi dung sai (Orb) là **±5°**.
  - *Ví dụ:* Mặt trời ở 0°, Sao Hỏa sẽ tạo góc Opposition (180°) nếu nằm trong phạm vi 175° - 185°. Góc Square (90°) hợp lệ trong phạm vi 85° - 95°.

## Key Market Cycles
- **Mercury Cycle (116 days):** Switches between Morning Star (Max West) and Evening Star (Max East). Strategy: Buy at Morning Star, Hold at Superior Conjunction, Sell at Evening Star.
- **Venus Cycle (584 days):** Major turning points at Maximum Elongation (47-48 degrees).
- **Mars Cycle (780 days):** Sharp market reversals often align with Mars 90° (Square) or 180° (Opposition) to the Sun.
- **Jupiter-Saturn Master Cycle (20/240 years):** Shifts in macro economic eras.
- **Nodal Cycle (Rahu/Ketu - 18.6 years):** Macro market peaks and troughs.

## Planetary Hours (Hora) Rules
- A planetary day begins at **Sunrise** (not midnight).
- The first Hora (hour) of the day belongs to the Lord of the Day.
- Subsequent Horas follow Chaldean order: Saturn -> Jupiter -> Mars -> Sun -> Venus -> Mercury -> Moon.
- **Trading Application:** Align Gann levels with favorable Horas (e.g., Jupiter Hora at a Gann Support = High probability long).

## Eclipses (Nhật Thực / Nguyệt Thực)
- Eclipses act as massive price magnets. The price level established on the day of a Solar Eclipse often dictates the trend for the next 6 months.

## Monthly & Yearly Trends
- The planetary ruler of the 1st day of the month/year dictates the general vibe.
- **King of the Year (Samvatsar):** Determined by the lord of the day of Chaitra Shukla Pratipada.

---
## Patreon Analysis Database (patreon-db)
**Location:** `/patreon-db/`
**Purpose:** Historical dataset for RAG-based Patreon post generation. LLM learns from past astrological + technical setups to produce data-backed daily analysis.
**Architecture:** One CSV per month (`data/YYYY-MM.csv`), ~57 columns per trading day.
**Status:** 2016-06 → 2026-05 ✅ COMPLETE (120 months, ~2,628 trading days, 10 years). Full backfill done 2026-05-29.

### Auto-Populated Columns (FULLY AUTO — no manual input)
- **Price:** Open/High/Low/Close, change%, range (yfinance GC=F)
- **Gann/Fib:** Swing high/low, 10 Fib levels (JSON), key level held/breached
- **Planetary:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn — sidereal/Vedic (Lahiri ayanamsa)
- **Moon:** Sign, degree, nakshatra (27 nakshatras)
- **Elongation:** Mercury, Venus, Mars, Jupiter, Saturn from Sun
- **Combust:** Auto-detected (Mercury ≤2°, Venus ≤4°, Mars/Saturn/Jupiter ≤8°)
- **Aspects:** Conjunction (±5°), Sextile/Square/Trine (±4°), Opposition (±5°)
- **Eclipse:** Solar/Lunar window (±15° of New/Full Moon)
- **Economic events:** Hardcoded schedule (NFP, CPI, PCE, FOMC, ISM, GDP, Retail Sales, Jobless Claims, etc.)
- **Market reaction:** Computed from OHLC ratios (strong_trend, moderate_trend, reversal_signal, consolidation, choppy)
- **Trend direction:** Bullish/bearish/neutral
- **Volatility:** Low/medium/high from daily range %
- **Dominant Hora:** Sunrise + Chaldean order (Swiss Ephemeris rise_trans, Saigon GMT+7)

### Key Files
- `SCHEMA.md` — full column documentation
- `collect.py` — auto-collect script (run: `python3 collect.py YYYY-MM`)
- `backfill/PROGRESS.md` — tracking progress
- `data/YYYY-MM.csv` — monthly data files

### Dependencies
- `pyswisseph` (Swiss Ephemeris for sidereal positions + sunrise)
- `yfinance` (gold price data)
- `pandas` (CSV handling)

### Analysis Reports
- `ANALYSIS_REPORT_2024-05_2025-04.md` — 251 trading days, 12 months
- `ANALYSIS_REPORT_2025-05_2026-05.md` — 268 trading days, 13 months
- **2023-05 → 2024-04 backfill complete** — 252 trading days, 12 months (2026-05-22)

### Coverage
- **Total:** 2016-06 → 2026-05 = 120 months, ~2,509 trading days, 10 years ✅
- **FOMC dates:** 2016-2025 all hardcoded in collect.py

### v2 Framework (2026-05-29)
- **collect_v2.py** — Enhanced collector with:
  - 🐛 US10Y timezone normalization bug FIXED (was 100% empty)
  - 🆕 `moon_nakshatra_lord` (auto-computed, no API needed)
  - 🆕 `sp500_change_pct` (^GSPC), `vix_close` (^VIX)
  - 🆕 `gold_volume`, `gold_atr_14`, `gold_rsi_14`
  - Modes: full month, incremental (--inc), dry run (--dry), backfill-all
- **analyze_v2.py** — Enhanced analysis (22 sections vs 16):
  - 🆕 Section 17: Nakshatra Lord Analysis
  - 🆕 Section 18: Rahu/Ketu Aspects
  - 🆕 Section 19: S&P 500 Correlation
  - 🆕 Section 20: VIX (Fear Index) Correlation
  - 🆕 Section 21: Multi-Factor Confluence (top 20 3-factor combos)
  - 🆕 Section 22: Technical Indicators (RSI, ATR bands)
- **fix_data.py** — Quick patch tool:
  - `--status` audit, `--us10y` fix, `--nakshatra` add lord, `--all` both

### Patches Applied 2026-05-29
- ✅ `moon_nakshatra_lord` added to all 120 CSVs (2,509 rows)
- ✅ US10Y patched: 2,507/2,509 rows (99.9%, up from 0%)
- ✅ S&P 500, VIX, Volume, ATR, RSI — full v2 backfill complete (120/120 months, 0 failures)
- ✅ Full v2 report + all 11 yearly reports regenerated (2,511 trading days)

### Astro-Quant Framework v2 (2026-05-29)
- **Dataset upgraded:** 1,103 → 2,511 trading days (2016-2026)
- **Old baseline:** 78% LONG, 85% SHORT (2022-2026 only)
- **New baseline:** Computing on full dataset with pre-COVID, COVID crash, recovery, surge
- Morning Star/Evening Star section added to analyze_v2.py
- Venus×DXY confluence: Morning Star+bearish DXY = 62.9% bullish vs Evening Star+bullish DXY = 35.7%
- New framework v2 being generated: ASTRO_QUANT_FRAMEWORK_V2.md

### Key Findings (2024-05 → 2025-04)
- **Nakshatra strongest predictor:** Purva Ashadha 100% bullish vs Jyeshtha 12.5% (88% spread)
- **Moon Sign:** Sagittarius 70.6%, Leo 69.6% bullish; Scorpio 22.7% weakest
- **Mars Retro:** +11.3% delta bullish vs direct (counter-intuitive)
- **Venus Retro:** HIGH VOLATILITY (range 1.62x)
- **Sun Conj Saturn:** 87.5% bullish, low vol
- **Moon Opposition Saturn:** +0.84% avg change (strongest bullish signal)
- **Gann Key Held:** range 25.8 vs 61.6 when breached (2.4x)
- **Jupiter Hora:** 66% bullish; Moon Hora: 41.7% bearish
- **Market reaction:** 21.1% reversal, only 8% strong trend → range-bound with sudden reversals

### Key Findings (2023-05 → 2024-04)
- **Baseline:** 48% bullish, avg change +0.001%, range 16.35 (lower vol than 2024-05 period)
- **Nakshatra:** Mula 90% bullish, Shatabhisha 83.3%, Ashwini 75% vs Mrigashira 12.5%, Rohini 14.3% (78% spread)
- **Moon Sign:** Sagittarius 72.7%, Libra 62.5% bullish; Taurus 11.1% weakest
- **Mercury Retro:** +10.5% delta bullish; Mercury Combust = 72.2% bullish, range 23.1
- **Venus Retro:** -12.9% delta bearish (opposite of 2024-05 period)
- **Saturn Retro:** bearish 42.3% vs direct 51.6% (opposite of 2024-05)
- **Sun Conj Saturn:** 71.4% bullish +0.72%; Sun Conj Moon: 83.3%
- **Moon Sextile Saturn:** 80% bullish (strongest Moon aspect)
- **Gann Key Held:** range 15.3 vs 58.1 breached (3.8x)
- **Moon Hora:** 58.7% bullish (opposite of 2024-05); Mars Hora: 44.2% bearish
- **Market reaction:** 31.3% reversal signal, only 2.8% strong trend → even more range-bound
- **Cross-period:** Nakshatra consistently strongest predictor; Moon Sign Sagittarius bullish in both periods

### Patreon Post Generator
- **Main:** `patreon_post_gen_v2.py` → `get_full_report_data()` → `ReportGenerator.generate_patreon_report()`
- **Format:** 10-section Format B (was 9, added Super Cycle Countdown)
- **Section 10:** Super Cycle Countdown — JS phase, Rahu/Saturn position, 7-factor scorecard, time to dead zone
- **V2 Scorer:** `astro_quant_scorer_v2.py` (233 scores, 2,511d backtest) — use for daily signals
- **V1 Scorer:** `research/astro_quant_scorer.py` — DEPRECATED, kept for reference only

### Super Cycle Framework (2026-05-29)
- **2-Layer System:** Super Cycle (strategic, 1-5yr, ghi đè tất cả) + Daily Scores (tactical, entry/exit timing)
- **Core Finding #1:** Jupiter-Saturn phase 0-120° = 100% structural shifts. 120-180° = ZERO shifts (dead zone)
- **Core Finding #2:** DXY correlation broken (+0.23) — gold & dollar rising together = de-dollarization super cycle
- **Core Finding #3:** Rahu in Aquarius = +26.0% avg 6m (most bullish). Rahu in Aries = -15.7% (most bearish)
- **Core Finding #4:** Saturn in Pisces (current) = highest volatility (1.48% std, 53% bullish)
- **Core Finding #5:** Venus Evening Star max elongation → avg +10.3% 6m return (6/6 positive)
- **Current Score (May 2026):** +2.05/3.0 Strongly Bullish, ~15 months to JS dead zone 120°
- **Red Flags (Exit triggers):** JS >120° (late 2027), Rahu → Capricorn (~Nov 2026), Saturn → Aries (~2027 Q2), DXY correlation normalize
- **Files:** `super_cycle_analyzer.py`, `SUPER_CYCLE_FRAMEWORK.md`, `ASTRO_QUANT_FRAMEWORK_V2.md`

## Historical Correlation Engine (2026-05-23)
**File:** `historical_correlation.py`
**Data:** 1,103 trading days (2022-01 → 2026-05)

Queries patreon-db for historically similar days based on:
- Nakshatra + Moon Sign + Moon Phase
- Dominant Hora
- Retrograde effects (delta bullish/bearish)
- Gann Key Level held vs breached
- Top 5 most similar days with similarity scoring

Returns 9 stat categories for narrative generation in Patreon posts.

## Enhanced Patreon Report (2026-05-23)
**Method:** `ReportGenerator.generate_patreon_report(data)` — 9 sections, ~12,000 chars

| Section | Content |
|---------|---------|
| 1 | Executive Summary + Aether AI Signal |
| 2 | Macro Context (DXY, Fed, news) |
| 3 | Multi-TF Technical (M30 + Gann 9 + Time Cycles) |
| 4 | Vedic Astrology (planets, aspects, Hora) |
| 5 | **CORRELATION LỊCH SỬ 4 NĂM (unique edge)** |
| 6 | Aether AI Deep Analysis |
| 7 | Strategy & Execution |
| 8 | Risk Matrix (6 risk types) |
| 9 | Forward Outlook 3-7 days |

**Key rule:** Patreon = deep research with historical data. Telegram = fast signal.
Always use `generate_patreon_report()` for Patreon posts, not `generate_report()`.

## Render Bot Architecture (2026-05-23)
- **Start Command:** `python web.py` (NOT `telegram_bot.py`)
- **Mode:** Webhook (not polling) — permanently eliminates 409 Conflicts
- **Key endpoints:** `/health` (UptimeRobot), `/webhook` (Telegram updates), `/broadcast` (auto report to subscribers)
- **Keep-alive:** UptimeRobot pings `/health` every 5 min

---
## Script: read_docx.py

```python
from docx import Document
import sys

def read_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        print('\n'.join(full_text))
    except Exception as e:
        print(f"Error reading docx: {e}")

if __name__ == "__main__":
    file_path = "/Users/kimssa/.openclaw/media/inbound/Ta_i_lie_u_chie_m_tinh_trading---b422153b-ad5a-4e18-a91e-4994407403f7.docx"
    read_docx(file_path)
```

---
## Script: ta_engine.py

```python
class TAEngine:
    FIB_LEVELS = [0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874]
    
    @staticmethod
    def calculate_fib_retracement(swing_high: float, swing_low: float, trend: str = 'UP'):
        diff = swing_high - swing_low
        levels = {}
        for ratio in TAEngine.FIB_LEVELS:
            if trend == 'UP':
                price = swing_low + (diff * ratio)
            else:
                price = swing_high - (diff * ratio)
            levels[str(ratio)] = round(price, 2)
        return levels

    @staticmethod
    def analyze_price_fibo(current_price, fib_levels):
        sorted_fibs = sorted([(float(k), v) for k, v in fib_levels.items()], key=lambda x: x[1])
        below = None
        above = None
        for i in range(len(sorted_fibs)-1):
            if sorted_fibs[i][1] <= current_price <= sorted_fibs[i+1][1]:
                below = sorted_fibs[i]
                above = sorted_fibs[i+1]
                break
        
        if not below and len(sorted_fibs) > 0 and current_price < sorted_fibs[0][1]:
            above = sorted_fibs[0]
        if not above and len(sorted_fibs) > 0 and current_price > sorted_fibs[-1][1]:
            below = sorted_fibs[-1]
            
        return {"below": below, "above": above}
```

---
## Script: test_report.py

```python
from run_bot import run_pipeline
import json
import sys
from io import StringIO

# We will intercept the output of run_pipeline
old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()

run_pipeline()

sys.stdout = old_stdout
data = json.loads(mystdout.getvalue())

from report_generator import ReportGenerator
print(ReportGenerator.generate_report(data))
```

---

## 2026-05-22: Astro-Quant Framework & Patreon Pipeline Built

### System Built
- **ASTRO_QUANT_FRAMEWORK.md** — 6-layer trading framework (Philosophy → Variables → States → Scoring → Output → Backtest)
- **astro_quant_scorer.py** — Regime-aware scoring engine. Backtest: LONG 78% win rate (177 signals), SHORT 85% (20 signals)
- **nightly_report.py** — Auto-generates fixed-format prediction every night
- **generate_patreon_post.py** — Historical analysis post generator
- **run_pipeline.py** — Full data pipeline: engines → scoring → pattern match
- **engines/** — Kim Ssa's 5 engines saved: hora_engine, astro_engine, gann_engine, ta_engine, data_fetcher

### Cron Job
- **Nightly Gold Forecast** — Runs 00:30 GMT+7 daily → generates `reports/FORECAST_YYYY-MM-DD.md`

### 4 Market States (Layer 3)
| State | % Days | Rule |
|-------|--------|------|
| Compression 🟡 | 45.9% | Range trade, wait for breakout |
| Expansion 🟢 | 22.1% | Trend follow, buy pullbacks |
| Exhaustion 🔴 | 22.1% | Fade breakout, liquidity sweeps |
| Fear 💀 | 9.9% | Reduce size 0.25x, wait for vol downgrade |

### Top Patterns (from 1103-day backtest)
- Jupiter Hora + Mula Nakshatra: 90% bullish (10 days)
- Thursday + Mula: 90% bullish
- Mercury Hora + Uttara Bhadrapada: 100% bearish (7 days)
- Gann Breached: range 4.0x normal ($92.5 vs $23.1)

### Template Format (Fixed 9 sections)
1. Tổng quan thị trường hôm nay
2. Khung thiên văn ngày mai (Moon, planets, aspects, Hora schedule)
3. Tín hiệu chính
4. Mức giá quan trọng (Gann S/R, Fib)
5. 💡 Đề xuất chiến lược (BUY/SELL LIMIT + Entry/SL/TP1/TP2/R:R)
6. 📝 Aether's Reasoning
7. 📰 Macro Context
8. 🔴 Key Risks
9. 📍 Vùng quan sát + 🛑 Cảnh báo Hora

### Forecast 2026-05-23
- Moon: Leo / Magha Nakshatra (high vol nhất — 20.9%)
- Sun Conjunct Uranus 0.4° — FLASH MOVE risk
- Mars Square Pluto 2.36° — extreme volatility
- Signal: BULLISH, Confidence 50% LOW
- Entry $4,446 near Gann Support $4,414 | SL $4,404 | TP2 $4,708 | R:R 1:6.2
- ⚠️ Results pending — Kim Ssa will verify tomorrow

### Key Files
- /patreon-db/ASTRO_QUANT_FRAMEWORK.md
- /patreon-db/astro_quant_scorer.py
- /patreon-db/nightly_report.py
- /patreon-db/reports/FORECAST_2026-05-23.md
- /patreon-db/engines/* (5 engine files)

---

## 2026-05-23: Patreon Auto-Post Pipeline Built & Deployed

### What Was Built
- **patreon_post_gen.py** — Full Patreon post generator using local swisseph (no API dependency). Calculates planetary positions (Vedic/Lahiri), aspects, Hora schedule, Gann levels, market state (4-state classification), entry/SL/TP, and formats clean V3 content.
- **patreon_poster.js** — Playwright browser automation script that logs into Patreon via Google OAuth, creates a new post, pastes content, uploads featured image, and saves as draft. Session cookies persist so subsequent runs auto-login.
- **PATREON_TEMPLATE_V3.md** — Final approved template format.

### Format V3 Rules (Approved by Kim Ssa)
- **Title:** `Dự Đoán Thị Trường Vàng DD/MM — AETHER Astro-Quant` (LUÔN THỐNG NHẤT, không dùng "Phân Tích" hay biến thể)
- **NO asterisks** (*) — Patreon editor shows them as literal text, looks ugly
- **NO markdown** (**, ##, ---) — use emoji separators instead
- **NO excessive blank lines** — max 1 between sections
- Use • for bullets, | for inline data separation
- 10 sections: Title, Technical, Gann/Fib, Astrology, 6-Layer Framework, Hora 24h, Strategy, Reasoning, Risks, Observation Zones
- News/macro events auto-detected from CSV economic_events column
- **Footer:** `Backtest: 4,629 trading days (2008-2026) | Super Cycle Framework v2.0`
- **Branding:** Always "AETHER" (never "Carmen" in user-facing text)
- **RAG:** Section 5g with 18-year historical patterns from TF-IDF index

### Content Pipeline (10 Sections)
1. 🔮 Title + key aspects subtitle
2. 📊 Technical Analysis (close data: price, EMA, DXY, vol, trend, reaction)
3. 📐 Gann & Fibonacci Levels
4. 🌌 Astrological Framework (planets, aspects, Moon analysis)
5. 🧬 6-Layer Astro-Quant Framework (scoring, market state, pattern matching)
6. ⏰ Hora Schedule 24h (14 periods, best/worst flagged)
7. 💡 Trading Strategy (direction, entry, SL, TP1, TP2, R:R)
8. 📝 Aether's Reasoning (narrative synthesis)
9. 🔴 Key Risks
10. 📍 Observation Zones

### YouTube Sync với Patreon (2026-05-27)
- **Cron dời:** 06:30 → 07:00 GMT+7 (chạy SAU Patreon content gen 06:55)
- **Sync direction:** `daily_pipeline.py` đọc signal từ `patreon-post-content-v3.md` sau khi filter chạy. Nếu filter nói NO_TRADE nhưng Patreon nói BUY → override thành BUY. Entry/TF có thể khác, direction không được trái ngược.
- **generate_script.py:** thêm signal SELL, patreon_override note
- **Lý do:** Filter engine quá cứng nhắc (binary count) → 0/4 filter trigger trong khi full AI analysis vẫn bullish. Sync direction từ Patreon = reuse AI compute, không maintain 2 engine riêng.

### Cron Reporting Policy (2026-05-27)
**TẤT CẢ cron jobs là isolated agentTurn + announce Telegram** — không phụ thuộc main session.
- `sessionTarget: "isolated"` — chạy nền, không bị block khi main session đang bận
- `delivery: { mode: "announce", to: "telegram:1336718742" }` — báo kết quả thành công/thất bại
- `payload.kind: "agentTurn"` — tự thực thi pipeline, không cần main session thức dậy
- **Nguyên tắc:** workflow cố định → isolated. Không systemEvent nào chặn main session.

### Model Assignment (2026-05-28)
| Task | Model | Ghi chú |
|------|-------|---------|
| Patreon Content Generator | deepseek-v4-flash | Ảnh Gemini 1K (đã fix từ 2K) |
| Aether Patreon Post | deepseek-v4-flash | Ảnh Gemini 1K |
| QuantEA Labs Blog | deepseek-v4-flash | thinking=high, viết article dài |
| YouTube Shorts Pipeline | mimo-v2.5-pro | Brainstorm + orchestrate (2026-05-28) |
| YouTube KPI Review | deepseek-v4-flash | Phân tích số liệu nhanh |
| Vedic Weekly #1-3 | qwen/qwen3.5-plus | Content tiếng Việt, Qwen tốt hơn |
| Auto Broadcast x2 | mimo-v2.5-pro | Chỉ curl, dùng model nhẹ |
| Workspace Cleanup | default | Script thuần |
| Hand-Post Pipeline | deepseek-v4-flash | Manual trigger |

⚠️ Mimo (xiaomi) không có image generation — chỉ text.
Ảnh: Gemini Imagen 1K (100% stable), không dùng 2K (80% timeout).

### Cron Jobs (all GMT+7, Mon-Fri)
- **06:55** — `Patreon Content Generator` (isolated): runs patreon_post_gen_v2.py (Sun-Thu)
- **06:58** — `Aether Patreon Post (No Image)` (main): runs patreon_poster.js → draft (Sun-Thu)
- **07:00** — `QuantEA Labs Daily Short` (isolated): YouTube Short pipeline synced with Patreon direction
- ⛔ **NO Gemini image generation** for Patreon — removed 2026-05-27 to save API costs

### Key Files Created
- /patreon-db/patreon_post_gen.py — Python content generator (local swisseph)
- /patreon-db/patreon_poster.js — Node.js Playwright Patreon auto-poster
- /patreon-db/patreon-post-content-v3.md — Latest generated content
- /patreon-db/PATREON_TEMPLATE_V3.md — Template reference
- /patreon-db/patreon_posts/ — Output directory for historical posts
- /patreon-db/patreon-session/ — Playwright browser session (cookies saved)

### Patreon Login
- Account: votiveacademy@gmail.com (Google OAuth)
- Session saved at patreon-db/patreon-session/
- Auto-login works — no manual intervention needed for subsequent runs

### Post URLs (Test Runs 2026-05-23)
- V1 (short): https://www.patreon.com/posts/158999540/edit
- V2 (full, has *): https://www.patreon.com/posts/158999971/edit
- V3 (final, clean): https://www.patreon.com/posts/159000405/edit

### Known Issues (RESOLVED)
- ~~Title field~~ ✅ Fixed: title selector now works correctly.
- ~~Content corruption (fragments at end)~~ ✅ Fixed 2026-05-27: replaced chunked `keyboard.insertText()` with atomic clipboard paste (`navigator.clipboard.writeText` + Meta+V). ProseMirror chunking race condition was ripping fragments from middle of content and dumping at end.
- Save button: Patreon auto-saves drafts continuously, manual save button not needed.
- Sunrise calculation: Uses previous day's JD for rise_trans (searches forward). Day rulers now correctly mapped (0=Moon/Mon, 5=Saturn/Sat, 6=Sun/Sun).

## 2026-05-23: Hand-Post Pipeline & Social Media Auto-Poster Built

### Hand-Post Pipeline (Kim Ssa viết bài → Carmen publish)
Kim Ssa gửi bài viết tay qua Telegram → Carmen xử lý toàn bộ:

```
node hand_post.js --content ./post.md [--image ./image.jpg] [--publish] [--platform patreon,x,meta]
```

| Bước | Platform | Script | Method |
|---|---|---|---|
| 1 | Patreon | `patreon_poster.js` → `patreon_publish.js` | Browser (draft or publish) |
| 2 | X/Twitter | `x_poster.js` | Browser (session saved) |
| 3 | Facebook Page | `meta_post.py` | Graph API ✅ |
| 4 | Instagram | `meta_post.py` | Graph API ✅ |

**QUAN TRỌNG:** Không chỉnh sửa bất kỳ cấu trúc nào trong bài của Kim Ssa. Copy-paste 100%.

### Social Media Footer Chuẩn
Mọi bài promo đều phải có footer:
```
📩 votive@vedicvn.com
🌍 vedicvn.com
📞 +84 385448747
```

### Unified Orchestrator
**`patreon-db/hand_post.js`** — single command posts to all platforms:
```bash
node hand_post.js --content ./post.md --image ./image.jpg --platform patreon,x,meta
```

### Platform-Specific Scripts
| Script | Chức năng | Method |
|---|---|---|
| `patreon_poster.js` | Tạo Patreon draft (auto-pipeline) | Browser |
| `patreon_publish.js` | Publish Patreon draft ngay | Browser |
| `x_poster.js` | Post lên X qua browser (session saved) | Browser |
| `meta-pipeline/meta_post.py` | Post lên Meta qua Graph API (FB Page + IG Business) | API ✅ |
| `meta_poster.js` | ~~Post lên Meta Business Suite (IG+FB) qua browser~~ — DEPRECATED 2026-05-28 | Browser ❌ |

### Session Directories (đã lưu, không cần login lại)
- `patreon-db/patreon-session/` — Patreon (votiveacademy@gmail.com, Google OAuth)
- `patreon-db/x-session/` — X/Twitter (@VotiveAstrology)
- `patreon-db/meta-session/` — ~~Meta Business Suite~~ — DEPRECATED 2026-05-28
- `meta-pipeline/.token` — Meta Page Access Token (API)

### Hand-Post Pipeline Rules (Kim Ssa gửi bài → Carmen post)
1. **Tạo ảnh** phù hợp chủ đề (Gemini Imagen / Google Imagen)
2. **Patreon:** Bài Patreon chỉ post lên Patreon. **KHÔNG post bài Patreon sang X, Meta, Telegram, YouTube hay bất kỳ kênh nào khác. Đây là quy tắc cứng.**
3. **X + Meta:** Dùng chung **một nội dung chiêm tinh riêng**, không phải bài Patreon, độ dài **≤2,000 ký tự** để an toàn dưới giới hạn Instagram 2,200 ký tự. Thêm footer.
4. **Meta (`meta_post.py`):** FB + IG post riêng qua API (không cần browser). FB: text + ảnh/video. IG: ảnh/video/carousel/reel. KHÔNG dùng browser automation nữa.
5. **IG text-only:** Instagram bắt buộc có ảnh/video — nếu bài không có ảnh, chỉ post FB.
6. **Footer chuẩn:** 📩 votive@vedicvn.com | 🌍 vedicvn.com | 📞 +84 385448747

### Known Bug (x_poster.js)
- Đã fix 2026-05-24: URL scraping trước đây lấy `a[href*="/status/"]` từ timeline → dính tweet random. Giờ navigate về profile để lấy đúng URL tweet vừa post.

### Platform Notes
- **X:** Browser automation (API bị lỗi "client-not-enrolled" do chưa gắn App vào Project). Dùng `x_poster.js`. X Premium → không giới hạn ký tự.
- **Meta (API):** Post qua Graph API — FB Page + IG Business (@votive_edu). Không cần browser, không cần login, không lo bị block. Token dài hạn (Page Access Token). IG bắt buộc có ảnh/video — text-only chỉ post FB.
- **Meta content:** Bài chiêm tinh social riêng ≤2,000 ký tự, dùng chung với X; không dùng bài Patreon.
- **Meta API credentials:** Page ID `177281685466511` (Votive Academy), IG ID `17841472353157389` (@votive_edu). Token trong `meta-pipeline/.token`.
- **Patreon:** Bài Patreon chỉ post Patreon. Bài auto-pipeline (cron job) vẫn để draft. Không cross-post nội dung Patreon sang bất kỳ nền tảng nào khác.

### .env Config
File: `patreon-db/.env` — chứa API keys cho X và Instagram (backup). Đã thêm vào .gitignore.
- X: OAuth 1.0a keys (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET) — hiện không dùng do lỗi Project enrollment
- Instagram: INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_BUSINESS_ACCOUNT_ID — hiện không dùng, đã chuyển qua browser

### Post URLs (2026-05-23 — Jupiter in Cancer)
- Patreon: https://www.patreon.com/posts/159001598
- X (promo): https://x.com/VotiveAstrology/status/2058040368000909422
- X (full analysis): https://x.com/VotiveAstrology/status/2058227660082598253
- Meta (IG+FB): Đã publish qua business.facebook.com

### Known Issues
- X API v2: App cần được enroll vào Project ("client-not-enrolled"). Workaround: dùng browser automation.
- Meta Business Suite: Cần login Facebook lần đầu với --visible. Session lưu xong thì chạy headless được.
- Meta composer: File upload cần 2 bước ("Thêm ảnh" → "Tải lên từ máy tính"), không dùng được input[type="file"] trực tiếp.
- Không nên bật toggle "Tùy chỉnh bài viết cho Facebook và Instagram" — để OFF, Meta tự xử lý cả 2 platform từ nội dung chung.

## 🚨 CONTENT VERIFICATION RULE (2026-05-25)
**CRITICAL — Kim Ssa's directive after YouTube video #002 error:**

### Calendar/Transit Content → MUST verify via Swiss Ephemeris
- **Mọi nội dung mang tính lịch** (planetary ingress, retrograde dates, eclipse dates, transit exact moments, planetary positions): **PHẢI check qua `pyswisseph` API** trước khi publish.
- **Tuyệt đối không** dùng web search, LLM knowledge, hay memory để xác định ngày transit.
- **Swiss Ephemeris là single source of truth** cho mọi dữ liệu thiên văn.

### Kiến thức/Tips/Tricks → OK to source externally
- Nội dung dạng kiến thức, tip, trick, phân tích, nhận định: có thể tìm từ web search, sách, tài liệu bên ngoài.
- Nhưng nếu trong đó có đề cập đến **ngày tháng cụ thể** của sự kiện thiên văn → vẫn phải verify qua swisseph.

### Verification Script
- `youtube-pipeline/verify_transit.py` — script verify nhanh ngày transit bằng pyswisseph
- Trước khi generate bất kỳ content YouTube/Telegram/Patreon nào có chứa ngày transit: chạy script verify trước.

### Incident Log
- **2026-05-25:** Video #002 (REKLeOxbm-g) nói "Sao Mộc vào Song Tử 14/5/2026" — SAI. 14/5 là ingress 2025. Jupiter vào Cự Giải 1/6/2026 21:00 GMT+7. Đã xoá video.

### YouTube Shorts Skill
- **Skill:** `~/.openclaw/plugin-skills/youtube-shorts/` — đóng gói toàn bộ pipeline thành skill tái sử dụng
- SKILL.md workflow + scripts/verify_transit.py + references/ (KPI targets, content strategy)

### ElevenLabs TTS (2026-05-25)
- **Key:** `youtube-pipeline/elevenlabs_key.txt` (gitignored, chmod 600)
- **Script:** `youtube-pipeline/elevenlabs_tts.py`
- **Voice:** Bella (free tier) — female English voice, phát âm tiếng Việt ở mức khá
- **Upgrade path:** Khi Kim Ssa nâng lên paid plan → switch sang Rachel hoặc multilingual v2
- **Note:** Key có thể thay đổi hoặc hết quota → Kim Ssa sẽ báo

## Image Generation Default (2026-05-26)
- **Provider:** Google Gemini (`gemini-3.1-flash-image-preview`)
- **Default resolution: 1K** — KHÔNG dùng 2K (luôn timeout, cùng giá)
- 1K đủ chất lượng cho social media, nhanh (~5-15s vs 60s+ timeout)
- Cả Patreon, X, Meta, YouTube Shorts đều dùng 1K
- ffmpeg scale ảnh 1K lên 1080×1920 cho Shorts vẫn đẹp

## YouTube Growth KPI — La Bàn Số Mệnh (2026-05-25)

**Kim Ssa directive:** Không quan tâm lịch/nội dung post. Chỉ nhìn KẾT QUẢ: sub, view, watch hours. Tự set KPI, tự đánh giá hàng tuần, tự điều chỉnh chiến lược.

### Baseline (25/5/2026)
| Metric | Value |
|--------|-------|
| Subscribers | 4 |
| Total Views | 5 |
| Videos | 2 |
| Watch Hours | ~0 |

### Monthly KPI Targets

| Metric | Week 1 (→2/6) | Week 2 (→9/6) | Week 3 (→16/6) | Week 4 (→23/6) |
|--------|---------------|---------------|----------------|----------------|
| Subscribers | 20 | 50 | 100 | 200 |
| Avg Views/video | 30 | 50 | 80 | 120 |
| Cumulative Views | 100 | 350 | 900 | 2,000 |
| Watch Hours | 1 | 3 | 8 | 20 |

### Leading Indicators (what I control)
- **5-7 Shorts/week** (daily cadence)
- **100% swisseph-verified** calendar content
- **Cross-post to X** every video (promo tweet)
- **Strong hook in first 2 seconds** every video
- **Reply comments ≤2h**
- **Upload public** — không unlisted, không cần Kim Ssa review (2026-05-26)

### Content Pillars
1. **Daily Transit (60%)** — Mặt Trăng vào nakshatra, góc chiếu hành tinh
2. **Major Events (25%)** — Ingress, retrograde, eclipse, conjunction
3. **Knowledge/Tips (15%)** — Nakshatra, hành tinh, chiêm tinh cơ bản

### Weekly Review Cadence
- **Every Monday:** Pull YouTube API stats → compare vs KPI → report Kim Ssa
- **<70% KPI:** Analyze root cause, pivot strategy
- **>120% KPI:** Scale what's working
- **Tracker:** `youtube-pipeline/kpi_tracker.json`

### Test Variables (Week 1)
- Post times: 7:00 vs 19:00 GMT+7
- Hashtags: #ChiêmTinh #VedicAstrology #Shorts #Transit
- Jupiter→Cancer là chủ đề chính (ingress 2/6)

## Google Flow (ĐÃ BỎ — 2026-05-24)
Pipeline Google Flow đã bị xoá toàn bộ do quá phức tạp và không stable:
- Google Flow chặn headless browser, bắt buộc headed
- Không có API, phải automation UI fragile
- Download không hoạt động (signed URLs)
- Quá nhiều edge cases → không đáng thời gian
→ Tập trung vào các pipeline khác ổn định hơn.

## Workspace Cleanup (2026-05-24)
- **Script:** `.openclaw/cleanup.sh` — xoá __pycache__, .DS_Store, browser cache, logs, reports disk usage
- **Cron:** Weekly Sunday 3AM GMT+7 (`d8f3c033`) — tự động dọn + báo cáo dung lượng
- **Result:** 1.9GB → 720MB (-1.1GB, -60%)
- **Gitignore:** thêm node_modules, browser cache, frames, *.mp4, *.jpg, *.png patterns
- **Structure:** patreon-db/ (471MB), video-pipeline/ (247MB, chỉ bot/ giữ lại), engines/ (92KB)

## 🚫 RED LINE: No Autonomous Cross-Posting (2026-05-26)
Kim Ssa directive: **KHÔNG tự ý làm những thứ không được hướng dẫn.**
- Auto Patreon → CHỈ Patreon draft. Không X, Meta, Telegram, hay bất kỳ đâu.
- YouTube Shorts → CHỈ YouTube. Không cross sang X, Meta, Telegram.
- Telegram broadcast → CHỈ Telegram.
- Chỉ Hand-Post Pipeline (Kim Ssa gửi bài tay) mới được cross-post đa nền tảng.
- **Nguyên tắc:** Mỗi pipeline có 1 output channel duy nhất. Không tự ý mở rộng. Không tự ý làm thêm.

---
## La Bàn Số Mệnh YouTube Channel 🇻🇳
**Pipeline:** `youtube-pipeline/` — Cron 9AM Mon-Fri
**Chủ đề:** Chiêm tinh Vedic, tử vi tiếng Việt

## GitHub Repositories (Master List)
| Repo | URL | Purpose |
|------|-----|---------|
| Quant-Labs | https://github.com/Oris7767/Quant-Labs | QuantEA Labs website (Astro/SSG) |
| Carmen-producer | https://github.com/Oris7767/Carmen-producer | Prompt bot / content producer |
| votive-astrologybot | https://github.com/Oris7767/votive-astrologybot | Astrology bot |
| Carmen-Intelligent | https://github.com/Oris7767/Carmen-Intelligent | Vedic market bot (Telegram) |

---
## QuantEA Labs Blog Website (2026-05-27)
**URL:** https://quantealabs.com
**GitHub:** https://github.com/Oris7767/Quant-Labs
**Stack:** Astro (SSG) + TypeScript + Tailwind CSS, deploy Netlify (auto-deploy on git push)
**Local path:** `/Users/kimssa/Documents/Quant-Labs/`
**Pipeline:** `website-pipeline/` in workspace

### Architecture
- Content-driven by Markdown files in `src/content/blog/`
- Carmen writes `.md` with frontmatter → git push → Netlify auto-deploy
- No CMS, no WordPress — pure static

### Auto-Publishing
- **Cron:** Tue & Fri 07:00 GMT+7 (`d3660f02`) — auto-write + publish article
- **On-demand:** Kim Ssa asks "viết bài về [topic]" → Carmen writes + auto-pushes
- **AUTO_COMMIT:** True — no review needed, Carmen tự push lên production
- **SEO:** Schema.org JSON-LD, OG/Twitter cards, sitemap, RSS — all auto

### Article Spec
- 1500-2500 words English, professional tone
- Required sections: Key Takeaways, The Setup, The Analysis, Risk Management, Conclusion
- Categories: Trading Strategy, Market Analysis, EA Development, Astrology Fundamentals, Risk Management
- Frontmatter: 15 fields including SEO keywords, reading time, schema type

### Content Calendar
- 2 articles/week (Tue + Fri)
- Topics rotate: planetary setups, Gann combos, historical patterns, risk management, EA previews
- Data-backed from patreon-db (4-year historical correlation engine)

---
## Vedic VN Blog — Supabase Pipeline (2026-05-31)
**Website:** https://vedicvn.netlify.app (deploy-preview-36 tested)
**Database:** Supabase (`qzyyiqzekduduoscdwjc.supabase.co`) — anon key with service_role
**Table:** `blog_posts` (id, title, content, excerpt, slug, author, date, image_url, tags)
**Storage buckets:** `blog_images` (unused), `blog-images` (active) — both public

### Pipeline
- **Script:** `blog-pipeline/publish.py` — Python, stdlib only, no pip dependencies
- **Birth chart bank:** `birth-chart-bank-data/birth_chart_clean.csv` (~10,143 records) → anonymous case studies in posts
- **3 content series:** (1) Pain points/chiêm tinh giải quyết vấn đề, (2) Bản tin thời không/transits, (3) Kiến thức nền tảng Vedic
- **9 templates total** (3 per series), round-robin publishing
- **Internal links:** Mọi bài đều link → `/vedic-chart`, social links (Facebook/X/Telegram), Patreon
- **Tags pool:** vedic, chiemtinh, dudoan, kienthuc, taichinh, healing, numerology

### Deployment
- **VPS:** `160.22.106.46` → `/root/blog-pipeline/` (root: `lV9!bVFKhqW@`)
- **VPS Cron:** Thứ 3 & Thứ 6, 07:00 GMT+7 (`0 0 * * 2,5` UTC) — publish 1 post each run
- **Log:** `/root/blog-pipeline/publish.log`
- **Local OpenClaw cron:** Disabled (moved to VPS to survive local shutdown)

### Initial batch (2026-05-31):
1. "Sao Mộc quá cảnh 2026" — transit finance
2. "Sao Thổ trong bản đồ sao" — career pain point
3. "Cung Mọc Lagna" — foundational knowledge

---

## Scheduled Crons (2026-06-01 — All moved to VPS + OpenClaw)

### VPS System Crontab (160.22.106.46)
| # | Lịch (GMT+7) | Script | Mục đích |
|---|-------------|--------|----------|
| 1 | `55 6 * * 0-4` | `patreon_daily.sh` | Patreon content gen + post draft (Sun-Thu 06:55) |
| 2 | `0 7 * * 1-5` | `curl POST /broadcast` | Broadcast phiên Á (07:00) |
| ~~3~~ | ~~`0 7 * * 1-5`~~ | ~~`quantealabs_short.sh`~~ | ~~QuantEA Labs Short~~ REMOVED (was posting trading to YouTube)
| 4 | `30 7 * * 1` | `kpi_weekly.sh` | YouTube KPI Weekly Review (Mon 07:30) |
| 5 | `0 9 * * 1-5` | `youtube_short.sh` | YouTube Shorts Pipeline (09:00, Mon-Fri) |
| 6 | `0 19 * * 1-5` | `curl POST /broadcast` | Broadcast phiên Mỹ (19:00) |
| 7 | `*/5 * * * *` | `check_notifications.sh` | Horoscope bot notify |
| 8 | `0 0 * * 2,5` | `blog-pipeline/publish.py` | Blog Vedic VN (T3/T6 07:00) |

### OpenClaw Cron Jobs (Vedic Weekly — need agent tools)
| # | Lịch (GMT+7) | Tên | Mục đích |
|---|-------------|-----|----------|
| 1 | Tue 09:00 | Vedic Weekly #1 | Research → image → X + Meta post |
| 2 | Thu 14:00 | Vedic Weekly #2 | Research → image → X + Meta post |
| 3 | Sat 20:00 | Vedic Weekly #3 | Research → image → X + Meta post |

### Files moved to VPS
- `/root/patreon-db/` — full patreon pipeline (scripts, data 222 CSVs, session, cover)
- `/root/engines/` — astro, gann, hora, ta, data_fetcher engines
- `/root/` — carmen_analyst.py, run_bot.py, report_generator.py, historical_correlation.py
- `/root/rag-gold/` — RAG engine + tfidf_store
- `/root/youtube-pipeline/` — daily_short.py, kpi_check.js, youtube_api.js, OAuth tokens, bg images

### Local Mac (OpenClaw)
- **0 system crons** (all deleted 2026-05-31 per request)
- **4 OpenClaw agent crons:**
  - Vedic Weekly #1 (Tue 09:00)
  - Vedic Weekly #2 (Thu 14:00)
  - Vedic Weekly #3 (Sat 20:00)
  - QuantEA Labs Blog Generator (Mon-Fri 05:30) — DeepSeek → MDX → git push → Netlify auto-deploy

## Brand Rules (2026-06-01)

### QuantEA Labs (quantealabs.com)
- **Ngôn ngữ:** Tiếng Anh 100%
- **Nội dung:** Quantitative Astro + Macro (lượng tử, chiêm tinh, vĩ mô)
- **GitHub:** https://github.com/Oris7767/Quant-Labs
- **Stack:** Astro SSG + TypeScript + Tailwind CSS, deploy Netlify
- **Blog Pipeline:** `blog_generator.py` — DeepSeek generates 3 content pillars:
  - Pillar 1 (The Proof): Trade breakdowns, case studies (Mon, Thu)
  - Pillar 2 (The Edge): Statistical insights, backtest data (Wed, Sat)
  - Pillar 3 (The Hook): Weekly market outlook + Gann levels (Tue, Fri, Sun)
- **Script:** `/Users/kimssa/Documents/Quant-Labs/blog_generator.py`
- **Cron:** OpenClaw isolated agentTurn, Mon-Fri 05:30 GMT+7
- **🔴 CẤM:**
  - Không viết tiếng Việt
  - Không nhắc đến Votive / votive-edu / votive.vn
  - Không PR, không link, không cross-promote Votive dưới bất kỳ hình thức nào
  - Không nội dung chiêm tinh thuần tuý (tử vi, xem lá số) — chỉ quant astro macro

### Votive (Brand Vedic VN)
- **Ngôn ngữ:** Tiếng Việt
- **Nội dung:** Chiêm tinh Vệ Đà (Vedic Astrology), tử vi, kiến thức nền tảng
- **Platforms:** X, Facebook, Instagram, Blog (Supabase → votive.vn)
- **Tone:** Gần gũi, tâm linh, giáo dục

### Patreon (Aether Astro-Quant)
- **Ngôn ngữ:** Tiếng Việt
- **Nội dung:** Gold trading analysis, Gann, Aether AI
- **Không:** Chiêm tinh thuần tuý (chỉ dùng data chiêm tinh cho trading)

## MT5 Trading Bot — Astro-Quant V3 (2026-06-02)

### VPS Windows (Oracle Cloud)
- **IP:** 138.252.133.45
- **OS:** Windows Server 2012 R2, 2GB RAM, 15GB SSD
- **User:** Administrator | **Pass:** AtakeV5OXL@jJ
- **Chi phí:** 50k VNĐ/tháng

### MT5 Account
- **Login:** 240115 | **Server:** CXMDirect-Demo | **Balance:** $1,000 Demo

### Telegram Bot
- **@astroeabot** (My Quant EA)
- **Token:** 896890…jlFw
- **Chat ID:** 1336718742

### Architecture V3
- **live_data.py** — Real-time: Yahoo Finance API (direct, bypass yfinance TLS) + pyswisseph 2.10.x
- **advanced_scorer.py** — LONG/SHORT scoring riêng (14 biến số × 2 hướng)
- **signal_generator.py** — Signal generation + quality rating
- **pattern_filter.py** — Pattern filtering (avoid/prioritize)
- **risk_manager.py** — 2% risk/trade, SL 0.5%, TP 2R, max 2 positions
- **position_monitor.py** — Trailing SL breakeven at 1R
- **telegram_notifier.py** — Entry/Exit/Daily Summary notifications

### Scoring Engine (14 variables × LONG/SHORT)
Nakshatra, Moon Sign, Nakshatra Lord, Retrograde, Combust, Hora, Moon Phase, Aspects, Gann, EMA, DXY, Venus Phase, Venus×DXY, RSI
- Regime-aware weights (low/medium/high vol)
- Score normalized -10 to +10
- Signal: LONG/SHORT/NEUTRAL with HIGH/MEDIUM/LOW confidence

### Key Bugs Fixed
1. `get_positions` None → `or []`
2. `free_margin` → `margin_free` (MT5 API)
3. pyswisseph 2.10.x return format change
4. yfinance TLS on Win 2012 R2 → direct Yahoo API fallback

### Scheduled
- Auto-start on boot (Windows Task Scheduler)
- Signal checks: 07:00 & 14:00 GMT+7

### Bot Path
`C:\astro_quant_mt5_bot\` on VPS 138.252.133.45

---

## Horoscope Bot — Diacritic & Self-Healing Fix (2026-06-05)

### Core Architecture Decision
- **Không dùng lookup table/filter** để fix tiếng Việt không dấu — gây sai chính tả
- **Không set max_tokens** cho MiMo API → model dùng full capacity
- **Self-healing auto-retry:** Phát hiện thiếu dấu → retry section đó (MAX_RETRIES=3)
- `_estimate_no_diacritic_ratio()`: kiểm tra Unicode range 0xC0-0x1EF9 + Vietnamese word patterns
- Kết quả: **100% sections có dấu** (4/7 pass lần 1, 3/7 retry lần 2)

### Raw Logging
- `data/raw_logs/{task_id}_attempt{N}_section_{M}.log` — timestamp, diacritic status, full content
- Dòng `NO DIACRITICS!` dễ detect

### File mapping
- `main.py`: self-healing loop, raw logging
- `pdf_generator.py`: Pattern 2 duplicate header fix
- `prompt_builder.py`: conditional max_tokens, diacritic recency footer

---

## BTC Astro-Quant Framework V1 (2026-06-02)

### BTC Database
- **Location:** `/Users/kimssa/Documents/Quant EA Trade/data/btc/`
- **Files:** 138 CSV (2015-01 → 2026-06), **4,170 trading days**, **97 columns**
- **Schema:** Giống hệt Aether gold database — OHLCV + Tech + Astro + Macro

### 3 New Macro Columns Added
| Column | Coverage | Source |
|--------|----------|--------|
| `halving_phase` | 100% | Hardcoded halving dates (2012, 2016, 2020, 2024, 2028) |
| `fear_greed` | 73% (2018+) | alternative.me API |
| `btc_dom_pct` | 99.9% | CoinMarketCap public API |

### BTC Scorer vs Gold Scorer: Key Differences
- **DROPPED:** Hora, Combust, Mercury Retrograde, Eclipse Effects
- **ADDED:** Halving Cycle Phase, Fear & Greed Index, BTC Dominance %
- **BOOSTED (vs gold):** Price vs SMA20 (×2.5), RSI (×2.0), EMA (×1.2)
- **REDUCED:** Nakshatra (×1.2 vs gold ×3.0), Moon Sign (×1.0 vs gold ×2.5)
- Tech indicators dominate (60%) vs Astro dominates for gold

### Performance (4,170 days)
- LONG: 30% of days, **64.8% win rate**, +0.90% avg
- SHORT: 10% of days, **64.4% bearish**, −0.95% avg
- HIGH CONFIDENCE: **79.0%** (81 calls)

### Top Patterns (confirmed from data)
1. **Price vs SMA20** — 63.8% above vs 39.7% below (24.1pp, 12/12 yrs)
2. **RSI-14** — extreme 80+ = 76% bullish, <20 = 24% (51.9pp spread)
3. **Nakshatra** — Purva Bhadrapada 61.2%, Swati 61.1%, Dhanishta 58.7%
4. **Halving Cycle** — post_halving_rally 57.0%, mid_cycle_downturn 49.0%
5. **Moon Conj Saturn** — 66.1% bullish (same as gold)
6. **Venus Morning Star + DXY Bearish** — 62.2% (same as gold 62.9%)
7. **F&G ≥ 60 + Below SMA20** — 76.4% bearish (best short setup)
8. **Taurus Moon + Below SMA20** — 69.3% bearish

### Files
- `btc_scorer.py` — scoring engine
- `collect_btc_macro.py` — daily macro data update
- `BTC_ASTRO_QUANT_FRAMEWORK_V1.md` — full framework doc (22KB)
- `BTC_PATTERN_REPORT.md`, `BTC_YEARLY_REPORT.md` — analysis reports

---

## VPS MT5 Bot — WinRM Access & Config

### VPS Windows (CXMDirect-Demo)
- **IP:** 138.252.133.45
- **OS:** Windows Server 2012 R2
- **User:** Administrator
- **Pass:** AtakeV5OXL@jJ
- **Connection:** WinRM (port 5985 HTTP, pywinrm)
- **Python:** 3.8.10 (`C:\Python38\`)
- **MT5:** `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Bot:** `C:\astro_quant_mt5_bot\`
- **Scheduled Task:** AstroQuantBot (auto-start, signal check 07:00 & 14:00 GMT+7)

### Critical Config
- **MT5 symbol:** `XAUUSDs` (CXMDirect dùng suffix "s" — không phải `XAUUSD`)
- **Yahoo Finance:** BLOCKED trên Win 2012 R2 (TLS issue) → lấy gold data từ MT5
- **`free_margin` → `margin_free`:** MT5 Python API cũ dùng `margin_free`
- **Tick 0/0:** Khi thị trường đóng, MT5 trả về bid=ask=0 → cần fallback daily close
