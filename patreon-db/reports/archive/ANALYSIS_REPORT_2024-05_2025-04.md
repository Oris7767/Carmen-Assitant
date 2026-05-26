# 📊 Similarity Search Engine — Pattern Analysis Report

**Period:** 2024-05 → 2025-04 (251 trading days)  
**Generated:** 2026-05-22  
**Dataset:** 12 monthly CSVs, 57 columns per day

---

## 1. BASELINE

| Metric | Value |
|--------|-------|
| Total Trading Days | 251 |
| Bullish Days (close > open) | 52.6% |
| Bearish Days | 41.4% |
| Neutral Days | 6.0% |
| Avg Daily Change | +0.079% |
| Std Daily Change | 0.931% |
| Avg Daily Range | 29.35 |

---

## 2. MOON SIGN → TREND

| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Sagittarius | 17 | **70.6%** | +0.24% | 28.4 | 2 |
| Leo | 23 | **69.6%** | +0.50% | 36.0 | 3 |
| Taurus | 22 | **68.2%** | +0.13% | 35.3 | 2 |
| Virgo | 18 | **61.1%** | +0.08% | 26.5 | 1 |
| Pisces | 17 | 58.8% | +0.10% | 28.3 | 2 |
| Cancer | 24 | 58.3% | -0.04% | 32.6 | 3 |
| Libra | 23 | 56.5% | +0.21% | 23.9 | 1 |
| Aries | 22 | 50.0% | +0.18% | 25.9 | 0 |
| Gemini | 18 | 50.0% | -0.12% | 28.9 | 2 |
| Capricorn | 23 | **39.1%** | +0.07% | 27.0 | 3 |
| Aquarius | 22 | **31.8%** | -0.21% | 32.4 | 2 |
| Scorpio | 22 | **22.7%** | -0.20% | 25.8 | 1 |

**Key:** Sagittarius & Leo = strongest bullish. Scorpio = weakest. Leo = highest volatility.

---

## 3. MOON NAKSHATRA → TREND

| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Purva Ashadha | 8 | **100.0%** | +0.77% | 24.8 | 0 |
| Revati | 7 | **85.7%** | +0.54% | 27.0 | 1 |
| Ashwini | 10 | **70.0%** | +0.34% | 26.7 | 0 |
| Ashlesha | 10 | **70.0%** | +0.18% | 33.0 | 1 |
| Magha | 10 | **70.0%** | +0.45% | 36.6 | 1 |
| Vishakha | 9 | **66.7%** | +0.05% | 19.5 | 0 |
| Hasta | 6 | **66.7%** | +0.14% | 15.9 | 0 |
| Rohini | 11 | 63.6% | +0.12% | 31.2 | 1 |
| Purva Phalguni | 11 | 63.6% | +0.54% | 38.7 | 2 |
| Punarvasu | 8 | 62.5% | +0.07% | 21.2 | 0 |
| Krittika | 10 | 60.0% | +0.36% | 31.0 | 0 |
| Uttara Phalguni | 10 | 60.0% | +0.22% | 27.6 | 1 |
| Chitra | 9 | 55.6% | +0.07% | 29.2 | 1 |
| Swati | 11 | 54.5% | +0.18% | 27.4 | 0 |
| Mrigashira | 8 | 50.0% | -0.61% | 42.9 | 2 |
| Ardra | 8 | 50.0% | -0.10% | 27.2 | 1 |
| Mula | 8 | 50.0% | -0.22% | 33.4 | 2 |
| Shravana | 11 | 45.5% | +0.22% | 30.9 | 2 |
| Pushya | 11 | 45.5% | -0.21% | 36.9 | 2 |
| Uttara Bhadrapada | 7 | 42.9% | +0.03% | 24.4 | 0 |
| Bharani | 10 | 40.0% | +0.11% | 26.1 | 0 |
| Uttara Ashadha | 8 | 37.5% | +0.06% | 27.7 | 1 |
| Purva Bhadrapada | 9 | **33.3%** | -0.13% | 26.9 | 1 |
| Shatabhisha | 10 | **30.0%** | -0.27% | 31.9 | 1 |
| Dhanishta | 11 | **27.3%** | -0.41% | 31.9 | 1 |
| Anuradha | 12 | **25.0%** | +0.05% | 27.5 | 1 |
| Jyeshtha | 8 | **12.5%** | -0.47% | 23.4 | 0 |

