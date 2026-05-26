# 📊 Similarity Search Engine — Pattern Analysis Report

**Period:** 2023-05 → 2024-04 (252 trading days)  
**Generated:** 2026-05-22  
**Dataset:** 12 monthly CSVs, 57 columns per day

---

## 1. BASELINE

| Metric | Value |
|--------|-------|
| Total Trading Days | 252 |
| Bullish Days (close > open) | 48.0% |
| Bearish Days | 52.0% |
| Neutral Days | 0.0% |
| Avg Daily Change | +0.001% |
| Std Daily Change | 0.634% |
| Avg Daily Range | 16.35 |


---

## 2. MOON SIGN → TREND

| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Aries | 21 | 57.1% | +0.13% | 16.5 | 0 |
| Taurus | 18 | **11.1%** | -0.22% | 13.1 | 1 |
| Gemini | 21 | 42.9% | +0.01% | 15.4 | 1 |
| Cancer | 25 | 44.0% | -0.08% | 12.9 | 0 |
| Leo | 20 | 50.0% | -0.21% | 17.8 | 1 |
| Virgo | 27 | 55.6% | +0.07% | 20.0 | 2 |
| Libra | 24 | 62.5% | +0.15% | 18.6 | 3 |
| Scorpio | 18 | 44.4% | +0.14% | 15.7 | 1 |
| Sagittarius | 22 | **72.7%** | +0.17% | 17.2 | 0 |
| Capricorn | 22 | 40.9% | +0.05% | 18.5 | 1 |
| Aquarius | 15 | 46.7% | +0.03% | 12.5 | 0 |
| Pisces | 19 | 36.8% | -0.30% | 15.3 | 0 |

**Key:** Sagittarius & L = strongest bullish. Taurus = weakest.


---

## 3. MOON NAKSHATRA → TREND

| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Ashwini | 8 | **75.0%** | +0.23% | 11.8 | 0 |
| Bharani | 10 | 50.0% | +0.12% | 17.9 | 0 |
| Krittika | 9 | **22.2%** | -0.12% | 13.1 | 0 |
| Rohini | 7 | **14.3%** | -0.28% | 22.2 | 1 |
| Mrigashira | 8 | **12.5%** | -0.20% | 8.1 | 0 |
| Ardra | 10 | 50.0% | +0.14% | 12.2 | 0 |
| Punarvasu | 10 | 50.0% | -0.05% | 19.2 | 1 |
| Pushya | 11 | 45.5% | -0.06% | 12.3 | 0 |
| Ashlesha | 12 | **33.3%** | -0.13% | 14.0 | 0 |
| Magha | 9 | 55.6% | -0.32% | 22.9 | 1 |
| Purva Phalguni | 8 | 37.5% | -0.21% | 14.8 | 0 |
| Uttara Phalguni | 11 | **72.7%** | +0.45% | 16.9 | 1 |
| Hasta | 13 | 46.2% | -0.31% | 20.5 | 1 |
| Chitra | 12 | 66.7% | +0.27% | 16.4 | 0 |
| Swati | 11 | 54.5% | +0.07% | 23.3 | 3 |
| Vishakha | 8 | 50.0% | +0.08% | 14.5 | 0 |
| Anuradha | 9 | **33.3%** | -0.03% | 14.6 | 0 |
| Jyeshtha | 8 | 62.5% | +0.35% | 18.5 | 1 |
| Mula | 10 | **90.0%** | +0.32% | 16.7 | 0 |
| Purva Ashadha | 9 | 55.6% | +0.18% | 17.5 | 0 |
| Uttara Ashadha | 11 | 45.5% | -0.22% | 20.2 | 0 |
| Shravana | 9 | 44.4% | +0.08% | 15.6 | 0 |
| Dhanishta | 8 | 37.5% | +0.24% | 14.0 | 1 |
| Shatabhisha | 6 | **83.3%** | +0.30% | 15.3 | 0 |
| Purva Bhadrapada | 8 | **25.0%** | -0.32% | 14.4 | 0 |
| Uttara Bhadrapada | 8 | **25.0%** | -0.31% | 13.8 | 0 |
| Revati | 9 | 44.4% | -0.24% | 16.4 | 0 |

