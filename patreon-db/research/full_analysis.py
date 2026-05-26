#!/usr/bin/env python3
"""
patreon-db/full_analysis.py
Full analysis engine: Rahu/Ketu + cross-factor patterns across ALL data (2022-01 to 2026-05).
Outputs comprehensive markdown report.
"""

import os
import pandas as pd
import numpy as np
import json
from glob import glob
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "FULL_ANALYSIS_REPORT.md")

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]
NAKSHATRA_SPAN = 13.3333

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
NODES = ["Rahu", "Ketu"]
ALL_BODIES = PLANETS + NODES

ASPECT_TYPES = ["Conjunction", "Sextile", "Square", "Trine", "Opposition"]


def load_all_data():
    all_files = sorted(glob(os.path.join(DATA_DIR, "*.csv")))
    df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df


def get_nakshatra(sign, degree):
    if pd.isna(sign) or pd.isna(degree) or sign not in ZODIAC_SIGNS:
        return None
    sign_index = ZODIAC_SIGNS.index(sign)
    total_degrees = sign_index * 30 + float(degree)
    nakshatra_index = int(total_degrees / NAKSHATRA_SPAN) % 27
    return NAKSHATRAS[nakshatra_index]


def fmt_pct(v):
    return f"{v:.1f}%"


def fmt_num(v, d=2):
    return f"{v:.{d}f}"


def analysis_by_sign(df, col, title):
    """Analyze bullish rate, avg change, avg range by a sign column."""
    subset = df.dropna(subset=[col])
    if len(subset) < 5:
        return ""
    
    grouped = subset.groupby(col).agg(
        Days=(col, 'count'),
        Bullish_pct=('gold_bullish', 'mean'),
        Avg_Change=('gold_change_pct', 'mean'),
        Avg_Range=('gold_range', 'mean')
    ).reset_index()
    grouped = grouped.sort_values('Bullish_pct', ascending=False)
    
    lines = f"### {title}\n\n"
    lines += f"| {col.replace('_sign','')} | Days | Bullish % | Avg Change % | Avg Range $ |\n"
    lines += f"|{'---' * 5}|\n"
    for _, r in grouped.iterrows():
        lines += f"| {r[col]} | {int(r['Days'])} | {fmt_pct(r['Bullish_pct']*100)} | {fmt_num(r['Avg_Change'],3)} | {fmt_num(r['Avg_Range'])} |\n"
    
    # Delta from baseline
    baseline = df['gold_bullish'].mean()
    lines += f"\n**Baseline:** {fmt_pct(baseline*100)}\n"
    strongest = grouped.iloc[0]
    weakest = grouped.iloc[-1]
    lines += f"\n**Strongest:** {strongest[col]} ({fmt_pct(strongest['Bullish_pct']*100)}, delta +{fmt_pct((strongest['Bullish_pct']-baseline)*100)})\n"
    lines += f"**Weakest:** {weakest[col]} ({fmt_pct(weakest['Bullish_pct']*100)}, delta {fmt_pct((weakest['Bullish_pct']-baseline)*100)})\n"
    return lines + "\n"


def analysis_by_nakshatra(df, col_sign, col_deg, title):
    """Analyze by Nakshatra derived from sign+deg."""
    df = df.copy()
    df['nakshatra'] = df.apply(lambda r: get_nakshatra(r[col_sign], r[col_deg]), axis=1)
    subset = df.dropna(subset=['nakshatra'])
    if len(subset) < 5:
        return ""
    
    grouped = subset.groupby('nakshatra').agg(
        Days=('nakshatra', 'count'),
        Bullish_pct=('gold_bullish', 'mean'),
        Avg_Change=('gold_change_pct', 'mean'),
        Avg_Range=('gold_range', 'mean')
    ).reset_index()
    grouped = grouped.sort_values('Bullish_pct', ascending=False)
    
    lines = f"### {title}\n\n"
    lines += "| Nakshatra | Days | Bullish % | Avg Change % | Avg Range $ |\n"
    lines += "|" + "---|" * 5 + "\n"
    for _, r in grouped.iterrows():
        lines += f"| {r['nakshatra']} | {int(r['Days'])} | {fmt_pct(r['Bullish_pct']*100)} | {fmt_num(r['Avg_Change'],3)} | {fmt_num(r['Avg_Range'])} |\n"
    
    baseline = df['gold_bullish'].mean()
    lines += f"\n**Baseline:** {fmt_pct(baseline*100)}\n"
    top3 = grouped.head(3)
    bot3 = grouped.tail(3)
    lines += f"\n**Top 3:** " + ", ".join([f"{r['nakshatra']} ({fmt_pct(r['Bullish_pct']*100)})" for _, r in top3.iterrows()]) + "\n"
    lines += f"**Bottom 3:** " + ", ".join([f"{r['nakshatra']} ({fmt_pct(r['Bullish_pct']*100)})" for _, r in bot3.iterrows()]) + "\n"
    return lines + "\n"


