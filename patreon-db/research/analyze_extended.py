#!/usr/bin/env python3
"""
Extended analysis: EMA, DXY, US10Y, Moon Phase correlations.
Appends additional sections to the main report.
"""
import sys
import os
import pandas as pd
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_all(start_month, end_month):
    dfs = []
    sm_y, sm_m = map(int, start_month.split('-'))
    em_y, em_m = map(int, end_month.split('-'))
    y, m = sm_y, sm_m
    while (y, m) <= (em_y, em_m):
        fname = f"{y}-{m:02d}.csv"
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            df = pd.read_csv(fpath)
            dfs.append(df)
        m += 1
        if m > 12:
            m = 1
            y += 1
    return pd.concat(dfs, ignore_index=True)

def is_bullish(series):
    return (series == True) | (series == 1) | (series == 'True')

def analyze_ema(df):
    """EMA 31 vs EMA 113 relation."""
    if 'gold_ema_relation' not in df.columns:
        return None
    
    lines = []
    lines.append("## 13. EMA 31 vs EMA 113 RELATION")
    lines.append("")
    
    # Overall
    above = df[df['gold_ema_relation'] == 'above']
    below = df[df['gold_ema_relation'] == 'below']
    
    lines.append("### Overall")
    lines.append("")
    lines.append("| EMA State | Days | % | Bullish % | AvgΔ | Range |")
    lines.append("|-----------|------|---|-----------|------|-------|")
    
    for label, g in [('EMA31 > EMA113', above), ('EMA31 < EMA113', below)]:
        if len(g) == 0:
            continue
        bl = is_bullish(g['gold_bullish'])
        lines.append(f"| {label} | {len(g)} | {len(g)/len(df)*100:.1f}% | {bl.sum()/len(g)*100:.1f}% | {g['gold_change_pct'].mean():+.2f}% | {g['gold_range'].mean():.1f} |")
    
    # EMA cross analysis: detect cross days
    df_sorted = df.sort_values('date')
    crosses = []
    for i in range(1, len(df_sorted)):
        prev = df_sorted.iloc[i-1]
        curr = df_sorted.iloc[i]
        if pd.notna(prev.get('gold_ema_relation')) and pd.notna(curr.get('gold_ema_relation')):
            if prev['gold_ema_relation'] != curr['gold_ema_relation'] and prev['gold_ema_relation'] != '' and curr['gold_ema_relation'] != '':
                crosses.append(curr)
    
    if crosses:
        cross_df = pd.DataFrame(crosses)
        bl = is_bullish(cross_df['gold_bullish'])
        lines.append("")
        lines.append(f"### EMA Cross Days ({len(crosses)} occurrences)")
        lines.append("")
        lines.append(f"- Bullish: {bl.sum()/len(cross_df)*100:.1f}%")
        lines.append(f"- AvgΔ: {cross_df['gold_change_pct'].mean():+.2f}%")
        lines.append(f"- Avg Range: {cross_df['gold_range'].mean():.1f}")
    
    # EMA state + Moon Sign combo
    lines.append("")
    lines.append("### EMA State × Moon Sign (Top Signals)")
    lines.append("")
    lines.append("| EMA State | Moon Sign | Days | Bullish % | AvgΔ | Range |")
    lines.append("|-----------|-----------|------|-----------|------|-------|")
    
    combos = df.groupby(['gold_ema_relation', 'moon_sign'])
    rows = []
    for (ema, sign), g in combos:
        if len(g) >= 5:
            bl = is_bullish(g['gold_bullish'])
            rows.append({'ema': ema, 'sign': sign, 'days': len(g), 'bl_pct': bl.sum()/len(g)*100, 'avg_d': g['gold_change_pct'].mean(), 'avg_r': g['gold_range'].mean()})
    
    rows.sort(key=lambda x: -x['bl_pct'])
    for r in rows[:15]:
        bold = "**" if r['bl_pct'] >= 65 or r['bl_pct'] <= 40 else ""
        lines.append(f"| {r['ema']} | {r['sign']} | {r['days']} | {bold}{r['bl_pct']:.1f}%{bold} | {r['avg_d']:+.2f}% | {r['avg_r']:.1f} |")
    
    return '\n'.join(lines)

