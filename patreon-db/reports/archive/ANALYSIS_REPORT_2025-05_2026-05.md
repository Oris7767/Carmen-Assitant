# 📊 Similarity Search Engine — Pattern Analysis Report

**Period:** May 2025 → May 2026 (268 trading days)  
**Generated:** 2026-05-22  
**Dataset:** 13 monthly CSVs, 57 columns per day

---

## 1. BASELINE

| Metric | Value |
|--------|-------|
| Total Trading Days | 268 |
| Bullish Days (close > open) | 53.0% |
| Bearish Days | 43.3% |
| Neutral Days | 3.7% |
| Avg Daily Change | +0.013% |
| Std Daily Change | 1.468% |
| Avg Daily Range | 65.72 |

---

## 2. MOON SIGN → TREND

| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Sagittarius | 24 | **70.8%** | +0.46% | 53.6 | 3 |
| Scorpio | 27 | **66.7%** | +0.06% | 52.6 | 3 |
| Cancer | 21 | 57.1% | +0.14% | 72.0 | 5 |
| Taurus | 22 | 54.5% | +0.11% | 73.7 | 2 |
| Pisces | 21 | 52.4% | -0.17% | 55.8 | 3 |
| Libra | 21 | 52.4% | +0.10% | 53.7 | 3 |
| Gemini | 24 | 50.0% | -0.46% | 74.8 | 4 |
| Virgo | 26 | 50.0% | -0.26% | **91.4** | 9 |
| Aquarius | 23 | 43.5% | +0.07% | 53.4 | 5 |
| Capricorn | 19 | 47.4% | +0.07% | 52.7 | 5 |
| Leo | 24 | 45.8% | +0.07% | 95.6 | 10 |
| Aries | 16 | **37.5%** | -0.01% | 48.7 | 1 |

**Key:** Sagittarius & Scorpio = strongest bullish. Aries = weakest. Virgo & Leo = highest volatility.

---

## 3. MOON NAKSHATRA → TREND

| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Anuradha | 12 | **83.3%** | +0.21% | 53.1 | 0 |
| Purva Ashadha | 11 | **72.7%** | +0.37% | 43.3 | 1 |
| Vishakha | 10 | **70.0%** | +0.26% | 46.6 | 0 |
| Mula | 12 | **66.7%** | +0.45% | 61.0 | 2 |
| Ashlesha | 10 | **70.0%** | +0.29% | **105.2** | 5 |
| Shravana | 8 | **62.5%** | +0.65% | 50.2 | 2 |
| Rohini | 9 | **66.7%** | +0.16% | 97.1 | 1 |
| Shatabhisha | 11 | **54.5%** | +0.46% | 61.7 | 4 |
| Hasta | 13 | 53.8% | +0.15% | 90.7 | 4 |
| Revati | 11 | 54.5% | -0.04% | 53.5 | 2 |
| Ardra | 12 | 50.0% | -0.92% | **108.9** | 3 |
| Jyeshtha | 12 | 50.0% | -0.10% | 56.5 | 3 |
| Swati | 10 | 50.0% | +0.05% | 62.5 | 3 |
| Uttara Phalguni | 12 | 58.3% | -0.29% | 75.2 | 5 |
| Magha | 10 | 50.0% | +0.15% | **125.2** | 6 |
| Ashwini | 9 | 55.6% | +0.12% | 47.0 | 0 |
| Punarvasu | 9 | 55.6% | +0.07% | 36.3 | 0 |
| Pushya | 9 | 44.4% | +0.11% | 41.2 | 0 |
| Krittika | 8 | 50.0% | +0.10% | 86.3 | 1 |
| Purva Bhadrapada | 10 | 50.0% | -0.21% | 41.8 | 0 |
| Uttara Ashadha | 8 | 50.0% | +0.17% | 38.0 | 1 |
| Chitra | 8 | 37.5% | -0.57% | 72.5 | 1 |
| Uttara Bhadrapada | 8 | 37.5% | -0.48% | 65.8 | 1 |
| Dhanishta | 8 | **25.0%** | -0.51% | 70.1 | 3 |
| Purva Phalguni | 11 | **27.3%** | -0.10% | 81.8 | 3 |
| Mrigashira | 11 | **36.4%** | -0.15% | 35.1 | 1 |
| Bharani | 6 | **16.7%** | -0.19% | 46.2 | 1 |

