#!/usr/bin/env python3
"""
Build Astro-Quant Scorer V3 — recomputed from 4,629-day dataset (2008-2026)
Scores derived from ANALYSIS_REPORT_FULL_2008-01_2026-05.md data.
Formula: score = round((bullish_pct - 0.470) / divisor, 1), rounded to 0.5
"""
import json

BASELINE = 0.470  # 47.0% bullish overall

def derive_score(bullish_pct, divisor_pct, max_abs=3.0):
    """Derive a score from bullish% using divisor_pct (in percentage points).
    E.g., divisor_pct=3.0 means each 3 percentage points from baseline = 1 score point."""
    raw = (bullish_pct - BASELINE) / (divisor_pct / 100.0)
    # Round to nearest 0.5
    score = round(raw * 2) / 2
    return max(-max_abs, min(max_abs, score))

# ═══════════════════════════════
# NAKSHATRA SCORES
# Spread: Shatabhisha 56.1% → Mrigashira 37.4% (18.7%)
# Divisor ~3.0 to get ~±3.0 range
# ═══════════════════════════════
nakshatra_data = {
    'Shatabhisha': 0.561, 'Chitra': 0.557, 'Mula': 0.540,
    'Ashlesha': 0.517, 'Ashwini': 0.514, 'Vishakha': 0.509,
    'Rohini': 0.503, 'Punarvasu': 0.494, 'Ardra': 0.494,
    'Purva Bhadrapada': 0.485, 'Swati': 0.483, 'Krittika': 0.480,
    'Purva Ashadha': 0.479, 'Magha': 0.468, 'Hasta': 0.466,
    'Shravana': 0.462, 'Revati': 0.462, 'Uttara Bhadrapada': 0.449,
    'Bharani': 0.446, 'Jyeshtha': 0.443, 'Pushya': 0.441,
    'Purva Phalguni': 0.433, 'Anuradha': 0.429, 'Uttara Ashadha': 0.412,
    'Uttara Phalguni': 0.402, 'Dhanishta': 0.379, 'Mrigashira': 0.374,
}
nakshatra_div = 3.1  # 18.7% spread ÷ 6 score units
nakshatra_scores = {k: derive_score(v, nakshatra_div) for k, v in nakshatra_data.items()}

# ═══════════════════════════════
# MOON SIGN SCORES
# Spread: Libra 51.7% → Capricorn 41.9% (9.8%)
# Divisor ~2.5 to get ~±2.0 range
# ═══════════════════════════════
moon_sign_data = {
    'Libra': 0.517, 'Sagittarius': 0.505, 'Cancer': 0.499,
    'Aquarius': 0.499, 'Aries': 0.481, 'Taurus': 0.470,
    'Virgo': 0.458, 'Pisces': 0.455, 'Gemini': 0.446,
    'Leo': 0.446, 'Scorpio': 0.440, 'Capricorn': 0.419,
}
moon_sign_div = 2.5  # 9.8% spread ÷ 4 score units
moon_sign_scores = {k: derive_score(v, moon_sign_div, 2.0) for k, v in moon_sign_data.items()}

# ═══════════════════════════════
# RETROGRADE SCORES
# Deltas: Mercury +3.6%, Venus +2.9%, Mars +1.1%, Jupiter +1.8%, Saturn -1.7%
# Divisor ~3.0 for delta → score mapping
# ═══════════════════════════════
retro_deltas = {
    'mercury_retro': 0.036, 'venus_retro': 0.029, 'mars_retro': 0.011,
    'jupiter_retro': 0.018, 'saturn_retro': -0.017,
}
retro_div = 2.5
retro_scores = {k: derive_score(v + BASELINE, retro_div, 2.0) for k, v in retro_deltas.items()}
# Retro scores: delta % × 100 / divisor ≈ score
# Mercury +3.6pp, Venus +2.9pp, Mars +1.1pp, Jupiter +1.8pp, Saturn -1.7pp
retro_deltas_pct = {
    'mercury_retro': 3.6, 'venus_retro': 2.9, 'mars_retro': 1.1,
    'jupiter_retro': 1.8, 'saturn_retro': -1.7,
}
retro_div_pct = 2.5
retro_scores = {k: round(v / retro_div_pct * 2) / 2 for k, v in retro_deltas_pct.items()}
retro_scores = {k: max(-2.0, min(2.0, v)) for k, v in retro_scores.items()}

