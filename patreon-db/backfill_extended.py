#!/usr/bin/env python3
"""
Backfill missing extended columns (EMA, DXY, US10Y, Moon Phase)
into existing CSV files from 2023-05 onwards.

Missing columns:
  gold_ema_31, gold_ema_113, gold_ema_relation
  dxy_close, dxy_change_pct, dxy_direction
  us10y_close, us10y_change
  moon_phase, moon_illumination_pct
"""
import sys
import os
import math
import pandas as pd
import yfinance as yf
import swisseph as swe

# ─── Swiss Ephemeris config ───
swe.set_ephe_path(None)
swe.set_sid_mode(swe.SIDM_LAHIRI)

GEO_LON = 106.7
GEO_LAT = 10.78
GEO_ALT = 0
TIMEZONE_OFFSET = 7

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

MISSING_COLS = [
    'gold_ema_31', 'gold_ema_113', 'gold_ema_relation',
    'dxy_close', 'dxy_change_pct', 'dxy_direction',
    'us10y_close', 'us10y_change',
    'moon_phase', 'moon_illumination_pct',
]

def jd_from_date(year, month, day):
    return swe.julday(year, month, day, 0.0)

def calculate_moon_phase(jd):
    sun_pos = swe.calc(jd, swe.SUN, swe.FLG_SWIEPH)
    moon_pos = swe.calc(jd, swe.MOON, swe.FLG_SWIEPH)
    sun_lon = sun_pos[0][0]
    moon_lon = moon_pos[0][0]
    phase_angle = (moon_lon - sun_lon) % 360
    illumination = round((1 - math.cos(math.radians(phase_angle))) / 2 * 100, 1)
    if phase_angle < 22.5:
        phase_name = "New Moon"
    elif phase_angle < 67.5:
        phase_name = "Waxing Crescent"
    elif phase_angle < 112.5:
        phase_name = "First Quarter"
    elif phase_angle < 157.5:
        phase_name = "Waxing Gibbous"
    elif phase_angle < 202.5:
        phase_name = "Full Moon"
    elif phase_angle < 247.5:
        phase_name = "Waning Gibbous"
    elif phase_angle < 292.5:
        phase_name = "Last Quarter"
    elif phase_angle < 337.5:
        phase_name = "Waning Crescent"
    else:
        phase_name = "New Moon"
    return phase_name, illumination

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def get_extended_gold_data(year, month, lookback_days=200):
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    from_dt = pd.to_datetime(start) - pd.Timedelta(days=lookback_days)
    start_early = from_dt.strftime("%Y-%m-%d")
    ticker = yf.Ticker("GC=F")
    try:
        df = ticker.history(start=start_early, end=end, interval="1d")
        if not df.empty:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"  Warning: gold data error: {e}", file=sys.stderr)
        return pd.DataFrame()

def get_dxy_data(year, month):
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    ticker = yf.Ticker("DX-Y.NYB")
    try:
        df = ticker.history(start=start, end=end, interval="1d")
        if not df.empty:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"  Warning: DXY data error: {e}", file=sys.stderr)
        return pd.DataFrame()

def get_us10y_data(year, month):
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    ticker = yf.Ticker("^TNX")
    try:
        df = ticker.history(start=start, end=end, interval="1d")
        if not df.empty:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"  Warning: US10Y data error: {e}", file=sys.stderr)
        return pd.DataFrame()

