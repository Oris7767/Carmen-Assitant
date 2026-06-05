# 🤖 ASTRO-QUANT BOT TRADING — Complete Specification

**Version:** 1.0  
**Date:** 2026-05-29  
**Engine:** Astro-Quant Framework V3 + Super Cycle Framework  
**Dataset validated:** 4,629 trading days (2008-01 → 2026-05, 18 years)

---

## ═══════════════════════════════════════════════════════
## 1. KIẾN TRÚC TỔNG QUAN
## ═══════════════════════════════════════════════════════

```
┌──────────────────────────────────────────────────┐
│                 DATA PIPELINE                     │
│  patreon-db/data/YYYY-MM.csv (222 files)          │
│  └── daily OHLC + astro + macro + technical      │
├──────────────────────────────────────────────────┤
│            SCORING ENGINE                         │
│  astro_quant_scorer_v2.py                        │
│  └── AstroQuantScorer.score(row) → signal         │
├──────────────────────────────────────────────────┤
│            SIGNAL FILTER                          │
│  LONG: composite_score ≥ +3.0 + MEDIUM+ conf      │
│  SHORT: composite_score ≤ -3.0 + MEDIUM+ conf     │
│  Skip: Friday, FOMC, NFP                          │
├──────────────────────────────────────────────────┤
│         RISK MANAGEMENT                           │
│  $2K capital, 2% risk/trade, max 2 pos            │
│  SL 0.5% fixed, TP 2R, max 2-day hold             │
│  Trailing BE @ 1R, 5% daily loss limit            │
├──────────────────────────────────────────────────┤
│              EXECUTION                            │
│  XAUUSD via broker API (MT4/MT5/cTrader)          │
└──────────────────────────────────────────────────┘
```

---

## ═══════════════════════════════════════════════════════
## 2. QUẢN LÝ VỐN (CAPITAL MANAGEMENT)
## ═══════════════════════════════════════════════════════

### 2.1 Thông số cố định

| Parameter | Value | Description |
|-----------|-------|-------------|
| `BASE_CAPITAL` | $2,000 | Vốn khởi điểm |
| `RISK_PER_TRADE` | 2% | % vốn risk mỗi lệnh |
| `MAX_POSITIONS` | 2 | Số lệnh mở đồng thời tối đa |
| `SL_PCT` | 0.5% | Stop loss = 0.5% của entry price |
| `TP_R_MULTIPLE` | 2.0 | Take profit = 2 × SL distance (RR 1:2) |
| `MAX_HOLD_DAYS` | 2 | Giữ lệnh tối đa 2 ngày (swing) |
| `TRAILING_BE_TRIGGER` | 1.0R | Dời SL về entry khi lời ≥ 1R |
| `DAILY_LOSS_LIMIT` | 5% | Dừng trade trong ngày nếu lỗ ≥ 5% vốn |
| `MAX_DRAWDOWN` | 15% | Dừng toàn bộ nếu DD từ peak ≥ 15% |

### 2.2 Công thức tính lot size

```python
# XAUUSD: 1 micro lot (0.01) = 1 oz = $1 P&L per $1 gold move

risk_amount = current_equity * 0.02          # 2% của vốn hiện tại
sl_distance = entry_price * 0.005            # 0.5% của giá entry

# LONG example: entry $2000, SL $1990 (distance = $10)
# risk = $40 → lots = 40/10 = 4.0 micro lots = 0.04 standard

micro_lots = risk_amount / sl_distance
micro_lots = max(0.01, round(micro_lots * 100) / 100)  # round 0.01

actual_risk = micro_lots * sl_distance
```

### 2.3 Công thức SL & TP

```python
# LONG
sl_price = entry_price - (entry_price * 0.005)
tp_price = entry_price + (entry_price * 0.005 * 2)   # 2R

# SHORT
sl_price = entry_price + (entry_price * 0.005)
tp_price = entry_price - (entry_price * 0.005 * 2)
```

### 2.4 Trailing Break-Even

```python
# Khi unrealized P&L đạt 1R → move SL về entry price
risk_per_trade = micro_lots * sl_distance
if direction == 'LONG':
    if (current_high - entry_price) * micro_lots >= risk_per_trade:
        sl_price = entry_price  # trail to BE
if direction == 'SHORT':
    if (entry_price - current_low) * micro_lots >= risk_per_trade:
        sl_price = entry_price  # trail to BE
```

### 2.5 Market Hours Filter