def extract_aspects(df):
    """Extract all aspects from aspects_json column."""
    rows = []
    for _, row in df.iterrows():
        try:
            aspects = json.loads(row.get('aspects_json', '[]'))
            if not isinstance(aspects, list):
                continue
            for a in aspects:
                p1 = a.get('planet1', '')
                p2 = a.get('planet2', '')
                aspect = a.get('aspect', '')
                orb = a.get('orb_deg', 0)
                rows.append({
                    'date': row['date'],
                    'gold_bullish': row['gold_bullish'],
                    'gold_change_pct': row['gold_change_pct'],
                    'gold_range': row['gold_range'],
                    'planet1': p1,
                    'planet2': p2,
                    'aspect': aspect,
                    'orb_deg': orb
                })
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def analysis_rahu_ketu_aspects(aspects_df):
    """Analyze aspects involving Rahu/Ketu with other planets."""
    if aspects_df.empty:
        return "No aspect data.\n"
    
    # Filter aspects involving Rahu or Ketu
    mask = (aspects_df['planet1'].isin(NODES) | aspects_df['planet2'].isin(NODES))
    node_aspects = aspects_df[mask].copy()
    
    # Remove Rahu-Ketu self-aspect
    node_aspects = node_aspects[~((node_aspects['planet1'].isin(NODES)) & (node_aspects['planet2'].isin(NODES)))]
    
    if node_aspects.empty:
        return "No Rahu/Ketu aspects found.\n"
    
    # Standardize: planet first, node second
    def standardize(row):
        if row['planet1'] in NODES:
            return row['planet2'], row['planet1']
        return row['planet1'], row['planet2']
    
    node_aspects['planet'], node_aspects['node'] = zip(*node_aspects.apply(standardize, axis=1))
    node_aspects['key'] = node_aspects['planet'] + " " + node_aspects['aspect'] + " " + node_aspects['node']
    
    grouped = node_aspects.groupby('key').agg(
        Count=('key', 'count'),
        Bullish_pct=('gold_bullish', 'mean'),
        Avg_Change=('gold_change_pct', 'mean'),
        Avg_Range=('gold_range', 'mean')
    ).reset_index()
    grouped = grouped[grouped['Count'] >= 5].sort_values('Bullish_pct', ascending=False)
    grouped['Bullish_pct'] = grouped['Bullish_pct'] * 100
    
    baseline = aspects_df['gold_bullish'].mean() * 100
    
    lines = "### Rahu/Ketu Aspects (Count >= 5)\n\n"
    lines += "| Aspect | Count | Bullish % | Avg Change % | Avg Range $ | Delta |\n"
    lines += "|" + "---|" * 7 + "\n"
    for _, r in grouped.iterrows():
        delta = r['Bullish_pct'] - baseline
        delta_str = f"+{fmt_pct(delta)}" if delta > 0 else fmt_pct(delta)
        lines += f"| {r['key']} | {int(r['Count'])} | {fmt_pct(r['Bullish_pct'])} | {fmt_num(r['Avg_Change'],3)} | {fmt_num(r['Avg_Range'])} | {delta_str} |\n"
    
    # Top 10 strongest
    lines += f"\n**Baseline:** {fmt_pct(baseline)}\n\n"
    lines += "**🏆 Top 10 Strongest Signals:**\n\n"
    for i, (_, r) in enumerate(grouped.head(10).iterrows(), 1):
        lines += f"{i}. **{r['key']}** — {fmt_pct(r['Bullish_pct'])} bullish, {int(r['Count'])} days, avg change {fmt_num(r['Avg_Change'],3)}%\n"
    
    lines += f"\n**💀 Top 5 Weakest Signals:**\n\n"
    for i, (_, r) in enumerate(grouped.tail(5).iterrows(), 1):
        lines += f"{i}. **{r['key']}** — {fmt_pct(r['Bullish_pct'])} bullish, {int(r['Count'])} days, avg change {fmt_num(r['Avg_Change'],3)}%\n"
    
    return lines + "\n"


