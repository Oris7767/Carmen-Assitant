#!/usr/bin/env python3
"""
patreon-db/analyze_v2.py — ENHANCED ANALYSIS ENGINE
====================================================
Generates analysis reports from patreon-db data.

New sections (vs v1):
  17. Nakshatra Lord Analysis        — ruler of the day's nakshatra
  18. Rahu/Ketu Aspects              — shadow planet specific
  19. S&P 500 Correlation            — equity market link
  20. VIX (Fear Index) Correlation   — risk sentiment
  21. Multi-Factor Confluence        — top 3-factor combos
  22. Technical Indicators           — RSI, ATR, Volume bands
  23. Data Quality Report            — completeness check

Modes:
  Full:         python3 analyze_v2.py --full
  Yearly:       python3 analyze_v2.py --yearly
  Single year:  python3 analyze_v2.py --year 2025
  Data audit:   python3 analyze_v2.py --audit

Usage:
    python3 analyze_v2.py --full              # Full 10-year report
    python3 analyze_v2.py --yearly            # All yearly reports
    python3 analyze_v2.py --year 2025         # Single year
    python3 analyze_v2.py --audit             # Data quality audit only
"""

import os
import sys
import json
import math
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime
from itertools import combinations

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

MOON_PHASE_ORDER = [
    'New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
    'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent'
]


def load_all_data():
    """Load all CSVs into one DataFrame."""
    all_dfs = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith('.csv'):
            path = os.path.join(DATA_DIR, f)
            df = pd.read_csv(path)
            all_dfs.append(df)
    combined = pd.concat(all_dfs, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])
    return combined


# ═══════════════════════════════════════════════════════════════
# DATA QUALITY AUDIT
# ═══════════════════════════════════════════════════════════════

def audit_data(df):
    """Run data quality audit and return report string."""
    lines = []
    lines.append("# 📋 Data Quality Audit")
    lines.append(f"")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Total rows:** {len(df)}")
    lines.append(f"**Date range:** {df['date'].min().strftime('%Y-%m-%d')} → {df['date'].max().strftime('%Y-%m-%d')}")
    lines.append(f"")

    # Check each column
    lines.append("## Column Completeness")
    lines.append("")
    lines.append("| Column | Filled | Empty | Fill % |")
    lines.append("|--------|--------|-------|--------|")

    total = len(df)
    issues = []

    for col in df.columns:
        filled = 0
        for v in df[col]:
            if v is not None and v != '' and v != 0 and not (isinstance(v, float) and pd.isna(v)):
                filled += 1
        pct = round(filled / total * 100, 1)
        flag = " ⚠️" if pct < 80 else (" 🔴" if pct < 10 else "")
        lines.append(f"| {col} | {filled} | {total - filled} | {pct}%{flag} |")
        if pct < 80 and pct > 0:
            issues.append((col, pct))
        elif pct == 0:
            issues.append((col, 0))

    lines.append(f"")

    if issues:
        lines.append("## ⚠️ Issues Found")
        lines.append("")
        for col, pct in issues:
            if pct == 0:
                lines.append(f"- 🔴 **{col}**: COMPLETELY EMPTY — needs backfill")
            else:
                lines.append(f"- ⚠️ **{col}**: Only {pct}% filled")

    # Check for date gaps
    lines.append(f"")
    lines.append("## Date Gaps Check")
    lines.append("")
    dates = sorted(df['date'].unique())
    gaps = []
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i-1]).days
        if delta > 4:  # Weekend/holiday
            gaps.append(f"{dates[i-1].strftime('%Y-%m-%d')} → {dates[i].strftime('%Y-%m-%d')} ({delta} days)")
    if gaps:
        lines.append(f"Found {len(gaps)} large gaps (>4 days):")
        for g in gaps[:10]:
            lines.append(f"  - {g}")
    else:
        lines.append("✅ No concerning gaps found (all gaps ≤4 days = normal weekends)")

    # V2 column check
    v2_cols = ["moon_nakshatra_lord", "sp500_change_pct", "vix_close", "gold_volume", "gold_atr_14", "gold_rsi_14"]
    missing_v2 = [c for c in v2_cols if c not in df.columns]
    if missing_v2:
        lines.append(f"")
        lines.append("## 🆕 V2 Columns Not Yet Collected")
        for c in missing_v2:
            lines.append(f"- `{c}` — run `collect_v2.py` backfill to add")

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════

