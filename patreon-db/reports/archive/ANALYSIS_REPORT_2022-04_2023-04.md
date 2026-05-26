# 📊 Phân Tích Dữ Liệu Gold (XAUUSD)

**Giai đoạn:** 2022-04 → 2023-04 (270 trading days)
**Generated:** 2026-05-22
**Dataset:** 13 monthly CSVs, 57 columns per day

---

## 1. BASELINE

| Metric | Value |
|--------|-------|
| Total Trading Days | 270 |
| Bullish Days (close > open) | 48.5% |
| Bearish Days | 51.5% |
| Neutral Days | 0.0% |
| Avg Daily Change | +0.005% |
| Std Daily Change | 0.802% |
| Avg Daily Range | 17.34 |

---

## 2. MOON SIGN → TREND

| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Sagittarius | 22 | **77.3%** | +0.42% | 20.4 | 2 |
| Libra | 17 | 58.8% | +0.29% | 18.0 | 1 |
| Leo | 25 | 56.0% | -0.01% | 17.1 | 3 |
| Aries | 21 | 52.4% | +0.00% | 14.7 | 2 |
| Taurus | 27 | 51.9% | +0.04% | 18.0 | 3 |
| Gemini | 29 | 51.7% | -0.00% | 17.2 | 2 |
| Cancer | 23 | 47.8% | +0.07% | 15.4 | 1 |
| Aquarius | 21 | 42.9% | +0.02% | 19.0 | 1 |
| Virgo | 23 | 39.1% | -0.11% | 18.4 | 1 |
| Scorpio | 22 | 36.4% | -0.23% | 18.7 | 2 |
| Capricorn | 15 | **33.3%** | -0.17% | 18.0 | 1 |
| Pisces | 25 | **32.0%** | -0.22% | 13.8 | 0 |

**Key:** Sagittarius (77.3% bullish) mạnh nhất. Pisces (32.0%) yếu nhất.
Sagittarius có biên độ lớn nhất (20.4).

---

## 3. MOON NAKSHATRA → TREND

| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |
|-----------|------|-----------|------|-------|---------|
| Mula | 10 | **90.0%** | +0.27% | 15.5 | 0 |
| Jyeshtha | 9 | 66.7% | +0.21% | 14.8 | 0 |
| Bharani | 8 | 62.5% | -0.07% | 15.4 | 0 |
| Chitra | 8 | 62.5% | +0.61% | 22.6 | 2 |
| Purva Phalguni | 12 | 58.3% | -0.07% | 21.9 | 2 |
| Rohini | 12 | 58.3% | +0.21% | 17.7 | 1 |
| Swati | 7 | 57.1% | +0.17% | 20.5 | 0 |
| Ashlesha | 9 | 55.6% | +0.16% | 16.5 | 1 |
| Purva Ashadha | 9 | 55.6% | +0.45% | 24.2 | 1 |
| Shatabhisha | 9 | 55.6% | +0.07% | 17.0 | 0 |
| Ardra | 13 | 53.8% | -0.02% | 20.7 | 2 |
| Mrigashira | 14 | 50.0% | -0.06% | 14.7 | 0 |
| Punarvasu | 12 | 50.0% | +0.12% | 14.9 | 0 |
| Vishakha | 8 | 50.0% | +0.27% | 15.6 | 1 |
| Ashwini | 11 | 45.5% | +0.07% | 15.0 | 2 |
| Hasta | 11 | 45.5% | -0.21% | 14.3 | 0 |
| Magha | 11 | 45.5% | +0.01% | 14.0 | 1 |
| Krittika | 9 | 44.4% | -0.12% | 20.5 | 2 |
| Uttara Ashadha | 9 | 44.4% | +0.02% | 20.7 | 2 |
| Pushya | 12 | 41.7% | -0.07% | 13.3 | 0 |
| Shravana | 5 | 40.0% | -0.03% | 17.7 | 0 |
| Uttara Phalguni | 10 | 40.0% | -0.19% | 18.0 | 0 |
| Dhanishta | 8 | 37.5% | -0.18% | 20.4 | 0 |
| Uttara Bhadrapada | 11 | 36.4% | -0.13% | 12.4 | 0 |
| Revati | 12 | **33.3%** | -0.29% | 14.5 | 0 |
| Purva Bhadrapada | 10 | **30.0%** | +0.04% | 19.1 | 1 |
| Anuradha | 11 | **9.1%** | -0.73% | 21.3 | 1 |

**Key:** Nakshatra là predictor mạnh nhất. Mula 90% bullish vs Anuradha 9.1% — chênh lệch 81%.
- **Bullish cluster:** Mula, Jyeshtha
- **Bearish cluster:** Revati, Purva Bhadrapada, Anuradha

---