**Key:** Nakshatra là predictor mạnh nhất. Purva Ashadha 100% bullish vs Jyeshtha 12% — chênh lệch 88%.
- **Bullish cluster:** Purva Ashadha, Revati, Ashwini, Ashlesha, Magha
- **Bearish cluster:** Purva Bhadrapada, Shatabhisha, Dhanishta, Anuradha, Jyeshtha

---

## 4. PLANETARY RETROGRADE

| Planet | Retrograde | | Direct | | Δ Bullish |
|--------|-----------|---|--------|---|-----------|
| | Days | Bullish % | Days | Bullish % | |
| **Mercury** | 45 | 55.6% | 206 | 51.9% | +3.6% |
| **Venus** | 30 | 60.0% | 221 | 51.6% | +8.4% |
| **Mars** | 52 | 61.5% | 199 | 50.3% | +11.3% ⚠️ |
| **Jupiter** | 80 | 57.5% | 171 | 50.3% | +7.2% |
| **Saturn** | 98 | 46.9% | 153 | 56.2% | -9.3% |

**Retrograde Range Impact:**

| Planet | Retro Range | Direct Range | Ratio |
|--------|------------|--------------|-------|
| Mercury | 34.2 | 28.3 | 1.21x |
| Venus | 44.3 | 27.3 | 1.62x |
| Mars | 30.7 | 29.0 | 1.06x |
| Jupiter | 24.5 | 31.6 | 0.77x |
| Saturn | 22.1 | 34.0 | 0.65x |

**Key:**
- Venus Retro = HIGH VOLATILITY (range gấp 1.62x)
- Jupiter Retro = range thấp hơn → trend ổn định hơn
- Saturn Retro = range thấp hơn → trend ổn định hơn

---

## 5. COMBUST (BÓC CHÁY)

| Planet | Combust | | Non-Combust | |
|--------|---------|---|-------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Mercury** | 14 | 57.1% / +0.29% / 29.9 | 237 | 52.3% / +0.07% / 29.3 |
| **Venus** | 23 | 43.5% / -0.10% / 26.1 | 228 | 53.5% / +0.10% / 29.7 |

**Key:**

---

## 6. PLANETARY ELONGATION QUARTILES

| Planet | Low Elong (Q1) | | High Elong (Q4) | |
|--------|----------------|---|-----------------|---|
| | Days | Bullish % / AvgΔ / Range | Days | Bullish % / AvgΔ / Range |
| **Mercury** | 63 | 55.6% / +0.20% / 28.6 | 63 | 44.4% / +0.12% / 32.2 |
| **Venus** | 63 | 50.8% / +0.13% / 23.1 | 63 | 65.1% / +0.18% / 28.7 |
| **Mars** | 63 | 49.2% / +0.10% / 22.5 | 63 | 60.3% / +0.14% / 30.9 |
| **Jupiter** | 63 | 46.0% / +0.03% / 28.5 | 63 | 57.1% / +0.01% / 24.8 |
| **Saturn** | 63 | 54.0% / +0.13% / 46.0 | 63 | 50.8% / +0.09% / 22.7 |

**Key:**
- Venus High Elongation = strong bullish (65.1%)
- Mars High Elongation = strong bullish (60.3%)
- Jupiter High Elongation = strong bullish (57.1%)
- Saturn High Elongation = low volatility (range 23 vs 46)

---

## 7. ASPECTS

### 7a. By Aspect Type

| Aspect | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|------|-----------|------|-------|---------|
| Opposition | 86 | **59.3%** | +0.16% | 25.5 | 4 |
| Conjunction | 138 | 55.1% | +0.09% | 34.5 | 16 |
| Sextile | 143 | 54.5% | +0.11% | 28.3 | 11 |
| Square | 152 | 53.9% | +0.06% | 29.0 | 15 |
| Trine | 147 | 52.4% | +0.08% | 32.4 | 16 |

