#!/usr/bin/env python3
"""
patreon-db/fix_data.py — Quick patch script
============================================
Patches existing CSV files with:
  1. US10Y data (fixes timezone bug from v1)
  2. moon_nakshatra_lord (trivially computed, no API needed)
  3. Can optionally re-collect with v2 for full new columns

Usage:
    python3 fix_data.py --us10y        Patch US10Y only (fast)
    python3 fix_data.py --nakshatra    Add nakshatra_lord column (instant)
    python3 fix_data.py --all          Patch everything possible without API
    python3 fix_data.py --status       Show what needs fixing
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

NAKSHATRA_LORDS = {
    "Ashwini": "Ketu", "Bharani": "Venus", "Krittika": "Sun",
    "Rohini": "Moon", "Mrigashira": "Mars", "Ardra": "Rahu",
    "Punarvasu": "Jupiter", "Pushya": "Saturn", "Ashlesha": "Mercury",
    "Magha": "Ketu", "Purva Phalguni": "Venus", "Uttara Phalguni": "Sun",
    "Hasta": "Moon", "Chitra": "Mars", "Swati": "Rahu",
    "Vishakha": "Jupiter", "Anuradha": "Saturn", "Jyeshtha": "Mercury",
    "Mula": "Ketu", "Purva Ashadha": "Venus", "Uttara Ashadha": "Sun",
    "Shravana": "Moon", "Dhanishta": "Mars", "Shatabhisha": "Rahu",
    "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada": "Saturn",
    "Revati": "Mercury",
}


def normalize_df_index(df):
    if df.empty: return df
    df = df.copy()
    # Remove timezone THEN normalize — normalize() alone keeps tz
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep='last')]
    return df


def fetch_us10y_month(year, month):
    """Fetch US10Y with normalized index."""
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    try:
        ticker = yf.Ticker("^TNX")
        df = ticker.history(start=start, end=end, interval="1d")
        if df.empty: return df
        return normalize_df_index(df)
    except Exception as e:
        print(f"  ⚠️  ^TNX error: {e}")
        return pd.DataFrame()


def patch_us10y_all():
    """Patch US10Y across all CSV files."""
    print("🔧 Patching US10Y across all months...")
    total_patched = 0
    
    for year in range(2016, 2027):
        start_month = 6 if year == 2016 else 1
        end_month = 6 if year == 2026 else 13
        for month in range(start_month, end_month):
            if year == 2026 and month > 5: break
            
            csv_path = os.path.join(DATA_DIR, f"{year}-{month:02d}.csv")
            if not os.path.exists(csv_path): continue
            
            df = pd.read_csv(csv_path)
            
            # Check if already has data
            has_data = 0
            for v in df.get('us10y_close', []):
                if v != '' and v != 0 and not (isinstance(v, float) and pd.isna(v)):
                    try:
                        if float(v) > 0: has_data += 1
                    except: pass
            
            if has_data > len(df) * 0.8:
                print(f"  {year}-{month:02d}: Already OK ({has_data}/{len(df)} rows)")
                continue
            
            us10y_df = fetch_us10y_month(year, month)
            if us10y_df.empty:
                print(f"  {year}-{month:02d}: No US10Y data available")
                continue
            
            us10y_df['us10y_change'] = us10y_df['Close'].diff()
            patched = 0
            
            for idx, row in df.iterrows():
                try:
                    ts = pd.to_datetime(row['date'])
                    if ts in us10y_df.index:
                        ur = us10y_df.loc[ts]
                        if isinstance(ur, pd.DataFrame): ur = ur.iloc[0]
                        df.at[idx, 'us10y_close'] = round(float(ur['Close']), 2)
                        if pd.notna(ur.get('us10y_change')):
                            df.at[idx, 'us10y_change'] = round(float(ur['us10y_change']), 2)
                        patched += 1
                except: pass
            
            df.to_csv(csv_path, index=False)
            print(f"  ✅ {year}-{month:02d}: Patched {patched}/{len(df)} rows")
            total_patched += patched
    
    print(f"\n✅ US10Y patch complete: {total_patched} rows patched")
    return total_patched


def patch_nakshatra_lord_all():
    """Add moon_nakshatra_lord column to all CSVs (no API needed)."""
    print("🔧 Adding moon_nakshatra_lord to all months...")
    total_patched = 0
    
    for year in range(2016, 2027):
        start_month = 6 if year == 2016 else 1
        end_month = 6 if year == 2026 else 13
        for month in range(start_month, end_month):
            if year == 2026 and month > 5: break
            
            csv_path = os.path.join(DATA_DIR, f"{year}-{month:02d}.csv")
            if not os.path.exists(csv_path): continue
            
            df = pd.read_csv(csv_path)
            
            # Check if column already exists
            if 'moon_nakshatra_lord' in df.columns:
                filled = sum(1 for v in df['moon_nakshatra_lord'] if v != '' and str(v).strip() != '')
                if filled > len(df) * 0.8:
                    print(f"  {year}-{month:02d}: nakshatra_lord already OK ({filled}/{len(df)})")
                    continue
            
            # Compute nakshatra lord from moon_nakshatra
            lords = []
            for nak in df['moon_nakshatra']:
                lords.append(NAKSHATRA_LORDS.get(str(nak).strip(), ""))
            
            df['moon_nakshatra_lord'] = lords
            
            # Ensure column order: insert after moon_nakshatra
            cols = list(df.columns)
            if 'moon_nakshatra_lord' in cols:
                cols.remove('moon_nakshatra_lord')
                nak_idx = cols.index('moon_nakshatra')
                cols.insert(nak_idx + 1, 'moon_nakshatra_lord')
                df = df[cols]
            
            df.to_csv(csv_path, index=False)
            total_patched += len(df)
            print(f"  ✅ {year}-{month:02d}: Added nakshatra_lord ({len(df)} rows)")
    
    print(f"\n✅ Nakshatra lord patch complete: {total_patched} rows")
    return total_patched


def check_status():
    """Report what data is present vs missing."""
    print("📊 Data Status Report\n")
    
    all_dfs = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith('.csv'):
            all_dfs.append(pd.read_csv(os.path.join(DATA_DIR, f)))
    
    df = pd.concat(all_dfs, ignore_index=True)
    total = len(df)
    print(f"Total rows: {total}")
    print(f"Date range: {df['date'].min()} → {df['date'].max()}")
    print(f"")
    
    checks = {
        "✅ Gold/Price": 'gold_close',
        "✅ Astrology": 'moon_sign',
        "✅ Nakshatra": 'moon_nakshatra',
        "✅ Aspects": 'aspects_json',
        "✅ DXY": 'dxy_close',
        "🔴 US10Y": 'us10y_close',
        "🆕 Nakshatra Lord": 'moon_nakshatra_lord',
        "🆕 S&P 500": 'sp500_change_pct',
        "🆕 VIX": 'vix_close',
        "🆕 Volume": 'gold_volume',
        "🆕 ATR(14)": 'gold_atr_14',
        "🆕 RSI(14)": 'gold_rsi_14',
    }
    
    for label, col in checks.items():
        if col not in df.columns:
            print(f"  {label}: ❌ Column missing")
            continue
        filled = 0
        for v in df[col]:
            if v != '' and v != 0 and not (isinstance(v, float) and pd.isna(v)):
                try:
                    if col in ('us10y_close', 'dxy_close', 'sp500_change_pct', 'vix_close', 'gold_atr_14', 'gold_rsi_14'):
                        if float(v) != 0: filled += 1
                    else:
                        filled += 1
                except:
                    if str(v).strip(): filled += 1
        
        pct = round(filled / total * 100, 1)
        if pct > 95:
            print(f"  {label}: ✅ {pct}% ({filled}/{total})")
        elif pct > 0:
            print(f"  {label}: ⚠️ {pct}% ({filled}/{total})")
        else:
            print(f"  {label}: 🔴 {pct}% — needs fix")


if __name__ == "__main__":
    if '--status' in sys.argv or len(sys.argv) < 2:
        check_status()
    elif '--us10y' in sys.argv:
        patch_us10y_all()
    elif '--nakshatra' in sys.argv:
        patch_nakshatra_lord_all()
    elif '--all' in sys.argv:
        patch_us10y_all()
        patch_nakshatra_lord_all()
    else:
        print("Usage: python3 fix_data.py [--status|--us10y|--nakshatra|--all]")
        check_status()