def backfill_month(filepath, year, month):
    """Backfill one month's CSV with missing columns."""
    df = pd.read_csv(filepath)
    
    # Check if already has all columns
    existing_cols = set(df.columns)
    still_missing = [c for c in MISSING_COLS if c not in existing_cols]
    if not still_missing:
        print(f"  SKIP: {os.path.basename(filepath)} — already complete")
        return True
    
    print(f"  Backfilling {os.path.basename(filepath)}: {len(still_missing)} cols missing")
    
    # ─── 1. Gold EMA ───
    gold_df = get_extended_gold_data(year, month, lookback_days=200)
    if not gold_df.empty:
        gold_df['ema_31'] = calc_ema(gold_df['Close'], 31)
        gold_df['ema_113'] = calc_ema(gold_df['Close'], 113)
    else:
        print(f"  ERROR: No gold data for EMA, skipping EMA", file=sys.stderr)
    
    # ─── 2. DXY ───
    dxy_df = get_dxy_data(year, month)
    if not dxy_df.empty:
        dxy_df['dxy_change_pct'] = dxy_df['Close'].pct_change() * 100
        dxy_prev = dxy_df['Close'].shift(1)
        dxy_df['dxy_direction'] = 'neutral'
        dxy_df.loc[dxy_df['Close'] > dxy_prev, 'dxy_direction'] = 'bullish'
        dxy_df.loc[dxy_df['Close'] < dxy_prev, 'dxy_direction'] = 'bearish'
    
    # ─── 3. US10Y ───
    us10y_df = get_us10y_data(year, month)
    if not us10y_df.empty:
        us10y_df['us10y_change'] = us10y_df['Close'].diff()
    
    # ─── 4. Moon phase ───
    # We need JD for each date
    moon_phases = []
    moon_illums = []
    
    for _, row in df.iterrows():
        date_str = str(row['date'])
        try:
            parts = date_str.split('-')
            yr, mo, dy = int(parts[0]), int(parts[1]), int(parts[2])
            jd = jd_from_date(yr, mo, dy)
            phase, illum = calculate_moon_phase(jd)
        except:
            phase, illum = "Unknown", 0
        moon_phases.append(phase)
        moon_illums.append(illum)
    
    # ─── 5. Build new columns ───
    new_ema_31 = []
    new_ema_113 = []
    new_ema_rel = []
    new_dxy_close = []
    new_dxy_change = []
    new_dxy_dir = []
    new_us10y_close = []
    new_us10y_change = []
    
    for _, row in df.iterrows():
        date_str = str(row['date'])
        
        # EMA
        if date_str in gold_df.index:
            grow = gold_df.loc[date_str]
            e31 = round(float(grow['ema_31']), 2) if 'ema_31' in gold_df.columns and pd.notna(grow.get('ema_31')) else ""
            e113 = round(float(grow['ema_113']), 2) if 'ema_113' in gold_df.columns and pd.notna(grow.get('ema_113')) else ""
            if e31 and e113:
                rel = "above" if e31 > e113 else "below"
            else:
                rel = ""
        else:
            e31, e113, rel = "", "", ""
        
        new_ema_31.append(e31)
        new_ema_113.append(e113)
        new_ema_rel.append(rel)
        
        # DXY
        if not dxy_df.empty and date_str in dxy_df.index:
            drow = dxy_df.loc[date_str]
            new_dxy_close.append(round(float(drow['Close']), 2))
            new_dxy_change.append(round(float(drow['dxy_change_pct']), 2) if pd.notna(drow.get('dxy_change_pct')) else "")
            new_dxy_dir.append(drow.get('dxy_direction', ''))
        else:
            new_dxy_close.append("")
            new_dxy_change.append("")
            new_dxy_dir.append("")
        
        # US10Y
        if not us10y_df.empty and date_str in us10y_df.index:
            urow = us10y_df.loc[date_str]
            new_us10y_close.append(round(float(urow['Close']), 2))
            new_us10y_change.append(round(float(urow['us10y_change']), 2) if pd.notna(urow.get('us10y_change')) else "")
        else:
            new_us10y_close.append("")
            new_us10y_change.append("")
    
    # Add columns to dataframe
    if 'gold_ema_31' in still_missing:
        df['gold_ema_31'] = new_ema_31
    if 'gold_ema_113' in still_missing:
        df['gold_ema_113'] = new_ema_113
    if 'gold_ema_relation' in still_missing:
        df['gold_ema_relation'] = new_ema_rel
    if 'dxy_close' in still_missing:
        df['dxy_close'] = new_dxy_close
    if 'dxy_change_pct' in still_missing:
        df['dxy_change_pct'] = new_dxy_change
    if 'dxy_direction' in still_missing:
        df['dxy_direction'] = new_dxy_dir
    if 'us10y_close' in still_missing:
        df['us10y_close'] = new_us10y_close
    if 'us10y_change' in still_missing:
        df['us10y_change'] = new_us10y_change
    if 'moon_phase' in still_missing:
        df['moon_phase'] = moon_phases
    if 'moon_illumination_pct' in still_missing:
        df['moon_illumination_pct'] = moon_illums
    
    # Reorder columns: put new columns in logical positions
    # Original order was: ... dominant_planet_hour, sunrise_local
    # New: ... dominant_planet_hour, sunrise_local, gold_ema_31, gold_ema_113, gold_ema_relation, dxy_close, dxy_change_pct, dxy_direction, us10y_close, us10y_change, moon_phase, moon_illumination_pct
    # Check what the 2022-04 column order was:
    # The 2022 files have these columns at the end: dxy_close, dxy_change_pct, dxy_direction, us10y_close, us10y_change
    # But no moon_phase or moon_illumination_pct in 2022-04... let me check
    
    df.to_csv(filepath, index=False)
    print(f"  ✅ Saved {os.path.basename(filepath)}: {len(df.columns)} columns")
    return True

def main():
    import glob
    files = sorted(glob.glob(os.path.join(DATA_DIR, "202*.csv")))
    
    # Target: 2023-05 to 2026-05
    target = [f for f in files if f >= os.path.join(DATA_DIR, "2023-05.csv") 
              and f <= os.path.join(DATA_DIR, "2026-05.csv")]
    
    # Filter to only those missing columns
    todo = []
    for f in target:
        df = pd.read_csv(f)
        still_missing = [c for c in MISSING_COLS if c not in df.columns]
        if still_missing:
            todo.append(f)
    
    print(f"Found {len(todo)} files needing backfill (out of {len(target)} total)")
    
    success = 0
    failed = 0
    skipped = 0
    
    for filepath in todo:
        # Extract year-month from filename
        basename = os.path.basename(filepath)
        ym = basename.replace('.csv', '')
        yr, mo = int(ym.split('-')[0]), int(ym.split('-')[1])
        
        try:
            ok = backfill_month(filepath, yr, mo)
            if ok:
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}", file=sys.stderr)
            failed += 1
    
    print(f"\nDone: {success} backfilled, {failed} failed")

if __name__ == '__main__':
    main()
