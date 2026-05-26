#!/usr/bin/env python3
"""
Similarity Search Engine - Pattern Analysis
Phân tích toàn bộ pattern tác động lên xu hướng giá vàng (XAUUSD)
Dataset: 268 trading days, May 2025 → May 2026
"""

import pandas as pd
import numpy as np
import json
import glob
import os
from collections import Counter

# ─── Load all data ───
data_dir = "/Users/kimssa/.openclaw/workspace/patreon-db/data"
files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
dfs = []
for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

all_data = pd.concat(dfs, ignore_index=True)
print(f"📊 Total rows: {len(all_data)}")
print(f"📅 Date range: {all_data['date'].min()} → {all_data['date'].max()}")
print()

# ═══════════════════════════════════════════════════
# 1. BASELINE
# ═══════════════════════════════════════════════════
print("=" * 60)
print("1. BASELINE TREND DISTRIBUTION")
print("=" * 60)
trend_dist = all_data['trend_direction'].value_counts()
total = len(all_data)
for t, c in trend_dist.items():
    pct = c / total * 100
    print(f"  {t}: {c} ({pct:.1f}%)")
print()
bullish_pct = all_data['gold_bullish'].mean() * 100
print(f"  Bullish days (close > open): {bullish_pct:.1f}%")
print(f"  Avg daily change: {all_data['gold_change_pct'].mean():.3f}%")
print(f"  Avg daily range: {all_data['gold_range'].mean():.2f}")
print(f"  Std daily change: {all_data['gold_change_pct'].std():.3f}%")
print()

# ═══════════════════════════════════════════════════
# 2. MOON SIGN ANALYSIS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("2. MOON SIGN → TREND PATTERN")
print("=" * 60)
moon_sign_stats = all_data.groupby('moon_sign').agg(
    count=('trend_direction', 'count'),
    bullish_pct=('gold_bullish', 'mean'),
    avg_change=('gold_change_pct', 'mean'),
    avg_range=('gold_range', 'mean'),
    high_vol_count=('volatility', lambda x: (x == 'high').sum()),
).round(3).sort_values('count', ascending=False)

for sign in moon_sign_stats.index:
    row = moon_sign_stats.loc[sign]
    print(f"  🌕 {sign:12s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f} | HighVol: {int(row['high_vol_count'])}")
print()

# ═══════════════════════════════════════════════════
# 3. MOON NAKSHATRA ANALYSIS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("3. MOON NAKSHATRA → TREND PATTERN (≥3 samples)")
print("=" * 60)
nakshatra_stats = all_data.groupby('moon_nakshatra').agg(
    count=('trend_direction', 'count'),
    bullish_pct=('gold_bullish', 'mean'),
    avg_change=('gold_change_pct', 'mean'),
    avg_range=('gold_range', 'mean'),
    high_vol_count=('volatility', lambda x: (x == 'high').sum()),
).round(3).sort_values('count', ascending=False)

for nak in nakshatra_stats.index:
    row = nakshatra_stats.loc[nak]
    if int(row['count']) >= 3:
        print(f"  {nak:20s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f} | HighVol: {int(row['high_vol_count'])}")
print()

# ═══════════════════════════════════════════════════
# 4. PLANETARY RETROGRADE IMPACT
# ═══════════════════════════════════════════════════
print("=" * 60)
print("4. PLANETARY RETROGRADE → TREND PATTERN")
print("=" * 60)
for planet in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
    retro_col = f'{planet}_retro'
    if retro_col in all_data.columns:
        retro_data = all_data[all_data[retro_col] == True]
        direct_data = all_data[all_data[retro_col] == False]
        if len(retro_data) > 0 and len(direct_data) > 0:
            r_bull = retro_data['gold_bullish'].mean() * 100
            d_bull = direct_data['gold_bullish'].mean() * 100
            r_chg = retro_data['gold_change_pct'].mean()
            d_chg = direct_data['gold_change_pct'].mean()
            r_rng = retro_data['gold_range'].mean()
            d_rng = direct_data['gold_range'].mean()
            r_hv = (retro_data['volatility'] == 'high').sum()
            d_hv = (direct_data['volatility'] == 'high').sum()
            print(f"  {planet.upper()}:")
            print(f"    Retrograde ({len(retro_data):3d}d): Bullish {r_bull:5.1f}% | AvgΔ {r_chg:+.2f}% | Range {r_rng:6.1f} | HighVol: {r_hv}")
            print(f"    Direct   ({len(direct_data):3d}d): Bullish {d_bull:5.1f}% | AvgΔ {d_chg:+.2f}% | Range {d_rng:6.1f} | HighVol: {d_hv}")
            diff = r_bull - d_bull
            print(f"    Δ Bullish: {diff:+.1f}% {'⚠️ SIGNIFICANT' if abs(diff) > 5 else ''}")
            print()