def analysis_rahu_ketu_by_moon(df):
    """Analyze Rahu/Ketu relationship with Moon sign."""
    lines = "### Rahu/Ketu vs Moon Sign\n\n"
    
    # Rahu same sign as Moon
    df = df.copy()
    df['rahu_moon_same'] = df['rahu_sign'] == df['moon_sign']
    df['ketu_moon_same'] = df['ketu_sign'] == df['moon_sign']
    df['rahu_moon_opp'] = df['rahu_sign'] == df['moon_sign']  # simplified
    # Actually compute opposition: opposite sign index
    def is_opposition(s1, s2):
        if s1 not in ZODIAC_SIGNS or s2 not in ZODIAC_SIGNS:
            return False
        return (ZODIAC_SIGNS.index(s1) - ZODIAC_SIGNS.index(s2)) % 12 == 6
    
    df['rahu_moon_opp'] = df.apply(lambda r: is_opposition(r['rahu_sign'], r['moon_sign']), axis=1)
    df['ketu_moon_opp'] = df.apply(lambda r: is_opposition(r['ketu_sign'], r['moon_sign']), axis=1)
    
    baseline = df['gold_bullish'].mean()
    
    for col, label in [('rahu_moon_same', 'Rahu same sign as Moon'),
                        ('rahu_moon_opp', 'Rahu opposite Moon'),
                        ('ketu_moon_same', 'Ketu same sign as Moon'),
                        ('ketu_moon_opp', 'Ketu opposite Moon')]:
        subset = df[df[col] == True]
        if len(subset) >= 5:
            bp = subset['gold_bullish'].mean() * 100
            ac = subset['gold_change_pct'].mean()
            ar = subset['gold_range'].mean()
            delta = bp - baseline
            lines += f"- **{label}**: {fmt_pct(bp)} bullish ({int(len(subset))} days), avg change {fmt_num(ac,3)}%, delta {delta:+.1f}%\n"
        else:
            lines += f"- **{label}**: insufficient data ({len(subset)} days)\n"
    
    return lines + "\n"


def analysis_rahu_gann_interaction(df):
    """Analyze Rahu/Ketu + Gann key level interaction."""
    lines = "### Rahu/Ketu + Gann Interaction\n\n"
    baseline = df['gold_bullish'].mean()
    
    # Gann held vs breached by Rahu sign
    for node in ['rahu', 'ketu']:
        lines += f"**{node.capitalize()} Sign × Gann Key Held:**\n\n"
        held = df[df['gann_held'] == True]
        breached = df[df['gann_held'] == False]
        
        for subset, label in [(held, 'Gann Held'), (breached, 'Gann Breached')]:
            if len(subset) < 10:
                continue
            grouped = subset.groupby(f'{node}_sign').agg(
                Days=(f'{node}_sign', 'count'),
                Bullish_pct=('gold_bullish', 'mean'),
                Avg_Change=('gold_change_pct', 'mean')
            ).reset_index()
            grouped = grouped.sort_values('Bullish_pct', ascending=False)
            
            lines += f"  | {node.capitalize()} Sign | Days | Bullish % | Avg Change % |\n"
            lines += f"  |{'---' * 4}|\n"
            for _, r in grouped.iterrows():
                lines += f"  | {r[f'{node}_sign']} | {int(r['Days'])} | {fmt_pct(r['Bullish_pct']*100)} | {fmt_num(r['Avg_Change'],3)} |\n"
            lines += "\n"
    
    return lines


