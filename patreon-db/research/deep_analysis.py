#!/usr/bin/env python3
"""
Deep Pattern Analysis for Gold (XAUUSD)
Analyzes all CSV files from patreon-db/data/ for advanced pattern discovery.
Fixed column names matching actual CSV schema.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import json

DATA_DIR = Path("/Users/kimssa/.openclaw/workspace/patreon-db/data")
OUTPUT = Path("/Users/kimssa/.openclaw/workspace/patreon-db/DEEP_ANALYSIS_REPORT.md")

def load_all():
    dfs = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")
    return pd.concat(dfs, ignore_index=True)

def safe_mean(series):
    return series.dropna().mean()

def analyze(df, label="", min_days=5):
    total = len(df)
    if total == 0:
        return {'label': label, 'days': 0, 'bullish_pct': 0, 'avg_change': 0, 'avg_range': 0, 'high_vol_pct': 0}
    bull = df['gold_bullish'].sum() if 'gold_bullish' in df.columns else 0
    avg_chg = safe_mean(df['gold_change_pct']) if 'gold_change_pct' in df.columns else 0
    avg_range = safe_mean(df['gold_range']) if 'gold_range' in df.columns else 0
    high_vol = (df['volatility'] == 'high').sum() if 'volatility' in df.columns else 0
    return {
        'label': label,
        'days': total,
        'bullish_pct': round(bull/total*100, 1) if total > 0 else 0,
        'avg_change': round(avg_chg, 3),
        'avg_range': round(avg_range, 1),
        'high_vol_pct': round(high_vol/total*100, 1) if total > 0 else 0
    }

def fmt_row(d):
    hv = d.get('high_vol_pct', 0)
    return f"| {d['label']} | {d['days']} | {d['bullish_pct']}% | {d['avg_change']:+.3f}% | ${d['avg_range']:.1f} | {hv}% |"

lines = []
def w(s=""):
    lines.append(s)

# ─── LOAD ───────────────────────────────────────────────────
print("Loading data...")
df = load_all()
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
print(f"Date range: {df['date'].min()} → {df['date'].max()}")

# Parse aspects_json
def parse_aspects(val):
    if pd.isna(val) or str(val).strip() == '' or str(val) == 'nan':
        return []
    try:
        return json.loads(str(val))
    except:
        return []

# Column name mapping (actual CSV columns):
# mercury_retro, venus_retro, mars_retro, jupiter_retro, saturn_retro
# mercury_elong_deg, mercury_elong_dir, venus_elong_deg, venus_elong_dir, mars_elong_deg, etc.
# mercury_combust, venus_combust, mars_combust
# gann_key_level_held, gann_breached_level, gann_reaction, gann_swing_high, gann_swing_low, gann_trend
# dominant_planet_hour
# moon_phase, moon_nakshatra, moon_sign, moon_deg, moon_illumination_pct
# gold_ema_relation (above/below)
# trend_direction, volatility, market_reaction
# economic_events, economic_impact
# dxy_close, dxy_change_pct, dxy_direction
# us10y_close, us10y_change

# ═══════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════
w(f"# 🔬 Deep Pattern Analysis: Gold (XAUUSD)")
w(f"")
w(f"**Dataset:** {df['date'].min()} → {df['date'].max()} ({len(df)} trading days)")
w(f"**Generated:** 2026-05-22")
w(f"**Columns:** {len(df.columns)}")
w(f"")

# ═══════════════════════════════════════════════
# 1. VENUS PHASE — MORNING STAR vs EVENING STAR
# ═══════════════════════════════════════════════
w("---")
w("## 1. 🌟 VENUS PHASE — MORNING STAR vs EVENING STAR")
w("")
w("Venus chu kỳ 584 ngày. Morning Star = Max West Elongation (greed). Evening Star = Max East (fear).")
w("")

# Venus elongation bands
df['venus_elong_band'] = df['venus_elong_deg'].apply(
    lambda x: 'Near Max (≥44°)' if pd.notna(x) and x >= 44 
    else ('Mid (20-44°)' if pd.notna(x) and x >= 20 
    else ('Near Sun (<20°)' if pd.notna(x) else 'Unknown'))
)

w("### Venus Elongation Magnitude → Gold Trend")
w("")
w("| Elongation Band | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|-----------------|------|-----------|-------|---------|----------|")
for band in ['Near Max (≥44°)', 'Mid (20-44°)', 'Near Sun (<20°)']:
    d = df[df['venus_elong_band'] == band]
    a = analyze(d, band)
    w(fmt_row(a))
w("")

# Venus phase (Morning/Evening Star from elong_dir)
w("### Venus Direction (Morning vs Evening Star)")
w("")
w("| Phase | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|-------|------|-----------|-------|---------|----------|")
for phase_dir, phase_name in [('W', 'Morning Star (W)'), ('E', 'Evening Star (E)')]:
    d = df[df['venus_elong_dir'] == phase_dir]
    a = analyze(d, phase_name)
    w(fmt_row(a))
w("")

# Venus Phase × Venus Retro (critical combination)
w("### Venus Phase × Venus Retro")
w("")
w("| Venus Phase | Venus Retro? | Days | Bullish % | AvgΔ% | Range $ |")
w("|-------------|-------------|------|-----------|-------|---------|")
for phase_dir, phase_name in [('W', 'Morning Star'), ('E', 'Evening Star')]:
    for retro in [True, False]:
        d = df[(df['venus_elong_dir'] == phase_dir) & (df['venus_retro'] == retro)]
        if len(d) >= 5:
            a = analyze(d, f"{phase_name} | {'Retro' if retro else 'Direct'}")
            w(fmt_row(a))
w("")

# Venus Phase × Moon Sign
w("### Venus Phase × Moon Sign (Best Combos, ≥8 days)")
w("")
w("| Venus Phase | Moon Sign | Days | Bullish % | AvgΔ% | Range $ |")
w("|-------------|-----------|------|-----------|-------|---------|")
for phase_dir, phase_name in [('W', 'Morning Star'), ('E', 'Evening Star')]:
    for sign in df['moon_sign'].dropna().unique():
        d = df[(df['venus_elong_dir'] == phase_dir) & (df['moon_sign'] == sign)]
        if len(d) >= 8:
            a = analyze(d, f"{phase_name} | {sign}")
            w(fmt_row(a))
w("")

# ═══════════════════════════════════════════════
# 2. MERCURY PHASE — 116-DAY CYCLE
# ═══════════════════════════════════════════════
w("---")
w("## 2. ☿️ MERCURY PHASE — 116-DAY CYCLE")
w("")
w("Mercury switches Morning Star ↔ Evening Star every ~58 days. Strategy: Buy Morning Star, Hold Superior Conj, Sell Evening Star.")
w("")

w("### Mercury Morning vs Evening Star")
w("")
w("| Phase | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|-------|------|-----------|-------|---------|----------|")
for phase_dir, phase_name in [('W', 'Morning Star (W)'), ('E', 'Evening Star (E)')]:
    d = df[df['mercury_elong_dir'] == phase_dir]
    a = analyze(d, phase_name)
    w(fmt_row(a))
w("")

# Mercury elong distance bands
df['mercury_elong_band'] = df['mercury_elong_deg'].apply(
    lambda x: 'Max Elong (≥20°)' if pd.notna(x) and abs(x) >= 20 
    else ('Mid (10-20°)' if pd.notna(x) and abs(x) >= 10 
    else ('Near Sun (<10°)' if pd.notna(x) else 'Unknown'))
)

w("### Mercury Distance from Sun → Gold Trend")
w("")
w("| Elongation | Days | Bullish % | AvgΔ% | Range $ |")
w("|------------|------|-----------|-------|---------|")
for band in ['Max Elong (≥20°)', 'Mid (10-20°)', 'Near Sun (<10°)']:
    d = df[df['mercury_elong_band'] == band]
    a = analyze(d, band)
    w(fmt_row(a))
w("")

# Mercury phase × Combust
w("### Mercury Phase × Combust")
w("")
w("| Phase | Combust? | Days | Bullish % | AvgΔ% | Range $ |")
w("|-------|----------|------|-----------|-------|---------|")
for phase_dir, phase_name in [('W', 'Morning Star'), ('E', 'Evening Star')]:
    for combust in [True, False]:
        d = df[(df['mercury_elong_dir'] == phase_dir) & (df['mercury_combust'] == combust)]
        if len(d) >= 5:
            a = analyze(d, f"{phase_name} | {'Combust' if combust else 'Not Combust'}")
            w(fmt_row(a))
w("")

# ═══════════════════════════════════════════════
# 3. DAY OF WEEK PATTERNS
# ═══════════════════════════════════════════════
w("---")
w("## 3. 📅 DAY OF WEEK PATTERNS")
w("")
w("| Day | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|-----|------|-----------|-------|---------|----------|")
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for day in day_order:
    d = df[df['day_of_week'] == day]
    a = analyze(d, day)
    w(fmt_row(a))
w("")

# Day × Nakshatra top combos
w("### Day × Nakshatra — Top Bullish (≥6 days)")
w("")
w("| Day | Nakshatra | Days | Bullish % | AvgΔ% | Range $ |")
w("|-----|-----------|------|-----------|-------|---------|")
combos = []
for day in day_order:
    for nak in df['moon_nakshatra'].dropna().unique():
        d = df[(df['day_of_week'] == day) & (df['moon_nakshatra'] == nak)]
        if len(d) >= 6:
            a = analyze(d, f"{day} | {nak}")
            combos.append(a)
combos_sorted = sorted(combos, key=lambda x: x['bullish_pct'], reverse=True)
for c in combos_sorted[:20]:
    w(fmt_row(c))
w("")

# ═══════════════════════════════════════════════
# 4. ECONOMIC EVENTS
# ═══════════════════════════════════════════════
w("---")
w("## 4. 📊 ECONOMIC EVENTS IMPACT")
w("")

df['has_economic'] = df['economic_events'].notna() & (df['economic_events'].astype(str).str.strip() != '') & (df['economic_events'].astype(str) != 'nan')

w("### Event Days vs Non-Event Days")
w("")
w("| Type | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|------|------|-----------|-------|---------|----------|")
d_eco = df[df['has_economic']]
d_no = df[~df['has_economic']]
w(fmt_row(analyze(d_eco, "Has Economic Events")))
w(fmt_row(analyze(d_no, "No Economic Events")))
w("")

w("### By Economic Impact Level")
w("")
w("| Impact | Days | Bullish % | AvgΔ% | Range $ |")
w("|--------|------|-----------|-------|---------|")
for impact in ['high', 'medium', 'low']:
    d = df[df['economic_impact'] == impact]
    if len(d) >= 5:
        w(fmt_row(analyze(d, impact.capitalize())))
w("")

# Event-specific analysis
w("### Top Economic Events (≥4 occurrences)")
w("")
events_list = []
for _, row in d_eco.iterrows():
    evt = str(row['economic_events'])
    for e in evt.split(','):
        e = e.strip()
        if e and len(e) > 2:
            events_list.append({'event': e, 'bullish': row['gold_bullish'], 'change': row['gold_change_pct'], 'range': row['gold_range']})

if events_list:
    events_df = pd.DataFrame(events_list)
    event_stats = events_df.groupby('event').agg(
        days=('bullish', 'count'),
        bullish_pct=('bullish', lambda x: x.sum()/len(x)*100 if len(x) > 0 else 0),
        avg_change=('change', 'mean'),
        avg_range=('range', 'mean')
    ).reset_index()
    event_stats = event_stats[event_stats['days'] >= 4].sort_values('bullish_pct', ascending=False)
    w("| Event | Days | Bullish % | AvgΔ% | Range $ |")
    w("|-------|------|-----------|-------|---------|")
    for _, r in event_stats.iterrows():
        w(f"| {str(r['event'])[:65]} | {int(r['days'])} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.3f}% | ${r['avg_range']:.1f} |")
w("")

# ═══════════════════════════════════════════════
# 5. MULTI-FACTOR COMBINATIONS
# ═══════════════════════════════════════════════
w("---")
w("## 5. 🧬 MULTI-FACTOR PATTERN COMBINATIONS")
w("")

# Define pattern groups
bullish_naks = ['Mula', 'Purva Ashadha', 'Ashwini']
bearish_naks = ['Uttara Bhadrapada', 'Anuradha', 'Dhanishta', 'Mrigashira']
bullish_moon = ['Sagittarius', 'Libra', 'Leo']
bearish_moon = ['Scorpio', 'Capricorn', 'Aquarius']

# 5A: Nakshatra × Mars Retro
w("### 5A. Nakshatra × Mars Retro (All, ≥5 days)")
w("")
w("| Nakshatra | Mars | Days | Bullish % | AvgΔ% | Range $ |")
w("|-----------|------|------|-----------|-------|---------|")
for nak in sorted(df['moon_nakshatra'].dropna().unique()):
    for retro_val, retro_name in [(True, 'Retro'), (False, 'Direct')]:
        d = df[(df['moon_nakshatra'] == nak) & (df['mars_retro'] == retro_val)]
        if len(d) >= 5:
            w(fmt_row(analyze(d, f"{nak} | Mars {retro_name}")))
w("")

# 5B: Triple signal
w("### 5B. Triple Confirmation Signals")
w("")
df['triple_bullish'] = df.apply(lambda r: (
    r['moon_nakshatra'] in bullish_naks and
    r['moon_sign'] in bullish_moon and
    r.get('dominant_planet_hour') in ['Venus', 'Jupiter']
), axis=1)
df['triple_bearish'] = df.apply(lambda r: (
    r['moon_nakshatra'] in bearish_naks and
    r['moon_sign'] in bearish_moon and
    r.get('dominant_planet_hour') in ['Mars']
), axis=1)

w("| Signal | Days | Bullish % | AvgΔ% | Range $ |")
w("|--------|------|-----------|-------|---------|")
w(fmt_row(analyze(df[df['triple_bullish']], "🔺 Triple Bullish")))
w(fmt_row(analyze(df[df['triple_bearish']], "🔻 Triple Bearish")))
w("")

# 5C: Gann × Top Nakshatra
w("### 5C. Gann Key Level × Nakshatra")
w("")
w("| Gann | Nakshatra | Days | Bullish % | AvgΔ% | Range $ |")
w("|------|-----------|------|-----------|-------|---------|")
for held_val, held_name in [(True, 'Held'), (False, 'Breached')]:
    for nak in bullish_naks + bearish_naks:
        d = df[(df['moon_nakshatra'] == nak) & (df['gann_key_level_held'] == held_val)]
        if len(d) >= 3:
            w(fmt_row(analyze(d, f"{held_name} | {nak}")))
w("")

# 5D: EMA × Moon Sign
w("### 5D. EMA Regime × Moon Sign")
w("")
w("| EMA | Moon Sign | Days | Bullish % | AvgΔ% | Range $ |")
w("|-----|-----------|------|-----------|-------|---------|")
for ema_val, ema_name in [('above', 'EMA31>113'), ('below', 'EMA31<113')]:
    for sign in df['moon_sign'].dropna().unique():
        d = df[(df['moon_sign'] == sign) & (df['gold_ema_relation'] == ema_val)]
        if len(d) >= 5:
            w(fmt_row(analyze(d, f"{ema_name} | {sign}")))
w("")

# 5E: Retro stacking
w("### 5E. Retrograde Stacking Count")
w("")
df['retro_count'] = df[['mercury_retro', 'venus_retro', 'mars_retro', 'jupiter_retro', 'saturn_retro']].sum(axis=1)
w("| Planets Retro | Days | Bullish % | AvgΔ% | Range $ |")
w("|---------------|------|-----------|-------|---------|")
for n in range(0, 5):
    d = df[df['retro_count'] == n]
    if len(d) >= 5:
        w(fmt_row(analyze(d, f"{n} planets retro")))
w("")

# 5F: Combust stacking
w("### 5F. Combust Stacking")
w("")
df['combust_count'] = df[['mercury_combust', 'venus_combust', 'mars_combust']].sum(axis=1)
w("| Planets Combust | Days | Bullish % | AvgΔ% | Range $ |")
w("|-----------------|------|-----------|-------|---------|")
for n in range(0, 4):
    d = df[df['combust_count'] == n]
    if len(d) >= 3:
        w(fmt_row(analyze(d, f"{n} planets combust")))
w("")

# ═══════════════════════════════════════════════
# 6. PLANET-TO-PLANET ASPECTS (ALL PAIRS)
# ═══════════════════════════════════════════════
w("---")
w("## 6. 🪐 ALL PLANET ASPECTS (from aspects_json)")
w("")

all_aspects = []
for _, row in df.iterrows():
    aspects = parse_aspects(row.get('aspects_json'))
    for asp in aspects:
        all_aspects.append({
            'date': row['date'],
            'planet1': asp.get('planet1', ''),
            'planet2': asp.get('planet2', ''),
            'aspect': asp.get('aspect', ''),
            'orb': asp.get('orb', 0),
            'bullish': row['gold_bullish'],
            'change': row['gold_change_pct'],
            'range': row['gold_range'],
            'vol': row['volatility']
        })

asp_df = pd.DataFrame(all_aspects)
if len(asp_df) > 0:
    asp_df['pair'] = asp_df['planet1'] + ' ' + asp_df['aspect'] + ' ' + asp_df['planet2']
    
    pair_stats = asp_df.groupby('pair').agg(
        days=('bullish', 'count'),
        bullish_pct=('bullish', lambda x: x.sum()/len(x)*100),
        avg_change=('change', 'mean'),
        avg_range=('range', 'mean')
    ).reset_index()
    
    w("### 🔼 Top 25 Most Bullish Aspects (≥10 days)")
    w("")
    w("| Aspect | Days | Bullish % | AvgΔ% | Range $ |")
    w("|--------|------|-----------|-------|---------|")
    for _, r in pair_stats[pair_stats['days'] >= 10].sort_values('bullish_pct', ascending=False).head(25).iterrows():
        w(f"| {r['pair']} | {int(r['days'])} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.3f}% | ${r['avg_range']:.1f} |")
    w("")
    
    w("### 🔽 Top 15 Most Bearish Aspects (≥10 days)")
    w("")
    w("| Aspect | Days | Bullish % | AvgΔ% | Range $ |")
    w("|--------|------|-----------|-------|---------|")
    for _, r in pair_stats[pair_stats['days'] >= 10].sort_values('bullish_pct').head(15).iterrows():
        w(f"| {r['pair']} | {int(r['days'])} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.3f}% | ${r['avg_range']:.1f} |")
    w("")
    
    # High vol aspects
    w("### 🌊 Highest Volatility Aspects (avg range ≥$50, ≥10 days)")
    w("")
    w("| Aspect | Days | Bullish % | AvgΔ% | Range $ |")
    w("|--------|------|-----------|-------|---------|")
    for _, r in pair_stats[(pair_stats['days'] >= 10) & (pair_stats['avg_range'] >= 50)].sort_values('avg_range', ascending=False).iterrows():
        w(f"| {r['pair']} | {int(r['days'])} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.3f}% | ${r['avg_range']:.1f} |")
    w("")

# ═══════════════════════════════════════════════
# 7. VOLATILITY REGIME × ASTRO
# ═══════════════════════════════════════════════
w("---")
w("## 7. 🌊 VOLATILITY REGIME DEEP DIVE")
w("")

w("### What Triggers HIGH Volatility?")
w("")
hv = df[df['volatility'] == 'high']
w(f"High volatility days: {len(hv)}/{len(df)} ({len(hv)/len(df)*100:.1f}%)")
w("")

# Nakshatra on high vol days
w("### Nakshatra — High Vol Frequency")
w("")
w("| Nakshatra | Total Days | HighVol Days | HV% | Avg Range $ |")
w("|-----------|-----------|-------------|-----|-------------|")
nak_hv = []
for nak in df['moon_nakshatra'].dropna().unique():
    total = len(df[df['moon_nakshatra'] == nak])
    hv_cnt = len(df[(df['moon_nakshatra'] == nak) & (df['volatility'] == 'high')])
    avg_r = safe_mean(df[(df['moon_nakshatra'] == nak) & (df['volatility'] == 'high')]['gold_range'])
    if total >= 8:
        nak_hv.append({'nak': nak, 'total': total, 'hv': hv_cnt, 'pct': hv_cnt/total*100, 'range': avg_r})

for ns in sorted(nak_hv, key=lambda x: x['pct'], reverse=True)[:15]:
    w(f"| {ns['nak']} | {ns['total']} | {ns['hv']} | {ns['pct']:.1f}% | ${ns['range']:.1f} |")
w("")

# Moon Sign on high vol
w("### Moon Sign — High Vol Frequency")
w("")
w("| Moon Sign | Total Days | HighVol Days | HV% | Avg Range $ |")
w("|-----------|-----------|-------------|-----|-------------|")
sign_hv = []
for sign in df['moon_sign'].dropna().unique():
    total = len(df[df['moon_sign'] == sign])
    hv_cnt = len(df[(df['moon_sign'] == sign) & (df['volatility'] == 'high')])
    avg_r = safe_mean(df[(df['moon_sign'] == sign) & (df['volatility'] == 'high')]['gold_range'])
    if total >= 8:
        sign_hv.append({'sign': sign, 'total': total, 'hv': hv_cnt, 'pct': hv_cnt/total*100, 'range': avg_r})

for ss in sorted(sign_hv, key=lambda x: x['pct'], reverse=True):
    w(f"| {ss['sign']} | {ss['total']} | {ss['hv']} | {ss['pct']:.1f}% | ${ss['range']:.1f} |")
w("")

# ═══════════════════════════════════════════════
# 8. CONSECUTIVE DAY STREAKS
# ═══════════════════════════════════════════════
w("---")
w("## 8. 📈 CONSECUTIVE STREAK ANALYSIS")
w("")

streaks = []
curr_streak = 0
curr_dir = None
for _, row in df.iterrows():
    if pd.isna(row['gold_bullish']):
        continue
    if row['gold_bullish']:
        if curr_dir == 'bullish':
            curr_streak += 1
        else:
            if curr_dir:
                streaks.append({'dir': curr_dir, 'len': curr_streak})
            curr_dir = 'bullish'
            curr_streak = 1
    else:
        if curr_dir == 'bearish':
            curr_streak += 1
        else:
            if curr_dir:
                streaks.append({'dir': curr_dir, 'len': curr_streak})
            curr_dir = 'bearish'
            curr_streak = 1
if curr_dir:
    streaks.append({'dir': curr_dir, 'len': curr_streak})

streaks_df = pd.DataFrame(streaks)

w("### Streak Length Distribution")
w("")
w("| Length | Bullish Streaks | Bearish Streaks |")
w("|--------|----------------|-----------------|")
for n in range(1, 9):
    b = len(streaks_df[(streaks_df['dir'] == 'bullish') & (streaks_df['len'] == n)])
    be = len(streaks_df[(streaks_df['dir'] == 'bearish') & (streaks_df['len'] == n)])
    w(f"| {n} | {b} | {be} |")
w("")

w(f"- **Max Bullish Streak:** {streaks_df[streaks_df['dir']=='bullish']['len'].max()} days")
w(f"- **Max Bearish Streak:** {streaks_df[streaks_df['dir']=='bearish']['len'].max()} days")
w(f"- **Avg Bullish Streak:** {streaks_df[streaks_df['dir']=='bullish']['len'].mean():.1f} days")
w(f"- **Avg Bearish Streak:** {streaks_df[streaks_df['dir']=='bearish']['len'].mean():.1f} days")
w("")

# ═══════════════════════════════════════════════
# 9. YEARLY & MONTHLY TRENDS
# ═══════════════════════════════════════════════
w("---")
w("## 9. 📆 YEARLY & MONTHLY DECOMPOSITION")
w("")

df['year'] = pd.to_datetime(df['date']).dt.year
df['month'] = pd.to_datetime(df['date']).dt.month

w("### By Year")
w("")
w("| Year | Days | Bullish % | AvgΔ% | Range $ |")
w("|------|------|-----------|-------|---------|")
for yr in sorted(df['year'].dropna().unique()):
    d = df[df['year'] == yr]
    w(fmt_row(analyze(d, str(int(yr)))))
w("")

w("### By Month (All Years)")
w("")
w("| Month | Days | Bullish % | AvgΔ% | Range $ |")
w("|-------|------|-----------|-------|---------|")
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for m in range(1, 13):
    d = df[df['month'] == m]
    w(fmt_row(analyze(d, month_names[m-1])))
w("")

# ═══════════════════════════════════════════════
# 10. MOON ILLUMINATION BANDS
# ═══════════════════════════════════════════════
w("---")
w("## 10. 🌙 MOON ILLUMINATION & PHASE DETAIL")
w("")

w("### Illumination Bands")
w("")
w("| Illumination | Days | Bullish % | AvgΔ% | Range $ |")
w("|--------------|------|-----------|-------|---------|")
bands = [(0, 25, 'Dark (0-25%)'), (25, 50, 'Growing (25-50%)'), (50, 75, 'Bright (50-75%)'), (75, 100, 'Full (75-100%)')]
for lo, hi, label in bands:
    d = df[(df['moon_illumination_pct'] >= lo) & (df['moon_illumination_pct'] < hi)]
    w(fmt_row(analyze(d, label)))
w("")

w("### Moon Phase Detail")
w("")
w("| Phase | Days | Bullish % | AvgΔ% | Range $ | HighVol% |")
w("|-------|------|-----------|-------|---------|----------|")
for phase in ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous', 'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']:
    d = df[df['moon_phase'] == phase]
    if len(d) >= 5:
        w(fmt_row(analyze(d, phase)))
w("")

# ═══════════════════════════════════════════════
# 11. HORA × NAKSHATRA MATRIX
# ═══════════════════════════════════════════════
w("---")
w("## 11. ⏰ HORA × NAKSHATRA MATRIX")
w("")

hora_list = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']

w("### Best Hora-Nakshatra Combos (≥5 days)")
w("")
w("| Hora | Nakshatra | Days | Bullish % | AvgΔ% | Range $ |")
w("|------|-----------|------|-----------|-------|---------|")
hora_combos = []
for hora in hora_list:
    for nak in df['moon_nakshatra'].dropna().unique():
        d = df[(df['dominant_planet_hour'] == hora) & (df['moon_nakshatra'] == nak)]
        if len(d) >= 5:
            a = analyze(d, f"{hora} | {nak}")
            hora_combos.append(a)

for c in sorted(hora_combos, key=lambda x: x['bullish_pct'], reverse=True)[:25]:
    w(fmt_row(c))
w("")

w("### Worst Hora-Nakshatra Combos (≥5 days)")
w("")
w("| Hora | Nakshatra | Days | Bullish % | AvgΔ% | Range $ |")
w("|------|-----------|------|-----------|-------|---------|")
for c in sorted(hora_combos, key=lambda x: x['bullish_pct'])[:15]:
    w(fmt_row(c))
w("")

# ═══════════════════════════════════════════════
# 12. DXY & US10Y DETAIL
# ═══════════════════════════════════════════════
w("---")
w("## 12. 💵 DXY & US10Y DEEP CORRELATION")
w("")

# DXY change bands
w("### DXY Change Magnitude → Gold")
w("")
df['dxy_abs_chg'] = df['dxy_change_pct'].abs()
w("| DXY \|Δ\| | Days | Gold Bullish % | Gold AvgΔ% | Gold Range $ |")
w("|----------|------|----------------|------------|-------------|")
for threshold, label in [(0, '<0.25%'), (0.25, '0.25-0.5%'), (0.5, '0.5-1.0%'), (1.0, '≥1.0%')]:
    d = df[(df['dxy_abs_chg'] >= threshold) & (df['dxy_abs_chg'] < threshold + 0.5 if threshold < 1.0 else 100)]
    if threshold == 1.0:
        d = df[df['dxy_abs_chg'] >= 1.0]
    if len(d) >= 5:
        w(f"| {label} | {len(d)} | {d['gold_bullish'].sum()/len(d)*100:.1f}% | {safe_mean(d['gold_change_pct']):+.3f}% | ${safe_mean(d['gold_range']):.1f} |")
w("")

# US10Y change bands
w("### US10Y Change → Gold")
w("")
df['us10y_abs_chg'] = df['us10y_change'].abs()
w("| US10Y Direction | Days | Gold Bullish % | Gold AvgΔ% | Gold Range $ |")
w("|-----------------|------|----------------|------------|-------------|")
for dirstr, direction in [('Rising', lambda x: x > 0), ('Falling', lambda x: x < 0), ('Flat', lambda x: x == 0)]:
    d = df[direction(df['us10y_change'])]
    if len(d) >= 5:
        w(f"| {dirstr} | {len(d)} | {d['gold_bullish'].sum()/len(d)*100:.1f}% | {safe_mean(d['gold_change_pct']):+.3f}% | ${safe_mean(d['gold_range']):.1f} |")
w("")

# ═══════════════════════════════════════════════
# 13. GANN REACTION PATTERNS
# ═══════════════════════════════════════════════
w("---")
w("## 13. 📐 GANN REACTION DETAIL")
w("")
if 'gann_reaction' in df.columns:
    w("### Gann Reaction Types")
    w("")
    w("| Reaction | Days | Bullish % | AvgΔ% | Range $ |")
    w("|----------|------|-----------|-------|---------|")
    for react in df['gann_reaction'].dropna().unique():
        d = df[df['gann_reaction'] == react]
        if len(d) >= 3:
            w(fmt_row(analyze(d, str(react))))
    w("")

if 'gann_breached_level' in df.columns:
    w("### Most Breached Levels")
    w("")
    breached = df[df['gann_breached_level'].notna() & (df['gann_breached_level'].astype(str).str.strip() != '') & (df['gann_breached_level'].astype(str) != 'nan')]
    if len(breached) > 0:
        w(f"Total breached days: {len(breached)}")
        w("")
        breach_counts = breached['gann_breached_level'].value_counts().head(10)
        w("| Level | Times Breached |")
        w("|-------|---------------|")
        for level, count in breach_counts.items():
            w(f"| {level} | {count} |")
    w("")

# ═══════════════════════════════════════════════
# 14. MARKET REACTION × ASTRO
# ═══════════════════════════════════════════════
w("---")
w("## 14. 📊 MARKET REACTION × NAKSHATRA")
w("")
w("### Reversal Signals by Nakshatra (Top)")
w("")
w("| Nakshatra | Total | Reversals | Rev% |")
w("|-----------|-------|-----------|------|")
for nak in df['moon_nakshatra'].dropna().unique():
    total = len(df[df['moon_nakshatra'] == nak])
    rev = len(df[(df['moon_nakshatra'] == nak) & (df['market_reaction'] == 'reversal_signal')])
    if total >= 10:
        w(f"| {nak} | {total} | {rev} | {rev/total*100:.1f}% |")
w("")

# ═══════════════════════════════════════════════
# 15. ULTIMATE PATTERN RANKING
# ═══════════════════════════════════════════════
w("---")
w("## 15. 🏆 ULTIMATE PATTERN RANKING")
w("")

patterns = []

# Single factors
for nak in df['moon_nakshatra'].dropna().unique():
    d = df[df['moon_nakshatra'] == nak]
    if len(d) >= 15:
        patterns.append({'pattern': f"Moon {nak} Nakshatra", 'days': len(d), 
                        'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for sign in df['moon_sign'].dropna().unique():
    d = df[df['moon_sign'] == sign]
    if len(d) >= 15:
        patterns.append({'pattern': f"Moon in {sign}", 'days': len(d), 
                        'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for planet in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
    d = df[df[f'{planet}_retro'] == True]
    if len(d) >= 15:
        patterns.append({'pattern': f"{planet.title()} Retro", 'days': len(d), 
                        'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for planet in ['mercury', 'venus', 'mars']:
    col = f'{planet}_combust'
    if col in df.columns:
        d = df[df[col] == True]
        if len(d) >= 8:
            patterns.append({'pattern': f"{planet.title()} Combust", 'days': len(d), 
                            'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for hora in df['dominant_planet_hour'].dropna().unique():
    d = df[df['dominant_planet_hour'] == hora]
    if len(d) >= 30:
        patterns.append({'pattern': f"{hora} Hora", 'days': len(d), 
                        'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for held_val, held_name in [(True, 'Held'), (False, 'Breached')]:
    d = df[df['gann_key_level_held'] == held_val]
    patterns.append({'pattern': f"Gann Key {held_name}", 'days': len(d), 
                    'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

# Combos
for nak in bullish_naks:
    for hora in ['Venus', 'Jupiter', 'Moon']:
        d = df[(df['moon_nakshatra'] == nak) & (df['dominant_planet_hour'] == hora)]
        if len(d) >= 4:
            patterns.append({'pattern': f"✨ {nak} + {hora} Hora", 'days': len(d), 
                            'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for nak in bullish_naks:
    for sign in bullish_moon:
        d = df[(df['moon_nakshatra'] == nak) & (df['moon_sign'] == sign)]
        if len(d) >= 3:
            patterns.append({'pattern': f"🎯 {nak} + {sign} Moon", 'days': len(d), 
                            'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

for nak in bullish_naks:
    d = df[(df['moon_nakshatra'] == nak) & (df['mercury_combust'] == True)]
    if len(d) >= 3:
        patterns.append({'pattern': f"🔥 Merc Combust + {nak}", 'days': len(d), 
                        'bp': d['gold_bullish'].sum()/len(d)*100, 'chg': safe_mean(d['gold_change_pct']), 'rng': safe_mean(d['gold_range'])})

# Sort
patterns_sorted = sorted(patterns, key=lambda x: x['bp'], reverse=True)

w("### 🔼 TOP 35 MOST BULLISH PATTERNS")
w("")
w("| # | Pattern | Days | Bullish % | AvgΔ% | Range $ |")
w("|---|---------|------|-----------|-------|---------|")
for i, p in enumerate(patterns_sorted[:35]):
    w(f"| {i+1} | {p['pattern']} | {p['days']} | {p['bp']:.1f}% | {p['chg']:+.3f}% | ${p['rng']:.1f} |")

w("")
w("### 🔽 BOTTOM 25 MOST BEARISH PATTERNS")
w("")
w("| # | Pattern | Days | Bullish % | AvgΔ% | Range $ |")
w("|---|---------|------|-----------|-------|---------|")
patterns_bearish = sorted(patterns, key=lambda x: x['bp'])
for i, p in enumerate(patterns_bearish[:25]):
    w(f"| {i+1} | {p['pattern']} | {p['days']} | {p['bp']:.1f}% | {p['chg']:+.3f}% | ${p['rng']:.1f} |")

w("")

# ═══════════════════════════════════════════════
# 16. FINAL CHECKLIST
# ═══════════════════════════════════════════════
w("---")
w("## 16. 🎯 TRADING DECISION FRAMEWORK")
w("")

w("### LONG SETUP CHECKLIST (Score ≥5 = A+ Setup)")
w("")
w("| Weight | Condition |")
w("|--------|-----------|")
w("| +3 | Moon in Mula / Purva Ashadha / Ashwini Nakshatra |")
w("| +2 | Moon in Sagittarius / Leo / Libra |")
w("| +2 | Mercury Combust |")
w("| +2 | Mars Retrograde |")
w("| +1 | Venus / Jupiter Hora Dominant |")
w("| +1 | Gann Key Level Held |")
w("| +1 | EMA31 > EMA113 |")
w("| +1 | DXY Bearish |")
w("| +1 | US10Y Falling |")
w("| +1 | First Quarter Moon Phase |")
w("| +1 | Venus Morning Star (W) |")
w("")

w("### SHORT SETUP CHECKLIST (Score ≥5 = A+ Setup)")
w("")
w("| Weight | Condition |")
w("|--------|-----------|")
w("| +3 | Moon in Uttara Bhadrapada / Anuradha / Dhanishta Nakshatra |")
w("| +2 | Moon in Scorpio / Capricorn / Aquarius |")
w("| +2 | Mars Direct (not retro) |")
w("| +1 | Saturn Retrograde |")
w("| +1 | Mars Hora Dominant |")
w("| +1 | Gann Key Level Breached |")
w("| +1 | EMA31 < EMA113 |")
w("| +1 | DXY Bullish |")
w("| +1 | US10Y Rising |")
w("| +1 | Waxing Crescent Moon |")
w("")

w("### ⚡ HIGH VOLATILITY WARNING FLAGS")
w("")
w("| Risk | Condition | Typical Range |")
w("|------|-----------|---------------|")
w("| 🔴 Critical | Gann Key Level Breached | 4x normal |")
w("| 🔴 Critical | Mars Combust | $64.3 |")
w("| 🔴 Critical | Sun Conjunction Mars | $55.1 |")
w("| 🟡 Elevated | Magha / Ardra / Uttara Phalguni Nakshatra | $39-47 |")
w("| 🟡 Elevated | Economic High Impact | Varies |")
w("| 🟡 Elevated | Full Moon | $36.3 |")
w("| 🟡 Elevated | Leo Moon Sign | $40.7 |")
w("")

w("---")
w("")
w(f"*Deep Analysis generated 2026-05-22 | {len(df)} days | {len(df['date'].unique())} unique dates | {len(df.columns)} columns*")
w(f"*Data: patreon-db/data/ 2022-01 → 2026-05*")

# Write
output = "\n".join(lines)
OUTPUT.write_text(output)
print(f"\n✅ Report written to {OUTPUT}")
print(f"   {len(lines)} lines, {len(output):,} chars")