**Key:** Nakshatra là predictor mạnh nhất. Anuradha 83% bullish vs Bharani 17% — chênh lệch 66%.
- **Bullish cluster:** Anuradha, Purva Ashadha, Vishakha, Mula, Ashlesha
- **Bearish cluster:** Bharani, Dhanishta, Purva Phalguni, Uttara Bhadrapada

---

## 4. PLANETARY RETROGRADE

| Planet | Retrograde | | Direct | | Δ Bullish |
|--------|-----------|---|--------|---|-----------|
| | Days | Bullish % | Days | Bullish % | |
| **Saturn** | 98 | **61.2%** | 170 | 48.2% | **+13.0% ⚠️** |
| **Mercury** | 46 | **43.5%** | 222 | 55.0% | **-11.5% ⚠️** |
| Jupiter | 81 | 51.9% | 187 | 53.5% | -1.6% |
| Venus | 0 | — | 268 | 53.0% | — |
| Mars | 0 | — | 268 | 53.0% | — |

**Retrograde Range Impact:**

| Planet | Retro Range | Direct Range | Ratio |
|--------|------------|--------------|-------|
| Jupiter | **90.7** | 54.9 | 1.65x |
| Saturn | 49.7 | **75.0** | 0.66x |
| Mercury | 67.5 | 65.4 | 1.03x |

**Key:**
- Saturn Retro = BULLISH cho gold, range thấp → trend ổn định
- Mercury Retro = BEARISH, volatility cao hơn
- Jupiter Retro = HIGH VOLATILITY (range gấp 1.65x)

---

## 5. COMBUST (BÓC CHÁY)

| Planet | Combust | | Non-Combust | |
|--------|---------|---|-------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Mercury** | 15 | 60.0% / +0.51% / 62.9 | 253 | 52.6% / -0.02% / 65.9 |
| **Venus** | 22 | 59.1% / +0.31% / **49.9** | 246 | 52.4% / -0.01% / 67.1 |
| **Mars** | 44 | 52.3% / -0.08% / **105.0** | 224 | 53.1% / +0.03% / 58.0 |

**Key:**
- Mars Combust = volatility amplifier mạnh nhất — range tăng 81% (105 vs 58)
- Venus Combust = LOW volatility — range chỉ 49.9
- Mercury Combust = mildly bullish (+0.51%)

---

## 6. PLANETARY ELONGATION QUARTILES

| Planet | Low Elong (Q1) | | High Elong (Q4) | |
|--------|----------------|---|-----------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Saturn** | 67 | 44.8% / -0.09% / 86.6 | 67 | **62.7%** / +0.18% / 52.3 |
| Venus | 67 | 56.7% / +0.05% / **88.5** | 67 | 53.7% / +0.03% / **43.1** |
| Mars | 67 | 53.7% / -0.03% / **94.4** | 67 | 53.7% / +0.03% / **43.1** |
| Jupiter | 67 | 53.7% / +0.01% / **41.4** | 67 | 55.2% / +0.04% / **91.0** |
| Mercury | 67 | 50.7% / -0.10% / 68.7 | 67 | 55.2% / -0.01% / 68.7 |

**Key:**
- Saturn High Elongation = strong bullish (62.7%)
- Venus/Mars High Elongation = low volatility (range 43)
- Jupiter High Elongation = high volatility (range 91)

---

## 7. ASPECTS

### 7a. By Aspect Type

| Aspect | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|------|-----------|------|-------|---------|
| Opposition | 99 | **60.0%** | +0.09% | 49.4 | 13 |
| Square | 202 | 55.0% | -0.06% | 59.1 | 34 |
| Trine | 282 | 56.0% | +0.08% | 64.2 | 57 |
| Sextile | 228 | 52.0% | +0.07% | 44.9 | 26 |
| Conjunction | 267 | 49.0% | -0.05% | 70.2 | 64 |

**Key:** Opposition = most bullish (60%). Conjunction = most bearish (49%) + highest volatility.