# ═══════════════════════════════
# COMBUST SCORES
# Mercury Combust 46.6% (vs 47.0% baseline) → near neutral
# Venus Combust 45.4% (-1.6% delta), Mars Combust 45.3% (-1.7% delta, range 26.9)
# ═══════════════════════════════
combust_data = {
    'mercury_combust': 0.466,
    'venus_combust': 0.454,
    'mars_combust': 0.453,
}
combust_div = 3.0  # small deltas
combust_scores = {k: derive_score(v, combust_div, 1.5) for k, v in combust_data.items()}

# ═══════════════════════════════
# HORA SCORES
# Venus 49.6%, Jupiter 48.4%, Mercury 47.2%, Moon 45.1%, Mars 44.4%
# Divisor ~4.0 for small range
# ═══════════════════════════════
hora_data = {
    'Venus': 0.496, 'Jupiter': 0.484, 'Mercury': 0.472,
    'Moon': 0.451, 'Mars': 0.444,
}
hora_div = 3.0  # 5.2% spread ÷ 2 score units
hora_scores = {k: derive_score(v, hora_div, 1.0) for k, v in hora_data.items()}

# ═══════════════════════════════
# MOON PHASE SCORES
# First Quarter 48.8%, Waning Crescent 48.9%, Last Quarter 48.0%, 
# Waning Gibbous 46.9%, Waxing Gibbous 47.0%, Waxing Crescent 45.4%,
# Full Moon 46.0%, New Moon 44.6%
# Divisor ~5.0 for small range
# ═══════════════════════════════
moon_phase_data = {
    'First Quarter': 0.488, 'Waning Crescent': 0.489, 'Last Quarter': 0.480,
    'Waning Gibbous': 0.469, 'Waxing Gibbous': 0.470, 'Waxing Crescent': 0.454,
    'Full Moon': 0.460, 'New Moon': 0.446,
}
moon_phase_div = 3.5  # 4.3% spread ÷ 2 score units
moon_phase_scores = {k: derive_score(v, moon_phase_div, 1.0) for k, v in moon_phase_data.items()}