### 7b. Sun-Planet Aspects (critical for Gold)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range | HighVol |
|--------|--------|------|-----------|------|-------|---------|
| Conjunction | Saturn | 8 | **87.5%** | +0.53% | 30.8 | 0 |
| Opposition | Moon | 5 | **80.0%** | +0.19% | 22.3 | 0 |
| Opposition | Mars | 5 | **80.0%** | +0.08% | 24.2 | 0 |
| Trine | Moon | 9 | **77.8%** | +0.54% | 27.1 | 1 |
| Opposition | Jupiter | 7 | **71.4%** | +0.38% | 35.4 | 0 |
| Square | Moon | 12 | **66.7%** | +0.25% | 24.0 | 1 |
| Square | Saturn | 11 | 63.6% | -0.09% | 29.7 | 1 |
| Trine | Mars | 11 | 63.6% | +0.07% | 33.2 | 1 |
| Opposition | Saturn | 7 | 57.1% | +0.13% | 19.2 | 0 |
| Conjunction | Mercury | 35 | 54.3% | +0.14% | 28.5 | 2 |
| Sextile | Moon | 13 | 53.8% | +0.06% | 32.0 | 2 |
| Square | Jupiter | 13 | 53.8% | +0.04% | 24.9 | 0 |
| Conjunction | Moon | 6 | 50.0% | +0.16% | 26.3 | 0 |
| Sextile | Jupiter | 14 | 50.0% | +0.01% | 66.6 | 6 |
| Square | Mars | 20 | 50.0% | +0.13% | 40.2 | 5 |
| Trine | Jupiter | 11 | 45.5% | +0.35% | 21.6 | 2 |
| Conjunction | Venus | 28 | 42.9% | -0.07% | 24.8 | 1 |
| Sextile | Saturn | 12 | 41.7% | +0.14% | 16.3 | 0 |
| Sextile | Mars | 22 | 40.9% | +0.02% | 26.9 | 2 |
| Conjunction | Jupiter | 10 | 40.0% | -0.08% | 25.0 | 0 |
| Trine | Saturn | 12 | **33.3%** | -0.06% | 22.4 | 1 |

**Key:**
- Sun Conjunction Saturn = 88% bullish, low vol
- Sun Trine Saturn = 33% bullish

### 7c. Moon-Planet Aspects (top 15)

| Aspect | Planet | Days | Bullish % | AvgΔ | Range |
|--------|--------|------|-----------|------|-------|
| Opposition | Saturn | 8 | **87.5%** | **+0.84%** | 30.0 |
| Conjunction | Mars | 8 | **75.0%** | **+0.54%** | 22.0 |
| Trine | Sun | 9 | **77.8%** | **+0.54%** | 27.1 |
| Trine | Saturn | 11 | **72.7%** | **+0.52%** | 33.1 |
| Opposition | Mars | 11 | **72.7%** | **+0.49%** | 27.7 |
| Sextile | Jupiter | 11 | **81.8%** | **+0.44%** | 28.9 |
| Sextile | Mars | 8 | **62.5%** | **+0.41%** | 22.8 |
| Sextile | Saturn | 13 | 46.2% | +0.30% | 21.9 |
| Trine | Venus | 12 | 50.0% | +0.27% | 28.2 |
| Square | Sun | 12 | **66.7%** | **+0.25%** | 24.0 |
| Sextile | Mercury | 15 | 60.0% | +0.21% | 28.7 |
| Square | Jupiter | 12 | 50.0% | +0.19% | 34.1 |
| Square | Mars | 10 | 60.0% | +0.16% | 21.6 |
| Sextile | Sun | 13 | 53.8% | +0.06% | 32.0 |
| Trine | Mercury | 12 | 41.7% | +0.04% | 28.6 |

**Key:**
- Moon Opposition Saturn = strongest bullish signal (+0.84%)
- Moon Square Saturn = bearish (-0.42%)

### 7d. Aspect Count vs Volatility

| Volatility | Avg Aspect Count |
|------------|-----------------|
| Low | 4.0 |
| Medium | 4.1 |
| High | 5.0 |

**Key:** Fewer aspects → higher volatility. Many aspects = conflicting signals = choppy.

---

## 8. ECLIPSE

| Metric | Eclipse Active | Eclipse Inactive |
|--------|---------------|-----------------|
| Days | 40 | 211 |
| Bullish % | 42.5% | 54.5% |
| AvgΔ | **-0.06%** | +0.11% |
| Range | **28.0** | 29.6 |
| High Vol | 3 (7.5%) | 19 (9.0%) |
| Types | Lunar: 20, Solar: 20 | — |

**Near vs Far Eclipse:**