## 4. PLANET RETROGRADE

| Planet | State | Days | Bullish % | AvgΔ | Range |
|--------|-------|------|-----------|------|-------|
| Mercury | Retro | 49 | 57.1% | +0.09% | 15.6 |
| Mercury | Direct | 221 | 46.6% | -0.01% | 17.7 |
| Venus | Direct | 270 | 48.5% | +0.01% | 17.3 |
| Mars | Retro | 51 | 58.8% | +0.23% | 16.6 |
| Mars | Direct | 219 | 46.1% | -0.05% | 17.5 |
| Jupiter | Retro | 83 | 44.6% | +0.02% | 15.6 |
| Jupiter | Direct | 187 | 50.3% | -0.00% | 18.1 |
| Saturn | Retro | 97 | 41.2% | -0.07% | 16.6 |
| Saturn | Direct | 173 | 52.6% | +0.05% | 17.7 |

### Retro vs Direct Delta

| Planet | Retro % | Direct % | Delta |
|--------|---------|----------|-------|
| Mars | 58.8% | 46.1% | 🟢 +12.7% |
| Mercury | 57.1% | 46.6% | 🟢 +10.5% |
| Jupiter | 44.6% | 50.3% | 🔴 -5.7% |
| Saturn | 41.2% | 52.6% | 🔴 -11.4% |

---

## 5. COMBUST (GẦN MẶT TRỜI)

| Planet | State | Days | Bullish % | AvgΔ | Range |
|--------|-------|------|-----------|------|-------|
| Mercury | Combust | 11 | 72.7% | +0.36% | 18.4 |
| Mercury | Not Combust | 259 | 47.5% | -0.01% | 17.3 |
| Venus | Combust | 21 | 42.9% | +0.03% | 17.6 |
| Venus | Not Combust | 249 | 49.0% | +0.00% | 17.3 |
| Mars | Not Combust | 270 | 48.5% | +0.01% | 17.3 |

---

## 6. SUN ASPECTS TO PLANETS

| Aspect | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Sun Opposition Mars | 5 | **80.0%** | -0.01% | 19.7 |
| Sun Square Saturn | 13 | **76.9%** | +0.35% | 17.4 |
| Sun Sextile Jupiter | 12 | 66.7% | +0.24% | 9.8 |
| Sun Trine Moon | 14 | 64.3% | +0.26% | 20.0 |
| Sun Trine Jupiter | 12 | 58.3% | +0.12% | 16.9 |
| Sun Opposition Moon | 7 | 57.1% | -0.00% | 17.0 |
| Sun Conjunction Mercury | 43 | 55.8% | +0.31% | 18.7 |
| Sun Square Moon | 13 | 53.8% | +0.22% | 13.5 |
| Sun Sextile Mars | 27 | 51.9% | -0.12% | 15.9 |
| Sun Sextile Moon | 12 | 50.0% | +0.01% | 12.5 |
| Sun Opposition Jupiter | 6 | 50.0% | +0.16% | 18.1 |
| Sun Conjunction Jupiter | 8 | 50.0% | -0.08% | 24.7 |
| Sun Conjunction Venus | 29 | 48.3% | +0.11% | 18.3 |
| Sun Sextile Saturn | 16 | 43.8% | +0.06% | 18.9 |
| Sun Square Mars | 24 | 41.7% | -0.07% | 17.8 |
| Sun Trine Saturn | 10 | 40.0% | -0.48% | 26.9 |
| Sun Trine Mars | 14 | 35.7% | -0.38% | 22.5 |
| Sun Conjunction Moon | 6 | **33.3%** | -0.01% | 15.2 |
| Sun Square Jupiter | 10 | **30.0%** | -0.15% | 16.2 |
| Sun Conjunction Saturn | 7 | **28.6%** | -0.09% | 14.6 |
| Sun Opposition Saturn | 8 | **12.5%** | -0.32% | 12.3 |

---

## 7. MOON ASPECTS TO PLANETS