```python
SKIP_ENTRY_DAYS = ['Friday']  # Không mở lệnh mới thứ 6
SKIP_EVENTS = ['FOMC', 'NFP'] # Không mở lệnh ngày FOMC, Non-Farm Payrolls

# Detection:
# - day_of_week == 'Friday'
# - 'FOMC' in economic_events.upper()
# - 'NON-FARM PAYROLLS (NFP)' in economic_events.upper()
```

---

## ═══════════════════════════════════════════════════════
## 3. CHIẾN LƯỢC LONG (BUY)
## ═══════════════════════════════════════════════════════

### 3.1 Signal Entry

```python
from astro_quant_scorer_v2 import AstroQuantScorer

score = AstroQuantScorer.score(row)

# ENTRY CONDITIONS (ALL must be true):
# 1. signal == 'LONG'
# 2. confidence in ['MEDIUM', 'HIGH']
# 3. NOT Friday
# 4. NOT FOMC/NFP day
# 5. active_positions < MAX_POSITIONS (2)
# 6. NOT daily_loss_limit hit
# 7. NOT max_drawdown hit

if (score['signal'] == 'LONG' and 
    score['confidence'] in ['MEDIUM', 'HIGH'] and
    not is_friday and not is_fomc_nfp):
    open_long()
```

### 3.2 Backtest Results (18 years)

| Mode | Final | Return | WR | PF | Max DD |
|------|-------|--------|-----|-----|--------|
| **Compound** | $2K → $42.7M | +2,135,687% | 54.1% | 4.55 | 13.4% |
| **Yearly Reset** | $38K → $63K | +1,250% (sum) | 54.1% | 4.55 | 8.0% avg |

| Yearly Reset | Value |
|-------------|-------|
| Năm có lãi | 17/19 (89%) |
| Năm lỗ | 2 (-0.6%, -0.7%) |
| Avg return/năm | +65.8% |
| Best năm | 2025 (+250%) |

### 3.3 Pattern Filter — NÊN vào LONG

| Category | Pattern | Win Rate | Notes |
|----------|---------|----------|-------|
| **Score** | Strong LONG (≥6) | 59.9% | Ưu tiên cao nhất |
| **Score** | LONG (3-6) | 49.6% | Base signal |
| **Nakshatra** | Chitra | 65.7% | #1 nakshatra |
| **Nakshatra** | Purva Phalguni | 64.3% | |
| **Nakshatra** | Magha | 60.9% | |
| **Nakshatra** | Punarvasu | 60.0% | |
| **Nakshatra** | Shatabhisha | 59.7% | Nhiều lệnh nhất (62) |
| **Moon Sign** | Leo | 61.5% | |
| **Moon Sign** | Libra | 56.9% | Nhiều lệnh nhất (137) |
| **Moon Sign** | Aquarius | 55.6% | |
| **Moon Phase** | Full Moon | 59.6% | |
| **Moon Phase** | Last Quarter | 55.5% | |
| **Moon Phase** | First Quarter | 54.2% | |
| **RSI** | Overbought (>70) | 53.6% | Trend-following |
| **RSI** | Strong (50-70) | 52.7% | |
| **Venus×DXY** | MS × DXY bearish | 53.7% | 520 lệnh |
| **Aspect** | Jupiter Sextile Saturn | 62.5% | |
| **Aspect** | Moon Sextile Mercury | 61.5% | |
| **Aspect** | Mercury Conj Venus | 60.5% | |
| **Aspect** | Jupiter Square Rahu/Ketu | 60.4% | |

### 3.4 Pattern Filter — TRÁNH LONG

| Category | Pattern | Win Rate | Risk |
|----------|---------|----------|------|
| **Nakshatra** | Hasta | 27.8% | ⛔ Tuyệt đối tránh |
| **Nakshatra** | Anuradha | 35.7% | ⛔ |
| **Nakshatra** | Ardra | 41.7% | ⚠️ |
| **Moon Sign** | Scorpio | 42.2% | ⚠️ |
| **Moon Sign** | Virgo | 42.5% | ⚠️ |
| **Moon Phase** | Waning Crescent | 45.9% | ⚠️ |
| **Moon Phase** | New Moon | 45.2% | ⚠️ |
| **RSI** | Oversold (<30) | 39.3% | ⛔ Không mua oversold |
| **Venus×DXY** | MS × DXY neutral | 26.7% | ⛔ |

---

## ═══════════════════════════════════════════════════════
## 4. CHIẾN LƯỢC SHORT (SELL)
## ═══════════════════════════════════════════════════════