def analyze_dxy(df):
    """DXY correlation with gold."""
    if 'dxy_close' not in df.columns:
        return None
    
    lines = []
    lines.append("")
    lines.append("## 14. DXY (DOLLAR INDEX) CORRELATION")
    lines.append("")
    
    # DXY direction vs gold
    dxy_df = df[df['dxy_direction'].notna() & (df['dxy_direction'] != '')]
    if len(dxy_df) > 0:
        lines.append("### DXY Direction → Gold Trend")
        lines.append("")
        lines.append("| DXY Direction | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        lines.append("|---------------|------|----------------|-----------|------------|")
        
        for dxy_dir in ['bullish', 'bearish', 'neutral']:
            g = dxy_df[dxy_df['dxy_direction'] == dxy_dir]
            if len(g) == 0:
                continue
            bl = is_bullish(g['gold_bullish'])
            lines.append(f"| {dxy_dir} | {len(g)} | {bl.sum()/len(g)*100:.1f}% | {g['gold_change_pct'].mean():+.2f}% | {g['gold_range'].mean():.1f} |")
        
        # DXY change magnitude vs gold
        dxy_df_valid = dxy_df[dxy_df['dxy_change_pct'].notna()]
        if len(dxy_df_valid) > 0:
            # Split DXY change into strong/weak
            dxy_df_valid = dxy_df_valid.copy()
            dxy_df_valid['dxy_abs_change'] = dxy_df_valid['dxy_change_pct'].abs()
            
            strong_dxy = dxy_df_valid[dxy_df_valid['dxy_abs_change'] >= 0.5]
            weak_dxy = dxy_df_valid[dxy_df_valid['dxy_abs_change'] < 0.5]
            
            lines.append("")
            lines.append("### DXY Change Magnitude → Gold Reaction")
            lines.append("")
            lines.append("| DXY |Δ| | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
            lines.append("|------|------|-------|----------------|-----------|------------|")
            
            if len(strong_dxy) > 0:
                bl = is_bullish(strong_dxy['gold_bullish'])
                lines.append(f"| ≥0.5% | {len(strong_dxy)} | {bl.sum()/len(strong_dxy)*100:.1f}% | {strong_dxy['gold_change_pct'].mean():+.2f}% | {strong_dxy['gold_range'].mean():.1f} |")
            if len(weak_dxy) > 0:
                bl = is_bullish(weak_dxy['gold_bullish'])
                lines.append(f"| <0.5% | {len(weak_dxy)} | {bl.sum()/len(weak_dxy)*100:.1f}% | {weak_dxy['gold_change_pct'].mean():+.2f}% | {weak_dxy['gold_range'].mean():.1f} |")
    
    # DXY level bands
    dxy_valid = df[df['dxy_close'].notna() & (df['dxy_close'] != '')]
    if len(dxy_valid) > 0:
        dxy_valid = dxy_valid.copy()
        dxy_valid['dxy_close'] = pd.to_numeric(dxy_valid['dxy_close'], errors='coerce')
        dxy_valid = dxy_valid.dropna(subset=['dxy_close'])
        
        if len(dxy_valid) > 0:
            q1 = dxy_valid['dxy_close'].quantile(0.33)
            q2 = dxy_valid['dxy_close'].quantile(0.66)
            
            lines.append("")
            lines.append("### DXY Level Bands")
            lines.append("")
            lines.append("| DXY Range | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
            lines.append("|-----------|------|----------------|-----------|------------|")
            
            low = dxy_valid[dxy_valid['dxy_close'] <= q1]
            mid = dxy_valid[(dxy_valid['dxy_close'] > q1) & (dxy_valid['dxy_close'] <= q2)]
            high = dxy_valid[dxy_valid['dxy_close'] > q2]
            
            for label, g in [(f'Low (≤{q1:.1f})', low), (f'Mid ({q1:.1f}-{q2:.1f})', mid), (f'High (>{q2:.1f})', high)]:
                if len(g) == 0:
                    continue
                bl = is_bullish(g['gold_bullish'])
                lines.append(f"| {label} | {len(g)} | {bl.sum()/len(g)*100:.1f}% | {g['gold_change_pct'].mean():+.2f}% | {g['gold_range'].mean():.1f} |")
    
    return '\n'.join(lines)

def analyze_us10y(df):
    """US 10Y Treasury yield correlation."""
    if 'us10y_close' not in df.columns:
        return None
    
    lines = []
    lines.append("")
    lines.append("## 15. US 10Y TREASURY YIELD CORRELATION")
    lines.append("")
    
    us_valid = df[df['us10y_close'].notna() & (df['us10y_close'] != '')]
    if len(us_valid) == 0:
        lines.append("No US10Y data available.")
        return '\n'.join(lines)
    
    us_valid = us_valid.copy()
    us_valid['us10y_close'] = pd.to_numeric(us_valid['us10y_close'], errors='coerce')
    us_valid = us_valid.dropna(subset=['us10y_close'])
    
    if len(us_valid) > 0:
        # Yield level bands
        q1 = us_valid['us10y_close'].quantile(0.33)
        q2 = us_valid['us10y_close'].quantile(0.66)
        
        lines.append("### Yield Level Bands")
        lines.append("")
        lines.append("| US10Y Range | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
        lines.append("|-------------|------|----------------|-----------|------------|")
        
        low = us_valid[us_valid['us10y_close'] <= q1]
        mid = us_valid[(us_valid['us10y_close'] > q1) & (us_valid['us10y_close'] <= q2)]
        high = us_valid[us_valid['us10y_close'] > q2]
        
        for label, g in [(f'Low (≤{q1:.2f}%)', low), (f'Mid ({q1:.2f}-{q2:.2f}%)', mid), (f'High (>{q2:.2f}%)', high)]:
            if len(g) == 0:
                continue
            bl = is_bullish(g['gold_bullish'])
            lines.append(f"| {label} | {len(g)} | {bl.sum()/len(g)*100:.1f}% | {g['gold_change_pct'].mean():+.2f}% | {g['gold_range'].mean():.1f} |")
    
    # Yield change direction
    us_change = df[df['us10y_change'].notna() & (df['us10y_change'] != '')]
    if len(us_change) > 0:
        us_change = us_change.copy()
        us_change['us10y_change'] = pd.to_numeric(us_change['us10y_change'], errors='coerce')
        us_change = us_change.dropna(subset=['us10y_change'])
        
        if len(us_change) > 0:
            rising = us_change[us_change['us10y_change'] > 0]
            falling = us_change[us_change['us10y_change'] < 0]
            
            lines.append("")
            lines.append("### Yield Change Direction → Gold")
            lines.append("")
            lines.append("| US10Y Change | Days | Gold Bullish % | Gold AvgΔ | Gold Range |")
            lines.append("|--------------|------|----------------|-----------|------------|")
            
            if len(rising) > 0:
                bl = is_bullish(rising['gold_bullish'])
                lines.append(f"| Rising | {len(rising)} | {bl.sum()/len(rising)*100:.1f}% | {rising['gold_change_pct'].mean():+.2f}% | {rising['gold_range'].mean():.1f} |")
            if len(falling) > 0:
                bl = is_bullish(falling['gold_bullish'])
                lines.append(f"| Falling | {len(falling)} | {bl.sum()/len(falling)*100:.1f}% | {falling['gold_change_pct'].mean():+.2f}% | {falling['gold_range'].mean():.1f} |")
    
    return '\n'.join(lines)

def analyze_moon_phase(df):
    """Moon phase analysis."""
    if 'moon_phase' not in df.columns:
        return None
    
    lines = []
    lines.append("")
    lines.append("## 16. MOON PHASE → TREND")
    lines.append("")
    
    mp_df = df[df['moon_phase'].notna() & (df['moon_phase'] != '') & (df['moon_phase'] != 'Unknown')]
    if len(mp_df) == 0:
        lines.append("No moon phase data available.")
        return '\n'.join(lines)
    
    # 8-phase breakdown
    phase_order = ['New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous', 
                   'Full Moon', 'Waning Gibbous', 'Last Quarter', 'Waning Crescent']
    
    lines.append("| Moon Phase | Days | Bullish % | AvgΔ | Range | HighVol |")
    lines.append("|------------|------|-----------|------|-------|---------|")
    
    rows = []
    for phase in phase_order:
        g = mp_df[mp_df['moon_phase'] == phase]
        if len(g) == 0:
            continue
        bl = is_bullish(g['gold_bullish'])
        rows.append({
            'phase': phase,
            'days': len(g),
            'bl_pct': bl.sum()/len(g)*100,
            'avg_d': g['gold_change_pct'].mean(),
            'avg_r': g['gold_range'].mean(),
            'high_vol': (g['volatility'] == 'high').sum(),
        })
    
    # Also add any phases not in the standard list
    for phase in mp_df['moon_phase'].unique():
        if phase not in phase_order:
            g = mp_df[mp_df['moon_phase'] == phase]
            bl = is_bullish(g['gold_bullish'])
            rows.append({
                'phase': phase,
                'days': len(g),
                'bl_pct': bl.sum()/len(g)*100,
                'avg_d': g['gold_change_pct'].mean(),
                'avg_r': g['gold_range'].mean(),
                'high_vol': (g['volatility'] == 'high').sum(),
            })
    
    rows.sort(key=lambda x: -x['bl_pct'])
    for r in rows:
        bold = "**" if r['bl_pct'] >= 60 or r['bl_pct'] <= 40 else ""
        lines.append(f"| {r['phase']} | {r['days']} | {bold}{r['bl_pct']:.1f}%{bold} | {r['avg_d']:+.2f}% | {r['avg_r']:.1f} | {r['high_vol']} |")
    
    # Illumination bands
    illum_valid = df[df['moon_illumination_pct'].notna() & (df['moon_illumination_pct'] != '')]
    if len(illum_valid) > 0:
        illum_valid = illum_valid.copy()
        illum_valid['moon_illumination_pct'] = pd.to_numeric(illum_valid['moon_illumination_pct'], errors='coerce')
        illum_valid = illum_valid.dropna(subset=['moon_illumination_pct'])
        
        if len(illum_valid) > 0:
            # Split into 4 bands: 0-25, 25-50, 50-75, 75-100
            lines.append("")
            lines.append("### Moon Illumination Bands")
            lines.append("")
            lines.append("| Illumination % | Days | Bullish % | AvgΔ | Range |")
            lines.append("|----------------|------|-----------|------|-------|")
            
            for label, low, high in [('0-25% (Dark)', 0, 25), ('25-50% (Growing)', 25, 50), 
                                       ('50-75% (Bright)', 50, 75), ('75-100% (Full)', 75, 101)]:
                g = illum_valid[(illum_valid['moon_illumination_pct'] >= low) & (illum_valid['moon_illumination_pct'] < high)]
                if len(g) == 0:
                    continue
                bl = is_bullish(g['gold_bullish'])
                lines.append(f"| {label} | {len(g)} | {bl.sum()/len(g)*100:.1f}% | {g['gold_change_pct'].mean():+.2f}% | {g['gold_range'].mean():.1f} |")
    
    return '\n'.join(lines)

def main():
    df = load_all(sys.argv[1], sys.argv[2])
    
    sections = []
    
    ema = analyze_ema(df)
    if ema:
        sections.append(ema)
    
    dxy = analyze_dxy(df)
    if dxy:
        sections.append(dxy)
    
    us10y = analyze_us10y(df)
    if us10y:
        sections.append(us10y)
    
    moon = analyze_moon_phase(df)
    if moon:
        sections.append(moon)
    
    print('\n\n---\n\n'.join(sections))

if __name__ == '__main__':
    main()
