# 📊 Patreon Analysis Database — Schema

## Structure
- **One CSV per month:** `data/YYYY-MM.csv`
- **One row per trading day**
- **Columns grouped by category** (see below)

## Column Groups

### A. DATE & PRICE (Core)
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `date` | YYYY-MM-DD | 2025-05-22 | Trading date (GMT+7) |
| `day_of_week` | string | Friday | |
| `gold_open` | float | 3125.50 | XAUUSD daily open |
| `gold_close` | float | 3148.20 | XAUUSD daily close |
| `gold_high` | float | 3155.80 | Daily high |
| `gold_low` | float | 3118.40 | Daily low |
| `gold_range` | float | 37.40 | high - low |
| `gold_change_pct` | float | 0.72 | (close-open)/open*100 |
| `gold_body_pct` | float | 0.60 | |close-open|/open*100 |
| `gold_bullish` | bool | true | close > open |
| `gold_ema_31` | float | 1923.74 | EMA(31) on gold close, 200-day lookback |
| `gold_ema_113` | float | 1883.68 | EMA(113) on gold close, 200-day lookback |
| `gold_ema_relation` | string | above | EMA31 vs EMA113: "above" or "below" |

### B. GANN & FIBONACCI (Technical)
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `swing_high` | float | 3155.80 | Recent swing high for fib calc |
| `swing_low` | float | 3118.40 | Recent swing low for fib calc |
| `swing_trend` | string | UP | UP or DOWN |
| `fib_0` | float | 3118.40 | |
| `fib_02126` | float | 3126.35 | |
| `fib_05` | float | 3137.10 | |
| `fib_0618` | float | 3143.03 | |
| `fib_07874` | float | 3148.39 | |
| `fib_1` | float | 3155.80 | |
| `fib_12126` | float | 3164.55 | |
| `fib_15` | float | 3174.25 | |
| `fib_1618` | float | 3185.57 | |
| `gann_primary_angle` | string | 1x1 bullish | Primary Gann fan angle status |
| `gann_key_level_held` | bool | true | Did price hold a key Gann/Fib level? |
| `gann_breached_level` | string | fib_0618 | Which level was breached (if any) |
| `gann_reaction` | string | bounce | bounce / break / rejection |

### C. ASTROLOGICAL — SUN & MOON
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `sun_sign` | string | Gemini | Vedic (sidereal) |
| `sun_degree` | float | 5.2 | Degrees in sign |
| `moon_sign` | string | Scorpio | Vedic |
| `moon_degree` | float | 12.8 | |
| `moon_nakshatra` | string | Jyeshtha | |
| `moon_nakshatra_lord` | string | Mercury | |
| `moon_phase` | string | Waning Gibbous | 8-phase: New Moon, Waxing Crescent, First Quarter, Waxing Gibbous, Full Moon, Waning Gibbous, Last Quarter, Waning Crescent |
| `moon_illumination_pct` | float | 78.7 | Moon illumination 0-100% |
| `moon_void` | bool | false | Void of course? |

### D. ASTROLOGICAL — PLANETS
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `mercury_sign` | string | Taurus | |
| `mercury_degree` | float | 15.3 | |
| `mercury_retrograde` | bool | false | |
| `mercury_elongation_dir` | string | W | W=Morning, E=Evening |
| `mercury_elongation_deg` | float | 18.5 | Degrees from Sun |
| `mercury_combust` | bool | false | Within orb of Sun? |
| `venus_sign` | string | Aries | |
| `venus_degree` | float | 22.1 | |
| `venus_retrograde` | bool | false | |
| `venus_elongation_dir` | string | E | |
| `venus_elongation_deg` | float | 45.2 | |
| `venus_combust` | bool | false | Within 4° of Sun? |
| `mars_sign` | string | Cancer | |
| `mars_degree` | float | 8.7 | |
| `mars_retrograde` | bool | false | |
| `mars_elongation_deg` | float | 35.1 | |
| `mars_combust` | bool | false | Within 8° of Sun? |
| `jupiter_sign` | string | Gemini | |
| `jupiter_degree` | float | 12.4 | |
| `jupiter_retrograde` | bool | false | |
| `jupiter_elongation_deg` | float | 120.3 | |
| `saturn_sign` | string | Pisces | |
| `saturn_degree` | float | 28.9 | |
| `saturn_retrograde` | bool | true | |
| `saturn_elongation_deg` | float | 150.2 | |