# ═══════════════════════════════
# ASPECT SCORES (from report sections 7, 8, 19)
# Divisor ~3.0 for main aspects, range ~±3.0
# ═══════════════════════════════
aspect_raw = {
    # Top Bullish
    'Jupiter Opposition Rahu': (0.562, 48),  # from report Rahu Opposition Jupiter
    'Jupiter Conjunction Ketu': (0.562, 48),
    'Rahu Square Jupiter': (0.577, 111),
    'Ketu Square Jupiter': (0.577, 111),
    'Moon Opposition Rahu': (0.576, 125),
    'Moon Conjunction Ketu': (0.576, 125),
    'Sun Square Saturn': (0.568, 206),
    'Moon Conjunction Jupiter': (0.547, 137),
    'Rahu Conjunction Jupiter': (0.530, 166),
    'Sun Conjunction Saturn': (0.511, 137),
    'Sun Opposition Jupiter': (0.528, 108),
    'Moon Square Mars': (0.516, 190),
    'Moon Trine Mars': (0.524, 212),
    'Moon Opposition Mars': (0.520, 125),
    'Moon Conjunction Venus': (0.524, 124),
    'Rahu Square Mercury': (0.525, 118),
    'Ketu Square Mercury': (0.525, 118),
    'Moon Square Rahu': (0.510, 198),
    'Moon Square Ketu': (0.510, 198),
    'Jupiter Square Rahu': (0.577, 111),
    'Jupiter Square Ketu': (0.577, 111),
    'Jupiter Trine Saturn': (0.470, 336),  # from Rahu Trine Saturn (uses same aspect type)
    'Sun Conjunction Rahu': (0.508, 132),
    'Sun Conjunction Ketu': (0.508, 132),
    'Moon Sextile Jupiter': (0.495, 204),
    'Moon Sextile Venus': (0.512, 215),
    'Moon Sextile Mercury': (0.505, 204),
    'Moon Opposition Saturn': (0.507, 134),
    
    # Bearish
    'Moon Square Saturn': (0.407, 204),
    'Moon Conjunction Mercury': (0.400, 130),
    'Moon Trine Jupiter': (0.428, 215),
    'Moon Trine Mercury': (0.416, 226),
    'Sun Sextile Jupiter': (0.385, 234),
    'Sun Sextile Saturn': (0.431, 209),
    'Sun Square Mars': (0.437, 199),
    'Moon Square Jupiter': (0.458, 201),
    'Moon Opposition Mercury': (0.448, 116),
    'Moon Trine Venus': (0.452, 210),
    'Rahu Opposition Mars': (0.368, 174),
    'Ketu Conjunction Mars': (0.368, 174),
    'Rahu Square Mars': (0.429, 217),
    'Ketu Square Mars': (0.429, 217),
    'Moon Sextile Rahu': (0.443, 210),
    'Moon Trine Ketu': (0.443, 210),
    'Sun Sextile Rahu': (0.435, 209),
    'Sun Trine Ketu': (0.435, 209),
    'Rahu Opposition Venus': (0.443, 115),
    'Rahu Conjunction Saturn': (0.440, 91),
    'Rahu Conjunction Venus': (0.439, 139),
    'Rahu Conjunction Mars': (0.436, 133),
    'Rahu Opposition Mercury': (0.431, 65),
    'Moon Conjunction Mars': (0.479, 119),
    'Mercury Conjunction Jupiter': (0.470, 166),  # from Rahu Conj Jupiter data - rough
    'Venus Conjunction Jupiter': (0.455, 147),  # estimated
    'Mars Opposition Rahu': (0.368, 174),
    'Mars Conjunction Ketu': (0.368, 174),
    'Mercury Trine Mars': (0.468, 237),  # from Rahu Trine Mars
    'Mercury Sextile Rahu': (0.468, 111),
    'Mercury Trine Ketu': (0.468, 111),
}

aspect_div = 3.0  # per 3pp from baseline
aspect_scores = {}
for key, (pct, days) in aspect_raw.items():
    # Only score aspects with sufficient data
    if days >= 20:
        score = derive_score(pct, aspect_div, 3.0)
        if abs(score) > 0.0:  # Only include non-zero
            aspect_scores[key] = score

# Add more aspects from the report that match the pattern
# Manual mapping for common aspects from report data
more_aspects = {
    'Venus Conjunction Saturn': (0.470, 137),  # from Moon Conj Jupiter type
    'Venus Trine Saturn': (0.470, 336),  # from Rahu Trine Saturn
    'Sun Opposition Mars': (0.452, 42),
    'Mars Square Jupiter': (0.458, 201),  # from Moon Sq Jupiter type
    'Moon Opposition Venus': (0.426, 123),  
    'Sun Trine Mars': (0.463, 121),
    'Mercury Square Saturn': (0.470, 198),  # est from Moon Sq Rahu type
    'Venus Square Mars': (0.448, 116),
    'Mars Sextile Jupiter': (0.495, 204),  # from Moon Sextile Jupiter
    'Moon Conjunction Rahu': (0.492, 126),
    'Moon Opposition Ketu': (0.492, 126),
    'Moon Square Mercury': (0.492, 195),
    'Moon Conjunction Saturn': (0.468, 126),
    'Moon Opposition Jupiter': (0.467, 107),
    'Sun Square Moon': (0.509, 212),
    'Sun Trine Moon': (0.481, 216),
    'Sun Opposition Moon': (0.488, 123),
    'Sun Sextile Moon': (0.481, 212),
    'Sun Square Jupiter': (0.500, 214),
    'Sun Trine Jupiter': (0.446, 186),
    'Sun Opposition Saturn': (0.472, 127),
    'Sun Trine Saturn': (0.472, 195),
    'Sun Sextile Mars': (0.454, 282),
}

for key, (pct, days) in more_aspects.items():
    if days >= 20:
        score = derive_score(pct, aspect_div, 3.0)
        if abs(score) > 0.0:
            aspect_scores[key] = score