### 7b. Sun-Planet Aspects (critical for Gold)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|--------|------|-----------|------|-------|---------|
| Conjunction | Jupiter | 9 | **78.0%** | +0.04% | 36.6 | 0 |
| Square | Moon | 13 | **69.0%** | +0.27% | 67.3 | 4 |
| Square | Jupiter | 13 | **69.0%** | -0.15% | **117.9** | 7 |
| Square | Saturn | 11 | **73.0%** | +0.06% | 35.9 | 0 |
| Opposition | Jupiter | 6 | **67.0%** | +0.21% | 28.1 | 0 |
| Conjunction | Saturn | 8 | **62.0%** | +0.33% | **123.6** | 4 |
| Opposition | Moon | 8 | **62.0%** | -0.44% | **117.1** | 2 |
| Sextile | Mars | 14 | **64.0%** | +0.01% | 33.1 | 0 |
| Conjunction | Venus | 27 | **59.0%** | +0.30% | 45.0 | 3 |
| Sextile | Saturn | 11 | 55.0% | +0.20% | 47.1 | 3 |
| Sextile | Moon | 12 | 58.0% | +0.08% | 62.7 | 4 |
| Sextile | Jupiter | 15 | 47.0% | -0.04% | 37.4 | 0 |
| Trine | Saturn | 12 | 50.0% | -0.02% | 50.5 | 1 |
| Conjunction | Mars | 27 | 48.0% | -0.27% | 87.8 | 5 |
| Trine | Moon | 13 | 46.0% | -0.01% | 49.2 | 0 |
| Conjunction | Mercury | 40 | 45.0% | +0.07% | 48.4 | 8 |
| Trine | Jupiter | 12 | **33.0%** | -0.70% | 96.9 | 4 |
| Conjunction | Moon | 5 | 40.0% | -0.87% | 90.0 | 1 |

**Key:**
- Sun Conj Jupiter = 78% bullish, low vol (36.6 range) — strongest combo
- Sun Square Jupiter = 69% bullish nhưng HIGH VOL (117.9 range)
- Sun Trine Jupiter = 33% bullish, bearish (-0.70%) — surprising
- Sun Conj Saturn = high vol (123.6) but bullish

### 7c. Moon-Planet Aspects (top 15)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range |
|--------|--------|------|-----------|------|-------|
| Sextile | Jupiter | 13 | **61.5%** | **+0.76%** | 63.3 |
| Trine | Mars | 13 | 53.8% | +0.48% | 67.8 |
| Square | Sun | 13 | **69.0%** | +0.27% | 67.3 |
| Trine | Saturn | 16 | **62.0%** | +0.14% | 42.2 |
| Trine | Jupiter | 12 | 58.0% | +0.17% | 52.0 |
| Trine | Venus | 14 | 57.0% | +0.13% | **100.1** |
| Sextile | Sun | 12 | 58.0% | +0.08% | 62.7 |
| Trine | Mercury | 16 | 44.0% | +0.07% | 73.1 |
| Square | Mars | 11 | 55.0% | +0.03% | 56.2 |
| Square | Jupiter | 15 | 53.0% | -0.53% | 74.7 |
| Square | Saturn | 17 | 53.0% | -0.49% | 96.0 |
| Sextile | Mercury | 13 | 38.0% | -0.32% | 42.0 |
| Opposition | Saturn | 11 | 45.0% | -0.57% | 73.7 |
| Sextile | Venus | 12 | 42.0% | -0.06% | 51.9 |
| Trine | Sun | 13 | 46.0% | -0.01% | 49.2 |

**Key:**
- Moon Sextile Jupiter = strongest bullish signal (+0.76%)
- Moon Opposition Saturn = bearish (-0.57%)
- Moon Square Saturn = bearish (-0.49%), high vol (96.0)

### 7d. Aspect Count vs Volatility

| Volatility | Avg Aspect Count |
|------------|-----------------|
| Low | 4.3 |
| Medium | — |
| High | 3.7 |

**Key:** Fewer aspects → higher volatility. Many aspects = conflicting signals = choppy.

---

## 8. ECLIPSE

| Metric | Eclipse Active | Eclipse Inactive |
|--------|---------------|-----------------|
| Days | 43 | 225 |
| Bullish % | 53.5% | 52.9% |
| AvgΔ | **-0.25%** | +0.06% |
| Range | **92.6** | 60.6 |
| High Vol | 15 (34.9%) | 38 (16.9%) |
| Types | Lunar: 22, Solar: 21 | — |

**Near vs Far Eclipse:**

| Window | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Far (>10 days) | 13 | **61.5%** | +0.54% | 83.7 |
| Near (±5 days) | 242 | 52.5% | -0.02% | 64.9 |

**Key:** Eclipse không thay đổi direction nhiều nhưng tăng volatility 53% (92.6 vs 60.6). Eclipse + ≥2 aspects = bearish pressure mạnh (-0.47%).

---

## 9. ECONOMIC EVENTS

| Impact | Days | Bullish % | AvgΔ | Range | Volatility Distribution |
|--------|------|-----------|------|-------|------------------------|
| High | 43 | **58.1%** | +0.04% | 74.4 | medium: 21, low: 15, high: 7 |
| Medium | 75 | 53.3% | +0.13% | 61.7 | medium: 34, low: 29, high: 12 |