# ═══════════════════════════════════════════════════
# 5. COMBUST (BÓC CHÁY) IMPACT
# ═══════════════════════════════════════════════════
print("=" * 60)
print("5. COMBUST (BÓC CHÁY) → TREND PATTERN")
print("=" * 60)
for planet in ['mercury', 'venus', 'mars']:
    combust_col = f'{planet}_combust'
    if combust_col in all_data.columns:
        c_data = all_data[all_data[combust_col] == True]
        nc_data = all_data[all_data[combust_col] == False]
        if len(c_data) > 0:
            c_bull = c_data['gold_bullish'].mean() * 100
            nc_bull = nc_data['gold_bullish'].mean() * 100
            c_chg = c_data['gold_change_pct'].mean()
            nc_chg = nc_data['gold_change_pct'].mean()
            c_rng = c_data['gold_range'].mean()
            nc_rng = nc_data['gold_range'].mean()
            c_hv = (c_data['volatility'] == 'high').sum()
            nc_hv = (nc_data['volatility'] == 'high').sum()
            print(f"  {planet.upper()} Combust:")
            print(f"    Combust    ({len(c_data):3d}d): Bullish {c_bull:5.1f}% | AvgΔ {c_chg:+.2f}% | Range {c_rng:6.1f} | HighVol: {c_hv}")
            print(f"    Non-Combust({len(nc_data):3d}d): Bullish {nc_bull:5.1f}% | AvgΔ {nc_chg:+.2f}% | Range {nc_rng:6.1f} | HighVol: {nc_hv}")
            print()

# ═══════════════════════════════════════════════════
# 6. ELONGATION QUARTILE ANALYSIS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("6. PLANETARY ELONGATION QUARTILES → TREND")
print("=" * 60)
for planet in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
    elong_col = f'{planet}_elong_deg'
    if elong_col in all_data.columns:
        q1 = all_data[all_data[elong_col] <= all_data[elong_col].quantile(0.25)]
        q4 = all_data[all_data[elong_col] >= all_data[elong_col].quantile(0.75)]
        if len(q1) > 5 and len(q4) > 5:
            q1_bull = q1['gold_bullish'].mean() * 100
            q4_bull = q4['gold_bullish'].mean() * 100
            q1_chg = q1['gold_change_pct'].mean()
            q4_chg = q4['gold_change_pct'].mean()
            q1_rng = q1['gold_range'].mean()
            q4_rng = q4['gold_range'].mean()
            print(f"  {planet.upper()} Elongation:")
            print(f"    Low elong (≤Q1, {len(q1):3d}d):  Bullish {q1_bull:5.1f}% | AvgΔ {q1_chg:+.2f}% | Range {q1_rng:6.1f}")
            print(f"    High elong(≥Q4, {len(q4):3d}d):  Bullish {q4_bull:5.1f}% | AvgΔ {q4_chg:+.2f}% | Range {q4_rng:6.1f}")
            print()

# ═══════════════════════════════════════════════════
# 7. ASPECTS ANALYSIS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("7. ASPECTS → TREND PATTERN")
print("=" * 60)

all_aspects = []
for _, row in all_data.iterrows():
    try:
        aspects = json.loads(row['aspects_json']) if pd.notna(row['aspects_json']) else []
        for a in aspects:
            all_aspects.append({
                'date': row['date'],
                'planet1': a['planet1'],
                'planet2': a['planet2'],
                'aspect': a['aspect'],
                'orb_deg': a['orb_deg'],
                'trend_direction': row['trend_direction'],
                'gold_bullish': row['gold_bullish'],
                'gold_change_pct': row['gold_change_pct'],
                'gold_range': row['gold_range'],
                'volatility': row['volatility']
            })
    except:
        pass

aspects_df = pd.DataFrame(all_aspects)
print(f"  Total aspect records parsed: {len(aspects_df)}")

# Aspect type impact
if len(aspects_df) > 0:
    aspect_type_stats = aspects_df.groupby('aspect').agg(
        count=('date', 'count'),
        bullish_pct=('gold_bullish', 'mean'),
        avg_change=('gold_change_pct', 'mean'),
        avg_range=('gold_range', 'mean'),
        high_vol=('volatility', lambda x: (x == 'high').sum())
    ).round(2).sort_values('count', ascending=False)
    
    print(f"\n  By Aspect Type:")
    for asp in aspect_type_stats.index:
        row = aspect_type_stats.loc[asp]
        print(f"    {asp:15s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f} | HighVol: {int(row['high_vol'])}")

# Sun-Planet aspects (critical for Gold)
print(f"\n  ☉ Sun-Planet Aspects (critical for Gold):")
sun_aspects = aspects_df[
    ((aspects_df['planet1'] == 'Sun') | (aspects_df['planet2'] == 'Sun'))
]
if len(sun_aspects) > 0:
    sun_aspect_stats = sun_aspects.groupby(['planet1', 'planet2', 'aspect']).agg(
        count=('date', 'count'),
        bullish_pct=('gold_bullish', 'mean'),
        avg_change=('gold_change_pct', 'mean'),
        avg_range=('gold_range', 'mean'),
        high_vol=('volatility', lambda x: (x == 'high').sum())
    ).round(2).sort_values('count', ascending=False)
    
    for idx in sun_aspect_stats.index:
        if isinstance(idx, tuple):
            p1, p2, asp = idx
            row = sun_aspect_stats.loc[idx]
            planet = p2 if p1 == 'Sun' else p1
            print(f"    ☉ {asp:12s} {planet:10s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f} | HighVol: {int(row['high_vol'])}")

