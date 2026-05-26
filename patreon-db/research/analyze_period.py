#!/usr/bin/env python3
"""Analyze a period of monthly CSVs and output a markdown report."""
import sys
import os
import pandas as pd
import json
from collections import defaultdict

def load_period(data_dir, start_month, end_month):
    """Load all CSVs in [start_month, end_month] range."""
    dfs = []
    months = []
    sm_y, sm_m = map(int, start_month.split('-'))
    em_y, em_m = map(int, end_month.split('-'))
    
    y, m = sm_y, sm_m
    while (y, m) <= (em_y, em_m):
        fname = f"{y}-{m:02d}.csv"
        fpath = os.path.join(data_dir, fname)
        if os.path.exists(fpath):
            df = pd.read_csv(fpath)
            dfs.append(df)
            months.append(fname[:-4])
        # next month
        m += 1
        if m > 12:
            m = 1
            y += 1
    
    if not dfs:
        print("No data found!", file=sys.stderr)
        sys.exit(1)
    
    combined = pd.concat(dfs, ignore_index=True)
    return combined, months

def safe_json(col):
    """Parse JSON column, return list of dicts."""
    results = []
    for v in col:
        try:
            results.append(json.loads(v))
        except:
            results.append({})
    return results

def analyze_baseline(df):
    total = len(df)
    bullish = (df['gold_bullish'] == True) | (df['gold_bullish'] == 1) | (df['gold_bullish'] == 'True')
    bearish = ~bullish & (df['gold_bullish'] != 'Neutral')
    neutral_count = total - bullish.sum() - bearish.sum()
    
    avg_change = df['gold_change_pct'].mean()
    std_change = df['gold_change_pct'].std()
    avg_range = df['gold_range'].mean()
    
    return {
        'total': total,
        'bullish_pct': bullish.sum() / total * 100,
        'bearish_pct': bearish.sum() / total * 100,
        'neutral_pct': neutral_count / total * 100,
        'avg_change': avg_change,
        'std_change': std_change,
        'avg_range': avg_range,
    }

def analyze_moon_sign(df):
    groups = df.groupby('moon_sign')
    rows = []
    for sign, g in groups:
        bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
        rows.append({
            'sign': sign,
            'days': len(g),
            'bullish_pct': bullish.sum() / len(g) * 100,
            'avg_change': g['gold_change_pct'].mean(),
            'avg_range': g['gold_range'].mean(),
            'high_vol_count': (g['volatility'] == 'high').sum(),
        })
    rows.sort(key=lambda x: -x['bullish_pct'])
    return rows

def analyze_nakshatra(df):
    groups = df.groupby('moon_nakshatra')
    rows = []
    for nak, g in groups:
        bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
        rows.append({
            'nakshatra': nak,
            'days': len(g),
            'bullish_pct': bullish.sum() / len(g) * 100,
            'avg_change': g['gold_change_pct'].mean(),
            'avg_range': g['gold_range'].mean(),
            'high_vol_count': (g['volatility'] == 'high').sum(),
        })
    rows.sort(key=lambda x: -x['bullish_pct'])
    return rows

def _aspect_key(asp):
    """Return (from, to, aspect) from aspect dict. Handles planet1/planet2 and from/to."""
    p1 = asp.get('planet1') or asp.get('from')
    p2 = asp.get('planet2') or asp.get('to')
    a = asp.get('aspect')
    return p1, p2, a

