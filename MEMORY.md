# MEMORY.md - Curated Trading & Astrological Knowledge

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
**Status:** 2024-05 → 2026-05 ✅ COMPLETE (519 trading days, 25 months). Analysis reports generated for both periods.

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
- **Total:** 2023-05 → 2026-05 = 771 trading days, 37 months ✅
- **FOMC dates:** 2023, 2024, 2025 all hardcoded in collect.py

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

### Next Steps
1. ✅ Build similarity search engine (find historically similar days) — DONE 2026-05-23
2. ✅ Build Patreon post generator (RAG-based narrative) — DONE 2026-05-23
3. Backtest patterns with walk-forward validation

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
| 1 | Executive Summary + Carmen AI Signal |
| 2 | Macro Context (DXY, Fed, news) |
| 3 | Multi-TF Technical (M30 + Gann 9 + Time Cycles) |
| 4 | Vedic Astrology (planets, aspects, Hora) |
| 5 | **CORRELATION LỊCH SỬ 4 NĂM (unique edge)** |
| 6 | Carmen AI Deep Analysis |
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
6. 📝 Carmen's Reasoning
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
- **NO asterisks** (*) — Patreon editor shows them as literal text, looks ugly
- **NO markdown** (**, ##, ---) — use emoji separators instead
- **NO excessive blank lines** — max 1 between sections
- Use • for bullets, | for inline data separation
- 10 sections: Title, Technical, Gann/Fib, Astrology, 6-Layer Framework, Hora 24h, Strategy, Reasoning, Risks, Observation Zones
- News/macro events auto-detected from CSV economic_events column

### Content Pipeline (10 Sections)
1. 🔮 Title + key aspects subtitle
2. 📊 Technical Analysis (close data: price, EMA, DXY, vol, trend, reaction)
3. 📐 Gann & Fibonacci Levels
4. 🌌 Astrological Framework (planets, aspects, Moon analysis)
5. 🧬 6-Layer Astro-Quant Framework (scoring, market state, pattern matching)
6. ⏰ Hora Schedule 24h (14 periods, best/worst flagged)
7. 💡 Trading Strategy (direction, entry, SL, TP1, TP2, R:R)
8. 📝 Carmen's Reasoning (narrative synthesis)
9. 🔴 Key Risks
10. 📍 Observation Zones

### Cron Jobs (GMT+7, Sun-Thu only)
- **00:30** — `Patreon Content Generator` (isolated): runs patreon_post_gen.py
- **00:35** — `Carmen Patreon Post` (main session): wakes Carmen to generate Gemini image + run patreon_poster.js → Patreon draft
- Only runs Sunday-Thursday evenings (forecasts for Mon-Fri trading days)

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

### Known Issues
- Title field: Patreon uses block-based editor, first line auto-becomes title. Script's title selector fails but it's cosmetic (content fills correctly).
- Save button: Patreon auto-saves drafts continuously, manual save button not needed.
- Sunrise calculation: Uses previous day's JD for rise_trans (searches forward). Day rulers now correctly mapped (0=Moon/Mon, 5=Saturn/Sat, 6=Sun/Sun).

## 2026-05-23: Hand-Post Pipeline & Social Media Auto-Poster Built

### Hand-Post Pipeline (Kim Ssa viết bài → Carmen publish)
Kim Ssa gửi bài viết tay qua Telegram → Carmen xử lý toàn bộ:

| Bước | Hành động |
|---|---|
| 1 | Generate ảnh phù hợp chủ đề (Gemini Imagen) |
| 2 | Copy-paste **100% nguyên văn** lên Patreon → auto-publish |
| 3 | Tạo post promo cho X (dài, tận dụng Premium) |
| 4 | Tạo post promo cho Meta (ngắn, visual) |
| 5 | Post lên X qua browser automation |
| 6 | Post lên Meta (IG + FB Page đồng thời) qua browser automation |

**QUAN TRỌNG:** Không chỉnh sửa bất kỳ cấu trúc nào trong bài của Kim Ssa. Copy-paste 100%.

### Social Media Footer Chuẩn
Mọi bài promo đều phải có footer:
```
📩 votive@vedicvn.com
🌍 vedicvn.com
📞 +84 385448747
```

### Scripts Đã Build
| Script | Chức năng |
|---|---|
| `patreon_poster.js` | Tạo Patreon draft (auto-pipeline) |
| `patreon_publish.js` | Publish Patreon draft ngay |
| `x_poster.js` | Post lên X qua browser (session saved) |
| `meta_poster.js` | Post lên Meta Business Suite (IG+FB) qua browser |
| `social_poster.js` | Post qua API (X API v2 + Instagram Graph API) — backup |

### Session Directories (đã lưu, không cần login lại)
- `patreon-db/patreon-session/` — Patreon (votiveacademy@gmail.com, Google OAuth)
- `patreon-db/x-session/` — X/Twitter (@VotiveAstrology)
- `patreon-db/meta-session/` — Meta Business Suite (Votive Academy FB + votive_edu IG)

### Hand-Post Pipeline Rules (Kim Ssa gửi bài → Carmen post)
1. **Tạo ảnh** phù hợp chủ đề (Gemini Imagen / Google Imagen)
2. **X (`x_poster.js`):** Copy NGUYÊN VĂN 100%, không thêm bớt, không chỉnh sửa. Full content (X Premium = unlimited). Thêm footer.
3. **Meta (`meta_poster.js`):** Cần rút gọn xuống ≤2,200 ký tự (giới hạn Instagram). FB+IG post chung 1 nội dung. KHÔNG bật toggle "Tùy chỉnh bài viết". Thêm footer.
4. **Footer chuẩn:** 📩 votive@vedicvn.com | 🌍 vedicvn.com | 📞 +84 385448747

### Known Bug (x_poster.js)
- Đã fix 2026-05-24: URL scraping trước đây lấy `a[href*="/status/"]` từ timeline → dính tweet random. Giờ navigate về profile để lấy đúng URL tweet vừa post.

### Platform Notes
- **X:** Browser automation (API bị lỗi "client-not-enrolled" do chưa gắn App vào Project). Dùng `x_poster.js`. X Premium → không giới hạn ký tự.
- **Meta Business Suite:** Post đồng thời IG + Facebook Page. UI tiếng Việt: "Tạo bài viết" → "Thêm ảnh" → "Tải lên từ máy tính" → "Đăng". Lỗi thường gặp: văn bản >2,200 ký tự → nút Đăng bị disable. Giải pháp: tạo file rút gọn riêng cho Meta.
- **Patreon:** Tự động publish (không draft) cho bài tay. Bài auto-pipeline (cron job) vẫn để draft.

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