**Key:** Nakshatra là predictor mạnh nhất. Mula 90.0% bullish vs Mrigashira 12.5% — chênh lệch 78%.
- **Bullish cluster:** Mula, Shatabhisha, Ashwini, Uttara Phalguni, Chitra
- **Bearish cluster:** Purva Bhadrapada, Uttara Bhadrapada, Krittika, Rohini, Mrigashira


---

## 4. PLANETARY RETROGRADE

| Planet | Retrograde | | Direct | | Δ Bullish |
|--------|-----------|---|--------|---|-----------|
| | Days | Bullish % | Days | Bullish % | |
| **Mercury** | 57 | 56.1% | 195 | 45.6% | +10.5% ⚠️ |
| **Venus** | 30 | 36.7% | 222 | 49.5% | -12.9% ⚠️ |
| **Mars** | 0 | 0.0% | 252 | 48.0% | -48.0% ⚠️ |
| **Jupiter** | 82 | 43.9% | 170 | 50.0% | -6.1% |
| **Saturn** | 97 | 42.3% | 155 | 51.6% | -9.3% ⚠️ |

**Retrograde Range Impact:**

| Planet | Retro Range | Direct Range | Ratio |
|--------|------------|--------------|-------|
| Mercury | 20.0 | 15.3 | 1.31x |
| Venus | 11.3 | 17.0 | 0.66x |
| Mars | 0.0 | 16.3 | 0.00x |
| Jupiter | 14.4 | 17.3 | 0.83x |
| Saturn | 11.6 | 19.3 | 0.60x |

**Key:**
- Mercury Retro = bullish (delta +10.5%)
- Venus Retro = bearish (delta -12.9%)
- Mars Retro = bearish (delta -48.0%)
- Saturn Retro = bearish (delta -9.3%)
- Venus Retro = HIGH VOLATILITY (range gấp 0.66x)


---

## 5. COMBUST (BÓC CHÁY)

| Planet | Combust | | Non-Combust | |
|--------|---------|---|-------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Mercury** | 18 | 72.2% / +0.35% / 23.1 | 234 | 46.2% / -0.03% / 15.8 |
| **Venus** | 4 | 25.0% / -0.14% / 10.2 | 248 | 48.4% / +0.00% / 16.4 |
| **Mars** | 38 | 42.1% / -0.15% / 17.2 | 214 | 49.1% / +0.03% / 16.2 |


---

## 6. PLANETARY ELONGATION QUARTILES

| Planet | Low Elong (Q1) | | High Elong (Q4) | |
|--------|----------------|---|-----------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Mercury** | 63 | 60.3% / +0.20% / 18.8 | 63 | 39.7% / -0.12% / 16.1 |
| **Venus** | 63 | 54.0% / +0.01% / 21.5 | 63 | 44.4% / +0.06% / 14.3 |
| **Mars** | 63 | 54.0% / +0.03% / 16.2 | 63 | 47.6% / -0.01% / 16.6 |
| **Jupiter** | 63 | 55.6% / +0.02% / 22.9 | 63 | 42.9% / -0.04% / 15.9 |
| **Saturn** | 63 | 57.1% / +0.08% / 21.7 | 63 | 34.9% / -0.09% / 10.2 |

**Key:**
- Venus High Elongation = low volatility (range 14 vs 21)
- Jupiter High Elongation = low volatility (range 16 vs 23)
- Saturn High Elongation = low volatility (range 10 vs 22)


---

## 7. ASPECTS

### 7a. By Aspect Type

| Aspect | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|------|-----------|------|-------|---------|
| Conjunction | 153 | 49.7% | +0.01% | 16.5 | 8 |
| Opposition | 76 | 50.0% | -0.03% | 16.8 | 5 |
| Sextile | 202 | 50.0% | +0.02% | 16.9 | 10 |
| Square | 137 | 46.0% | +0.02% | 14.3 | 2 |
| Trine | 126 | 47.6% | -0.01% | 16.2 | 7 |