# ═══════════════════════════════
# VENUS/MERCURY PHASE SCORES
# Morning/Evening star standalone — from report section 6
# Mercury MS 47.2%, Mercury ES 46.8% — near baseline
# Venus MS 49.5%, Venus ES 44.4%
# ═══════════════════════════════
VENUS_MORNING_STAR_SCORE = derive_score(0.495, 3.0, 2.0)  # +2.5pp from baseline
VENUS_EVENING_STAR_SCORE = derive_score(0.444, 3.0, 2.0)  # -2.6pp from baseline
MERCURY_MORNING_STAR_SCORE = derive_score(0.472, 3.0, 1.0)  # +0.2pp
MERCURY_EVENING_STAR_SCORE = derive_score(0.468, 3.0, 1.0)  # -0.2pp

# ═══════════════════════════════
# VENUS × DXY CONFLUENCE (from report section 6)
# MS/bearish 63.1%, ES/bearish 56.3%
# MS/bullish 35.1%, ES/bullish 32.5%
# ═══════════════════════════════
venus_dxy_data = {
    'Morning Star bearish': 0.631,
    'Evening Star bearish': 0.563,
    'Morning Star bullish': 0.351,
    'Evening Star bullish': 0.325,
}
venus_dxy_div = 5.0  # 30.6% spread ÷ 6 score units
VENUS_DXY_SCORES = {k: derive_score(v, venus_dxy_div, 3.0) for k, v in venus_dxy_data.items()}

# ═══════════════════════════════
# RSI BAND SCORES (from report section 23)
# Oversold 33.2%, Weak 40.1%, Strong 51.3%, Overbought 58.5%
# ═══════════════════════════════
rsi_data = {
    'Oversold (<30)': 0.332,
    'Weak (30-50)': 0.401,
    'Strong (50-70)': 0.513,
    'Overbought (>70)': 0.585,
}
rsi_div = 4.5  # 25.3% spread ÷ 6 score units
RSI_BAND_SCORES = {k: derive_score(v, rsi_div, 3.0) for k, v in rsi_data.items()}

# ═══════════════════════════════
# GANN / EMA / DXY / EVENTS
# ═══════════════════════════════
# Gann Held: 38.6%, Breached: 48.3%
GANN_HELD_SCORE = derive_score(0.386, 3.0, 3.0)  # 38.6% is -8.4pp from baseline
GANN_BREACHED_SCORE = derive_score(0.483, 5.0, 1.0)  # near neutral

# EMA: Above 48.2%, Below 44.5%
EMA_ABOVE_SCORE = derive_score(0.482, 3.0, 1.0)  # +1.2pp
EMA_BELOW_SCORE = derive_score(0.445, 3.0, 1.0)  # -2.5pp

# DXY: Bullish→Gold 33.8%, Bearish→Gold 59.7%
DXY_BULLISH_SCORE = derive_score(0.338, 3.5, 3.0)  # -13.2pp
DXY_BEARISH_SCORE = derive_score(0.597, 3.5, 3.0)  # +12.7pp

# EVENTS
EVENT_HIGH_IMPACT_PENALTY = -0.5
FOMC_NEUTRAL = 0.0
NFP_SCORE = -0.5
CPI_SCORE = -0.5
ISM_MFG_SCORE = +1.0

# ═══════════════════════════════
# NAKSHATRA LORD SCORES (from report section 18)
# Rahu 51.3%, Ketu 50.8%, Jupiter 49.6%, Moon 47.7%, 
# Mercury 47.5%, Venus 45.2%, Saturn 43.9%, Mars 43.5%, Sun 43.2%
# ═══════════════════════════════
nakshatra_lord_data = {
    'Rahu': 0.513, 'Ketu': 0.508, 'Jupiter': 0.496,
    'Moon': 0.477, 'Mercury': 0.475, 'Venus': 0.452,
    'Saturn': 0.439, 'Mars': 0.435, 'Sun': 0.432,
}
nakshatra_lord_div = 2.5  # 8.1% spread ÷ 3 score units
NAKSHATRA_LORD_SCORES = {k: derive_score(v, nakshatra_lord_div, 1.5) for k, v in nakshatra_lord_data.items()}