# Moon-Planet aspects
print(f"\n  ☽ Moon-Planet Aspects:")
moon_aspects = aspects_df[
    ((aspects_df['planet1'] == 'Moon') | (aspects_df['planet2'] == 'Moon'))
]
if len(moon_aspects) > 0:
    moon_aspect_stats = moon_aspects.groupby(['planet1', 'planet2', 'aspect']).agg(
        count=('date', 'count'),
        bullish_pct=('gold_bullish', 'mean'),
        avg_change=('gold_change_pct', 'mean'),
        avg_range=('gold_range', 'mean'),
    ).round(2).sort_values('count', ascending=False).head(15)
    
    for idx in moon_aspect_stats.index:
        if isinstance(idx, tuple):
            p1, p2, asp = idx
            row = moon_aspect_stats.loc[idx]
            planet = p2 if p1 == 'Moon' else p1
            print(f"    ☽ {asp:12s} {planet:10s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f}")

# Aspect count vs volatility
if 'aspect_count' in all_data.columns:
    print(f"\n  Aspect Count vs Volatility:")
    for vol in ['low', 'medium', 'high']:
        grp = all_data[all_data['volatility'] == vol]
        print(f"    {vol:8s}: avg aspects = {grp['aspect_count'].mean():.1f} (n={len(grp)})")

print()

# ═══════════════════════════════════════════════════
# 8. ECLIPSE IMPACT
# ═══════════════════════════════════════════════════
print("=" * 60)
print("8. ECLIPSE → TREND PATTERN")
print("=" * 60)
eclipse_active = all_data[all_data['eclipse_active'] == True]
eclipse_inactive = all_data[all_data['eclipse_active'] == False]
print(f"  Eclipse Active ({len(eclipse_active)} days):")
print(f"    Bullish: {eclipse_active['gold_bullish'].mean()*100:.1f}% | AvgΔ: {eclipse_active['gold_change_pct'].mean():+.2f}% | Range: {eclipse_active['gold_range'].mean():.1f}")
print(f"    Volatility: {eclipse_active['volatility'].value_counts().to_dict()}")
print(f"    Types: {eclipse_active['eclipse_type'].value_counts().to_dict()}")

print(f"\n  Eclipse Inactive ({len(eclipse_inactive)} days):")
print(f"    Bullish: {eclipse_inactive['gold_bullish'].mean()*100:.1f}% | AvgΔ: {eclipse_inactive['gold_change_pct'].mean():+.2f}% | Range: {eclipse_inactive['gold_range'].mean():.1f}")
print(f"    Volatility: {eclipse_inactive['volatility'].value_counts().to_dict()}")

# Days from eclipse
near_eclipse = all_data[all_data['eclipse_days_away'].abs() <= 5]
far_eclipse = all_data[all_data['eclipse_days_away'].abs() > 10]
print(f"\n  Near Eclipse (±5 days, {len(near_eclipse)}d): Bullish {near_eclipse['gold_bullish'].mean()*100:.1f}% | AvgΔ {near_eclipse['gold_change_pct'].mean():+.2f}% | Range {near_eclipse['gold_range'].mean():.1f}")
print(f"  Far Eclipse (>10 days, {len(far_eclipse)}d):   Bullish {far_eclipse['gold_bullish'].mean()*100:.1f}% | AvgΔ {far_eclipse['gold_change_pct'].mean():+.2f}% | Range {far_eclipse['gold_range'].mean():.1f}")
print()

# ═══════════════════════════════════════════════════
# 9. ECONOMIC EVENTS IMPACT
# ═══════════════════════════════════════════════════
print("=" * 60)
print("9. ECONOMIC EVENTS → TREND PATTERN")
print("=" * 60)
for label, grp in [("High Impact", all_data[all_data['economic_impact'] == 'high']),
                    ("Medium Impact", all_data[all_data['economic_impact'] == 'medium']),
                    ("Low Impact", all_data[all_data['economic_impact'] == 'low'])]:
    if len(grp) > 0:
        print(f"  {label} ({len(grp)} days):")
        print(f"    Bullish: {grp['gold_bullish'].mean()*100:.1f}% | AvgΔ: {grp['gold_change_pct'].mean():+.2f}% | Range: {grp['gold_range'].mean():.1f}")
        print(f"    Volatility: {grp['volatility'].value_counts().to_dict()}")
        print()

# ═══════════════════════════════════════════════════
# 10. GANN/FIBONACCI REACTION
# ═══════════════════════════════════════════════════
print("=" * 60)
print("10. GANN/FIBONACCI REACTION → TREND")
print("=" * 60)
reaction_stats = all_data.groupby('gann_reaction').agg(
    count=('trend_direction', 'count'),
    bullish_pct=('gold_bullish', 'mean'),
    avg_change=('gold_change_pct', 'mean'),
    avg_range=('gold_range', 'mean'),
).round(2)
for reaction in reaction_stats.index:
    if pd.notna(reaction):
        row = reaction_stats.loc[reaction]
        print(f"  {reaction:15s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f}")