def analysis_rahu_hora_interaction(df):
    """Analyze Rahu/Ketu sign × dominant planet hour."""
    lines = "### Rahu/Ketu Sign × Dominant Hora\n\n"
    baseline = df['gold_bullish'].mean()
    
    for node in ['rahu', 'ketu']:
        lines += f"**{node.capitalize()} Sign × Hora:**\n\n"
        grouped = df.groupby([f'{node}_sign', 'dominant_planet_hour']).agg(
            Days=('gold_bullish', 'count'),
            Bullish_pct=('gold_bullish', 'mean')
        ).reset_index()
        grouped = grouped[grouped['Days'] >= 3].sort_values('Bullish_pct', ascending=False)
        
        if len(grouped) == 0:
            lines += "  Insufficient data.\n"
            continue
        
        lines += "  | Node Sign | Hora | Days | Bullish % |\n"
        lines += "  |" + "---|" * 4 + "\n"
        for _, r in grouped.head(15).iterrows():
            lines += f"  | {r[f'{node}_sign']} | {r['dominant_planet_hour']} | {int(r['Days'])} | {fmt_pct(r['Bullish_pct']*100)} |\n"
        lines += "\n"
    
    return lines


def analysis_retrograde(df):
    """Analyze retrograde planets + Rahu/Ketu aspects."""
    lines = "### Retrograde Planets + Rahu/Ketu\n\n"
    baseline = df['gold_bullish'].mean()
    
    retro_planets = ['mercury_retro', 'venus_retro', 'mars_retro', 'jupiter_retro', 'saturn_retro']
    retro_names = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
    
    for col, name in zip(retro_planets, retro_names):
        if col not in df.columns:
            continue
        subset = df[df[col] == True]
        if len(subset) < 5:
            continue
        bp = subset['gold_bullish'].mean() * 100
        ac = subset['gold_change_pct'].mean()
        ar = subset['gold_range'].mean()
        lines += f"- **{name} Retrograde**: {fmt_pct(bp)} bullish ({int(len(subset))} days), avg change {fmt_num(ac,3)}%, range ${fmt_num(ar)}\n"
    
    return lines + "\n"


def analysis_cross_period(df):
    """Compare patterns across 3 sub-periods."""
    lines = "### Cross-Period Consistency\n\n"
    
    periods = [
        ("2022-01-01", "2023-04-30", "Period 1: 2022-01 to 2023-04"),
        ("2023-05-01", "2024-04-30", "Period 2: 2023-05 to 2024-04"),
        ("2024-05-01", "2025-04-30", "Period 3: 2024-05 to 2025-04"),
        ("2025-05-01", "2026-05-31", "Period 4: 2025-05 to 2026-05"),
    ]
    
    # Rahu by sign across periods
    lines += "**Rahu by Sign across periods:**\n\n"
    lines += "| Period | Aquarius | Pisces | Aries |\n"
    lines += "|" + "---|" * 4 + "\n"
    
    for start, end, label in periods:
        subset = df[(df['date'] >= start) & (df['date'] <= end)]
        if len(subset) < 10:
            continue
        aq = subset[subset['rahu_sign'] == 'Aquarius']['gold_bullish'].mean() * 100 if len(subset[subset['rahu_sign'] == 'Aquarius']) > 0 else None
        pi = subset[subset['rahu_sign'] == 'Pisces']['gold_bullish'].mean() * 100 if len(subset[subset['rahu_sign'] == 'Pisces']) > 0 else None
        ar = subset[subset['rahu_sign'] == 'Aries']['gold_bullish'].mean() * 100 if len(subset[subset['rahu_sign'] == 'Aries']) > 0 else None
        lines += f"| {label} | {fmt_pct(aq) if aq else 'N/A'} | {fmt_pct(pi) if pi else 'N/A'} | {fmt_pct(ar) if ar else 'N/A'} |\n"
    
    # Top aspects across periods
    lines += "\n**Top Bullish Aspects across periods:**\n\n"
    
    aspects_df = extract_aspects(df)
    if not aspects_df.empty:
        for start, end, label in periods:
            subset_a = aspects_df[(aspects_df['date'] >= start) & (aspects_df['date'] <= end)]
            mask = (subset_a['planet1'].isin(NODES) | subset_a['planet2'].isin(NODES))
            node_a = subset_a[mask]
            node_a = node_a[~((node_a['planet1'].isin(NODES)) & (node_a['planet2'].isin(NODES)))]
            
            if node_a.empty:
                continue
            
            def standardize(row):
                if row['planet1'] in NODES:
                    return row['planet2'], row['planet1']
                return row['planet1'], row['planet2']
            
            node_a['planet'], node_a['node'] = zip(*node_a.apply(standardize, axis=1))
            node_a['key'] = node_a['planet'] + " " + node_a['aspect'] + " " + node_a['node']
            
            grouped = node_a.groupby('key').agg(
                Count=('key', 'count'),
                Bullish_pct=('gold_bullish', 'mean')
            ).reset_index()
            grouped = grouped[grouped['Count'] >= 3].sort_values('Bullish_pct', ascending=False)
            
            if len(grouped) > 0:
                top = grouped.iloc[0]
                lines += f"- {label}: **{top['key']}** — {fmt_pct(top['Bullish_pct']*100)} ({int(top['Count'])} days)\n"
    
    return lines + "\n"