### 4.1 Signal Entry

```python
score = AstroQuantScorer.score(row)

# ENTRY CONDITIONS:
# 1. signal == 'SHORT'
# 2. confidence in ['MEDIUM', 'HIGH']
# 3. NOT Friday
# 4. NOT FOMC/NFP day
# 5. active_positions < MAX_POSITIONS (2)
# 6. NOT daily_loss_limit hit
# 7. NOT max_drawdown hit

if (score['signal'] == 'SHORT' and 
    score['confidence'] in ['MEDIUM', 'HIGH'] and
    not is_friday and not is_fomc_nfp):
    open_short()
```

### 4.2 Backtest Results (18 years)

| Mode | Final | Return | WR | PF | Max DD |
|------|-------|--------|-----|-----|--------|
| **Compound** | $2K → $6.1M | +304,437% | 50.6% | 2.22 | 19.7% |
| **Yearly Reset** | $38K → $59.5K | +1,073% (sum) | 50.6% | 2.22 | 9.1% avg |

| Yearly Reset | Value |
|-------------|-------|
| Năm có lãi | **19/19 (100%)** 🔥 |
| Năm lỗ | 0 |
| Avg return/năm | +56.5% |
| Best năm | 2016 (+125%), 2018 (+124%) |

### 4.3 Pattern Filter — NÊN vào SHORT

| Category | Pattern | Bearish % | Notes |
|----------|---------|-----------|-------|
| **Score** | Strong SHORT (≤-6) | ~60% WR | Ưu tiên cao nhất |
| **Score** | SHORT (-6 to -3) | ~49% WR | Base signal |
| **Nakshatra** | Mrigashira | 62.6% | #1 SHORT nakshatra |
| **Nakshatra** | Dhanishta | 62.1% | #2 SHORT |
| **Nakshatra** | Uttara Phalguni | 59.8% | |
| **Nakshatra** | Uttara Ashadha | 58.8% | |
| **Nakshatra** | Anuradha | 57.1% | |
| **Moon Sign** | Capricorn | 58.1% | #1 SHORT moon |
| **Moon Sign** | Scorpio | 56.0% | |
| **Moon Sign** | Leo | 55.4% | |
| **Moon Sign** | Gemini | 55.4% | |
| **Moon Phase** | New Moon | 55.4% | #1 SHORT phase |
| **Moon Phase** | Waxing Crescent | 54.6% | |
| **Hora** | Mars | 55.6% | #1 SHORT hora |
| **RSI** | Oversold (<30) | 66.8% | 🔥 Trend continuation down |
| **RSI** | Weak (30-50) | 59.9% | |
| **Nakshatra Lord** | Sun | 56.8% | |
| **Nakshatra Lord** | Mars | 56.5% | |
| **Nakshatra Lord** | Saturn | 56.1% | |
| **Venus×DXY** | ES × DXY bullish | 67.5% | 🔥 Strongest confluence |
| **Venus×DXY** | MS × DXY bullish | 64.9% | |
| **Retrograde** | Saturn Retro | 54.1% | +1.7pp delta |
| **Combust** | Mars Combust | 54.7% | +1.8pp delta, wider SL |
| **Aspect** | Jupiter Opp Saturn | 67.1% | #1 SHORT aspect |
| **Aspect** | Venus Opp Mars | 64.6% | |
| **Aspect** | Mars Opp Rahu/Ketu | 63.2% | |
| **Aspect** | Sun Sextile Jupiter | 61.5% | |
| **Macro** | DXY Bullish | 66.2% | 🔥 Strong SHORT |
| **Technical** | Gann Key Level HELD | 61.4% | Compression → breakdown |
| **Technical** | EMA31 < EMA113 | 55.5% | Bear trend |

### 4.4 Pattern Filter — TRÁNH SHORT

| Category | Pattern | Bearish % | Risk |
|----------|---------|-----------|------|
| **Nakshatra** | Shatabhisha | 43.9% | ⛔ Tuyệt đối tránh SHORT |
| **Nakshatra** | Chitra | 44.3% | ⛔ |
| **Nakshatra** | Mula | 46.0% | ⚠️ |
| **Moon Sign** | Libra | 48.3% | ⛔ |
| **Moon Sign** | Sagittarius | 49.5% | ⚠️ |
| **Moon Phase** | Waning Crescent | 51.1% | ⚠️ |
| **Moon Phase** | First Quarter | 51.2% | ⚠️ |
| **Hora** | Venus | 50.4% | ⛔ |
| **RSI** | Overbought (>70) | 41.5% | ⛔ Không short overbought |
| **Venus×DXY** | MS × DXY bearish | 36.9% | ⛔ Tuyệt đối tránh |
| **Retrograde** | Mercury Retro | 50.1% | ⚠️ -3.7pp delta |
| **Retrograde** | Venus Retro | 50.3% | ⚠️ -2.9pp delta |
| **Macro** | DXY Bearish | 40.3% | ⛔ |
| **Aspect** | Jupiter Square Rahu/Ketu | 42.3% | ⛔ |