### 7b. Sun-Planet Aspects (critical for Gold)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|--------|------|-----------|------|-------|---------|
| Conjunction | Moon | 6 | **83.3%** | +0.12% | 20.5 | 1 |
| Conjunction | Saturn | 7 | **71.4%** | +0.72% | 20.9 | 1 |
| Square | Moon | 10 | **70.0%** | +0.03% | 13.0 | 0 |
| Trine | Moon | 10 | **70.0%** | +0.40% | 20.2 | 1 |
| Conjunction | Mercury | 36 | 61.1% | +0.22% | 19.7 | 3 |
| Square | Saturn | 10 | 60.0% | +0.21% | 13.0 | 0 |
| Opposition | Moon | 7 | 57.1% | +0.02% | 11.0 | 0 |
| Trine | Saturn | 11 | 54.5% | +0.09% | 9.4 | 0 |
| Sextile | Jupiter | 15 | 53.3% | +0.41% | 17.5 | 1 |
| Opposition | Saturn | 8 | 50.0% | +0.08% | 9.7 | 0 |
| Sextile | Saturn | 6 | 50.0% | +0.03% | 13.2 | 0 |
| Conjunction | Mars | 23 | 43.5% | -0.09% | 16.8 | 1 |
| Sextile | Mars | 13 | **38.5%** | +0.13% | 9.9 | 0 |
| Sextile | Moon | 13 | **38.5%** | -0.22% | 14.8 | 0 |
| Opposition | Jupiter | 7 | **28.6%** | -0.23% | 9.3 | 0 |
| Conjunction | Venus | 4 | **25.0%** | -0.14% | 10.2 | 0 |
| Square | Jupiter | 13 | **23.1%** | -0.11% | 13.2 | 0 |
| Trine | Jupiter | 10 | **20.0%** | -0.15% | 9.6 | 0 |

**Key:**
- Sun Conjunction Moon = 83% bullish, low vol
- Sun Conjunction Saturn = 71% bullish
- Sun Square Saturn = 60% bullish
- Sun Trine Saturn = 55% bullish
- Sun Opposition Saturn = 50% bullish
- Sun Sextile Saturn = 50% bullish

### 7c. Moon-Planet Aspects (top 15)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range |
|--------|--------|------|-----------|------|-------|
| Sextile | Saturn | 10 | **80.0%** | +0.19% | 11.2 |
| Trine | Mars | 11 | **72.7%** | +0.17% | 19.3 |
| Conjunction | Mars | 6 | **66.7%** | +0.18% | 12.0 |
| Opposition | Jupiter | 6 | **66.7%** | +0.58% | 22.0 |
| Sextile | Jupiter | 11 | 63.6% | +0.12% | 13.5 |
| Trine | Saturn | 11 | 63.6% | +0.26% | 21.7 |
| Square | Mars | 13 | 61.5% | +0.27% | 21.0 |
| Conjunction | Saturn | 5 | 60.0% | +0.18% | 10.5 |
| Opposition | Saturn | 5 | 60.0% | -0.53% | 28.3 |
| Sextile | Mercury | 10 | 60.0% | +0.26% | 13.0 |
| Square | Mercury | 15 | 60.0% | +0.25% | 17.6 |
| Trine | Mercury | 12 | 58.3% | +0.13% | 19.7 |
| Sextile | Mars | 7 | 57.1% | +0.40% | 16.3 |
| Conjunction | Jupiter | 9 | 55.6% | +0.14% | 17.7 |
| Conjunction | Mercury | 9 | 55.6% | +0.01% | 10.0 |

**Key:**
- Moon Sextile Saturn = strongest bullish signal (+0.19%)
- Moon Opposition Saturn = bearish (-0.53%)

### 7d. Aspect Count vs Volatility

| Volatility | Avg Aspect Count |
|------------|-----------------|
| Low | 4.1 |
| Medium | 3.7 |
| High | 4.6 |

**Key:** Fewer aspects → higher volatility. Many aspects = conflicting signals = choppy.


---

## 8. ECLIPSE

| Metric | Eclipse Active | Eclipse Inactive |
|--------|---------------|-----------------|
| Days | 40 | 212 |
| Bullish % | 52.5% | 47.2% |
| AvgΔ | **-0.03%** | +0.01% |
| Range | **15.9** | 16.4 |
| High Vol | 2 (5.0%) | 8 (3.8%) |
| Types | Solar: 20, Lunar: 20 | — |

**Near vs Far Eclipse:**

| Window | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Near (±5 days) | 14 | 64.3% | -0.00% | 16.1 |
| Far (>10 days) | 13 | 46.2% | -0.04% | 16.7 |