**Key:** High economic impact = slightly more bullish but higher range. Economic events alone không đủ để predict direction.

---

## 10. GANN/FIBONACCI

| Signal | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Key Level HELD | 173 | **55.5%** | +0.13% | **42.7** |
| Key Level NOT HELD | 95 | 48.4% | -0.20% | **107.7** |
| Gann Bounce | 173 | 55.5% | +0.13% | 42.7 |

**Key:** Gann key level held = range thấp (42.7), trend ổn định. Breached = range gấp 2.5x (107.7), bearish.

---

## 11. DOMINANT PLANET HOUR

| Hora | Days | Bullish % | AvgΔ | Range | HighVol |
|------|------|-----------|------|-------|---------|
| Venus | 55 | **60.0%** | -0.12% | 69.6 | 11 |
| Moon | 51 | **59.0%** | +0.27% | 72.1 | 10 |
| Mars | 55 | 53.0% | +0.06% | 64.3 | 9 |
| Mercury | 55 | 49.0% | +0.11% | 50.8 | 9 |
| Jupiter | 52 | 44.0% | -0.26% | 72.7 | 14 |

**Key:** Jupiter Hora = most bearish (44%) + highest volatility. Venus Hora = most bullish (60%).

---

## 12. DAY OF WEEK

| Day | Days | Bullish % | AvgΔ | Range |
|-----|------|-----------|------|-------|
| Friday | 55 | **60.0%** | -0.12% | 69.6 |
| Monday | 51 | **59.0%** | +0.27% | 72.1 |
| Tuesday | 55 | 53.0% | +0.06% | 64.3 |
| Wednesday | 55 | 49.0% | +0.11% | 50.8 |
| Thursday | 52 | 44.0% | -0.26% | 72.7 |

**Key:** Monday & Friday = bullish. Thursday = bearish.

---

## 13. COMBINED PATTERNS — HIGH CONFIDENCE

### 🟢 Bullish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Anuradha | 12 | **83.3%** | +0.21% | 53.2 |
| Mercury Retro + High Econ | 9 | **77.8%** | +0.71% | 69.2 |
| Venus Trine Jupiter | 8 | **75.0%** | +0.72% | 46.2 |
| Moon in Sagittarius | 24 | **70.8%** | +0.46% | 53.6 |
| Venus Combust | 22 | **59.1%** | +0.31% | 49.9 |
| Moon Sextile Jupiter | 13 | **61.5%** | +0.76% | 63.3 |
| Moon Trine Mars | 13 | 53.8% | +0.48% | 67.8 |
| Mercury Combust | 15 | **60.0%** | +0.51% | 62.9 |
| Jupiter High Elongation | 67 | 55.2% | +0.04% | 91.0 |
| Gann Bounce | 173 | 55.5% | +0.13% | 42.7 |
| Saturn Retro + Bullish | 60 | **100.0%** | +0.82% | 49.2 |

### 🔴 Bearish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Bharani | 6 | **16.7%** | -0.19% | 46.2 |
| Moon in Dhanishta | 8 | **25.0%** | -0.51% | 70.1 |
| Moon in Purva Phalguni | 11 | **27.3%** | -0.10% | 81.8 |
| Venus Square Jupiter | 10 | **20.0%** | **-1.01%** | 82.9 |
| Mercury Retro | 46 | **43.5%** | -0.21% | 67.5 |
| Jupiter Hora | 52 | **44.0%** | -0.26% | 72.7 |
| Saturn Low Elongation | 67 | **44.8%** | -0.09% | 86.6 |
| Mars Combust + High Vol | 12 | **41.7%** | -0.87% | **275.9** |
| Eclipse + ≥2 Aspects | 39 | 51.3% | -0.47% | 89.5 |
| Moon Square Saturn | 17 | 52.9% | -0.49% | 96.0 |

### ⚡ Extreme Volatility Patterns

| Pattern | Days | Avg Range | Multiplier |
|---------|------|-----------|------------|
| Mars Combust + High Vol | 12 | **275.9** | 4.2x |
| Mars Combust | 44 | **105.0** | 1.6x |
| Ardra nakshatra | 12 | **108.9** | 1.7x |
| Ashlesha nakshatra | 10 | **105.2** | 1.6x |
| Magha nakshatra | 10 | **125.2** | 1.9x |
| Gann Key NOT HELD | 95 | **107.7** | 1.6x |
| Sun Conj Saturn | 8 | **123.6** | 1.9x |
| Sun Square Jupiter | 13 | **117.9** | 1.8x |
| Sun Opposition Moon | 8 | **117.1** | 1.8x |