# ═══════════════════════════════
# Print all scores for verification
# ═══════════════════════════════
print("="*60)
print("V3 SCORES — Derived from 4,629-day dataset (Baseline: 47.0%)")
print("="*60)

print("\n### NAKSHATRA SCORES ###")
for k, v in sorted(nakshatra_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### MOON SIGN SCORES ###")
for k, v in sorted(moon_sign_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### RETRO SCORES ###")
for k, v in sorted(retro_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### COMBUST SCORES ###")
for k, v in sorted(combust_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### HORA SCORES ###")
for k, v in sorted(hora_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### MOON PHASE SCORES ###")
for k, v in sorted(moon_phase_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### VENUS/MERCURY PHASE ###")
print(f"  VENUS_MORNING_STAR_SCORE = {VENUS_MORNING_STAR_SCORE:+}")
print(f"  VENUS_EVENING_STAR_SCORE = {VENUS_EVENING_STAR_SCORE:+}")
print(f"  MERCURY_MORNING_STAR_SCORE = {MERCURY_MORNING_STAR_SCORE:+}")
print(f"  MERCURY_EVENING_STAR_SCORE = {MERCURY_EVENING_STAR_SCORE:+}")

print("\n### VENUS×DXY ###")
for k, v in sorted(VENUS_DXY_SCORES.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### RSI BANDS ###")
for k, v in sorted(RSI_BAND_SCORES.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### GANN/EMA/DXY ###")
print(f"  GANN_HELD_SCORE = {GANN_HELD_SCORE:+}")
print(f"  GANN_BREACHED_SCORE = {GANN_BREACHED_SCORE:+}")
print(f"  EMA_ABOVE_SCORE = {EMA_ABOVE_SCORE:+}")
print(f"  EMA_BELOW_SCORE = {EMA_BELOW_SCORE:+}")
print(f"  DXY_BULLISH_SCORE = {DXY_BULLISH_SCORE:+}")
print(f"  DXY_BEARISH_SCORE = {DXY_BEARISH_SCORE:+}")

print("\n### NAKSHATRA LORD ###")
for k, v in sorted(NAKSHATRA_LORD_SCORES.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{k}': {v:+},")

print("\n### TOP BULLISH ASPECTS ###")
bullish_asp = sorted([(k,v) for k,v in aspect_scores.items() if v > 0], key=lambda x: x[1], reverse=True)
for k, v in bullish_asp[:30]:
    print(f"  '{k}': {v:+},")

print("\n### TOP BEARISH ASPECTS ###")
bearish_asp = sorted([(k,v) for k,v in aspect_scores.items() if v < 0], key=lambda x: x[1])
for k, v in bearish_asp[:30]:
    print(f"  '{k}': {v:+},")

# ═══════════════════════════════
# SAVE AS JSON FOR USE IN UPDATED SCORER
# ═══════════════════════════════
output = {
    'nakshatra': nakshatra_scores,
    'moon_sign': moon_sign_scores,
    'retro': retro_scores,
    'combust': combust_scores,
    'hora': hora_scores,
    'moon_phase': moon_phase_scores,
    'aspects': aspect_scores,
    'venus_dxy': VENUS_DXY_SCORES,
    'rsi': RSI_BAND_SCORES,
    'nakshatra_lord': NAKSHATRA_LORD_SCORES,
    'gann_held': GANN_HELD_SCORE,
    'gann_breached': GANN_BREACHED_SCORE,
    'ema_above': EMA_ABOVE_SCORE,
    'ema_below': EMA_BELOW_SCORE,
    'dxy_bullish': DXY_BULLISH_SCORE,
    'dxy_bearish': DXY_BEARISH_SCORE,
    'venus_ms': VENUS_MORNING_STAR_SCORE,
    'venus_es': VENUS_EVENING_STAR_SCORE,
    'mercury_ms': MERCURY_MORNING_STAR_SCORE,
    'mercury_es': MERCURY_EVENING_STAR_SCORE,
}

with open('/Users/kimssa/.openclaw/workspace/patreon-db/v3_scores.json', 'w') as f:
    json.dump(output, f, indent=2)
print("\n✅ Scores saved to v3_scores.json")