print()
held = all_data[all_data['gann_key_level_held'] == True]
not_held = all_data[all_data['gann_key_level_held'] == False]
print(f"  Gann Key Level HELD ({len(held)}d): Bullish {held['gold_bullish'].mean()*100:.1f}% | AvgΔ {held['gold_change_pct'].mean():+.2f}% | Range {held['gold_range'].mean():.1f}")
print(f"  Gann Key Level NOT HELD ({len(not_held)}d): Bullish {not_held['gold_bullish'].mean()*100:.1f}% | AvgΔ {not_held['gold_change_pct'].mean():+.2f}% | Range {not_held['gold_range'].mean():.1f}")
print()

# ═══════════════════════════════════════════════════
# 11. DOMINANT PLANET HOUR
# ═══════════════════════════════════════════════════
print("=" * 60)
print("11. DOMINANT PLANET HOUR → TREND")
print("=" * 60)
hora_stats = all_data.groupby('dominant_planet_hour').agg(
    count=('trend_direction', 'count'),
    bullish_pct=('gold_bullish', 'mean'),
    avg_change=('gold_change_pct', 'mean'),
    avg_range=('gold_range', 'mean'),
    high_vol_count=('volatility', lambda x: (x == 'high').sum()),
).round(2).sort_values('count', ascending=False)

for hora in hora_stats.index:
    if pd.notna(hora):
        row = hora_stats.loc[hora]
        print(f"  {hora:12s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f} | HighVol: {int(row['high_vol_count'])}")
print()

# ═══════════════════════════════════════════════════
# 12. DAY OF WEEK
# ═══════════════════════════════════════════════════
print("=" * 60)
print("12. DAY OF WEEK → TREND")
print("=" * 60)
dow_stats = all_data.groupby('day_of_week').agg(
    count=('trend_direction', 'count'),
    bullish_pct=('gold_bullish', 'mean'),
    avg_change=('gold_change_pct', 'mean'),
    avg_range=('gold_range', 'mean'),
).round(2)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for day in day_order:
    if day in dow_stats.index:
        row = dow_stats.loc[day]
        print(f"  {day:10s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f}")
print()

# ═══════════════════════════════════════════════════
# 13. COMBINED PATTERNS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("13. HIGH-CONFIDENCE COMBINED PATTERNS")
print("=" * 60)

patterns = []

# Mars Retro + High Vol
p = all_data[(all_data['mars_retro'] == True) & (all_data['volatility'] == 'high')]
if len(p) > 2:
    patterns.append(("Mars Retro + High Vol", p))

# Eclipse + Multiple Aspects
p = all_data[(all_data['eclipse_active'] == True) & (all_data['aspect_count'] >= 2)]
if len(p) > 0:
    patterns.append(("Eclipse + ≥2 Aspects", p))

# Mercury Retro + High Econ Impact
p = all_data[(all_data['mercury_retro'] == True) & (all_data['economic_impact'] == 'high')]
if len(p) > 2:
    patterns.append(("Mercury Retro + High Econ", p))

# Venus Combust
p = all_data[all_data['venus_combust'] == True]
if len(p) > 2:
    patterns.append(("Venus Combust", p))

# Jupiter Hora
p = all_data[all_data['dominant_planet_hour'] == 'Jupiter']
if len(p) > 2:
    patterns.append(("Jupiter Hora", p))

# Saturn Hora
p = all_data[all_data['dominant_planet_hour'] == 'Saturn']
if len(p) > 2:
    patterns.append(("Saturn Hora", p))

# Sun Square Mars
sun_mars_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Sun') & (aspects_df['planet2'] == 'Mars')) |
    ((aspects_df['planet1'] == 'Mars') & (aspects_df['planet2'] == 'Sun'))
) & (aspects_df['aspect'] == 'Square')]
if len(sun_mars_sq) > 0:
    dates_sq = sun_mars_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_sq)]
    patterns.append(("Sun Square Mars", p))

# Sun Opposition Mars
sun_mars_op = aspects_df[(
    ((aspects_df['planet1'] == 'Sun') & (aspects_df['planet2'] == 'Mars')) |
    ((aspects_df['planet1'] == 'Mars') & (aspects_df['planet2'] == 'Sun'))
) & (aspects_df['aspect'] == 'Opposition')]
if len(sun_mars_op) > 0:
    dates_op = sun_mars_op['date'].unique()
    p = all_data[all_data['date'].isin(dates_op)]
    patterns.append(("Sun Opposition Mars", p))