### 4.5 Excel table — Năm tốt nhất cho SHORT

| Năm | Return | Context |
|-----|--------|---------|
| 2016 | +124.6% | Post-rate-hike recovery |
| 2018 | +124.1% | Fed tightening |
| 2013 | +106.8% | Taper tantrum |
| 2015 | +97.9% | Bear market bottom |
| 2022 | +77.0% | Fed aggressive hikes |

→ SHORT hoạt động mạnh nhất trong **bear market & tightening cycle**.

---

## ═══════════════════════════════════════════════════════
## 5. QUY TẮC KẾT HỢP LONG + SHORT
## ═══════════════════════════════════════════════════════

### 5.1 Chế độ ưu tiên

```python
# Mặc định: cho phép cả LONG và SHORT
# LONG ưu tiên hơn trong bull market
# SHORT ưu tiên hơn trong bear/consolidation

# Market regime detection:
if ema_31 > ema_113 and dxy_direction == 'bearish':
    priority = 'LONG'    # Bull market
elif ema_31 < ema_113 and dxy_direction == 'bullish':
    priority = 'SHORT'   # Bear market
else:
    priority = 'BOTH'    # Mixed
```

### 5.2 Tín hiệu mạnh nhất (HIGH confidence)

```python
# LONG HIGH confidence: composite_score ≥ +6.0
#   → WR 59.9%, 162 lệnh trong 18 năm

# SHORT HIGH confidence: composite_score ≤ -6.0
#   → WR ~60%, similar frequency
```

### 5.3 Daily workflow

```
1. Sáng 7:00 GMT+7 — chạy collect.py để lấy data hôm nay
2. Score row hiện tại bằng AstroQuantScorer.score()
3. Kiểm tra:
   a. Có phải Friday/FOMC/NFP không? → skip
   b. Daily loss đã hit 5% chưa? → skip
   c. Max DD đã hit 15% chưa? → stop toàn bộ
   d. Số position hiện tại < 2? → có thể mở lệnh mới
4. Nếu LONG signal (≥+3.0):
   a. Check pattern filter — có nằm trong TRÁNH LONG không?
   b. Nếu score ≥ 6 → vào lệnh ngay
   c. Nếu score 3-6 → check thêm nakshatra/moon sign/RSI
5. Nếu SHORT signal (≤-3.0):
   a. Check pattern filter — có nằm trong TRÁNH SHORT không?
   b. Nếu score ≤ -6 → vào lệnh ngay
   c. Nếu score -6 to -3 → check thêm pattern
6. Quản lý lệnh đang mở:
   a. Check SL/TP hit
   b. Check max hold (2 ngày) → force close
   c. Check trailing BE trigger (1R profit → move SL to entry)
7. Cuối ngày: log P&L, update equity curve
```

---

## ═══════════════════════════════════════════════════════
## 6. DATA DEPENDENCIES
## ═══════════════════════════════════════════════════════

### 6.1 Required CSV Columns (from patreon-db)

**Price:**
- `date`, `day_of_week`, `gold_open`, `gold_high`, `gold_low`, `gold_close`, `gold_range`

**Technical:**
- `gold_atr_14`, `gold_rsi_14`, `gold_ema_31`, `gold_ema_113`, `gold_ema_relation`
- `gann_key_level_held`, `gann_held`

**Astro — Moon:**
- `moon_nakshatra`, `moon_nakshatra_lord`, `moon_sign`, `moon_phase`

**Astro — Planets:**
- `mercury_retro`, `venus_retro`, `mars_retro`, `jupiter_retro`, `saturn_retro`
- `mercury_combust`, `venus_combust`, `mars_combust`
- `mercury_elong_dir`, `venus_elong_dir`

**Astro — Aspects:**
- `aspects_json` (JSON array of aspect objects)

**Macro:**
- `dxy_direction`, `economic_events`, `economic_impact`

**Other:**
- `dominant_planet_hour` (Hora)
- `eclipse_active`