def analyze_moon_sign_aspect(df):
    """Analyze Moon aspects to planets."""
    aspects_col = safe_json(df['aspects_json'])
    results = defaultdict(lambda: {'days': 0, 'bullish': 0, 'avg_change': [], 'avg_range': []})
    
    for i, aspects in enumerate(aspects_col):
        if not isinstance(aspects, list):
            continue
        for asp in aspects:
            if not isinstance(asp, dict):
                continue
            p1, p2, a = _aspect_key(asp)
            if p1 != 'Moon' and p2 != 'Moon':
                continue
            key = f"Moon {a} {p2 if p1 == 'Moon' else p1}"
            bullish = (df.iloc[i]['gold_bullish'] == True) or (df.iloc[i]['gold_bullish'] == 1) or (df.iloc[i]['gold_bullish'] == 'True')
            results[key]['days'] += 1
            if bullish:
                results[key]['bullish'] += 1
            results[key]['avg_change'].append(df.iloc[i]['gold_change_pct'])
            results[key]['avg_range'].append(df.iloc[i]['gold_range'])
    
    rows = []
    for k, v in results.items():
        if v['days'] >= 8:  # minimum sample
            rows.append({
                'aspect': k,
                'days': v['days'],
                'bullish_pct': v['bullish'] / v['days'] * 100,
                'avg_change': sum(v['avg_change']) / len(v['avg_change']),
                'avg_range': sum(v['avg_range']) / len(v['avg_range']),
            })
    rows.sort(key=lambda x: -x['bullish_pct'])
    return rows

def analyze_planet_retro(df):
    rows = []
    for planet in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
        retro_col = f'{planet}_retro'
        if retro_col not in df.columns:
            continue
        for retro_val, label in [(True, 'Retro'), (False, 'Direct')]:
            mask = df[retro_col] == retro_val
            g = df[mask]
            if len(g) < 5:
                continue
            bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
            rows.append({
                'planet': planet.capitalize(),
                'state': label,
                'days': len(g),
                'bullish_pct': bullish.sum() / len(g) * 100,
                'avg_change': g['gold_change_pct'].mean(),
                'avg_range': g['gold_range'].mean(),
            })
    
    # Compute deltas
    planet_deltas = {}
    for r in rows:
        if r['state'] == 'Retro':
            planet_deltas[r['planet']] = {'retro': r}
        else:
            if r['planet'] in planet_deltas:
                planet_deltas[r['planet']]['direct'] = r
    
    deltas = []
    for p, vals in planet_deltas.items():
        if 'retro' in vals and 'direct' in vals:
            delta = vals['retro']['bullish_pct'] - vals['direct']['bullish_pct']
            deltas.append({
                'planet': p,
                'retro_bullish': vals['retro']['bullish_pct'],
                'direct_bullish': vals['direct']['bullish_pct'],
                'delta': delta,
            })
    deltas.sort(key=lambda x: -x['delta'])
    return rows, deltas

def analyze_combust(df):
    rows = []
    for planet in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']:
        col = f'{planet}_combust'
        if col not in df.columns:
            continue
        for combust_val, label in [(True, 'Combust'), (False, 'Not Combust')]:
            mask = df[col] == combust_val
            g = df[mask]
            if len(g) < 5:
                continue
            bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
            rows.append({
                'planet': planet.capitalize(),
                'state': label,
                'days': len(g),
                'bullish_pct': bullish.sum() / len(g) * 100,
                'avg_change': g['gold_change_pct'].mean(),
                'avg_range': g['gold_range'].mean(),
            })
    return rows

def analyze_gann(df):
    held = df[df['gann_key_level_held'] == True]
    breached = df[df['gann_key_level_held'] == False]
    
    results = {}
    if len(held) > 0:
        bullish = (held['gold_bullish'] == True) | (held['gold_bullish'] == 1) | (held['gold_bullish'] == 'True')
        results['held'] = {
            'days': len(held),
            'bullish_pct': bullish.sum() / len(held) * 100,
            'avg_range': held['gold_range'].mean(),
            'avg_change': held['gold_change_pct'].mean(),
        }
    if len(breached) > 0:
        bullish = (breached['gold_bullish'] == True) | (breached['gold_bullish'] == 1) | (breached['gold_bullish'] == 'True')
        results['breached'] = {
            'days': len(breached),
            'bullish_pct': bullish.sum() / len(breached) * 100,
            'avg_range': breached['gold_range'].mean(),
            'avg_change': breached['gold_change_pct'].mean(),
        }
    return results

def analyze_planet_hour(df):
    groups = df.groupby('dominant_planet_hour')
    rows = []
    for hour, g in groups:
        if pd.isna(hour) or hour == 'Unknown':
            continue
        bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
        rows.append({
            'hora': hour,
            'days': len(g),
            'bullish_pct': bullish.sum() / len(g) * 100,
            'avg_change': g['gold_change_pct'].mean(),
            'avg_range': g['gold_range'].mean(),
        })
    rows.sort(key=lambda x: -x['bullish_pct'])
    return rows