| Aspect | Days | Bullish % | AvgΔ | Range |
|--------|------|-----------|------|-------|
| Moon Square Mars | 10 | **80.0%** | +0.28% | 15.6 |
| Moon Square Jupiter | 14 | **78.6%** | +0.36% | 18.1 |
| Moon Conjunction Mars | 9 | 66.7% | +0.22% | 15.5 |
| Moon Trine Sun | 14 | 64.3% | +0.26% | 20.0 |
| Moon Sextile Venus | 14 | 64.3% | +0.44% | 19.0 |
| Moon Opposition Jupiter | 8 | 62.5% | -0.04% | 16.0 |
| Moon Opposition Venus | 10 | 60.0% | -0.14% | 14.2 |
| Moon Trine Venus | 12 | 58.3% | +0.14% | 25.3 |
| Moon Square Mercury | 9 | 55.6% | +0.08% | 24.3 |
| Moon Square Sun | 13 | 53.8% | +0.22% | 13.5 |
| Moon Sextile Mars | 13 | 53.8% | +0.14% | 13.6 |
| Moon Square Venus | 12 | 50.0% | -0.23% | 18.4 |
| Moon Sextile Sun | 12 | 50.0% | +0.01% | 12.5 |
| Moon Sextile Saturn | 14 | 50.0% | -0.21% | 14.2 |
| Moon Trine Mars | 13 | 46.2% | -0.01% | 17.0 |
| Moon Trine Saturn | 13 | 46.2% | +0.04% | 14.8 |
| Moon Sextile Mercury | 11 | 45.5% | +0.03% | 13.9 |
| Moon Conjunction Jupiter | 9 | 44.4% | -0.04% | 9.6 |
| Moon Opposition Saturn | 10 | 40.0% | -0.02% | 16.5 |
| Moon Trine Mercury | 10 | 40.0% | +0.03% | 15.2 |
| Moon Square Saturn | 10 | 40.0% | -0.20% | 19.1 |
| Moon Trine Jupiter | 9 | **22.2%** | -0.11% | 13.6 |

---

## 8. GANN KEY LEVEL HELD vs BREACHED

| State | Days | Bullish % | AvgΔ | Range |
|-------|------|-----------|------|-------|
| Held | 263 | 49.0% | +0.02% | 16.6 |
| Breached | 7 | 28.6% | -0.58% | 45.2 |

**Key:** Range khi breached gấp 2.7x so với held.

---

## 9. DOMINANT PLANET HOUR (HORA)

| Hora | Days | Bullish % | AvgΔ | Range |
|------|------|-----------|------|-------|
| Venus | 55 | 58.2% | -0.03% | 18.9 |
| Mercury | 56 | 50.0% | +0.09% | 15.0 |
| Jupiter | 55 | 49.1% | +0.07% | 18.5 |
| Mars | 56 | 44.6% | +0.03% | 16.4 |
| Moon | 48 | **39.6%** | -0.17% | 17.9 |

---

## 10. MARKET REACTION DISTRIBUTION

| Reaction | Days | % of Total | Bullish % | AvgΔ | Range |
|----------|------|------------|-----------|------|-------|
| reversal_signal | 72 | 26.7% | 51.4% | +0.00% | 17.2 |
| mild_trend | 65 | 24.1% | 50.8% | +0.02% | 18.1 |
| consolidation | 50 | 18.5% | 42.0% | +0.01% | 4.2 |
| choppy | 32 | 11.9% | 40.6% | -0.08% | 12.6 |
| moderate_trend | 31 | 11.5% | 58.1% | +0.17% | 27.0 |
| strong_trend | 20 | 7.4% | 45.0% | -0.17% | 40.7 |

---

## 11. VOLATILITY REGIMES

| Volatility | Days | % of Total | Bullish % | AvgΔ | Range |
|------------|------|------------|-----------|------|-------|
| high | 19 | 7.0% | 57.9% | +0.22% | 44.0 |
| low | 167 | 61.9% | 46.7% | -0.01% | 10.3 |
| medium | 84 | 31.1% | 50.0% | -0.01% | 25.3 |

---

## 12. ECLIPSE PERIODS

| Metric | Value |
|--------|-------|
| Eclipse Days | 41 |
| Bullish % | 53.7% |
| AvgΔ | -0.02% |
| Avg Range | 17.6 |

---

## 🔑 KEY FINDINGS SUMMARY

- **Nakshatra strongest predictor:** Mula 90% bullish vs Anuradha 9.1% (81% spread)
- **Moon Sign:** Sagittarius 77.3% bullish; Pisces 32.0% weakest
- **Mars Retro:** bullish hơn direct (+12.7% delta)
- **Mercury Retro:** bullish hơn direct (+10.5% delta)
- **Jupiter Retro:** bearish hơn direct (-5.7% delta)
- **Mercury Combust:** 72.7% bullish, range 18.4
- **Venus Combust:** 42.9% bullish, range 17.6
- **Sun Opposition Mars:** 80.0% bullish, -0.01%
- **Sun Square Saturn:** 76.9% bullish, +0.35%
- **Sun Sextile Jupiter:** 66.7% bullish, +0.24%
- **Gann Key Held:** range 16.6 vs 45.2 breached (2.7x)
- **Hora:** Venus 58% bullish; Moon 39.6% bearish
- **Market reaction:** 26.7% reversal, only 7.4% strong trend → range-bound với sudden reversals

---

*Report generated by analyze_period.py | Data: 2022-04 → 2023-04 | 270 trading days*