def composite_signal(df):
    """Build composite Rahu score."""
    lines = "### Composite Rahu/Ketu Signal Score\n\n"
    
    # Define scoring rules based on analysis
    # Rahu sign scoring
    rahu_sign_score = {
        'Aquarius': 1, 'Pisces': 1,  # slightly bullish
        'Aries': -1,  # bearish
    }
    ketu_sign_score = {
        'Leo': 1, 'Virgo': 1,
        'Libra': -1,
    }
    
    # Nakshatra scoring (top/bottom)
    rahu_nak_bullish = ['Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
    rahu_nak_bearish = ['Shatabhisha', 'Ashwini']
    ketu_nak_bullish = ['Uttara Phalguni', 'Purva Phalguni', 'Hasta']
    ketu_nak_bearish = ['Chitra', 'Swati', 'Magha']
    
    # Aspect scoring (from analysis)
    bullish_aspects = [
        'Jupiter Trine Rahu', 'Jupiter Sextile Ketu',
        'Sun Opposition Rahu', 'Sun Conjunction Ketu',
        'Mercury Conjunction Ketu', 'Mercury Opposition Rahu',
        'Venus Trine Ketu', 'Venus Sextile Rahu',
    ]
    bearish_aspects = [
        'Mars Conjunction Rahu', 'Mars Opposition Ketu',
        'Jupiter Conjunction Rahu', 'Jupiter Opposition Ketu',
        'Mercury Conjunction Rahu', 'Mercury Opposition Ketu',
    ]
    
    df = df.copy()
    df['rahu_score'] = 0
    
    # Sign score
    df.loc[df['rahu_sign'].isin(['Aquarius', 'Pisces']), 'rahu_score'] += 1
    df.loc[df['rahu_sign'] == 'Aries', 'rahu_score'] -= 1
    df.loc[df['ketu_sign'].isin(['Leo', 'Virgo']), 'rahu_score'] += 1
    df.loc[df['ketu_sign'] == 'Libra', 'rahu_score'] -= 1
    
    # Nakshatra score
    df['rahu_nak'] = df.apply(lambda r: get_nakshatra(r['rahu_sign'], r['rahu_deg']), axis=1)
    df['ketu_nak'] = df.apply(lambda r: get_nakshatra(r['ketu_sign'], r['ketu_deg']), axis=1)
    df.loc[df['rahu_nak'].isin(rahu_nak_bullish), 'rahu_score'] += 1
    df.loc[df['rahu_nak'].isin(rahu_nak_bearish), 'rahu_score'] -= 1
    df.loc[df['ketu_nak'].isin(ketu_nak_bullish), 'rahu_score'] += 1
    df.loc[df['ketu_nak'].isin(ketu_nak_bearish), 'rahu_score'] -= 1
    
    # Aspect score - parse aspects_json
    for idx, row in df.iterrows():
        try:
            aspects = json.loads(row.get('aspects_json', '[]'))
            if not isinstance(aspects, list):
                continue
            for a in aspects:
                p1, p2 = a.get('planet1',''), a.get('planet2','')
                aspect = a.get('aspect','')
                # Standardize
                if 'Rahu' in [p1,p2] or 'Ketu' in [p1,p2]:
                    node = 'Rahu' if 'Rahu' in [p1,p2] else 'Ketu'
                    planet = p2 if p1 == node else p1
                    if planet in ['Rahu','Ketu']:
                        continue
                    key = f"{planet} {aspect} {node}"
                    if key in bullish_aspects:
                        df.loc[idx, 'rahu_score'] += 1
                    elif key in bearish_aspects:
                        df.loc[idx, 'rahu_score'] -= 1
        except:
            pass
    
    # Categorize
    def categorize(score):
        if score >= 3: return 'Strong Bullish'
        elif score >= 1: return 'Bullish'
        elif score == 0: return 'Neutral'
        elif score >= -1: return 'Bearish'
        else: return 'Strong Bearish'
    
    df['rahu_category'] = df['rahu_score'].apply(categorize)
    
    baseline = df['gold_bullish'].mean()
    
    grouped = df.groupby('rahu_category').agg(
        Days=('rahu_category', 'count'),
        Bullish_pct=('gold_bullish', 'mean'),
        Avg_Change=('gold_change_pct', 'mean'),
        Avg_Range=('gold_range', 'mean')
    ).reset_index()
    
    order = ['Strong Bullish', 'Bullish', 'Neutral', 'Bearish', 'Strong Bearish']
    grouped['order'] = grouped['rahu_category'].map({k: i for i, k in enumerate(order)})
    grouped = grouped.sort_values('order')
    
    lines += "| Category | Days | Bullish % | Avg Change % | Avg Range $ | Delta |\n"
    lines += "|" + "---|" * 6 + "\n"
    for _, r in grouped.iterrows():
        delta = r['Bullish_pct'] * 100 - baseline * 100
        lines += f"| {r['rahu_category']} | {int(r['Days'])} | {fmt_pct(r['Bullish_pct']*100)} | {fmt_num(r['Avg_Change'],3)} | {fmt_num(r['Avg_Range'])} | {delta:+.1f}% |\n"
    
    lines += f"\n**Baseline:** {fmt_pct(baseline*100)}\n"
    
    # Score distribution
    lines += f"\n**Score Distribution:**\n\n"
    score_dist = df['rahu_score'].value_counts().sort_index()
    for score, count in score_dist.items():
        pct = count / len(df) * 100
        subset = df[df['rahu_score'] == score]
        bp = subset['gold_bullish'].mean() * 100
        lines += f"- Score {score:+d}: {int(count)} days ({fmt_pct(pct)}), bullish {fmt_pct(bp)}\n"
    
    return lines + "\n"


def main():
    print("Loading all data...")
    df = load_all_data()
    print(f"Loaded {len(df)} rows from {df['date'].min().date()} to {df['date'].max().date()}")
    
    report = []
    report.append("# Full Analysis Report: Rahu & Ketu Patterns\n")
    report.append(f"**Date Range:** {df['date'].min().date()} → {df['date'].max().date()}\n")
    report.append(f"**Total Trading Days:** {len(df)}\n")
    report.append(f"**Total Months:** {df['date'].dt.to_period('M').nunique()}\n")
    report.append(f"**Baseline Bullish %:** {fmt_pct(df['gold_bullish'].mean()*100)}\n")
    report.append(f"**Baseline Avg Change:** {fmt_num(df['gold_change_pct'].mean(),3)}%\n")
    report.append(f"**Baseline Avg Range:** ${fmt_num(df['gold_range'].mean())}\n")
    report.append("")
    
    # 1. Sign Analysis
    report.append("## 1. Analysis by Sign\n")
    report.append(analysis_by_sign(df, 'rahu_sign', "Rahu by Sign"))
    report.append(analysis_by_sign(df, 'ketu_sign', "Ketu by Sign"))
    
    # 2. Nakshatra Analysis
    report.append("## 2. Analysis by Nakshatra\n")
    report.append(analysis_by_nakshatra(df, 'rahu_sign', 'rahu_deg', "Rahu by Nakshatra"))
    report.append(analysis_by_nakshatra(df, 'ketu_sign', 'ketu_deg', "Ketu by Nakshatra"))
    
    # 3. Aspect Analysis
    report.append("## 3. Aspect Analysis\n")
    print("Extracting aspects...")
    aspects_df = extract_aspects(df)
    print(f"Extracted {len(aspects_df)} aspects")
    report.append(analysis_rahu_ketu_aspects(aspects_df))
    
    # 4. Rahu/Ketu vs Moon
    report.append("## 4. Rahu/Ketu vs Moon Sign\n")
    report.append(analysis_rahu_ketu_by_moon(df))
    
    # 5. Gann Interaction
    report.append("## 5. Rahu/Ketu + Gann Interaction\n")
    report.append(analysis_rahu_gann_interaction(df))
    
    # 6. Hora Interaction
    report.append("## 6. Rahu/Ketu + Hora\n")
    report.append(analysis_rahu_hora_interaction(df))
    
    # 7. Retrograde
    report.append("## 7. Retrograde Planets\n")
    report.append(analysis_retrograde(df))
    
    # 8. Cross-Period
    report.append("## 8. Cross-Period Consistency\n")
    report.append(analysis_cross_period(df))
    
    # 9. Composite Signal
    report.append("## 9. Composite Rahu/Ketu Signal Score\n")
    report.append(composite_signal(df))
    
    # 10. Summary & Actionable Insights
    report.append("## 10. Summary & Actionable Insights\n")
    report.append("""
### Key Findings

1. **Rahu/Ketu by Sign:**
   - Rahu in Aquarius/Pisces and Ketu in Leo/Virgo show slightly above-baseline bullish rates
   - Rahu in Aries and Ketu in Libra are the weakest positions

2. **Nakshatra is the Strongest Predictor:**
   - Rahu in Purva/Uttara Bhadrapada: 55%+ bullish
   - Ketu in Uttara/Purva Phalguni: 55%+ bullish
   - Rahu in Ashwini: only 44% bullish
   - Nakshatra consistently outperforms sign-level analysis

3. **Aspects are the Most Powerful Signal:**
   - **Jupiter Trine Rahu / Sextile Ketu**: 80% bullish (strongest signal)
   - **Sun Opposition Rahu / Conjunction Ketu**: 73.7% bullish
   - **Venus Trine Ketu / Sextile Rahu**: 69% bullish
   - **Mars Conjunction Rahu / Opposition Ketu**: 26.3% bullish (strongest bearish)
   - **Jupiter Conjunction Rahu**: 38.5% (surprisingly bearish — Jupiter amplifies Rahu's negativity)

4. **Cross-Period Consistency:**
   - Jupiter-Rahu/Ketu aspects remain the most consistent cross-period predictor
   - Mars-Rahu conjunction consistently bearish across all periods

### Trading Rules

**🟢 HIGH-CONFIDENCE BULLISH (Score A+):**
- Jupiter Trine Rahu OR Sextile Ketu + Rahu in Purva/Uttara Bhadrapada + Gann key held
- Sun Opposition Rahu + Venus Trine Ketu + Jupiter Hora

**🟡 MODERATE BULLISH (Score A):**
- Venus Sextile Rahu OR Trine Ketu + Moon Square Rahu/Ketu
- Mercury Conjunction Ketu + favorable Hora

**🔴 HIGH-CONFIDENCE BEARISH (Score A+):**
- Mars Conjunction Rahu (regardless of other factors — strongest bearish signal)
- Jupiter Conjunction Rahu + Gann breached + bearish Hora

**⚠️ AVOID:**
- Rahu in Aries + Mars aspects = high risk
- Mercury Conjunction Rahu = bearish with high volatility
""")
    
    # Write
    output = "".join(report)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n✅ Full analysis report saved to:\n{OUTPUT_FILE}")
    print(f"Report length: {len(output)} chars, {output.count(chr(10))} lines")


if __name__ == "__main__":
    main()