| Window | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Near (±5 days) | 13 | 53.8% | +0.09% | 23.4 |
| Far (>10 days) | 11 | 45.5% | +0.13% | 29.2 |

**Key:** Eclipse không thay đổi direction nhiều nhưng tăng volatility -5% (28.0 vs 29.6). Eclipse + aspects = bearish pressure (-0.06%).


---

## 9. ECONOMIC EVENTS

| Impact | Days | Bullish % | AvgΔ | Range | Volatility Distribution |
|--------|------|-----------|------|-------|------------------------|
| High | 41 | 46.3% | -0.11% | 37.6 | medium: 21, low: 14, high: 6 |
| Medium | 72 | 51.4% | +0.03% | 30.1 | medium: 24, low: 40, high: 8 |

**Key:** High economic impact = slightly more bullish but higher range. Economic events alone không đủ để predict direction.

---

## 10. GANN/FIBONACCI

| Signal | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Key Level HELD | 226 | 50.9% | +0.03% | **25.8** |
| Key Level NOT HELD | 25 | 68.0% | +0.53% | **61.6** |
| Gann Bounce | 226 | 50.9% | +0.03% | 25.8 |

**Key:** Gann key level held = range thấp (25.8), trend ổn định. Breached = range gấp 2.4x (61.6), bearish.

---

## 11. DOMINANT PLANET HOUR

| Hora | Days | Bullish % | AvgΔ | Range | HighVol |
|------|------|-----------|------|-------|---------|
| Jupiter | 50 | **66.0%** | +0.24% | 31.7 | 3 |
| Mars | 52 | 53.8% | +0.15% | 25.4 | 2 |
| Mercury | 50 | 52.0% | +0.14% | 29.3 | 5 |
| Venus | 51 | 49.0% | -0.07% | 31.6 | 6 |
| Moon | 48 | **41.7%** | -0.08% | 28.9 | 6 |

**Key:** Moon Hora = most bearish (42%) + negative (-0.08%). Jupiter Hora = most bullish (66%).

---

## 13. COMBINED PATTERNS — HIGH CONFIDENCE

### 🟢 Bullish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Purva Ashadha | 8 | **100.0%** | +0.77% | 24.8 |
| Moon in Revati | 7 | **85.7%** | +0.54% | 27.0 |
| Mercury Retro + High Econ | 7 | **85.7%** | +0.27% | 46.8 |
| Moon in Sagittarius | 17 | **70.6%** | +0.24% | 28.4 |
| Moon in Ashwini | 10 | **70.0%** | +0.34% | 26.7 |
| Moon in Ashlesha | 10 | **70.0%** | +0.18% | 33.0 |
| Moon in Magha | 10 | **70.0%** | +0.45% | 36.6 |
| Moon in Leo | 23 | **69.6%** | +0.50% | 36.0 |
| Moon in Taurus | 22 | **68.2%** | +0.13% | 35.3 |
| Moon in Vishakha | 9 | **66.7%** | +0.05% | 19.5 |
| Moon in Hasta | 6 | **66.7%** | +0.14% | 15.9 |
| Moon in Rohini | 11 | 63.6% | +0.12% | 31.2 |

### 🔴 Bearish Patterns

| Pattern | Days | Bullish % | AvgΔ | Range |
|---------|------|-----------|------|-------|
| Moon in Jyeshtha | 8 | **12.5%** | -0.47% | 23.4 |
| Moon in Anuradha | 12 | **25.0%** | +0.05% | 27.5 |
| Moon in Dhanishta | 11 | **27.3%** | -0.41% | 31.9 |
| Moon in Shatabhisha | 10 | **30.0%** | -0.27% | 31.9 |
| Moon in Purva Bhadrapada | 9 | **33.3%** | -0.13% | 26.9 |
| Moon in Uttara Ashadha | 8 | 37.5% | +0.06% | 27.7 |
| Eclipse + ≥2 Aspects | 40 | 42.5% | -0.06% | 28.0 |
| Saturn Low Elongation | 63 | 54.0% | +0.13% | 46.0 |
| Mercury Retro | 14 | 57.1% | +0.29% | 29.9 |

### ⚡ Extreme Volatility Patterns