# Venus Trine Jupiter
venus_jup_tr = aspects_df[(
    ((aspects_df['planet1'] == 'Venus') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Venus'))
) & (aspects_df['aspect'] == 'Trine')]
if len(venus_jup_tr) > 0:
    dates_vjt = venus_jup_tr['date'].unique()
    p = all_data[all_data['date'].isin(dates_vjt)]
    patterns.append(("Venus Trine Jupiter", p))

# Venus Square Jupiter
venus_jup_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Venus') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Venus'))
) & (aspects_df['aspect'] == 'Square')]
if len(venus_jup_sq) > 0:
    dates_vjs = venus_jup_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_vjs)]
    patterns.append(("Venus Square Jupiter", p))

# Moon Conjunction Jupiter
moon_jup_cj = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Conjunction')]
if len(moon_jup_cj) > 0:
    dates_mjc = moon_jup_cj['date'].unique()
    p = all_data[all_data['date'].isin(dates_mjc)]
    patterns.append(("Moon Conj Jupiter", p))

# Moon Square Saturn
moon_sat_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Saturn')) |
    ((aspects_df['planet1'] == 'Saturn') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Square')]
if len(moon_sat_sq) > 0:
    dates_mss = moon_sat_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_mss)]
    patterns.append(("Moon Square Saturn", p))

# Gann Bounce
p = all_data[all_data['gann_reaction'] == 'bounce']
if len(p) > 2:
    patterns.append(("Gann Bounce", p))

# Gann Break
p = all_data[all_data['gann_reaction'] == 'break']
if len(p) > 2:
    patterns.append(("Gann Break", p))

for name, p in patterns:
    print(f"\n  🎯 {name} ({len(p)} days):")
    print(f"    Bullish: {p['gold_bullish'].mean()*100:.1f}% | AvgΔ: {p['gold_change_pct'].mean():+.2f}% | Range: {p['gold_range'].mean():.1f}")
    print(f"    Volatility: {p['volatility'].value_counts().to_dict()}")
    print(f"    Trend: {p['trend_direction'].value_counts().to_dict()}")

print()

# ═══════════════════════════════════════════════════
# 14. CORRELATION MATRIX
# ═══════════════════════════════════════════════════
print("=" * 60)
print("14. CORRELATION: FEATURES vs PRICE CHANGE")
print("=" * 60)

numeric_cols = ['gold_change_pct', 'gold_range', 'gold_bullish']
elong_cols = [c for c in all_data.columns if 'elong_deg' in c]
deg_cols = [c for c in all_data.columns if '_deg' in c and 'elong' not in c]
numeric_cols.extend(elong_cols)
numeric_cols.extend(deg_cols)
numeric_cols = [c for c in numeric_cols if c in all_data.columns]

corr = all_data[numeric_cols].corr()['gold_change_pct'].sort_values(key=abs, ascending=False)
print(f"\n  Top correlations with gold_change_pct:")
for col in corr.index[:20]:
    if col != 'gold_change_pct':
        print(f"    {col:30s}: {corr[col]:+.3f}")

print()

# ═══════════════════════════════════════════════════
# 15. VOLATILITY PREDICTORS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("15. VOLATILITY PREDICTORS")
print("=" * 60)
high_vol = all_data[all_data['volatility'] == 'high']
low_vol = all_data[all_data['volatility'] == 'low']

print(f"\n  High Volatility days ({len(high_vol)}):")
print(f"    Economic impact: {high_vol['economic_impact'].value_counts().to_dict()}")
print(f"    Avg aspect_count: {high_vol['aspect_count'].mean():.1f}")
print(f"    Eclipse active: {(high_vol['eclipse_active'] == True).sum()} days")
print(f"    Mars retro: {(high_vol['mars_retro'] == True).sum()} days")
print(f"    Venus combust: {(high_vol['venus_combust'] == True).sum()} days")

print(f"\n  Low Volatility days ({len(low_vol)}):")
print(f"    Economic impact: {low_vol['economic_impact'].value_counts().to_dict()}")
print(f"    Avg aspect_count: {low_vol['aspect_count'].mean():.1f}")
print(f"    Eclipse active: {(low_vol['eclipse_active'] == True).sum()} days")
print(f"    Mars retro: {(low_vol['mars_retro'] == True).sum()} days")
print(f"    Venus combust: {(low_vol['venus_combust'] == True).sum()} days")
print()

# ═══════════════════════════════════════════════════
# 16. MARKET REACTION PATTERNS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("16. MARKET REACTION DISTRIBUTION")
print("=" * 60)
reaction_dist = all_data['market_reaction'].value_counts()
for r, c in reaction_dist.items():
    pct = c / total * 100
    print(f"  {r}: {c} ({pct:.1f}%)")
print()

# ═══════════════════════════════════════════════════
# 17. PLANET SIGN PLACEMENT IMPACT
# ═══════════════════════════════════════════════════
print("=" * 60)
print("17. PLANET SIGN PLACEMENT → TREND")
print("=" * 60)
for planet in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']:
    sign_col = f'{planet}_sign'
    if sign_col in all_data.columns:
        sign_stats = all_data.groupby(sign_col).agg(
            count=('trend_direction', 'count'),
            bullish_pct=('gold_bullish', 'mean'),
            avg_change=('gold_change_pct', 'mean'),
            avg_range=('gold_range', 'mean'),
        ).round(3).sort_values('count', ascending=False)
        
        # Only show top 3 signs by count for readability
        print(f"\n  {planet.upper()} Sign:")
        for i, sign in enumerate(sign_stats.index):
            if i >= 3:
                break
            row = sign_stats.loc[sign]
            print(f"    {sign:12s}: {int(row['count']):3d}d | Bullish: {row['bullish_pct']*100:5.1f}% | AvgΔ: {row['avg_change']:+.2f}% | Range: {row['avg_range']:.1f}")