def analyze_market_reaction(df):
    groups = df.groupby('market_reaction')
    rows = []
    for reaction, g in groups:
        bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
        rows.append({
            'reaction': reaction,
            'days': len(g),
            'pct': len(g) / len(df) * 100,
            'bullish_pct': bullish.sum() / len(g) * 100,
            'avg_change': g['gold_change_pct'].mean(),
            'avg_range': g['gold_range'].mean(),
        })
    rows.sort(key=lambda x: -x['days'])
    return rows

def analyze_eclipse(df):
    eclipse_df = df[df['eclipse_active'] == True]
    if len(eclipse_df) == 0:
        return None
    bullish = (eclipse_df['gold_bullish'] == True) | (eclipse_df['gold_bullish'] == 1) | (eclipse_df['gold_bullish'] == 'True')
    return {
        'days': len(eclipse_df),
        'bullish_pct': bullish.sum() / len(eclipse_df) * 100,
        'avg_change': eclipse_df['gold_change_pct'].mean(),
        'avg_range': eclipse_df['gold_range'].mean(),
    }

def analyze_sun_aspect(df):
    """Sun conjunctions/aspects to planets."""
    aspects_col = safe_json(df['aspects_json'])
    results = defaultdict(lambda: {'days': 0, 'bullish': 0, 'avg_change': [], 'avg_range': []})
    
    for i, aspects in enumerate(aspects_col):
        if not isinstance(aspects, list):
            continue
        for asp in aspects:
            if not isinstance(asp, dict):
                continue
            p1, p2, a = _aspect_key(asp)
            if a not in ['Conjunction', 'Opposition', 'Square', 'Trine', 'Sextile']:
                continue
            if p1 != 'Sun' and p2 != 'Sun':
                continue
            key = f"Sun {a} {p2 if p1 == 'Sun' else p1}"
            bullish = (df.iloc[i]['gold_bullish'] == True) or (df.iloc[i]['gold_bullish'] == 1) or (df.iloc[i]['gold_bullish'] == 'True')
            results[key]['days'] += 1
            if bullish:
                results[key]['bullish'] += 1
            results[key]['avg_change'].append(df.iloc[i]['gold_change_pct'])
            results[key]['avg_range'].append(df.iloc[i]['gold_range'])
    
    rows = []
    for k, v in results.items():
        if v['days'] >= 5:
            rows.append({
                'aspect': k,
                'days': v['days'],
                'bullish_pct': v['bullish'] / v['days'] * 100,
                'avg_change': sum(v['avg_change']) / len(v['avg_change']),
                'avg_range': sum(v['avg_range']) / len(v['avg_range']),
            })
    rows.sort(key=lambda x: -x['bullish_pct'])
    return rows

def analyze_volatility(df):
    groups = df.groupby('volatility')
    rows = []
    for vol, g in groups:
        bullish = (g['gold_bullish'] == True) | (g['gold_bullish'] == 1) | (g['gold_bullish'] == 'True')
        rows.append({
            'vol': vol,
            'days': len(g),
            'pct': len(g) / len(df) * 100,
            'bullish_pct': bullish.sum() / len(g) * 100,
            'avg_change': g['gold_change_pct'].mean(),
            'avg_range': g['gold_range'].mean(),
        })
    return rows