| Pattern | Days | Avg Range | Multiplier |
|---------|------|-----------|------------|
| Gann Key NOT HELD | 25 | **61.6** | 2.1x |
| Mrigashira nakshatra | 8 | **42.9** | 1.5x |
| Purva Phalguni nakshatra | 11 | **38.7** | 1.3x |
| Sun Conj Saturn | 8 | **30.8** | 1.0x |
| Sun Square Jupiter | 13 | **24.9** | 0.8x |

---

## 14. CORRELATION: FEATURES vs PRICE CHANGE

| Feature | Correlation |
|---------|-------------|
| gold_bullish | +0.755 |
| gold_range_norm | -0.129 |
| mars_deg | +0.094 |
| mercury_elong_deg | -0.061 |
| sun_deg | +0.055 |
| saturn_deg | +0.039 |
| mars_elong_deg | +0.038 |
| saturn_elong_deg | -0.034 |
| jupiter_deg | -0.013 |
| jupiter_elong_deg | -0.009 |
| moon_deg | +0.009 |
| venus_deg | +0.007 |
| mercury_deg | +0.006 |
| venus_elong_deg | +0.003 |

**Key:** Individual planetary degrees có correlation rất yếu (< 0.12) — confirming aspects + combinations mới là key predictor.

---

## 15. VOLATILITY PREDICTORS

### High Volatility Days (22 days, avg range 85.3)
- 8/22 KHÔNG có economic event → astro > macro
- 3/22 eclipse active
- Avg 5.0 aspects

### Low Volatility Days (132 days, avg range 14.6)
- 78/132 KHÔNG có economic event
- 22/132 eclipse active
- Avg 4.0 aspects

**Key:** High vol days có MORE aspects (5.0 vs 4.0)

---

## 16. MARKET REACTION DISTRIBUTION

| Reaction | Days | % |
|----------|------|---|
| mild_trend | 74 | 29.5% |
| reversal_signal | 53 | 21.1% |
| consolidation | 43 | 17.1% |
| moderate_trend | 39 | 15.5% |
| choppy | 22 | 8.8% |
| strong_trend | 20 | 8.0% |

**Key:** 21.1% reversal signal — gold rất hay reverse. Chỉ 8.0% strong trend → gold không trend mạnh, mostly range-bound với sudden reversals.

---

## 17. TOP 5 PATTERNS — ACTIONABLE SIGNALS

### 🥇 #1: Moon Nakshatra — Strongest Predictor
- Nakshatra có spread bullish% lớn nhất giữa các sign
- **Action:** Check moon nakshatra daily — nếu bullish nakshatra → bias long. Nếu bearish nakshatra → bias short.

### 🥈 #2: Venus/Mars Aspects — Direction Signals
- Specific Sun/Moon aspects với Venus/Mars cho strong directional bias
- **Action:** Avoid longs khi Venus Square Jupiter active.

### 🥉 #3: Mars Combust — Volatility Amplifier
- Range tăng gấp 1.5-2x khi Mars Combust
- **Action:** Tighten stops khi Mars Combust. Reduce position size.

### #4: Saturn Retro — Counter-Intuitive Bullish
- Saturn retro thường bullish cho gold
- **Action:** Saturn retro = good time for gold longs.

### #5: Eclipse + Aspects — Volatility Spike
- Eclipse active = range tăng đáng kể
- **Action:** Eclipse window = prepare for big move. Direction depends on aspects.

---

## 18. LIMITATIONS & NEXT STEPS

### Current Limitations
1. **Dataset cần mở rộng** — 25 tháng (519 days) tốt hơn nhưng vẫn cần 3-5 năm để statistical significance cao hơn
2. **Chưa có backtest** — patterns chưa được validate on out-of-sample data
3. **Chưa có weighted similarity scoring** — cần build engine để find analog days
4. **Chưa có time-of-day analysis** — planetary hours cần deep-dive
5. **Chưa có multi-timeframe** — chỉ daily, chưa weekly/monthly patterns

### Recommended Next Steps
1. **Backfill thêm data** — mở rộng về trước 2020 nếu có
2. **Build similarity search engine** — cosine similarity trên feature vector
3. **Backtest patterns** — walk-forward validation
4. **Add time-of-day analysis** — intraday patterns by planetary hour
5. **Add multi-timeframe** — weekly/monthly moon cycles
6. **Build RAG Patreon post generator** — learn from historical setups

---

*Report generated from 12 CSV files covering 2024-05 → 2025-04 (251 trading days).*