---

## 14. CORRELATION: FEATURES vs PRICE CHANGE

| Feature | Correlation |
|---------|-------------|
| gold_bullish | +0.640 |
| gold_range | -0.416 |
| saturn_elong_deg | +0.116 |
| saturn_deg | -0.052 |
| venus_deg | -0.042 |
| jupiter_elong_deg | -0.032 |
| mercury_deg | -0.030 |
| sun_deg | -0.026 |
| venus_elong_deg | +0.022 |
| mercury_elong_deg | +0.022 |
| mars_elong_deg | +0.017 |
| moon_deg | +0.013 |
| mars_deg | +0.007 |
| jupiter_deg | -0.002 |

**Key:** Individual planetary degrees có correlation rất yếu (< 0.12) — confirming aspects + combinations mới là key predictor.

---

## 15. VOLATILITY PREDICTORS

### High Volatility Days (53 days, avg range 164.3)
- 34/53 KHÔNG có economic event → astro > macro
- 15/53 eclipse active
- Avg 3.7 aspects
- Mars retro: 0 days
- Venus combust: 3 days

### Low Volatility Days (105 days, avg range 24.5)
- 61/105 KHÔNG có economic event
- 10/105 eclipse active
- Avg 4.3 aspects
- Venus combust: 12 days

**Key:** High vol days có FEWER aspects (3.7 vs 4.3) — conflicting aspects = choppy but not extreme vol. True volatility comes from Mars Combust + Eclipse + specific nakshatras.

---

## 16. MARKET REACTION DISTRIBUTION

| Reaction | Days | % |
|----------|------|---|
| reversal_signal | 74 | 27.6% |
| mild_trend | 61 | 22.8% |
| moderate_trend | 46 | 17.2% |
| strong_trend | 36 | 13.4% |
| consolidation | 32 | 11.9% |
| choppy | 19 | 7.1% |

**Key:** 27.6% reversal signal — gold rất hay reverse. Chỉ 13.4% strong trend → gold không trend mạnh, mostly range-bound với sudden reversals.

---

## 17. TOP 5 PATTERNS — ACTIONABLE SIGNALS

### 🥇 #1: Moon Nakshatra — Strongest Predictor
- Anuradha: 83.3% bullish
- Bharani: 16.7% bullish
- **Action:** Check moon nakshatra daily — nếu Anuradha/Purva Ashadha/Vishakha → bias bullish. Nếu Bharani/Dhanishta/Purva Phalguni → bias bearish.

### 🥈 #2: Venus Square Jupiter — Strong Bearish
- 20% bullish, avg -1.01%
- **Action:** Avoid longs khi Venus Square Jupiter active.

### 🥉 #3: Mars Combust — Volatility Amplifier
- Range 105 (gấp 2x bình thường)
- Mars Combust + High Vol = range 275.9 (4.2x!)
- **Action:** Tighten stops khi Mars Combust. Reduce position size.

### #4: Saturn Retro — Counter-Intuitive Bullish
- +13% delta bullish vs direct
- Range thấp (49.7) → trend ổn định
- **Action:** Saturn retro = good time for gold longs.

### #5: Eclipse + Aspects — Volatility Spike
- Eclipse active = range tăng 53%
- Eclipse + ≥2 aspects = bearish (-0.47%)
- **Action:** Eclipse window = prepare for big move. Direction depends on aspects.

---

## 18. LIMITATIONS & NEXT STEPS

### Current Limitations
1. **268 days chưa đủ** — cần ít nhất 3-5 năm (800-1200 days) để statistical significance
2. **Chưa có backtest** — patterns chưa được validate on out-of-sample data
3. **Chưa có weighted similarity scoring** — cần build engine để find analog days
4. **Chưa có time-of-day analysis** — planetary hours cần deep-dive
5. **Chưa có multi-timeframe** — chỉ daily, chưa weekly/monthly patterns

### Recommended Next Steps
1. **Backfill thêm 3-5 năm** data (2020-2025)
2. **Build similarity search engine** — cosine similarity trên feature vector
3. **Backtest patterns** — walk-forward validation
4. **Add time-of-day analysis** — intraday patterns by planetary hour
5. **Add multi-timeframe** — weekly/monthly moon cycles
6. **Build RAG Patreon post generator** — learn from historical setups

---

*Report generated from 13 CSV files covering May 2025 → May 2026 (268 trading days).*