### 6.2 Scoring Engine

- **File:** `patreon-db/astro_quant_scorer_v2.py`
- **Class:** `AstroQuantScorer`
- **Method:** `AstroQuantScorer.score(row)` → dict with:
  - `signal`: 'LONG' | 'SHORT' | 'NEUTRAL'
  - `confidence`: 'HIGH' | 'MEDIUM' | 'LOW'
  - `composite_score`: -10 to +10
  - `market_state`: 'expansion' | 'compression' | 'exhaustion' | 'fear'
  - `volatility_regime`: 'low' | 'medium' | 'high'

---

## ═══════════════════════════════════════════════════════
## 7. IMPLEMENTATION CHECKLIST
## ═══════════════════════════════════════════════════════

### Phase 1: Core Bot
- [ ] Load patreon-db data pipeline (daily collect.py)
- [ ] Integrate AstroQuantScorer.score()
- [ ] Implement signal filter (direction + confidence)
- [ ] Implement skip rules (Friday, FOMC, NFP)
- [ ] Calculate position size (2% risk, 0.5% SL)
- [ ] Open positions via broker API

### Phase 2: Risk Management
- [ ] SL/TP monitoring (check every candle/tick)
- [ ] Trailing BE (move SL to entry at 1R profit)
- [ ] Max hold enforcement (close after 2 days)
- [ ] Daily loss limit (5% → stop trading for the day)
- [ ] Max drawdown monitor (15% → hard stop)

### Phase 3: Pattern Filter
- [ ] Filter nakshatra TRÁNH list (Hasta, Anuradha, Ardra for LONG)
- [ ] Filter moon sign TRÁNH list (Scorpio, Virgo for LONG)
- [ ] Filter RSI (no LONG when RSI < 30)
- [ ] Filter Venus×DXY (no LONG when MS × DXY neutral)
- [ ] Prioritize HIGH confidence signals (≥6 or ≤-6)

### Phase 4: Monitoring
- [ ] Daily P&L log
- [ ] Equity curve tracking
- [ ] Weekly/Monthly performance report
- [ ] Telegram notification for trades + daily summary

---

## ═══════════════════════════════════════════════════════
## 8. CODE REFERENCE
## ═══════════════════════════════════════════════════════

### 8.1 Backtest Engine
- **File:** `patreon-db/astro_quant_backtest_live.py`
- Contains full simulation with all risk rules implemented
- Reference for position sizing, SL/TP, trailing BE logic

### 8.2 Key Functions

```python
# Position sizing (LONG example)
def calculate_long_position(equity, entry_price):
    risk_amount = equity * 0.02
    sl_distance = entry_price * 0.005
    sl_price = entry_price - sl_distance
    tp_price = entry_price + sl_distance * 2
    micro_lots = max(0.01, round(risk_amount / sl_distance * 100) / 100)
    return sl_price, tp_price, micro_lots

# Signal check
def should_enter_long(row):
    score = AstroQuantScorer.score(row)
    if score['signal'] != 'LONG':
        return False
    if score['confidence'] not in ['MEDIUM', 'HIGH']:
        return False
    if row['day_of_week'] == 'Friday':
        return False
    events = str(row.get('economic_events', ''))
    if 'FOMC' in events.upper():
        return False
    if 'NON-FARM PAYROLLS (NFP)' in events.upper():
        return False
    # Pattern filter (optional but recommended)
    nakshatra = row.get('moon_nakshatra', '')
    if nakshatra in ['Hasta', 'Anuradha', 'Ardra']:
        return False  # TRÁNH
    rsi = row.get('gold_rsi_14')
    if rsi and rsi < 30:
        return False  # Không LONG oversold
    return True
```

---

## ═══════════════════════════════════════════════════════
## 9. PERFORMANCE EXPECTATIONS
## ═══════════════════════════════════════════════════════

### With $2,000 starting capital (yearly reset mode):

| Strategy | Avg/Year | Best Year | Worst Year | Profitable |
|----------|----------|-----------|------------|------------|
| **LONG only** | +65.8% | +250% (2025) | -0.7% (2013) | 89% |
| **SHORT only** | +56.5% | +125% (2016) | +5.9% (2010) | 100% |
| **LONG + SHORT** | ~+100%* | — | — | ~95%* |

*Estimated combined

---

*Specification generated by Carmen 🪐 for Kim Ssa — 2026-05-29*  
*Validated on 4,629 trading days across 18 years (2008-2026)*