print()
print("=" * 60)
print("✅ ANALYSIS COMPLETE — 268 trading days analyzed")
print("=" * 60)
#!/usr/bin/env python3
"""
Similarity Search Engine - Combined Patterns & Correlation (Part 2)
"""

import pandas as pd
import numpy as np
import json
import glob
import os

data_dir = "/Users/kimssa/.openclaw/workspace/patreon-db/data"
files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
dfs = [pd.read_csv(f) for f in files]
all_data = pd.concat(dfs, ignore_index=True)

# Parse aspects
all_aspects = []
for _, row in all_data.iterrows():
    try:
        aspects = json.loads(row['aspects_json']) if pd.notna(row['aspects_json']) else []
        for a in aspects:
            all_aspects.append({
                'date': row['date'],
                'planet1': a['planet1'],
                'planet2': a['planet2'],
                'aspect': a['aspect'],
                'orb_deg': a['orb_deg'],
                'trend_direction': row['trend_direction'],
                'gold_bullish': row['gold_bullish'],
                'gold_change_pct': row['gold_change_pct'],
                'gold_range': row['gold_range'],
                'volatility': row['volatility']
            })
    except:
        pass

aspects_df = pd.DataFrame(all_aspects)

# Add aspect_count to all_data
aspect_counts = all_data['aspects_json'].apply(
    lambda x: len(json.loads(x)) if pd.notna(x) else 0
)
all_data['aspect_count'] = aspect_counts

total = len(all_data)

# ═══════════════════════════════════════════════════
# 13. COMBINED PATTERNS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("13. HIGH-CONFIDENCE COMBINED PATTERNS")
print("=" * 60)

patterns = []

# Mars Retro + High Vol
p = all_data[(all_data['mars_retro'] == True) & (all_data['volatility'] == 'high')]
if len(p) > 2:
    patterns.append(("Mars Retro + High Vol", p))

# Eclipse + Multiple Aspects
p = all_data[(all_data['eclipse_active'] == True) & (all_data['aspect_count'] >= 2)]
if len(p) > 0:
    patterns.append(("Eclipse + ≥2 Aspects", p))

# Mercury Retro + High Econ Impact
p = all_data[(all_data['mercury_retro'] == True) & (all_data['economic_impact'] == 'high')]
if len(p) > 2:
    patterns.append(("Mercury Retro + High Econ", p))

# Venus Combust
p = all_data[all_data['venus_combust'] == True]
if len(p) > 2:
    patterns.append(("Venus Combust", p))

# Jupiter Hora
p = all_data[all_data['dominant_planet_hour'] == 'Jupiter']
if len(p) > 2:
    patterns.append(("Jupiter Hora", p))

# Saturn Hora
p = all_data[all_data['dominant_planet_hour'] == 'Saturn']
if len(p) > 2:
    patterns.append(("Saturn Hora", p))

# Sun Square Mars
sun_mars_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Sun') & (aspects_df['planet2'] == 'Mars')) |
    ((aspects_df['planet1'] == 'Mars') & (aspects_df['planet2'] == 'Sun'))
) & (aspects_df['aspect'] == 'Square')]
if len(sun_mars_sq) > 0:
    dates_sq = sun_mars_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_sq)]
    patterns.append(("Sun Square Mars", p))

# Sun Opposition Mars
sun_mars_op = aspects_df[(
    ((aspects_df['planet1'] == 'Sun') & (aspects_df['planet2'] == 'Mars')) |
    ((aspects_df['planet1'] == 'Mars') & (aspects_df['planet2'] == 'Sun'))
) & (aspects_df['aspect'] == 'Opposition')]
if len(sun_mars_op) > 0:
    dates_op = sun_mars_op['date'].unique()
    p = all_data[all_data['date'].isin(dates_op)]
    patterns.append(("Sun Opposition Mars", p))

# Venus Trine Jupiter
venus_jup_tr = aspects_df[(
    ((aspects_df['planet1'] == 'Venus') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Venus'))
) & (aspects_df['aspect'] == 'Trine')]
if len(venus_jup_tr) > 0:
    dates_vjt = venus_jup_tr['date'].unique()
    p = all_data[all_data['date'].isin(dates_vjt)]
    patterns.append(("Venus Trine Jupiter", p))

# Venus Square Jupiter
venus_jup_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Venus') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Venus'))
) & (aspects_df['aspect'] == 'Square')]
if len(venus_jup_sq) > 0:
    dates_vjs = venus_jup_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_vjs)]
    patterns.append(("Venus Square Jupiter", p))

