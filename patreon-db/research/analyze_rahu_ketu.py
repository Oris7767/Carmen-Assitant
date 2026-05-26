#!/usr/bin/env python3
"""
patreon-db/analyze_rahu_ketu.py

Analyzes the full dataset (2023-05 to 2026-05) to find patterns
related to Rahu and Ketu.

- Rahu/Ketu by Sign & Nakshatra
- Rahu/Ketu Aspects
- Correlations with Moon Sign, Gann Levels, and Hora

Outputs a detailed markdown report.
"""

import os
import pandas as pd
import json
from glob import glob
from datetime import datetime

# --- Config ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "ANALYSIS_REPORT_RAHU_KETU.md")
START_DATE = "2023-05-01"
END_DATE = "2026-05-31"

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]
NAKSHATRA_SPAN = 13.3333  # 13°20'

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]

# --- Helper Functions ---

def load_data():
    """Loads all CSVs within the date range into a single DataFrame."""
    all_files = sorted(glob(os.path.join(DATA_DIR, "*.csv")))
    
    # Filter files based on date range
    relevant_files = []
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d").replace(day=1)
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d").replace(day=1)
    
    for f in all_files:
        try:
            file_date_str = os.path.basename(f).replace('.csv', '')
            file_dt = datetime.strptime(file_date_str, "%Y-%m").replace(day=1)
            if start_dt <= file_dt <= end_dt:
                relevant_files.append(f)
        except ValueError:
            continue

    if not relevant_files:
        print(f"No data files found for the period {START_DATE} to {END_DATE}.")
        return pd.DataFrame()

    df = pd.concat((pd.read_csv(f) for f in relevant_files), ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def get_nakshatra(sign, degree):
    """Calculates Nakshatra from a planet's sign and degree."""
    if sign not in ZODIAC_SIGNS:
        return None
    sign_index = ZODIAC_SIGNS.index(sign)
    total_degrees = sign_index * 30 + degree
    nakshatra_index = int(total_degrees / NAKSHATRA_SPAN)
    return NAKSHATRAS[nakshatra_index]

def analyze_by_attribute(df, attribute_col, title):
    """Generic analysis function for attributes like Sign or Nakshatra."""
    results = df.groupby(attribute_col)['gold_bullish'].agg(['count', lambda x: x.mean() * 100])
    results.rename(columns={'<lambda_0>': 'bullish_pct'}, inplace=True)
    
    # Add avg change and range
    avg_change = df.groupby(attribute_col)['gold_change_pct'].mean()
    avg_range = df.groupby(attribute_col)['gold_range'].mean()
    results = results.join(avg_change).join(avg_range)
    
    results.rename(columns={
        'count': 'Days',
        'bullish_pct': 'Bullish %',
        'gold_change_pct': 'Avg Change %',
        'gold_range': 'Avg Range $'
    }, inplace=True)
    
    results = results.sort_values('Bullish %', ascending=False)
    results['Bullish %'] = results['Bullish %'].round(1)
    results['Avg Change %'] = results['Avg Change %'].round(3)
    results['Avg Range $'] = results['Avg Range $'].round(2)
    
    return f"### {title}\n\n{results.to_markdown()}\n\n"

def analyze_aspects(df):
    """Analyzes aspects involving Rahu and Ketu."""
    aspect_data = []
    for index, row in df.iterrows():
        try:
            aspects = json.loads(row['aspects_json'])
            for aspect in aspects:
                p1, p2 = aspect['planet1'], aspect['planet2']
                if 'Rahu' in [p1, p2] or 'Ketu' in [p1, p2]:
                    # Standardize order (planet first, then node)
                    node = 'Rahu' if 'Rahu' in [p1, p2] else 'Ketu'
                    planet = p2 if p1 == node else p1
                    if planet in ['Rahu', 'Ketu']: continue # Skip Rahu-Ketu aspect

                    aspect_data.append({
                        'date': row['date'],
                        'gold_bullish': row['gold_bullish'],
                        'gold_change_pct': row['gold_change_pct'],
                        'gold_range': row['gold_range'],
                        'planet': planet,
                        'node': node,
                        'aspect_type': aspect['aspect']
                    })
        except (json.JSONDecodeError, TypeError):
            continue
            
    if not aspect_data:
        return "### Rahu/Ketu Aspect Analysis\n\nNo valid aspect data found.\n\n"

    aspect_df = pd.DataFrame(aspect_data)
    aspect_df['aspect_key'] = aspect_df['planet'] + " " + aspect_df['aspect_type'] + " " + aspect_df['node']
    
    results = aspect_df.groupby('aspect_key')['gold_bullish'].agg(['count', lambda x: x.mean() * 100])
    results.rename(columns={'<lambda_0>': 'bullish_pct'}, inplace=True)
    
    avg_change = aspect_df.groupby('aspect_key')['gold_change_pct'].mean()
    avg_range = aspect_df.groupby('aspect_key')['gold_range'].mean()
    results = results.join(avg_change).join(avg_range)

    results.rename(columns={
        'count': 'Count',
        'bullish_pct': 'Bullish %',
        'gold_change_pct': 'Avg Change %',
        'gold_range': 'Avg Range $'
    }, inplace=True)

    results = results[results['Count'] >= 5] # Filter for significance
    results = results.sort_values('Bullish %', ascending=False)
    results['Bullish %'] = results['Bullish %'].round(1)
    results['Avg Change %'] = results['Avg Change %'].round(3)
    results['Avg Range $'] = results['Avg Range $'].round(2)

    return f"### Rahu/Ketu Aspect Analysis (Count >= 5)\n\n{results.to_markdown()}\n\n"


# --- Main Execution ---

def main():
    df = load_data()
    if df.empty:
        return

    # --- Pre-computation ---
    df['rahu_nakshatra'] = df.apply(lambda row: get_nakshatra(row['rahu_sign'], row['rahu_deg']), axis=1)
    df['ketu_nakshatra'] = df.apply(lambda row: get_nakshatra(row['ketu_sign'], row['ketu_deg']), axis=1)

    # --- Analysis ---
    report_parts = []
    
    # Header and Baseline
    total_days = len(df)
    baseline_bullish_pct = df['gold_bullish'].mean() * 100
    report_parts.append(f"# Analysis Report: Rahu & Ketu Patterns ({START_DATE} to {END_DATE})\n")
    report_parts.append(f"**Total Trading Days Analyzed:** {total_days}\n")
    report_parts.append(f"**Baseline Bullish %:** {baseline_bullish_pct:.1f}%\n\n")
    
    # Sign Analysis
    report_parts.append("## 1. Analysis by Sign\n")
    report_parts.append(analyze_by_attribute(df, 'rahu_sign', "Rahu by Sign"))
    report_parts.append(analyze_by_attribute(df, 'ketu_sign', "Ketu by Sign"))

    # Nakshatra Analysis
    report_parts.append("## 2. Analysis by Nakshatra\n")
    report_parts.append(analyze_by_attribute(df.dropna(subset=['rahu_nakshatra']), 'rahu_nakshatra', "Rahu by Nakshatra"))
    report_parts.append(analyze_by_attribute(df.dropna(subset=['ketu_nakshatra']), 'ketu_nakshatra', "Ketu by Nakshatra"))

    # Aspect Analysis
    report_parts.append("## 3. Aspect Analysis\n")
    report_parts.append(analyze_aspects(df))

    # --- Write Report ---
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("".join(report_parts))
        
    print(f"Analysis complete. Report saved to:\n{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