def analyze_period(df, period_name, output_path):
    """Generate full analysis report."""
    total_days = len(df)
    if total_days == 0:
        return

    bullish_days = len(df[df['gold_bullish'] == True])
    bullish_pct = round(bullish_days / total_days * 100, 1)
    bearish_pct = round(100 - bullish_pct, 1)
    avg_change = round(df['gold_change_pct'].mean(), 3)
    std_change = round(df['gold_change_pct'].std(), 3)
    avg_range = round(df['gold_range'].mean(), 2)
    date_start = df['date'].min().strftime('%Y-%m-%d')
    date_end = df['date'].max().strftime('%Y-%m-%d')

    report = []
    def h(text=""): report.append(text)

    h(f"# 📊 Phân Tích Dữ Liệu Gold (XAUUSD) — v2")
    h(f"")
    h(f"**Giai đoạn:** {date_start} → {date_end} ({total_days} trading days)")
    h(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 1. BASELINE ═══
    h(f"## 1. BASELINE")
    h(f"")
    h(f"| Metric | Value |")
    h(f"|--------|-------|")
    h(f"| Total Trading Days | {total_days} |")
    h(f"| Bullish Days | {bullish_pct}% |")
    h(f"| Bearish Days | {bearish_pct}% |")
    h(f"| Avg Daily Change | {avg_change}% |")
    h(f"| Std Daily Change | {std_change}% |")
    h(f"| Avg Daily Range | {avg_range} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 2. MOON SIGN ═══
    h(f"## 2. MOON SIGN → TREND")
    h(f"")
    h(f"| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |")
    h(f"|-----------|------|-----------|------|-------|---------|")

    moon_sign_stats = []
    for sign in ZODIAC_SIGNS:
        sub = df[df['moon_sign'] == sign]
        if len(sub) == 0: continue
        days = len(sub)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        moon_sign_stats.append((sign, days, bp, ad, rg, hv))

    moon_sign_stats.sort(key=lambda x: x[2], reverse=True)
    for sign, days, bp, ad, rg, hv in moon_sign_stats:
        ad_str = f"+{ad}" if ad > 0 else str(ad)
        h(f"| {sign} | {days} | **{bp}%** | {ad_str}% | {rg} | {hv} |")

    if moon_sign_stats:
        h(f"")
        h(f"**Key:** {moon_sign_stats[0][0]} ({moon_sign_stats[0][2]}% bullish) mạnh nhất. "
          f"{moon_sign_stats[-1][0]} ({moon_sign_stats[-1][2]}% bullish) yếu nhất.")
        hv_sign = max(moon_sign_stats, key=lambda x: x[4])
        h(f"{hv_sign[0]} có biên độ lớn nhất ({hv_sign[4]}).")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 3. MOON NAKSHATRA ═══
    h(f"## 3. MOON NAKSHATRA → TREND")
    h(f"")
    h(f"| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |")
    h(f"|-----------|------|-----------|------|-------|---------|")

    nak_stats = []
    for nak in df['moon_nakshatra'].dropna().unique():
        if str(nak).strip() == '': continue
        sub = df[df['moon_nakshatra'] == nak]
        days = len(sub)
        if days < 5: continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        nak_stats.append((str(nak), days, bp, ad, rg, hv))

    nak_stats.sort(key=lambda x: x[2], reverse=True)
    for nak, days, bp, ad, rg, hv in nak_stats:
        ad_str = f"+{ad}" if ad > 0 else str(ad)
        h(f"| {nak} | {days} | **{bp}%** | {ad_str}% | {rg} | {hv} |")

    h(f"")
    if nak_stats:
        top_nak, bot_nak = nak_stats[0], nak_stats[-1]
        spread = top_nak[2] - bot_nak[2]
        h(f"**Key:** {top_nak[0]} {top_nak[2]}% bullish vs {bot_nak[0]} {bot_nak[2]}% — spread {spread}%.")
        bullish_cluster = [n[0] for n in nak_stats if n[2] >= 55]
        bearish_cluster = [n[0] for n in nak_stats if n[2] <= 45]
        if bullish_cluster:
            h(f"- **Bullish cluster:** {', '.join(bullish_cluster)}")
        if bearish_cluster:
            h(f"- **Bearish cluster:** {', '.join(bearish_cluster)}")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 4. RETROGRADE ═══
    h(f"## 4. PLANET RETROGRADE")
    h(f"")
    h(f"| Planet | State | Days | Bullish % | AvgΔ | Range |")
    h(f"|--------|-------|------|-----------|------|-------|")

    retro_planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    retro_stats = {}
    for planet in retro_planets:
        col = f"{planet}_retro"
        if col not in df.columns: continue
        for state, label in [(True, 'Retro'), (False, 'Direct')]:
            sub = df[df[col] == state]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {planet.capitalize()} | {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
            if planet not in retro_stats: retro_stats[planet] = {}
            retro_stats[planet][label] = bp

    h(f"")
    h(f"### Delta (Retro - Direct)")
    h(f"")
    h(f"| Planet | Retro % | Direct % | Delta |")
    h(f"|--------|---------|----------|-------|")
    for planet in retro_planets:
        if planet in retro_stats and 'Retro' in retro_stats[planet] and 'Direct' in retro_stats[planet]:
            rp, dp = retro_stats[planet]['Retro'], retro_stats[planet]['Direct']
            delta = rp - dp
            emoji = "🟢" if delta > 0 else "🔴"
            h(f"| {planet.capitalize()} | {rp}% | {dp}% | {emoji} {'+' if delta >= 0 else ''}{round(delta,1)}% |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 5. COMBUST ═══
    h(f"## 5. COMBUST")
    h(f"")
    h(f"| Planet | State | Days | Bullish % | AvgΔ | Range |")
    h(f"|--------|-------|------|-----------|------|-------|")
    for planet in ['mercury', 'venus', 'mars']:
        col = f"{planet}_combust"
        if col not in df.columns: continue
        for state, label in [(True, 'Combust'), (False, 'Not Combust')]:
            sub = df[df[col] == state]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {planet.capitalize()} | {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 6. MERCURY & VENUS ELONGATION (MORNING/EVENING STAR) 🆕 ═══
    h(f"## 6. MORNING STAR / EVENING STAR 🆕")
    h(f"")
    h(f"*Mercury & Venus elongation analysis — morning star (W) = planet rises before Sun, evening star (E) = visible after sunset.*")
    h(f"")

    # Mercury Elongation
    merc_col = 'mercury_elong_dir'
    if merc_col in df.columns:
        h(f"### Mercury — Morning Star (W) vs Evening Star (E)")
        h(f"")
        h(f"| Phase | Days | Bullish % | AvgΔ | Range | HighVol |")
        h(f"|-------|------|-----------|------|-------|---------|")
        for phase, label in [('W', 'Morning Star 🌅'), ('E', 'Evening Star 🌇')]:
            sub = df[df[merc_col] == phase]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            hv = len(sub[sub['volatility']=='high'])
            h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} | {hv} |")

        h(f"")
        h(f"### Mercury Elongation Bands → Gold")
        h(f"")
        h(f"| Elongation | Days | Bullish % | AvgΔ | Range |")
        h(f"|------------|------|-----------|------|-------|")
        merc_deg = pd.to_numeric(df['mercury_elong_deg'], errors='coerce')
        for label, lo, hi in [('0-5° (Combust)', 0, 5), ('5-18° (Under Beams)', 5, 18),
                               ('18-28° (Max Elongation)', 18, 28), ('>28° (Free)', 28, 999)]:
            mask = (merc_deg >= lo) & (merc_deg < hi)
            sub = df[mask]
            days = len(sub)
            if days < 3: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
        h(f"")

    # Venus Elongation
    ven_col = 'venus_elong_dir'
    if ven_col in df.columns:
        h(f"### Venus — Morning Star (W) vs Evening Star (E)")
        h(f"")
        h(f"| Phase | Days | Bullish % | AvgΔ | Range | HighVol |")
        h(f"|-------|------|-----------|------|-------|---------|")
        for phase, label in [('W', 'Morning Star 🌅'), ('E', 'Evening Star 🌇')]:
            sub = df[df[ven_col] == phase]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            hv = len(sub[sub['volatility']=='high'])
            h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} | {hv} |")

        h(f"")
        h(f"### Venus Elongation Bands → Gold")
        h(f"")
        h(f"| Elongation | Days | Bullish % | AvgΔ | Range |")
        h(f"|------------|------|-----------|------|-------|")
        ven_deg = pd.to_numeric(df['venus_elong_deg'], errors='coerce')
        for label, lo, hi in [('0-5° (Combust)', 0, 5), ('5-30°', 5, 30),
                               ('30-47° (Max Elongation)', 30, 47), ('>47° (Full)', 47, 999)]:
            mask = (ven_deg >= lo) & (ven_deg < hi)
            sub = df[mask]
            days = len(sub)
            if days < 3: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
        h(f"")

        # Cross: Venus phase × DXY direction
        h(f"### Venus Phase × DXY Direction (Confluence)")
        h(f"")
        h(f"| Venus Phase | DXY | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        h(f"|-------------|-----|------|----------------|-----------|------------|")
        for phase, plabel in [('W', 'Morning Star'), ('E', 'Evening Star')]:
            for dxy_dir in ['bullish', 'bearish']:
                sub = df[(df[ven_col] == phase) & (df['dxy_direction'] == dxy_dir)]
                days = len(sub)
                if days < 10: continue
                bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
                ad = round(sub['gold_change_pct'].mean(), 2)
                rg = round(sub['gold_range'].mean(), 1)
                h(f"| {plabel} | {dxy_dir} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

    h(f"")
    h(f"---")
    h(f"")

    # ═══ 7-8. ASPECTS (Sun & Moon) ═══
    def extract_aspects(df, planet_filter):
        """Extract aspects from aspects_json, filtered by planet."""
        results = []
        for _, row in df.iterrows():
            aj = row.get('aspects_json', '[]')
            if pd.isna(aj) or str(aj).strip() == '': continue
            try:
                aspects = json.loads(aj)
            except: continue
            for asp in aspects:
                p1, p2 = asp.get('planet1',''), asp.get('planet2','')
                if planet_filter in (p1, p2):
                    other = p2 if p1 == planet_filter else p1
                    key = f"{planet_filter} {asp['aspect']} {other}"
                    results.append((key, row['gold_bullish'], row['gold_change_pct'], row['gold_range']))
        return results

    def process_aspects(aspect_list, min_days=3):
        stats = defaultdict(lambda: {'days': 0, 'bullish': 0, 'changes': [], 'ranges': []})
        for key, bull, chg, rng in aspect_list:
            stats[key]['days'] += 1
            if bull: stats[key]['bullish'] += 1
            stats[key]['changes'].append(chg)
            stats[key]['ranges'].append(rng)
        result = []
        for key, s in stats.items():
            if s['days'] < min_days: continue
            result.append((key, s['days'],
                          round(s['bullish']/s['days']*100,1),
                          round(np.mean(s['changes']),2),
                          round(np.mean(s['ranges']),1)))
        result.sort(key=lambda x: x[2], reverse=True)
        return result

    # Sun Aspects
    h(f"## 7. SUN ASPECTS")
    h(f"")
    h(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
    h(f"|--------|------|-----------|------|-------|")
    sun_asp_list = process_aspects(extract_aspects(df, "Sun"))
    for key, days, bp, ad, rg in sun_asp_list:
        h(f"| {key} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # Moon Aspects
    h(f"## 8. MOON ASPECTS")
    h(f"")
    h(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
    h(f"|--------|------|-----------|------|-------|")
    moon_asp_list = process_aspects(extract_aspects(df, "Moon"))
    for key, days, bp, ad, rg in moon_asp_list:
        h(f"| {key} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 8. GANN ═══
    h(f"## 9. GANN KEY LEVEL")
    h(f"")
    h(f"| State | Days | Bullish % | AvgΔ | Range |")
    h(f"|-------|------|-----------|------|-------|")
    for state_val, label in [(True, 'Held'), (False, 'Breached')]:
        col = 'gann_held' if 'gann_held' in df.columns else 'gann_key_level_held'
        if col not in df.columns: continue
        sub = df[df[col] == state_val]
        days = len(sub)
        if days == 0: continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        h(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

    held_sub = df[df.get('gann_held', df.get('gann_key_level_held', pd.Series(dtype=bool))) == True]
    breach_sub = df[df.get('gann_held', df.get('gann_key_level_held', pd.Series(dtype=bool))) == False]
    if len(held_sub) > 0 and len(breach_sub) > 0:
        mult = round(breach_sub['gold_range'].mean() / max(held_sub['gold_range'].mean(), 0.01), 1)
        h(f"")
        h(f"**Key:** Range breached gấp {mult}x held.")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 9. HORA ═══
    h(f"## 10. DOMINANT HORA")
    h(f"")
    h(f"| Hora | Days | Bullish % | AvgΔ | Range |")
    h(f"|------|------|-----------|------|-------|")
    hora_stats = []
    for hora in df['dominant_planet_hour'].dropna().unique():
        if str(hora).strip() == '': continue
        sub = df[df['dominant_planet_hour'] == hora]
        days = len(sub)
        if days == 0: continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hora_stats.append((str(hora), days, bp, ad, rg))
    hora_stats.sort(key=lambda x: x[2], reverse=True)
    for hora, days, bp, ad, rg in hora_stats:
        h(f"| {hora} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 10. MARKET REACTION ═══
    h(f"## 11. MARKET REACTION")
    h(f"")
    h(f"| Reaction | Days | % | Bullish % | AvgΔ | Range |")
    h(f"|----------|------|---|-----------|------|-------|")
    for reaction in df['market_reaction'].dropna().unique():
        if str(reaction).strip() == '': continue
        sub = df[df['market_reaction'] == reaction]
        days = len(sub)
        pct = round(days / total_days * 100, 1)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        h(f"| {reaction} | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 11. VOLATILITY ═══
    h(f"## 12. VOLATILITY REGIMES")
    h(f"")
    h(f"| Volatility | Days | % | Bullish % | AvgΔ | Range |")
    h(f"|------------|------|---|-----------|------|-------|")
    for vol in ['low', 'medium', 'high']:
        sub = df[df['volatility'] == vol]
        days = len(sub)
        pct = round(days / total_days * 100, 1) if total_days else 0
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1) if days > 0 else 0
        ad = round(sub['gold_change_pct'].mean(), 2) if days > 0 else 0
        rg = round(sub['gold_range'].mean(), 1) if days > 0 else 0
        h(f"| {vol} | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 12. ECLIPSE ═══
    h(f"## 13. ECLIPSE PERIODS")
    h(f"")
    eclipse_df = df[df['eclipse_active'] == True]
    if len(eclipse_df) > 0:
        edays = len(eclipse_df)
        ebp = round(len(eclipse_df[eclipse_df['gold_bullish']==True]) / edays * 100, 1)
        ead = round(eclipse_df['gold_change_pct'].mean(), 2)
        erg = round(eclipse_df['gold_range'].mean(), 1)
        h(f"| Metric | Value |")
        h(f"|--------|-------|")
        h(f"| Eclipse Days | {edays} |")
        h(f"| Bullish % | {ebp}% |")
        h(f"| AvgΔ | {ead}% |")
        h(f"| Avg Range | {erg} |")
    else:
        h("*No eclipse days in period.*")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 13. EMA ═══
    h(f"## 14. EMA 31 vs 113")
    h(f"")
    h(f"| EMA State | Days | % | Bullish % | AvgΔ | Range |")
    h(f"|-----------|------|---|-----------|------|-------|")
    for state in ['above', 'below']:
        sub = df[df['gold_ema_relation'] == state]
        days = len(sub)
        pct = round(days / total_days * 100, 1)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1) if days > 0 else 0
        ad = round(sub['gold_change_pct'].mean(), 2) if days > 0 else 0
        rg = round(sub['gold_range'].mean(), 1) if days > 0 else 0
        label = f"EMA31 > EMA113" if state == 'above' else f"EMA31 < EMA113"
        h(f"| {label} | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 14. DXY ═══
    h(f"## 15. DXY CORRELATION")
    h(f"")
    h(f"### DXY Direction → Gold")
    h(f"")
    h(f"| DXY | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    h(f"|-----|------|----------------|-----------|------------|")
    for dxy_dir in ['bullish', 'bearish', 'neutral']:
        sub = df[df['dxy_direction'] == dxy_dir]
        days = len(sub)
        if days == 0: continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        h(f"| {dxy_dir} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 15. US10Y ═══
    us10y_num = pd.to_numeric(df['us10y_close'], errors='coerce')
    us10y_has_data = us10y_num.notna().sum() > 10

    h(f"## 16. US10Y TREASURY YIELD")
    h(f"")
    if not us10y_has_data:
        h("⚠️ **US10Y data not available.** Run `collect_v2.py --fix-us10y` to backfill.")
    else:
        h(f"### Yield Direction → Gold")
        h(f"")
        h(f"| US10Y Δ | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        h(f"|---------|------|----------------|-----------|------------|")
        us10y_chg = pd.to_numeric(df['us10y_change'], errors='coerce')
        for label, sub in [('Rising', df[us10y_chg > 0]), ('Falling', df[us10y_chg < 0])]:
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

        h(f"")
        h(f"### Yield Bands")
        h(f"")
        h(f"| Yield Range | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        h(f"|-------------|------|----------------|-----------|------------|")
        valid = us10y_num.dropna()
        if len(valid) > 0:
            q33, q67 = valid.quantile(0.33), valid.quantile(0.67)
            for label, lo, hi in [('Low', None, q33), ('Mid', q33, q67), ('High', q67, None)]:
                mask = us10y_num <= hi if lo is None else (us10y_num > lo if hi is None else ((us10y_num > lo) & (us10y_num <= hi)))
                sub = df[mask]
                days = len(sub)
                if days == 0: continue
                bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
                ad = round(sub['gold_change_pct'].mean(), 2)
                rg = round(sub['gold_range'].mean(), 1)
                h(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 16. MOON PHASE ═══
    h(f"## 17. MOON PHASE")
    h(f"")
    h(f"| Moon Phase | Days | Bullish % | AvgΔ | Range | HighVol |")
    h(f"|------------|------|-----------|------|-------|---------|")
    for phase in MOON_PHASE_ORDER:
        sub = df[df['moon_phase'] == phase]
        days = len(sub)
        if days == 0: continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        h(f"| {phase} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} | {hv} |")
    h(f"")
    h(f"---")
    h(f"")

    # ─── NEW SECTIONS (v2) ───

    # ═══ 17. NAKSHATRA LORD ═══
    nakshatra_lord_col = 'moon_nakshatra_lord'
    if nakshatra_lord_col in df.columns and df[nakshatra_lord_col].notna().sum() > 10:
        h(f"## 18. NAKSHATRA LORD → TREND 🆕")
        h(f"")
        h(f"| Nakshatra Lord | Days | Bullish % | AvgΔ | Range | HighVol |")
        h(f"|----------------|------|-----------|------|-------|---------|")
        lord_stats = []
        for lord in df[nakshatra_lord_col].dropna().unique():
            if str(lord).strip() == '': continue
            sub = df[df[nakshatra_lord_col] == lord]
            days = len(sub)
            if days < 5: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            hv = len(sub[sub['volatility']=='high'])
            lord_stats.append((str(lord), days, bp, ad, rg, hv))
        lord_stats.sort(key=lambda x: x[2], reverse=True)
        for lord, days, bp, ad, rg, hv in lord_stats:
            h(f"| {lord} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} | {hv} |")
        if lord_stats:
            h(f"")
            h(f"**Key:** {lord_stats[0][0]}-ruled nakshatras strongest ({lord_stats[0][2]}%), "
              f"{lord_stats[-1][0]}-ruled weakest ({lord_stats[-1][2]}%).")
    else:
        h(f"## 18. NAKSHATRA LORD 🆕")
        h("")
        h("⚠️ `moon_nakshatra_lord` column not available. Run `collect_v2.py` to add.")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 18. RAHU/KETU ASPECTS ═══
    h(f"## 19. RAHU & KETU ASPECTS 🆕")
    h(f"")

    rahu_aspects = []
    ketu_aspects = []
    for _, row in df.iterrows():
        aj = row.get('aspects_json', '[]')
        if pd.isna(aj) or str(aj).strip() == '': continue
        try: aspects = json.loads(aj)
        except: continue
        for asp in aspects:
            p1, p2 = asp['planet1'], asp['planet2']
            for node in ['Rahu', 'Ketu']:
                if node in (p1, p2):
                    other = p2 if p1 == node else p1
                    key = f"{node} {asp['aspect']} {other}"
                    entry = (key, row['gold_bullish'], row['gold_change_pct'], row['gold_range'])
                    if node == 'Rahu': rahu_aspects.append(entry)
                    else: ketu_aspects.append(entry)

    rahu_asp_list = process_aspects(rahu_aspects, min_days=5)
    ketu_asp_list = process_aspects(ketu_aspects, min_days=5)

    if rahu_asp_list:
        h(f"### Rahu (North Node) Aspects")
        h(f"")
        h(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
        h(f"|--------|------|-----------|------|-------|")
        for key, days, bp, ad, rg in rahu_asp_list:
            h(f"| {key} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

    if ketu_asp_list:
        h(f"")
        h(f"### Ketu (South Node) Aspects")
        h(f"")
        h(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
        h(f"|--------|------|-----------|------|-------|")
        for key, days, bp, ad, rg in ketu_asp_list:
            h(f"| {key} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

    if not rahu_asp_list and not ketu_asp_list:
        h("*Insufficient data for Rahu/Ketu aspect analysis.*")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 19. S&P 500 CORRELATION ═══
    sp500_col = 'sp500_change_pct'
    if sp500_col in df.columns:
        sp500_num = pd.to_numeric(df[sp500_col], errors='coerce')
        sp500_has = sp500_num.notna().sum() > 10
    else:
        sp500_has = False

    h(f"## 20. S&P 500 CORRELATION 🆕")
    h(f"")
    if not sp500_has:
        h("⚠️ S&P 500 data not available. Run `collect_v2.py` to add.")
    else:
        h(f"### S&P 500 Direction → Gold")
        h(f"")
        h(f"| S&P 500 | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        h(f"|---------|------|----------------|-----------|------------|")
        for label, mask in [('Rising', sp500_num > 0), ('Falling', sp500_num < 0), ('Flat', sp500_num == 0)]:
            sub = df[mask]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 20. VIX CORRELATION ═══
    vix_col = 'vix_close'
    if vix_col in df.columns:
        vix_num = pd.to_numeric(df[vix_col], errors='coerce')
        vix_has = vix_num.notna().sum() > 10
    else:
        vix_has = False

    h(f"## 21. VIX (FEAR INDEX) CORRELATION 🆕")
    h(f"")
    if not vix_has:
        h("⚠️ VIX data not available. Run `collect_v2.py` to add.")
    else:
        h(f"### VIX Bands → Gold")
        h(f"")
        h(f"| VIX Band | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        h(f"|----------|------|----------------|-----------|------------|")
        valid_vix = vix_num.dropna()
        if len(valid_vix) > 0:
            q33, q67 = valid_vix.quantile(0.33), valid_vix.quantile(0.67)
            for label, lo, hi in [('Low (<{:.1f})'.format(q33), None, q33),
                                   ('Mid', q33, q67),
                                   ('High (>{:.1f})'.format(q67), q67, None)]:
                mask = vix_num <= hi if lo is None else (vix_num > lo if hi is None else ((vix_num > lo) & (vix_num <= hi)))
                sub = df[mask]
                days = len(sub)
                if days == 0: continue
                bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
                ad = round(sub['gold_change_pct'].mean(), 2)
                rg = round(sub['gold_range'].mean(), 1)
                h(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 21. MULTI-FACTOR CONFLUENCE ═══
    h(f"## 22. MULTI-FACTOR CONFLUENCE 🆕")
    h(f"")
    h("*Top 3-factor combinations ranked by bullish % (min 10 days)*")
    h(f"")

    # Define factors
    factors = {}
    factors['Moon Sign'] = df['moon_sign'].fillna('').astype(str)
    factors['Nakshatra'] = df['moon_nakshatra'].fillna('').astype(str)
    factors['Moon Phase'] = df['moon_phase'].fillna('').astype(str)
    factors['Hora'] = df['dominant_planet_hour'].fillna('').astype(str)
    factors['DXY'] = df['dxy_direction'].fillna('').astype(str)
    factors['EMA'] = df['gold_ema_relation'].fillna('').astype(str)
    factors['Volatility'] = df['volatility'].fillna('').astype(str)

    # Find all combinations of factor keys that have enough data
    factor_keys = list(factors.keys())
    conf_results = []

    for combo in combinations(factor_keys, 3):
        f1, f2, f3 = combo
        # Get unique values for each factor
        vals1 = [v for v in factors[f1].unique() if v]
        vals2 = [v for v in factors[f2].unique() if v]
        vals3 = [v for v in factors[f3].unique() if v]

        # Try top 3 values per factor
        for v1 in vals1[:5]:
            for v2 in vals2[:5]:
                for v3 in vals3[:5]:
                    mask = (factors[f1] == v1) & (factors[f2] == v2) & (factors[f3] == v3)
                    sub = df[mask]
                    if len(sub) < 10: continue
                    bp = round(len(sub[sub['gold_bullish']==True]) / len(sub) * 100, 1)
                    ad = round(sub['gold_change_pct'].mean(), 2)
                    conf_results.append((bp, len(sub), ad, f"{v1}/{v2}/{v3}", f"{f1}+{f2}+{f3}"))

    conf_results.sort(key=lambda x: (x[0], x[1]), reverse=True)

    if conf_results:
        h(f"| Rank | Factors | Combo | Days | Bullish % | AvgΔ |")
        h(f"|------|---------|-------|------|-----------|------|")
        for i, (bp, days, ad, combo_val, combo_name) in enumerate(conf_results[:20]):
            h(f"| {i+1} | {combo_name} | {combo_val} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% |")
    else:
        h("*Insufficient data for multi-factor analysis.*")
    h(f"")
    h(f"---")
    h(f"")

    # ═══ 22. TECHNICAL INDICATORS ═══
    h(f"## 23. TECHNICAL INDICATORS 🆕")
    h(f"")

    # RSI
    rsi_col = 'gold_rsi_14'
    if rsi_col in df.columns:
        rsi_num = pd.to_numeric(df[rsi_col], errors='coerce')
        rsi_has = rsi_num.notna().sum() > 10
    else:
        rsi_has = False

    if rsi_has:
        h(f"### RSI(14) Bands → Next-Day Trend")
        h(f"")
        h(f"| RSI Band | Days | Bullish % | AvgΔ | Range |")
        h(f"|----------|------|-----------|------|-------|")
        for label, lo, hi in [('Oversold (<30)', 0, 30), ('Weak (30-50)', 30, 50),
                               ('Strong (50-70)', 50, 70), ('Overbought (>70)', 70, 100)]:
            mask = (rsi_num >= lo) & (rsi_num < hi)
            sub = df[mask]
            days = len(sub)
            if days == 0: continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")

    # ATR
    atr_col = 'gold_atr_14'
    if atr_col in df.columns:
        atr_num = pd.to_numeric(df[atr_col], errors='coerce')
        atr_has = atr_num.notna().sum() > 10
    else:
        atr_has = False

    if atr_has:
        h(f"")
        h(f"### ATR(14) Bands → Trend")
        h(f"")
        h(f"| ATR Band | Days | Bullish % | AvgΔ | Range |")
        h(f"|----------|------|-----------|------|-------|")
        valid_atr = atr_num.dropna()
        if len(valid_atr) > 0:
            q50 = valid_atr.median()
            for label, mask in [('Below Median', atr_num <= q50), ('Above Median', atr_num > q50)]:
                sub = df[mask]
                days = len(sub)
                if days == 0: continue
                bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
                ad = round(sub['gold_change_pct'].mean(), 2)
                rg = round(sub['gold_range'].mean(), 1)
                h(f"| {label} | {days} | **{bp}%** | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    else:
        h("⚠️ ATR/RSI data not available. Run `collect_v2.py` to add.")

    h(f"")
    h(f"---")
    h(f"")

    # ═══ 23. KEY FINDINGS ═══
    h(f"## 🔑 KEY FINDINGS")
    h(f"")

    if nak_stats:
        h(f"- **Nakshatra:** {nak_stats[0][0]} {nak_stats[0][2]}% vs {nak_stats[-1][0]} {nak_stats[-1][2]}% (spread {nak_stats[0][2]-nak_stats[-1][2]}%)")
    if moon_sign_stats:
        h(f"- **Moon Sign:** {moon_sign_stats[0][0]} {moon_sign_stats[0][2]}% bullish; {moon_sign_stats[-1][0]} {moon_sign_stats[-1][2]}% weakest")
    for planet in retro_planets:
        if planet in retro_stats and 'Retro' in retro_stats[planet] and 'Direct' in retro_stats[planet]:
            delta = retro_stats[planet]['Retro'] - retro_stats[planet]['Direct']
            if abs(delta) > 2:
                h(f"- **{planet.capitalize()} Retro:** {'bullish' if delta>0 else 'bearish'} hơn direct ({'+' if delta>=0 else ''}{round(delta,1)}% delta)")
    if sun_asp_list:
        h(f"- **Top Sun Aspect:** {sun_asp_list[0][0]} — {sun_asp_list[0][2]}% bullish ({sun_asp_list[0][1]} days)")
    if moon_asp_list:
        h(f"- **Top Moon Aspect:** {moon_asp_list[0][0]} — {moon_asp_list[0][2]}% bullish ({moon_asp_list[0][1]} days)")
    if hora_stats:
        h(f"- **Hora:** {hora_stats[0][0]} {hora_stats[0][2]}% bullish; {hora_stats[-1][0]} {hora_stats[-1][2]}% weakest")
    reversal_pct = round(len(df[df['market_reaction']=='reversal_signal']) / total_days * 100, 1)
    strong_pct = round(len(df[df['market_reaction']=='strong_trend']) / total_days * 100, 1)
    h(f"- **Market:** {reversal_pct}% reversal, {strong_pct}% strong trend")
    h(f"- **DXY inverse:** DXY bullish→Gold {round(len(df[(df['dxy_direction']=='bullish')&(df['gold_bullish']==True)])/max(len(df[df['dxy_direction']=='bullish']),1)*100,1)}% bullish; DXY bearish→Gold {round(len(df[(df['dxy_direction']=='bearish')&(df['gold_bullish']==True)])/max(len(df[df['dxy_direction']=='bearish']),1)*100,1)}% bullish")

    if conf_results:
        h(f"- **Best Combo:** {conf_results[0][3]} ({conf_results[0][4]}) — {conf_results[0][0]}% bullish over {conf_results[0][1]} days")

    h(f"")
    h(f"---")
    h(f"")
    h(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | {date_start} → {date_end} | {total_days} days*")

    # Write
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"  ✅ {period_name}: {total_days} days → {output_path}")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 analyze_v2.py --full         Full 10-year report")
        print("  python3 analyze_v2.py --yearly       All yearly reports")
        print("  python3 analyze_v2.py --year 2025    Single year")
        print("  python3 analyze_v2.py --audit        Data quality audit")
        sys.exit(1)

    print("Loading data...")
    df = load_all_data()
    df['date'] = pd.to_datetime(df['date'])
    print(f"  {len(df)} rows loaded")

    if '--audit' in sys.argv:
        audit = audit_data(df)
        path = os.path.join(REPORTS_DIR, "DATA_AUDIT.md")
        with open(path, 'w') as f: f.write(audit)
        print(f"\n{audit[:2000]}")
        print(f"\n... saved to {path}")
        return

    if '--year' in sys.argv:
        idx = sys.argv.index('--year')
        year = int(sys.argv[idx + 1])
        if year == 2016:
            mask = (df['date'] >= '2016-06-01') & (df['date'] <= '2016-12-31')
            period_name = f"{year} (Jun-Dec)"
        elif year == 2026:
            mask = (df['date'] >= '2026-01-01') & (df['date'] <= '2026-05-31')
            period_name = f"{year} (Jan-May)"
        else:
            mask = (df['date'] >= f'{year}-01-01') & (df['date'] <= f'{year}-12-31')
            period_name = str(year)
        sub = df[mask]
        path = os.path.join(REPORTS_DIR, f"ANALYSIS_REPORT_{year}.md")
        analyze_period(sub, period_name, path)
        return

    if '--yearly' in sys.argv:
        for year in range(2016, 2027):
            if year == 2016:
                mask = (df['date'] >= '2016-06-01') & (df['date'] <= '2016-12-31')
                period_name = f"{year} (Jun-Dec)"
            elif year == 2026:
                mask = (df['date'] >= '2026-01-01') & (df['date'] <= '2026-05-31')
                period_name = f"{year} (Jan-May)"
            else:
                mask = (df['date'] >= f'{year}-01-01') & (df['date'] <= f'{year}-12-31')
                period_name = str(year)
            sub = df[mask]
            if len(sub) == 0: continue
            path = os.path.join(REPORTS_DIR, f"ANALYSIS_REPORT_{year}.md")
            analyze_period(sub, period_name, path)
            print()
        return

    if '--full' in sys.argv:
        mask = (df['date'] >= '2016-06-01') & (df['date'] <= '2026-05-31')
        path = os.path.join(REPORTS_DIR, "ANALYSIS_REPORT_FULL_2016-06_2026-05.md")
        analyze_period(df[mask], "2016-06 → 2026-05 (10Y)", path)
        return


if __name__ == "__main__":
    main()