# Moon Conjunction Jupiter
moon_jup_cj = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Conjunction')]
if len(moon_jup_cj) > 0:
    dates_mjc = moon_jup_cj['date'].unique()
    p = all_data[all_data['date'].isin(dates_mjc)]
    patterns.append(("Moon Conj Jupiter", p))

# Moon Square Saturn
moon_sat_sq = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Saturn')) |
    ((aspects_df['planet1'] == 'Saturn') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Square')]
if len(moon_sat_sq) > 0:
    dates_mss = moon_sat_sq['date'].unique()
    p = all_data[all_data['date'].isin(dates_mss)]
    patterns.append(("Moon Square Saturn", p))

# Gann Bounce
p = all_data[all_data['gann_reaction'] == 'bounce']
if len(p) > 2:
    patterns.append(("Gann Bounce", p))

# Gann Break
p = all_data[all_data['gann_reaction'] == 'break']
if len(p) > 2:
    patterns.append(("Gann Break", p))

# Gann Rejection
p = all_data[all_data['gann_reaction'] == 'rejection']
if len(p) > 2:
    patterns.append(("Gann Rejection", p))

# Saturn Retro + Bullish
p = all_data[(all_data['saturn_retro'] == True) & (all_data['gold_bullish'] == True)]
if len(p) > 5:
    patterns.append(("Saturn Retro + Bullish", p))

# Moon Sagittarius (strongest bullish moon sign)
p = all_data[all_data['moon_sign'] == 'Sagittarius']
if len(p) > 2:
    patterns.append(("Moon in Sagittarius", p))

# Moon in Anuradha nakshatra (83.3% bullish)
p = all_data[all_data['moon_nakshatra'] == 'Anuradha']
if len(p) > 2:
    patterns.append(("Moon in Anuradha", p))

# Moon in Bharani nakshatra (16.7% bullish - worst)
p = all_data[all_data['moon_nakshatra'] == 'Bharani']
if len(p) > 2:
    patterns.append(("Moon in Bharani", p))

# Moon in Dhanishta nakshatra (25% bullish)
p = all_data[all_data['moon_nakshatra'] == 'Dhanishta']
if len(p) > 2:
    patterns.append(("Moon in Dhanishta", p))

# Moon in Purva Phalguni (27.3% bullish)
p = all_data[all_data['moon_nakshatra'] == 'Purva Phalguni']
if len(p) > 2:
    patterns.append(("Moon in Purva Phalguni", p))

# Mars Combust + High Vol
p = all_data[(all_data['mars_combust'] == True) & (all_data['volatility'] == 'high')]
if len(p) > 2:
    patterns.append(("Mars Combust + High Vol", p))

# Mercury Combust
p = all_data[all_data['mercury_combust'] == True]
if len(p) > 2:
    patterns.append(("Mercury Combust", p))

# Jupiter Elongation High (Q4)
p = all_data[all_data['jupiter_elong_deg'] >= all_data['jupiter_elong_deg'].quantile(0.75)]
if len(p) > 5:
    patterns.append(("Jupiter High Elongation", p))

# Saturn Elongation Low (Q1)
p = all_data[all_data['saturn_elong_deg'] <= all_data['saturn_elong_deg'].quantile(0.25)]
if len(p) > 5:
    patterns.append(("Saturn Low Elongation", p))

# Moon Sextile Jupiter (strong bullish)
moon_jup_se = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Jupiter')) |
    ((aspects_df['planet1'] == 'Jupiter') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Sextile')]
if len(moon_jup_se) > 0:
    dates_mjs = moon_jup_se['date'].unique()
    p = all_data[all_data['date'].isin(dates_mjs)]
    patterns.append(("Moon Sextile Jupiter", p))

# Moon Trine Mars (bullish)
moon_mars_tr = aspects_df[(
    ((aspects_df['planet1'] == 'Moon') & (aspects_df['planet2'] == 'Mars')) |
    ((aspects_df['planet1'] == 'Mars') & (aspects_df['planet2'] == 'Moon'))
) & (aspects_df['aspect'] == 'Trine')]
if len(moon_mars_tr) > 0:
    dates_mmt = moon_mars_tr['date'].unique()
    p = all_data[all_data['date'].isin(dates_mmt)]
    patterns.append(("Moon Trine Mars", p))

for name, p in patterns:
    print(f"\n  🎯 {name} ({len(p)} days):")
    print(f"    Bullish: {p['gold_bullish'].mean()*100:.1f}% | AvgΔ: {p['gold_change_pct'].mean():+.2f}% | Range: {p['gold_range'].mean():.1f}")
    print(f"    Volatility: {p['volatility'].value_counts().to_dict()}")
    print(f"    Trend: {p['trend_direction'].value_counts().to_dict()}")

print()

# ═══════════════════════════════════════════════════
# 14. CORRELATION MATRIX
# ═══════════════════════════════════════════════════
print("=" * 60)
print("14. CORRELATION: FEATURES vs PRICE CHANGE")
print("=" * 60)

numeric_cols = ['gold_change_pct', 'gold_range', 'gold_bullish']
elong_cols = [c for c in all_data.columns if 'elong_deg' in c]
deg_cols = [c for c in all_data.columns if '_deg' in c and 'elong' not in c]
numeric_cols.extend(elong_cols)
numeric_cols.extend(deg_cols)
numeric_cols = [c for c in numeric_cols if c in all_data.columns]

corr = all_data[numeric_cols].corr()['gold_change_pct'].sort_values(key=abs, ascending=False)
print(f"\n  Top correlations with gold_change_pct:")
for col in corr.index[:20]:
    if col != 'gold_change_pct':
        print(f"    {col:30s}: {corr[col]:+.3f}")

print()

# ═══════════════════════════════════════════════════
# 15. VOLATILITY PREDICTORS
# ═══════════════════════════════════════════════════
print("=" * 60)
print("15. VOLATILITY PREDICTORS")
print("=" * 60)
high_vol = all_data[all_data['volatility'] == 'high']
low_vol = all_data[all_data['volatility'] == 'low']

print(f"\n  High Volatility days ({len(high_vol)}):")
print(f"    Economic impact: {high_vol['economic_impact'].value_counts().to_dict()}")
print(f"    Avg aspect_count: {high_vol['aspect_count'].mean():.1f}")
print(f"    Eclipse active: {(high_vol['eclipse_active'] == True).sum()} days")
print(f"    Mars retro: {(high_vol['mars_retro'] == True).sum()} days")
print(f"    Venus combust: {(high_vol['venus_combust'] == True).sum()} days")
print(f"    Avg range: {high_vol['gold_range'].mean():.1f}")

print(f"\n  Low Volatility days ({len(low_vol)}):")
print(f"    Economic impact: {low_vol['economic_impact'].value_counts().to_dict()}")
print(f"    Avg aspect_count: {low_vol['aspect_count'].mean():.1f}")
print(f"    Eclipse active: {(low_vol['eclipse_active'] == True).sum()} days")
print(f"    Mars retro: {(low_vol['mars_retro'] == True).sum()} days")
print(f"    Venus combust: {(low_vol['venus_combust'] == True).sum()} days")
print(f"    Avg range: {low_vol['gold_range'].mean():.1f}")
print()

# ═══════════════════════════════════════════════════
# 16. MARKET REACTION
# ═══════════════════════════════════════════════════
print("=" * 60)
print("16. MARKET REACTION DISTRIBUTION")
print("=" * 60)
reaction_dist = all_data['market_reaction'].value_counts()
for r, c in reaction_dist.items():
    pct = c / total * 100
    print(f"  {r}: {c} ({pct:.1f}%)")
print()

# ═══════════════════════════════════════════════════
# 17. FEATURE IMPORTANCE (Random Forest proxy)
# ═══════════════════════════════════════════════════
print("=" * 60)
print("17. FEATURE IMPORTANCE (Random Forest → bullish)")
print("=" * 60)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    
    # Build feature matrix
    features = {}
    feature_names = []
    
    # Numeric features
    for col in ['gold_range', 'sun_deg', 'moon_deg', 'mercury_deg', 'venus_deg', 
                'mars_deg', 'jupiter_deg', 'saturn_deg',
                'mercury_elong_deg', 'venus_elong_deg', 'mars_elong_deg',
                'jupiter_elong_deg', 'saturn_elong_deg', 'eclipse_days_away']:
        if col in all_data.columns:
            features[col] = all_data[col].fillna(0)
            feature_names.append(col)
    
    # Binary features
    for col in ['mercury_retro', 'venus_retro', 'mars_retro', 'jupiter_retro', 'saturn_retro',
                'mercury_combust', 'venus_combust', 'mars_combust', 'eclipse_active',
                'gann_key_level_held']:
        if col in all_data.columns:
            features[col] = all_data[col].astype(int).fillna(0)
            feature_names.append(col)
    
    # Categorical features (label encoded)
    cat_cols = ['moon_sign', 'moon_nakshatra', 'dominant_planet_hour', 
                'economic_impact', 'volatility', 'gann_reaction']
    le_dict = {}
    for col in cat_cols:
        if col in all_data.columns:
            le = LabelEncoder()
            features[col] = le.fit_transform(all_data[col].astype(str))
            le_dict[col] = le
            feature_names.append(col)
    
    # Aspect count
    features['aspect_count'] = aspect_counts
    
    X = pd.DataFrame(features)
    y = all_data['gold_bullish'].astype(int)
    
    # Drop rows with NaN
    valid_mask = X.notna().all(axis=1) & y.notna()
    X = X[valid_mask]
    y = y[valid_mask]
    
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)
    
    importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    
    print(f"\n  Top 20 features for predicting bullish/bearish:")
    for i, (feat, imp) in enumerate(importances.items()):
        if i >= 20:
            break
        print(f"    {feat:30s}: {imp:.4f}")
    
    print(f"\n  Model accuracy: {model.score(X, y):.3f}")
    
except ImportError:
    print("  sklearn not available, skipping RF analysis")

print()
print("=" * 60)
print("✅ ANALYSIS COMPLETE — 268 trading days analyzed")
print("=" * 60)