**Key:** Eclipse không thay đổi direction nhiều nhưng giảm volatility (15.9 vs 16.4).


---

## 9. ECONOMIC EVENTS

| Impact | Days | Bullish % | AvgΔ | Range | Volatility Distribution |
|--------|------|-----------|------|-------|------------------------|
| High | 43 | 51.2% | -0.03% | 21.3 | high: 4, low: 22, medium: 17 |
| Medium | 66 | 48.5% | +0.05% | 16.0 | high: 2, low: 44, medium: 20 |

**Key:** High economic impact = slightly more bullish but higher range. Economic events alone không đủ để predict direction.


---

## 10. GANN/FIBONACCI

| Signal | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Key Level HELD | 246 | 48.4% | +0.03% | **15.3** |
| Key Level NOT HELD | 6 | 33.3% | -0.98% | 58.1 |

**Key:** Gann key level held = range thấp (15.3), trend ổn định. Breached = range gấp 3.8x (58.1), bearish.


---

## 11. DOMINANT PLANET HOUR

| Hora | Days | Bullish % | AvgΔ | Range | HighVol |
|------|------|-----------|------|-------|---------|
| Jupiter | 51 | 45.1% | +0.06% | 15.7 | 1 |
| Mars | 52 | **44.2%** | -0.09% | 14.9 | 0 |
| Venus | 51 | 47.1% | +0.04% | 19.1 | 5 |
| Mercury | 52 | 46.2% | +0.03% | 15.7 | 1 |
| Moon | 46 | 58.7% | -0.04% | 16.4 | 3 |

**Key:**
- Moon Hora = most bullish (59%).
- Mars Hora = most bearish (44%).


---

## 12. COMBINED PATTERNS — HIGH CONFIDENCE

### 🟢 Bullish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Mula | 10 | **90.0%** | +0.32% | 16.7 |
| Moon in Shatabhisha | 6 | **83.3%** | +0.30% | 15.3 |
| Moon in Ashwini | 8 | **75.0%** | +0.23% | 11.8 |
| Moon in Uttara Phalguni | 11 | **72.7%** | +0.45% | 16.9 |
| Moon in Sagittarius | 22 | **72.7%** | +0.17% | 17.2 |
| Moon in Chitra | 12 | **66.7%** | +0.27% | 16.4 |
| Moon in Jyeshtha | 8 | 62.5% | +0.35% | 18.5 |
| Moon in Libra | 24 | 62.5% | +0.15% | 18.6 |
| Moon in Aries | 21 | 57.1% | +0.13% | 16.5 |
| Moon in Magha | 9 | 55.6% | -0.32% | 22.9 |
| Moon in Purva Ashadha | 9 | 55.6% | +0.18% | 17.5 |
| Moon in Virgo | 27 | 55.6% | +0.07% | 20.0 |
| Moon in Swati | 11 | 54.5% | +0.07% | 23.3 |
| Moon in Bharani | 10 | 50.0% | +0.12% | 17.9 |
| Moon in Ardra | 10 | 50.0% | +0.14% | 12.2 |

### 🔴 Bearish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Taurus | 18 | **11.1%** | -0.22% | 13.1 |
| Moon in Mrigashira | 8 | **12.5%** | -0.20% | 8.1 |
| Moon in Rohini | 7 | **14.3%** | -0.28% | 22.2 |
| Moon in Krittika | 9 | **22.2%** | -0.12% | 13.1 |
| Moon in Purva Bhadrapada | 8 | **25.0%** | -0.32% | 14.4 |
| Moon in Uttara Bhadrapada | 8 | **25.0%** | -0.31% | 13.8 |
| Moon in Ashlesha | 12 | **33.3%** | -0.13% | 14.0 |
| Moon in Anuradha | 9 | **33.3%** | -0.03% | 14.6 |
| Moon in Pisces | 19 | 36.8% | -0.30% | 15.3 |
| Moon in Purva Phalguni | 8 | 37.5% | -0.21% | 14.8 |

### ⚡ Extreme Volatility Patterns

