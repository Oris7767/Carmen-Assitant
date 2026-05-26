#!/usr/bin/env python3
"""
Backfill Gann Square of 9 columns into all existing CSVs.
NEW COLUMNS: gann_base, gann_scale, gann_nearest_support, gann_nearest_resistance,
             gann_gap, gann_held, gann_breached, gann_levels_json

KEY FIX: Gann levels are calculated from SWING HIGH (structural anchor),
not from close price. Close is then checked against those levels.
Threshold: 2% of close price (~$60 at $3000).
"""
import sys
import os
import math
import json
import pandas as pd
import glob

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

GANN_CRITICAL_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]

def gann_extract_base(price):
    price_str = str(int(price))
    if len(price_str) >= 3:
        return int(price_str[:3])
    return int(price)

def gann_scale_factor(price):
    return 10 if price >= 1000 else 1.0

def gann_calculate_levels(price):
    """Calculate Gann S9 levels from a structural anchor (swing high)."""
    base = gann_extract_base(price)
    scale = gann_scale_factor(price)
    root = math.sqrt(base)
    all_levels = []
    for angle in GANN_CRITICAL_ANGLES:
        factor = angle / 180.0
        res = (root + factor) ** 2 * scale
        sup = (root - factor) ** 2 * scale
        all_levels.append({'angle': angle, 'price': round(res, 2), 'direction': 'resistance'})
        all_levels.append({'angle': angle, 'price': round(sup, 2), 'direction': 'support'})
    all_levels.sort(key=lambda x: x['price'])
    below = [l for l in all_levels if l['price'] <= price]
    above = [l for l in all_levels if l['price'] > price]
    nearest_support = max(below, key=lambda x: x['price']) if below else None
    nearest_resistance = min(above, key=lambda x: x['price']) if above else None
    return {
        'base': base,
        'scale': scale,
        'all_levels': all_levels,
        'nearest_support_price': nearest_support['price'] if nearest_support else None,
        'nearest_resistance_price': nearest_resistance['price'] if nearest_resistance else None,
    }

NEW_COLS = [
    'gann_base', 'gann_scale', 'gann_nearest_support', 'gann_nearest_resistance',
    'gann_gap', 'gann_held', 'gann_breached', 'gann_levels_json',
]

def backfill_gann(filepath):
    df = pd.read_csv(filepath)
    existing = set(df.columns)
    still_missing = [c for c in NEW_COLS if c not in existing]
    if not still_missing:
        # Check if gann_held has any True values — if not, re-fill with corrected logic
        if 'gann_held' in df.columns and df['gann_held'].sum() > 0:
            return True  # already has valid data
        still_missing = NEW_COLS  # re-fill with corrected logic
    
    if not still_missing:
        return True
    
    print(f"  Backfilling {os.path.basename(filepath)}: {len(still_missing)} cols")
    
    bases = []
    scales = []
    supports = []
    resistances = []
    gaps = []
    helds = []
    breachees = []
    levels_jsons = []
    
    for _, row in df.iterrows():
        close = float(row['gold_close'])
        swing_high = float(row['gold_high'])
        
        # KEY FIX: Calculate Gann from SWING HIGH, not close
        g = gann_calculate_levels(swing_high)
        
        ns = g['nearest_support_price'] if g['nearest_support_price'] else ""
        nr = g['nearest_resistance_price'] if g['nearest_resistance_price'] else ""
        gap = round(float(nr) - float(ns), 2) if ns and nr else ""
        
        # Gann held check: within 2% of close price from nearest level
        g_held = False
        g_breach = ""
        if ns and nr:
            threshold = close * 0.02  # 2% of close price
            dist_sup = abs(close - float(ns))
            dist_res = abs(close - float(nr))
            if dist_sup < threshold:
                g_held = True
                g_breach = f"support_{ns}"
            elif dist_res < threshold:
                g_held = True
                g_breach = f"resistance_{nr}"
        
        levels_data = {
            'base': g['base'],
            'scale': g['scale'],
            'supports': [l['price'] for l in g['all_levels'] if l['direction'] == 'support'],
            'resistances': [l['price'] for l in g['all_levels'] if l['direction'] == 'resistance'],
        }
        
        bases.append(g['base'])
        scales.append(g['scale'])
        supports.append(ns)
        resistances.append(nr)
        gaps.append(gap)
        helds.append(g_held)
        breachees.append(g_breach)
        levels_jsons.append(json.dumps(levels_data, ensure_ascii=False))
    
    if 'gann_base' in still_missing:
        df['gann_base'] = bases
    if 'gann_scale' in still_missing:
        df['gann_scale'] = scales
    if 'gann_nearest_support' in still_missing:
        df['gann_nearest_support'] = supports
    if 'gann_nearest_resistance' in still_missing:
        df['gann_nearest_resistance'] = resistances
    if 'gann_gap' in still_missing:
        df['gann_gap'] = gaps
    if 'gann_held' in still_missing:
        df['gann_held'] = helds
    if 'gann_breached' in still_missing:
        df['gann_breached'] = breachees
    if 'gann_levels_json' in still_missing:
        df['gann_levels_json'] = levels_jsons
    
    df.to_csv(filepath, index=False)
    print(f"  ✅ {os.path.basename(filepath)}: {len(df.columns)} cols, gann_held={sum(helds)}")
    return True

def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "202*.csv")))
    print(f"Found {len(files)} files to process")
    
    success = 0
    failed = 0
    
    for filepath in files:
        try:
            backfill_gann(filepath)
            success += 1
        except Exception as e:
            print(f"  ❌ ERROR: {filepath}: {e}")
            failed += 1
    
    print(f"\nDone: {success} backfilled, {failed} failed")

if __name__ == '__main__':
    main()