### D+. ASTROLOGICAL — RAHU & KETU (SHADOW PLANETS / LUNAR NODES)
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `rahu_sign` | string | Leo | North Node (Mean Node), Vedic sidereal. Always retrograde. |
| `rahu_degree` | float | 15.3 | Degrees in sign |
| `ketu_sign` | string | Aquarius | South Node = Rahu + 180°. Always retrograde. |
| `ketu_degree` | float | 15.3 | Degrees in sign |
| *Note* | | | No combust/elongation flags — shadow planets only contribute to aspects. |

### E. ASTROLOGICAL — ASPECTS & EVENTS
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `aspects_major` | string | Mars Square Sun, Venus Trine Jupiter | Pipe-separated: \| |
| `aspect_count` | int | 3 | Number of major aspects (within ±5° orb) |
| `eclipse_active` | bool | false | Within eclipse window (~10 days)? |
| `eclipse_type` | string | null | Solar / Lunar / null |
| `eclipse_days_away` | int | 0 | 0=day of, positive=future, negative=past |
| `aspects_json` | json | [...] | All aspects including Rahu/Ketu, with planet names, aspect type, orb |
| `dominant_planet_hour` | string | Mars | First Hora of the day (from sunrise) |
| `trading_hora_favorable` | bool | true | Is the dominant Hora favorable for direction? |

### F. ECONOMIC & MACRO
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `economic_events` | string | US CPI 3.2%, FOMC Minutes | Key events that day |
| `economic_impact` | string | high | low / medium / high |
| `dxy_close` | float | 103.74 | Dollar Index close |
| `dxy_change_pct` | float | -0.35 | DXY daily change % |
| `dxy_direction` | string | bearish | DXY direction vs previous close |
| `us10y_close` | float | 2.85 | US 10Y Treasury yield (%) |
| `us10y_change` | float | 0.05 | US10Y daily change |
| `sp500_change_pct` | float | 0.45 | |

### G. MARKET REACTION & ANALYSIS
| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `session_asia_range` | string | 3118-3132 | Asia session high-low |
| `session_london_range` | string | 3125-3148 | |
| `session_ny_range` | string | 3135-3155 | |
| `market_reaction` | string | bullish reversal | Description of how market reacted |
| `trend_direction` | string | bullish | Daily trend bias |
| `volatility` | string | medium | low / medium / high |
| `pattern_match` | string | Mars square + Fib 0.618 hold → reversal | Pattern identified |
| `analysis_notes` | string | [Kim's manual annotation] | Free text — Kim's actual analysis |
| `setup_quality` | string | A+ | A+ / A / B / C / F — how clean was the setup? |

### H. SIMILARITY SCORES (computed at query time, NOT stored)
These are computed on-the-fly when searching for analogs.

---

## File Naming
```
patreon-db/
├── SCHEMA.md          ← this file
├── collect.py         ← auto-collect script
├── search.py          ← similarity search engine
├── generate_post.py   ← Patreon post generator
├── backfill/          ← backfill tracking
│   └── PROGRESS.md
└── data/
    ├── 2025-05.csv
    ├── 2025-06.csv
    ├── ...
    └── 2026-05.csv
```

## Backfill Protocol
- **One month per session**
- **Verify before moving on**
- **Kim Ssa reviews each month's data before next month starts**
- **Progress tracked in backfill/PROGRESS.md**