def generate_report(df, months, start_month, end_month):
    lines = []
    total_days = len(df)
    lines.append(f"# 📊 Phân Tích Dữ Liệu Gold (XAUUSD)")
    lines.append(f"")
    lines.append(f"**Giai đoạn:** {start_month} → {end_month} ({total_days} trading days)")
    lines.append(f"**Generated:** 2026-05-22")
    lines.append(f"**Dataset:** {len(months)} monthly CSVs, 57 columns per day")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 1. BASELINE
    lines.append("## 1. BASELINE")
    lines.append(f"")
    bl = analyze_baseline(df)
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Trading Days | {bl['total']} |")
    lines.append(f"| Bullish Days (close > open) | {bl['bullish_pct']:.1f}% |")
    lines.append(f"| Bearish Days | {bl['bearish_pct']:.1f}% |")
    lines.append(f"| Neutral Days | {bl['neutral_pct']:.1f}% |")
    lines.append(f"| Avg Daily Change | {bl['avg_change']:+.3f}% |")
    lines.append(f"| Std Daily Change | {bl['std_change']:.3f}% |")
    lines.append(f"| Avg Daily Range | {bl['avg_range']:.2f} |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 2. MOON SIGN
    lines.append("## 2. MOON SIGN → TREND")
    lines.append(f"")
    ms = analyze_moon_sign(df)
    lines.append("| Moon Sign | Days | Bullish % | AvgΔ | Range | HighVol |")
    lines.append("|-----------|------|-----------|------|-------|---------|")
    for r in ms:
        bold = "**" if r['bullish_pct'] >= 65 or r['bullish_pct'] <= 35 else ""
        lines.append(f"| {r['sign']} | {r['days']} | {bold}{r['bullish_pct']:.1f}%{bold} | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} | {r['high_vol_count']} |")
    
    # Key insights
    strongest = ms[0]
    weakest = ms[-1]
    lines.append(f"")
    lines.append(f"**Key:** {strongest['sign']} ({strongest['bullish_pct']:.1f}% bullish) mạnh nhất. {weakest['sign']} ({weakest['bullish_pct']:.1f}%) yếu nhất.")
    high_vol = max(ms, key=lambda x: x['avg_range'])
    lines.append(f"{high_vol['sign']} có biên độ lớn nhất ({high_vol['avg_range']:.1f}).")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 3. NAKSHATRA
    lines.append("## 3. MOON NAKSHATRA → TREND")
    lines.append(f"")
    nk = analyze_nakshatra(df)
    lines.append("| Nakshatra | Days | Bullish % | AvgΔ | Range | HighVol |")
    lines.append("|-----------|------|-----------|------|-------|---------|")
    for r in nk:
        bold = "**" if r['bullish_pct'] >= 70 or r['bullish_pct'] <= 35 else ""
        lines.append(f"| {r['nakshatra']} | {r['days']} | {bold}{r['bullish_pct']:.1f}%{bold} | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} | {r['high_vol_count']} |")
    
    nk_strongest = nk[0]
    nk_weakest = nk[-1]
    spread = nk_strongest['bullish_pct'] - nk_weakest['bullish_pct']
    lines.append(f"")
    lines.append(f"**Key:** Nakshatra là predictor mạnh nhất. {nk_strongest['nakshatra']} {nk_strongest['bullish_pct']:.0f}% bullish vs {nk_weakest['nakshatra']} {nk_weakest['bullish_pct']:.1f}% — chênh lệch {spread:.0f}%.")
    
    bullish_cluster = [r['nakshatra'] for r in nk if r['bullish_pct'] >= 65]
    bearish_cluster = [r['nakshatra'] for r in nk if r['bullish_pct'] <= 35]
    if bullish_cluster:
        lines.append(f"- **Bullish cluster:** {', '.join(bullish_cluster)}")
    if bearish_cluster:
        lines.append(f"- **Bearish cluster:** {', '.join(bearish_cluster)}")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 4. PLANET RETROGRADE
    lines.append("## 4. PLANET RETROGRADE")
    lines.append(f"")
    pr, deltas = analyze_planet_retro(df)
    lines.append("| Planet | State | Days | Bullish % | AvgΔ | Range |")
    lines.append("|--------|-------|------|-----------|------|-------|")
    for r in pr:
        lines.append(f"| {r['planet']} | {r['state']} | {r['days']} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    
    if deltas:
        lines.append(f"")
        lines.append("### Retro vs Direct Delta")
        lines.append("")
        lines.append("| Planet | Retro % | Direct % | Delta |")
        lines.append("|--------|---------|----------|-------|")
        for d in deltas:
            direction = "🟢" if d['delta'] > 0 else "🔴"
            lines.append(f"| {d['planet']} | {d['retro_bullish']:.1f}% | {d['direct_bullish']:.1f}% | {direction} {d['delta']:+.1f}% |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 5. COMBUST
    lines.append("## 5. COMBUST (GẦN MẶT TRỜI)")
    lines.append(f"")
    cb = analyze_combust(df)
    lines.append("| Planet | State | Days | Bullish % | AvgΔ | Range |")
    lines.append("|--------|-------|------|-----------|------|-------|")
    for r in cb:
        lines.append(f"| {r['planet']} | {r['state']} | {r['days']} | {r['bullish_pct']:.1f}% | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 6. SUN ASPECTS
    lines.append("## 6. SUN ASPECTS TO PLANETS")
    lines.append(f"")
    sa = analyze_sun_aspect(df)
    if sa:
        lines.append("| Aspect | Days | Bullish % | AvgΔ | Range |")
        lines.append("|--------|------|-----------|------|-------|")
        for r in sa:
            bold = "**" if r['bullish_pct'] >= 70 or r['bullish_pct'] <= 35 else ""
            lines.append(f"| {r['aspect']} | {r['days']} | {bold}{r['bullish_pct']:.1f}%{bold} | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    else:
        lines.append("No significant Sun aspects found.")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 7. MOON ASPECTS
    lines.append("## 7. MOON ASPECTS TO PLANETS")
    lines.append(f"")
    ma = analyze_moon_sign_aspect(df)
    if ma:
        lines.append("| Aspect | Days | Bullish % | AvgΔ | Range |")
        lines.append("|--------|------|-----------|------|-------|")
        for r in ma:
            bold = "**" if r['bullish_pct'] >= 70 or r['bullish_pct'] <= 35 else ""
            lines.append(f"| {r['aspect']} | {r['days']} | {bold}{r['bullish_pct']:.1f}%{bold} | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    else:
        lines.append("No significant Moon aspects found.")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 8. GANN KEY LEVEL
    lines.append("## 8. GANN KEY LEVEL HELD vs BREACHED")
    lines.append(f"")
    gl = analyze_gann(df)
    if 'held' in gl and 'breached' in gl:
        lines.append("| State | Days | Bullish % | AvgΔ | Range |")
        lines.append("|-------|------|-----------|------|-------|")
        lines.append(f"| Held | {gl['held']['days']} | {gl['held']['bullish_pct']:.1f}% | {gl['held']['avg_change']:+.2f}% | {gl['held']['avg_range']:.1f} |")
        lines.append(f"| Breached | {gl['breached']['days']} | {gl['breached']['bullish_pct']:.1f}% | {gl['breached']['avg_change']:+.2f}% | {gl['breached']['avg_range']:.1f} |")
        ratio = gl['breached']['avg_range'] / gl['held']['avg_range'] if gl['held']['avg_range'] > 0 else 0
        lines.append(f"")
        lines.append(f"**Key:** Range khi breached gấp {ratio:.1f}x so với held.")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 9. PLANET HOUR
    lines.append("## 9. DOMINANT PLANET HOUR (HORA)")
    lines.append(f"")
    ph = analyze_planet_hour(df)
    lines.append("| Hora | Days | Bullish % | AvgΔ | Range |")
    lines.append("|------|------|-----------|------|-------|")
    for r in ph:
        bold = "**" if r['bullish_pct'] >= 60 or r['bullish_pct'] <= 40 else ""
        lines.append(f"| {r['hora']} | {r['days']} | {bold}{r['bullish_pct']:.1f}%{bold} | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 10. MARKET REACTION
    lines.append("## 10. MARKET REACTION DISTRIBUTION")
    lines.append(f"")
    mr = analyze_market_reaction(df)
    lines.append("| Reaction | Days | % of Total | Bullish % | AvgΔ | Range |")
    lines.append("|----------|------|------------|-----------|------|-------|")
    for r in mr:
        lines.append(f"| {r['reaction']} | {r['days']} | {r['pct']:.1f}% | {r['bullish_pct']:.1f}% | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 11. VOLATILITY
    lines.append("## 11. VOLATILITY REGIMES")
    lines.append(f"")
    vr = analyze_volatility(df)
    lines.append("| Volatility | Days | % of Total | Bullish % | AvgΔ | Range |")
    lines.append("|------------|------|------------|-----------|------|-------|")
    for r in vr:
        lines.append(f"| {r['vol']} | {r['days']} | {r['pct']:.1f}% | {r['bullish_pct']:.1f}% | {r['avg_change']:+.2f}% | {r['avg_range']:.1f} |")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 12. ECLIPSE
    lines.append("## 12. ECLIPSE PERIODS")
    lines.append(f"")
    ec = analyze_eclipse(df)
    if ec:
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Eclipse Days | {ec['days']} |")
        lines.append(f"| Bullish % | {ec['bullish_pct']:.1f}% |")
        lines.append(f"| AvgΔ | {ec['avg_change']:+.2f}% |")
        lines.append(f"| Avg Range | {ec['avg_range']:.1f} |")
    else:
        lines.append("No eclipse periods in this dataset.")
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    
    # 13. KEY FINDINGS SUMMARY
    lines.append("## 🔑 KEY FINDINGS SUMMARY")
    lines.append(f"")
    
    # Nakshatra
    lines.append(f"- **Nakshatra strongest predictor:** {nk_strongest['nakshatra']} {nk_strongest['bullish_pct']:.0f}% bullish vs {nk_weakest['nakshatra']} {nk_weakest['bullish_pct']:.1f}% ({spread:.0f}% spread)")
    
    # Moon sign
    lines.append(f"- **Moon Sign:** {strongest['sign']} {strongest['bullish_pct']:.1f}% bullish; {weakest['sign']} {weakest['bullish_pct']:.1f}% weakest")
    
    # Retrograde highlights
    if deltas:
        for d in deltas[:3]:
            direction = "bullish hơn" if d['delta'] > 0 else "bearish hơn"
            lines.append(f"- **{d['planet']} Retro:** {direction} direct ({d['delta']:+.1f}% delta)")
    
    # Combust highlights
    for r in cb:
        if r['state'] == 'Combust' and r['days'] >= 10:
            lines.append(f"- **{r['planet']} Combust:** {r['bullish_pct']:.1f}% bullish, range {r['avg_range']:.1f}")
    
    # Sun aspects
    if sa:
        for r in sa[:3]:
            lines.append(f"- **{r['aspect']}:** {r['bullish_pct']:.1f}% bullish, {r['avg_change']:+.2f}%")
    
    # Gann
    if 'held' in gl and 'breached' in gl:
        ratio = gl['breached']['avg_range'] / gl['held']['avg_range'] if gl['held']['avg_range'] > 0 else 0
        lines.append(f"- **Gann Key Held:** range {gl['held']['avg_range']:.1f} vs {gl['breached']['avg_range']:.1f} breached ({ratio:.1f}x)")
    
    # Hora
    if ph:
        best_hora = ph[0]
        worst_hora = ph[-1]
        lines.append(f"- **Hora:** {best_hora['hora']} {best_hora['bullish_pct']:.0f}% bullish; {worst_hora['hora']} {worst_hora['bullish_pct']:.1f}% bearish")
    
    # Market reaction
    if mr:
        reversal = [r for r in mr if 'reversal' in r['reaction'].lower()]
        strong_trend = [r for r in mr if 'strong' in r['reaction'].lower()]
        desc_parts = []
        if reversal:
            desc_parts.append(f"{reversal[0]['pct']:.1f}% reversal")
        if strong_trend:
            desc_parts.append(f"only {strong_trend[0]['pct']:.1f}% strong trend")
        if desc_parts:
            lines.append(f"- **Market reaction:** {', '.join(desc_parts)} → range-bound với sudden reversals")
    
    lines.append(f"")
    lines.append("---")
    lines.append(f"")
    lines.append(f"*Report generated by analyze_period.py | Data: {start_month} → {end_month} | {total_days} trading days*")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    data_dir = sys.argv[1] if len(sys.argv) > 1 else 'data'
    start = sys.argv[2] if len(sys.argv) > 2 else '2022-04'
    end = sys.argv[3] if len(sys.argv) > 3 else '2023-04'
    
    df, months = load_period(data_dir, start, end)
    print(f"Loaded {len(df)} rows from {len(months)} months: {months[0]} → {months[-1]}", file=sys.stderr)
    
    report = generate_report(df, months, start, end)
    print(report)
