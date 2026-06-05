#!/usr/bin/env python3
"""
analyze_yearly.py — Generate per-year analysis reports from patreon-db data.
Follows the format of ANALYSIS_REPORT_FULL_2022-01_2026-05.md
"""

import os
import sys
import json
import math
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

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

def analyze_period(df, period_name, output_path):
    """Generate full analysis report for a DataFrame slice."""
    
    total_days = len(df)
    if total_days == 0:
        print(f"  No data for {period_name}")
        return
    
    bullish_days = len(df[df['gold_bullish'] == True])
    bearish_days = len(df[df['gold_bullish'] == False])
    bullish_pct = round(bullish_days / total_days * 100, 1)
    bearish_pct = round(bearish_days / total_days * 100, 1)
    avg_change = round(df['gold_change_pct'].mean(), 3)
    std_change = round(df['gold_change_pct'].std(), 3)
    avg_range = round(df['gold_range'].mean(), 2)
    
    # Date range
    date_start = df['date'].min().strftime('%Y-%m-%d')
    date_end = df['date'].max().strftime('%Y-%m-%d')
    
    report = []
    report.append(f"# 📊 Phân Tích Dữ Liệu Gold (XAUUSD)")
    report.append(f"")
    report.append(f"**Giai đoạn:** {date_start} → {date_end} ({total_days} trading days)")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 1. BASELINE ═══
    report.append(f"## 1. BASELINE")
    report.append(f"")
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| Total Trading Days | {total_days} |")
    report.append(f"| Bullish Days (close > open) | {bullish_pct}% |")
    report.append(f"| Bearish Days | {bearish_pct}% |")
    report.append(f"| Avg Daily Change | {avg_change}% |")
    report.append(f"| Std Daily Change | {std_change}% |")
    report.append(f"| Avg Daily Range | {avg_range} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 2. MOON SIGN ═══
    report.append(f"## 2. MOON SIGN → TREND")
    report.append(f"")
    report.append(f"| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |")
    report.append(f"|-----------|------|-----------|------|-------|---------|")
    
    moon_sign_stats = []
    for sign in ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']:
        mask = df['moon_sign'] == sign
        sub = df[mask]
        if len(sub) == 0:
            continue
        days = len(sub)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        moon_sign_stats.append((sign, days, bp, ad, rg, hv))
    
    moon_sign_stats.sort(key=lambda x: x[2], reverse=True)
    for sign, days, bp, ad, rg, hv in moon_sign_stats:
        ad_str = f"+{ad}" if ad > 0 else str(ad)
        report.append(f"| {sign} | {days} | **{bp}%** | {ad_str}% | {rg} | {hv} |")
    
    strongest = moon_sign_stats[0] if moon_sign_stats else None
    weakest = moon_sign_stats[-1] if moon_sign_stats else None
    report.append(f"")
    if strongest and weakest:
        report.append(f"**Key:** {strongest[0]} ({strongest[2]}% bullish) mạnh nhất. {weakest[0]} ({weakest[2]}% bullish) yếu nhất.")
        # Find highest range
        hv_sign = max(moon_sign_stats, key=lambda x: x[4])
        report.append(f"{hv_sign[0]} có biên độ lớn nhất ({hv_sign[4]}).")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 3. MOON NAKSHATRA ═══
    report.append(f"## 3. MOON NAKSHATRA → TREND")
    report.append(f"")
    report.append(f"| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |")
    report.append(f"|-----------|------|-----------|------|-------|---------|")
    
    nak_stats = []
    for nak in df['moon_nakshatra'].unique():
        if pd.isna(nak) or str(nak).strip() == '':
            continue
        sub = df[df['moon_nakshatra'] == nak]
        days = len(sub)
        if days < 5:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        nak_stats.append((str(nak), days, bp, ad, rg, hv))
    
    nak_stats.sort(key=lambda x: x[2], reverse=True)
    for nak, days, bp, ad, rg, hv in nak_stats:
        ad_str = f"+{ad}" if ad > 0 else str(ad)
        report.append(f"| {nak} | {days} | **{bp}%** | {ad_str}% | {rg} | {hv} |")
    
    report.append(f"")
    if nak_stats:
        top_nak = nak_stats[0]
        bot_nak = nak_stats[-1]
        spread = top_nak[2] - bot_nak[2]
        report.append(f"**Key:** Nakshatra là predictor mạnh nhất. {top_nak[0]} {top_nak[2]}% bullish vs {bot_nak[0]} {bot_nak[2]}% — chênh lệch {spread}%.")
        report.append(f"- **Bullish cluster:** {', '.join([n[0] for n in nak_stats if n[2] >= 55])}")
        report.append(f"- **Bearish cluster:** {', '.join([n[0] for n in nak_stats if n[2] <= 45])}")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 4. PLANET RETROGRADE ═══
    report.append(f"## 4. PLANET RETROGRADE")
    report.append(f"")
    report.append(f"| Planet | State | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|--------|-------|------|-----------|------|-------|")
    
    retro_planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
    retro_stats = {}
    for planet in retro_planets:
        col = f"{planet}_retro"
        if col not in df.columns:
            continue
        for state, label in [(True, 'Retro'), (False, 'Direct')]:
            sub = df[df[col] == state]
            days = len(sub)
            if days == 0:
                continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            report.append(f"| {planet.capitalize()} | {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
            if planet not in retro_stats:
                retro_stats[planet] = {}
            retro_stats[planet][label] = bp
    
    report.append(f"")
    report.append(f"### Retro vs Direct Delta")
    report.append(f"")
    report.append(f"| Planet | Retro % | Direct % | Delta |")
    report.append(f"|--------|---------|----------|-------|")
    for planet in retro_planets:
        if planet in retro_stats and 'Retro' in retro_stats[planet] and 'Direct' in retro_stats[planet]:
            rp = retro_stats[planet]['Retro']
            dp = retro_stats[planet]['Direct']
            delta = rp - dp
            emoji = "🟢" if delta > 0 else "🔴"
            report.append(f"| {planet.capitalize()} | {rp}% | {dp}% | {emoji} {'+' if delta >= 0 else ''}{round(delta,1)}% |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 5. COMBUST ═══
    report.append(f"## 5. COMBUST (GẦN MẶT TRỜI)")
    report.append(f"")
    report.append(f"| Planet | State | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|--------|-------|------|-----------|------|-------|")
    
    combust_planets = ['mercury', 'venus', 'mars']
    for planet in combust_planets:
        col = f"{planet}_combust"
        if col not in df.columns:
            continue
        for state, label in [(True, 'Combust'), (False, 'Not Combust')]:
            sub = df[df[col] == state]
            days = len(sub)
            if days == 0:
                continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            report.append(f"| {planet.capitalize()} | {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 6. SUN ASPECTS ═══
    report.append(f"## 6. SUN ASPECTS TO PLANETS")
    report.append(f"")
    
    sun_aspects = []
    for _, row in df.iterrows():
        aspects_json = row.get('aspects_json', '[]')
        if pd.isna(aspects_json) or str(aspects_json).strip() == '':
            continue
        try:
            aspects = json.loads(aspects_json)
        except:
            continue
        for asp in aspects:
            p1, p2 = asp.get('planet1',''), asp.get('planet2','')
            asp_type = asp.get('aspect','')
            if 'Sun' in (p1, p2):
                other = p2 if p1 == 'Sun' else p1
                key = f"Sun {asp_type} {other}"
                sun_aspects.append((key, row['gold_bullish'], row['gold_change_pct'], row['gold_range']))
    
    sun_asp_stats = defaultdict(lambda: {'days': 0, 'bullish': 0, 'changes': [], 'ranges': []})
    for key, bull, chg, rng in sun_aspects:
        sun_asp_stats[key]['days'] += 1
        if bull:
            sun_asp_stats[key]['bullish'] += 1
        sun_asp_stats[key]['changes'].append(chg)
        sun_asp_stats[key]['ranges'].append(rng)
    
    sun_asp_list = []
    for key, stats in sun_asp_stats.items():
        if stats['days'] < 3:
            continue
        bp = round(stats['bullish'] / stats['days'] * 100, 1)
        ad = round(np.mean(stats['changes']), 2)
        rg = round(np.mean(stats['ranges']), 1)
        sun_asp_list.append((key, stats['days'], bp, ad, rg))
    
    sun_asp_list.sort(key=lambda x: x[2], reverse=True)
    
    report.append(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|--------|------|-----------|------|-------|")
    for key, days, bp, ad, rg in sun_asp_list:
        ad_str = f"+{ad}" if ad >= 0 else str(ad)
        report.append(f"| {key} | {days} | **{bp}%** | {ad_str}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 7. MOON ASPECTS ═══
    report.append(f"## 7. MOON ASPECTS TO PLANETS")
    report.append(f"")
    
    moon_aspects = []
    for _, row in df.iterrows():
        aspects_json = row.get('aspects_json', '[]')
        if pd.isna(aspects_json) or str(aspects_json).strip() == '':
            continue
        try:
            aspects = json.loads(aspects_json)
        except:
            continue
        for asp in aspects:
            p1, p2 = asp.get('planet1',''), asp.get('planet2','')
            asp_type = asp.get('aspect','')
            if 'Moon' in (p1, p2):
                other = p2 if p1 == 'Moon' else p1
                key = f"Moon {asp_type} {other}"
                moon_aspects.append((key, row['gold_bullish'], row['gold_change_pct'], row['gold_range']))
    
    moon_asp_stats = defaultdict(lambda: {'days': 0, 'bullish': 0, 'changes': [], 'ranges': []})
    for key, bull, chg, rng in moon_aspects:
        moon_asp_stats[key]['days'] += 1
        if bull:
            moon_asp_stats[key]['bullish'] += 1
        moon_asp_stats[key]['changes'].append(chg)
        moon_asp_stats[key]['ranges'].append(rng)
    
    moon_asp_list = []
    for key, stats in moon_asp_stats.items():
        if stats['days'] < 3:
            continue
        bp = round(stats['bullish'] / stats['days'] * 100, 1)
        ad = round(np.mean(stats['changes']), 2)
        rg = round(np.mean(stats['ranges']), 1)
        moon_asp_list.append((key, stats['days'], bp, ad, rg))
    
    moon_asp_list.sort(key=lambda x: x[2], reverse=True)
    
    report.append(f"| Aspect | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|--------|------|-----------|------|-------|")
    for key, days, bp, ad, rg in moon_asp_list:
        ad_str = f"+{ad}" if ad >= 0 else str(ad)
        report.append(f"| {key} | {days} | **{bp}%** | {ad_str}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 8. GANN KEY LEVEL ═══
    report.append(f"## 8. GANN KEY LEVEL HELD vs BREACHED")
    report.append(f"")
    report.append(f"| State | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|-------|------|-----------|------|-------|")
    
    for state_val, state_label in [(True, 'Held'), (False, 'Breached')]:
        # Use gann_held column if available, otherwise use gann_key_level_held
        if 'gann_held' in df.columns:
            sub = df[df['gann_held'] == state_val]
        elif 'gann_key_level_held' in df.columns:
            sub = df[df['gann_key_level_held'] == state_val]
        else:
            continue
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {state_label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    
    # Calculate multiplier
    held_sub = df[df.get('gann_held', df.get('gann_key_level_held', pd.Series(dtype=bool))) == True]
    breach_sub = df[df.get('gann_held', df.get('gann_key_level_held', pd.Series(dtype=bool))) == False]
    if len(held_sub) > 0 and len(breach_sub) > 0:
        held_range = held_sub['gold_range'].mean()
        breach_range = breach_sub['gold_range'].mean()
        mult = round(breach_range / held_range, 1) if held_range > 0 else 0
        report.append(f"")
        report.append(f"**Key:** Range khi breached gấp {mult}x so với held.")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 9. HORA ═══
    report.append(f"## 9. DOMINANT PLANET HOUR (HORA)")
    report.append(f"")
    report.append(f"| Hora | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|------|------|-----------|------|-------|")
    
    hora_stats = []
    for hora in df['dominant_planet_hour'].unique():
        if pd.isna(hora) or str(hora).strip() == '':
            continue
        sub = df[df['dominant_planet_hour'] == hora]
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hora_stats.append((str(hora), days, bp, ad, rg))
    
    hora_stats.sort(key=lambda x: x[2], reverse=True)
    for hora, days, bp, ad, rg in hora_stats:
        ad_str = f"+{ad}" if ad >= 0 else str(ad)
        report.append(f"| {hora} | {days} | {bp}% | {ad_str}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 10. MARKET REACTION ═══
    report.append(f"## 10. MARKET REACTION DISTRIBUTION")
    report.append(f"")
    report.append(f"| Reaction | Days | % of Total | Bullish % | AvgΔ | Range |")
    report.append(f"|----------|------|------------|-----------|------|-------|")
    
    for reaction in df['market_reaction'].unique():
        if pd.isna(reaction) or str(reaction).strip() == '':
            continue
        sub = df[df['market_reaction'] == reaction]
        days = len(sub)
        pct = round(days / total_days * 100, 1)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {reaction} | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 11. VOLATILITY REGIMES ═══
    report.append(f"## 11. VOLATILITY REGIMES")
    report.append(f"")
    report.append(f"| Volatility | Days | % of Total | Bullish % | AvgΔ | Range |")
    report.append(f"|------------|------|------------|-----------|------|-------|")
    
    for vol in ['low', 'medium', 'high']:
        sub = df[df['volatility'] == vol]
        days = len(sub)
        pct = round(days / total_days * 100, 1)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1) if days > 0 else 0
        ad = round(sub['gold_change_pct'].mean(), 2) if days > 0 else 0
        rg = round(sub['gold_range'].mean(), 1) if days > 0 else 0
        report.append(f"| {vol} | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 12. ECLIPSE ═══
    report.append(f"## 12. ECLIPSE PERIODS")
    report.append(f"")
    eclipse_df = df[df['eclipse_active'] == True]
    if len(eclipse_df) > 0:
        eclipse_days = len(eclipse_df)
        eclipse_bp = round(len(eclipse_df[eclipse_df['gold_bullish']==True]) / eclipse_days * 100, 1)
        eclipse_ad = round(eclipse_df['gold_change_pct'].mean(), 2)
        eclipse_rg = round(eclipse_df['gold_range'].mean(), 1)
        report.append(f"| Metric | Value |")
        report.append(f"|--------|-------|")
        report.append(f"| Eclipse Days | {eclipse_days} |")
        report.append(f"| Bullish % | {eclipse_bp}% |")
        report.append(f"| AvgΔ | {eclipse_ad}% |")
        report.append(f"| Avg Range | {eclipse_rg} |")
    else:
        report.append(f"*No eclipse days in this period.*")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 13. EMA RELATION ═══
    report.append(f"## 13. EMA 31 vs EMA 113 RELATION")
    report.append(f"")
    report.append(f"| EMA State | Days | % | Bullish % | AvgΔ | Range |")
    report.append(f"|-----------|------|---|-----------|------|-------|")
    
    for state in ['above', 'below']:
        sub = df[df['gold_ema_relation'] == state]
        days = len(sub)
        pct = round(days / total_days * 100, 1)
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1) if days > 0 else 0
        ad = round(sub['gold_change_pct'].mean(), 2) if days > 0 else 0
        rg = round(sub['gold_range'].mean(), 1) if days > 0 else 0
        report.append(f"| EMA31 {'>' if state == 'above' else '<'} EMA113 | {days} | {pct}% | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    
    # EMA × Moon Sign (top combos)
    report.append(f"")
    report.append(f"### EMA State × Moon Sign (Top Signals)")
    report.append(f"")
    report.append(f"| EMA State | Moon Sign | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|-----------|-----------|------|-----------|------|-------|")
    
    ema_moon = []
    for ema_state in ['above', 'below']:
        ema_sub = df[df['gold_ema_relation'] == ema_state]
        for sign in ema_sub['moon_sign'].unique():
            if pd.isna(sign) or str(sign).strip() == '':
                continue
            sub = ema_sub[ema_sub['moon_sign'] == sign]
            days = len(sub)
            if days < 10:
                continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            ema_moon.append((ema_state, str(sign), days, bp, ad, rg))
    
    ema_moon.sort(key=lambda x: x[3], reverse=True)
    for ema_state, sign, days, bp, ad, rg in ema_moon[:15]:
        ad_str = f"+{ad}" if ad >= 0 else str(ad)
        report.append(f"| {ema_state} | {sign} | {days} | **{bp}%** | {ad_str}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 14. DXY CORRELATION ═══
    report.append(f"## 14. DXY (DOLLAR INDEX) CORRELATION")
    report.append(f"")
    report.append(f"### DXY Direction → Gold Trend")
    report.append(f"")
    report.append(f"| DXY Direction | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    report.append(f"|---------------|------|----------------|-----------|------------|")
    
    for dxy_dir in ['bullish', 'bearish', 'neutral']:
        sub = df[df['dxy_direction'] == dxy_dir]
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {dxy_dir} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    
    # DXY magnitude
    report.append(f"")
    report.append(f"### DXY Change Magnitude → Gold Reaction")
    report.append(f"")
    report.append(f"| DXY |Δ| | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    report.append(f"|------|------|-------|----------------|-----------|------------|")
    
    dxy_high = df[pd.to_numeric(df['dxy_change_pct'], errors='coerce').abs() >= 0.5]
    dxy_low = df[pd.to_numeric(df['dxy_change_pct'], errors='coerce').abs() < 0.5]
    for label, sub in [('≥0.5%', dxy_high), ('<0.5%', dxy_low)]:
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    
    # DXY level bands
    report.append(f"")
    report.append(f"### DXY Level Bands")
    report.append(f"")
    report.append(f"| DXY Range | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    report.append(f"|-----------|------|----------------|-----------|------------|")
    
    dxy_numeric = pd.to_numeric(df['dxy_close'], errors='coerce')
    if dxy_numeric.notna().sum() > 0:
        q33 = dxy_numeric.quantile(0.33)
        q67 = dxy_numeric.quantile(0.67)
        for label, lo, hi in [('Low', None, q33), ('Mid', q33, q67), ('High', q67, None)]:
            if lo is None:
                sub = df[dxy_numeric <= hi]
            elif hi is None:
                sub = df[dxy_numeric > lo]
            else:
                sub = df[(dxy_numeric > lo) & (dxy_numeric <= hi)]
            days = len(sub)
            if days == 0:
                continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            report.append(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 15. US10Y CORRELATION ═══
    report.append(f"## 15. US 10Y TREASURY YIELD CORRELATION")
    report.append(f"")
    report.append(f"### Yield Change Direction → Gold")
    report.append(f"")
    report.append(f"| US10Y Change | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    report.append(f"|--------------|------|----------------|-----------|------------|")
    
    us10y_num = pd.to_numeric(df['us10y_close'], errors='coerce')
    us10y_chg = pd.to_numeric(df['us10y_change'], errors='coerce')
    
    rising = df[us10y_chg > 0]
    falling = df[us10y_chg < 0]
    for label, sub in [('Rising', rising), ('Falling', falling)]:
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    
    # US10Y level bands
    report.append(f"")
    report.append(f"### Yield Level Bands")
    report.append(f"")
    report.append(f"| US10Y Range | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
    report.append(f"|-------------|------|----------------|-----------|------------|")
    
    if us10y_num.notna().sum() > 0:
        q33 = us10y_num.quantile(0.33)
        q67 = us10y_num.quantile(0.67)
        for label, lo, hi in [('Low', None, q33), ('Mid', q33, q67), ('High', q67, None)]:
            if lo is None:
                sub = df[us10y_num <= hi]
            elif hi is None:
                sub = df[us10y_num > lo]
            else:
                sub = df[(us10y_num > lo) & (us10y_num <= hi)]
            days = len(sub)
            if days == 0:
                continue
            bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
            ad = round(sub['gold_change_pct'].mean(), 2)
            rg = round(sub['gold_range'].mean(), 1)
            report.append(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 16. MOON PHASE ═══
    report.append(f"## 16. MOON PHASE → TREND")
    report.append(f"")
    report.append(f"| Moon Phase | Days | Bullish % | AvgΔ | Range | HighVol |")
    report.append(f"|------------|------|-----------|------|-------|---------|")
    
    phase_order = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
                   'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
    for phase in phase_order:
        sub = df[df['moon_phase'] == phase]
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        hv = len(sub[sub['volatility']=='high'])
        report.append(f"| {phase} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} | {hv} |")
    
    # Moon illumination bands
    report.append(f"")
    report.append(f"### Moon Illumination Bands")
    report.append(f"")
    report.append(f"| Illumination % | Days | Bullish % | AvgΔ | Range |")
    report.append(f"|----------------|------|-----------|------|-------|")
    
    illum = pd.to_numeric(df['moon_illumination_pct'], errors='coerce')
    for label, lo, hi in [('0-25% (Dark)', 0, 25), ('25-50% (Growing)', 25, 50), 
                          ('50-75% (Bright)', 50, 75), ('75-100% (Full)', 75, 101)]:
        sub = df[(illum >= lo) & (illum < hi)]
        days = len(sub)
        if days == 0:
            continue
        bp = round(len(sub[sub['gold_bullish']==True]) / days * 100, 1)
        ad = round(sub['gold_change_pct'].mean(), 2)
        rg = round(sub['gold_range'].mean(), 1)
        report.append(f"| {label} | {days} | {bp}% | {'+' if ad >= 0 else ''}{ad}% | {rg} |")
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    
    # ═══ 17. KEY FINDINGS ═══
    report.append(f"## 🔑 KEY FINDINGS SUMMARY")
    report.append(f"")
    
    # Nakshatra
    if nak_stats:
        top_nak = nak_stats[0]
        bot_nak = nak_stats[-1]
        spread = top_nak[2] - bot_nak[2]
        report.append(f"- **Nakshatra strongest predictor:** {top_nak[0]} {top_nak[2]}% bullish vs {bot_nak[0]} {bot_nak[2]}% ({spread}% spread)")
    
    # Moon Sign
    if moon_sign_stats:
        report.append(f"- **Moon Sign:** {moon_sign_stats[0][0]} {moon_sign_stats[0][2]}% bullish; {moon_sign_stats[-1][0]} {moon_sign_stats[-1][2]}% weakest")
    
    # Retrograde
    for planet in retro_planets:
        if planet in retro_stats and 'Retro' in retro_stats[planet] and 'Direct' in retro_stats[planet]:
            delta = retro_stats[planet]['Retro'] - retro_stats[planet]['Direct']
            if abs(delta) > 2:
                direction = "bullish hơn" if delta > 0 else "bearish hơn"
                report.append(f"- **{planet.capitalize()} Retro:** {direction} direct ({'+' if delta >= 0 else ''}{round(delta,1)}% delta)")
    
    # Combust
    for planet in combust_planets:
        col = f"{planet}_combust"
        if col not in df.columns:
            continue
        combust_sub = df[df[col] == True]
        not_combust_sub = df[df[col] == False]
        if len(combust_sub) > 5:
            c_bp = round(len(combust_sub[combust_sub['gold_bullish']==True]) / len(combust_sub) * 100, 1)
            nc_bp = round(len(not_combust_sub[not_combust_sub['gold_bullish']==True]) / len(not_combust_sub) * 100, 1)
            delta = c_bp - nc_bp
            report.append(f"- **{planet.capitalize()} Combust:** {c_bp}% bullish, range {round(combust_sub['gold_range'].mean(),1)} ({'+' if delta >= 0 else ''}{round(delta,1)}% vs not combust)")
    
    # Gann
    if len(held_sub) > 0 and len(breach_sub) > 0:
        report.append(f"- **Gann Key Held:** range {round(held_sub['gold_range'].mean(),1)} vs {round(breach_sub['gold_range'].mean(),1)} breached ({mult}x)")
    
    # Top Sun aspect
    if sun_asp_list:
        report.append(f"- **Top Sun Aspect:** {sun_asp_list[0][0]} — {sun_asp_list[0][2]}% bullish ({sun_asp_list[0][1]} days)")
    
    # Top Moon aspect
    if moon_asp_list:
        report.append(f"- **Top Moon Aspect:** {moon_asp_list[0][0]} — {moon_asp_list[0][2]}% bullish ({moon_asp_list[0][1]} days)")
    
    # Hora
    if hora_stats:
        report.append(f"- **Hora:** {hora_stats[0][0]} {hora_stats[0][2]}% bullish; {hora_stats[-1][0]} {hora_stats[-1][2]}% weakest")
    
    # Market structure
    reversal_pct = round(len(df[df['market_reaction']=='reversal_signal']) / total_days * 100, 1)
    strong_pct = round(len(df[df['market_reaction']=='strong_trend']) / total_days * 100, 1)
    report.append(f"- **Market structure:** {reversal_pct}% reversal signal, {strong_pct}% strong trend")
    
    # DXY
    dxy_bull_sub = df[df['dxy_direction'] == 'bullish']
    dxy_bear_sub = df[df['dxy_direction'] == 'bearish']
    if len(dxy_bull_sub) > 10 and len(dxy_bear_sub) > 10:
        dxy_bull_gold = round(len(dxy_bull_sub[dxy_bull_sub['gold_bullish']==True]) / len(dxy_bull_sub) * 100, 1)
        dxy_bear_gold = round(len(dxy_bear_sub[dxy_bear_sub['gold_bullish']==True]) / len(dxy_bear_sub) * 100, 1)
        report.append(f"- **DXY inverse:** DXY bullish → Gold {dxy_bull_gold}% bullish; DXY bearish → Gold {dxy_bear_gold}% bullish")
    
    report.append(f"")
    report.append(f"---")
    report.append(f"")
    report.append(f"*Report generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Data: {date_start} → {date_end} | {total_days} trading days*")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"  ✅ {period_name}: {total_days} days → {output_path}")


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print("Loading data...")
    df = load_all_data()
    df['date'] = pd.to_datetime(df['date'])
    
    # Generate full period report
    print("\nGenerating full period report...")
    mask = (df['date'] >= '2016-06-01') & (df['date'] <= '2026-05-31')
    analyze_period(df[mask], "2016-06 → 2026-05 (10 Years)", 
                   os.path.join(REPORTS_DIR, "ANALYSIS_REPORT_FULL_2016-06_2026-05.md"))
    
    # Generate per-year reports
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
        if len(sub) == 0:
            continue
        
        output_path = os.path.join(REPORTS_DIR, f"ANALYSIS_REPORT_{year}.md")
        print(f"\nAnalyzing {period_name}...")
        analyze_period(sub, period_name, output_path)
    
    print(f"\n{'='*60}")
    print(f"All reports saved to: {REPORTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