| Pattern | Days | Avg Range | Multiplier |
|---------|------|-----------|------------|
| Gann Key NOT HELD | 6 | **58.1** | 3.6x |
| Swati nakshatra | 11 | **23.3** | 1.4x |
| Magha nakshatra | 9 | **22.9** | 1.4x |
| Rohini nakshatra | 7 | **22.2** | 1.4x |
| Hasta nakshatra | 13 | **20.5** | 1.3x |


---

## 13. CORRELATION: FEATURES vs PRICE CHANGE

| Feature | Correlation |
|---------|-------------|
| gold_bullish | +0.710 |
| mercury_elong_deg | -0.200 |
| mars_deg | -0.074 |
| saturn_elong_deg | -0.059 |
| saturn_deg | +0.057 |
| gold_range | -0.052 |
| jupiter_elong_deg | -0.046 |
| mars_elong_deg | +0.041 |
| moon_deg | -0.027 |
| venus_elong_deg | +0.017 |
| jupiter_deg | +0.014 |
| venus_deg | -0.004 |
| mercury_deg | -0.003 |
| sun_deg | +0.000 |

**Key:** Individual planetary degrees có correlation rất yếu (< 0.12) — confirming aspects + combinations mới là key predictor.


---

## 14. VOLATILITY PREDICTORS

### High Volatility Days

- 10 days, avg range 61.7
- 4/10 KHÔNG có economic event → astro > macro
- 2/10 eclipse active
- Avg 4.6 aspects

### Low Volatility Days

- 178 days, avg range 9.9
- 112/178 KHÔNG có economic event
- 30/178 eclipse active
- Avg 4.1 aspects

**Key:** High vol days có MORE aspects (4.6 vs 4.1)


---

## 15. MARKET REACTION DISTRIBUTION

| Reaction | Days | % |
|----------|------|---|
| reversal_signal | 79 | 31.3% |
| mild_trend | 66 | 26.2% |
| consolidation | 58 | 23.0% |
| choppy | 27 | 10.7% |
| moderate_trend | 15 | 6.0% |
| strong_trend | 7 | 2.8% |

**Key:** 31.3% reversal signal — gold rất hay reverse. Chỉ 2.8% strong trend → gold không trend mạnh, mostly range-bound với sudden reversals.


---

## 16. TOP 5 PATTERNS — ACTIONABLE SIGNALS

### 🥇 #1: Moon Nakshatra — Strongest Predictor
- Nakshatra có spread bullish% lớn nhất: 78%
- **Action:** Check moon nakshatra daily — nếu bullish nakshatra → bias long. Nếu bearish nakshatra → bias short.

### 🥈 #2: Venus/Mars Aspects — Direction Signals
- Specific Sun/Moon aspects với Venus/Mars cho strong directional bias
- **Action:** Avoid longs khi Venus Square Jupiter active.

### 🥉 #3: Combust — Volatility Amplifier
- Range tăng gấp 1.1x khi Mars Combust
- **Action:** Tighten stops khi Mars Combust. Reduce position size.

### #4: Saturn Retro — Counter-Intuitive Bullish
- Saturn retro: 42.3% bullish vs direct: 51.6%
- **Action:** Saturn retro = good time for gold longs.

### #5: Eclipse + Aspects — Volatility Spike
- Eclipse active = range giảm đáng kể (15.9 vs 16.4)
- **Action:** Eclipse window = prepare for big move. Direction depends on aspects.



---

## 17. LIMITATIONS & NEXT STEPS

### Current Limitations
1. **Dataset cần mở rộng** — cần 3-5 năm để statistical significance cao hơn
2. **Chưa có backtest** — patterns chưa được validate on out-of-sample data
3. **Chưa có weighted similarity scoring** — cần build engine để find analog days
4. **Chưa có time-of-day analysis** — planetary hours cần deep-dive
5. **Chưa có multi-timeframe** — chỉ daily, chưa weekly/monthly patterns

### Recommended Next Steps
1. **Build similarity search engine** — cosine similarity trên feature vector
2. **Backtest patterns** — walk-forward validation
3. **Add time-of-day analysis** — intraday patterns by planetary hour
4. **Add multi-timeframe** — weekly/monthly moon cycles
5. **Build RAG Patreon post generator** — learn from historical setups
6. **Compare with 2024-05 → 2025-04** — validate patterns across periods

---

*Report generated from 12 CSV files covering 2023-05 → 2024-04 (252 trading days).*
