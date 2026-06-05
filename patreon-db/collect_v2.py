#!/usr/bin/env python3
"""
patreon-db/collect_v2.py — ENHANCED COLLECTOR
=============================================
Bug fixes vs v1:
  - US10Y timezone normalization (was 100% empty due to TZ mismatch)
  - DXY timezone normalization
  - All external data normalized to date-only index before join

New columns (vs v1):
  - moon_nakshatra_lord       — ruler of the nakshatra
  - sp500_change_pct          — S&P 500 daily change
  - vix_close                 — VIX fear index
  - gold_volume               — trading volume
  - gold_atr_14               — Average True Range (14-day)
  - gold_rsi_14               — Relative Strength Index (14-day)

Modes:
  - Full month:  python3 collect_v2.py 2025-05
  - Incremental: python3 collect_v2.py 2025-05 --inc  (only fill missing days)
  - Dry run:     python3 collect_v2.py 2025-05 --dry
  - Backfill:    python3 collect_v2.py --backfill-all  (re-process all 120 months)

Usage:
    python3 collect_v2.py 2025-05              # full month
    python3 collect_v2.py 2025-05 --inc        # incremental (fill gaps only)
    python3 collect_v2.py 2025-05 --dry        # preview
    python3 collect_v2.py --backfill-all       # re-process everything
    python3 collect_v2.py --fix-us10y          # only fix US10Y across all CSVs
"""

import sys
import os
import json
import math
import calendar
import pandas as pd
import numpy as np
import yfinance as yf
import swisseph as swe
from datetime import datetime, date, timedelta
from collections import defaultdict

# ─── Swiss Ephemeris config ───
swe.set_ephe_path(None)
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ─── Config ───
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

GEO_LON, GEO_LAT, GEO_ALT = 106.7, 10.78, 0
TIMEZONE_OFFSET = 7

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON,
    "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}
RAHU_NODE = swe.MEAN_NODE

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra Lords (Vedic rulership)
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

FIB_RATIOS = [0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874]
GANN_CRITICAL_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]

COMBUST_ORBS = {"Mars": 8, "Saturn": 8, "Jupiter": 8, "Venus": 4, "Mercury": 2}
CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
DAY_LORDS = {
    "Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury",
    "Thursday": "Jupiter", "Friday": "Venus", "Saturday": "Saturn", "Sunday": "Sun",
}

# ─── Column definitions ───
# Full ordered column list matching CSVs
ALL_COLUMNS = [
    "date", "day_of_week",
    "gold_open", "gold_close", "gold_high", "gold_low", "gold_range",
    "gold_change_pct", "gold_bullish",
    "gold_ema_31", "gold_ema_113", "gold_ema_relation",
    "gann_swing_high", "gann_swing_low", "gann_trend",
    "fib_levels_json",
    "gann_key_level_held", "gann_breached_level", "gann_reaction",
    "gann_base", "gann_scale", "gann_nearest_support", "gann_nearest_resistance",
    "gann_gap", "gann_held", "gann_breached", "gann_levels_json",
    "sun_sign", "sun_deg",
    "moon_sign", "moon_deg", "moon_nakshatra", "moon_nakshatra_lord",
    "mercury_sign", "mercury_deg", "mercury_retro",
    "venus_sign", "venus_deg", "venus_retro",
    "mars_sign", "mars_deg", "mars_retro",
    "jupiter_sign", "jupiter_deg", "jupiter_retro",
    "saturn_sign", "saturn_deg", "saturn_retro",
    "rahu_sign", "rahu_deg",
    "ketu_sign", "ketu_deg",
    "mercury_elong_deg", "mercury_elong_dir", "mercury_combust",
    "venus_elong_deg", "venus_elong_dir", "venus_combust",
    "mars_elong_deg", "mars_combust",
    "jupiter_elong_deg", "saturn_elong_deg",
    "aspects_json",
    "eclipse_active", "eclipse_type", "eclipse_days_away",
    "moon_phase", "moon_illumination_pct",
    "economic_events", "economic_impact",
    "market_reaction", "trend_direction", "volatility",
    "dominant_planet_hour", "sunrise_local",
    "dxy_close", "dxy_change_pct", "dxy_direction",
    "us10y_close", "us10y_change",
    # ─── NEW v2 columns ───
    "sp500_change_pct", "vix_close",
    "gold_volume", "gold_atr_14", "gold_rsi_14",
]

# Columns added in v2 (for backfill detection)
V2_NEW_COLUMNS = [
    "moon_nakshatra_lord",
    "sp500_change_pct", "vix_close",
    "gold_volume", "gold_atr_14", "gold_rsi_14",
]

# ─── Economic Events DB (same as v1) ───
ECONOMIC_EVENTS_DB = {
    "nfp": {"name": "Non-Farm Payrolls (NFP)", "schedule": "first_friday", "time_et": "08:30", "impact": "high"},
    "unemployment": {"name": "Unemployment Rate", "schedule": "first_friday", "time_et": "08:30", "impact": "high"},
    "avg_hourly_earnings": {"name": "Average Hourly Earnings", "schedule": "first_friday", "time_et": "08:30", "impact": "medium"},
    "cpi": {"name": "CPI (Consumer Price Index)", "schedule": "cpi_window", "time_et": "08:30", "impact": "high"},
    "pce": {"name": "PCE Price Index", "schedule": "pce_window", "time_et": "08:30", "impact": "high"},
    "fomc": {"name": "FOMC Rate Decision", "schedule": "fomc_dates", "time_et": "14:00", "impact": "high"},
    "fomc_minutes": {"name": "FOMC Minutes", "schedule": "fomc_minutes", "time_et": "14:00", "impact": "medium"},
    "gdp": {"name": "GDP (Advance Estimate)", "schedule": "gdp_windows", "time_et": "08:30", "impact": "high"},
    "retail_sales": {"name": "Retail Sales", "schedule": "retail_window", "time_et": "08:30", "impact": "medium"},
    "ism_mfg": {"name": "ISM Manufacturing PMI", "schedule": "first_business_day", "time_et": "10:00", "impact": "medium"},
    "ism_services": {"name": "ISM Services PMI", "schedule": "third_business_day", "time_et": "10:00", "impact": "medium"},
    "jobless_claims": {"name": "Initial Jobless Claims", "schedule": "weekly_thursday", "time_et": "08:30", "impact": "low"},
    "adp": {"name": "ADP Non-Farm Employment", "schedule": "mid_month", "time_et": "08:15", "impact": "medium"},
    "consumer_confidence": {"name": "Consumer Confidence", "schedule": "last_tuesday", "time_et": "10:00", "impact": "medium"},
    "michigan_sentiment": {"name": "U of Michigan Consumer Sentiment", "schedule": "michigan_window", "time_et": "10:00", "impact": "medium"},
    "trade_balance": {"name": "Trade Balance", "schedule": "monthly", "time_et": "08:30", "impact": "low"},
    "durable_goods": {"name": "Durable Goods Orders", "schedule": "durable_window", "time_et": "08:30", "impact": "medium"},
    "housing_starts": {"name": "Housing Starts", "schedule": "housing_window", "time_et": "08:30", "impact": "medium"},
    "existing_home_sales": {"name": "Existing Home Sales", "schedule": "housing_window", "time_et": "10:00", "impact": "low"},
    "new_home_sales": {"name": "New Home Sales", "schedule": "durable_window", "time_et": "10:00", "impact": "medium"},
}

FOMC_DATES_BY_YEAR = {
    2016: [date(2016,1,27),date(2016,3,16),date(2016,4,27),date(2016,6,15),date(2016,7,27),date(2016,9,21),date(2016,11,2),date(2016,12,14)],
    2017: [date(2017,2,1),date(2017,3,15),date(2017,5,3),date(2017,6,14),date(2017,7,26),date(2017,9,20),date(2017,11,1),date(2017,12,13)],
    2018: [date(2018,1,31),date(2018,3,21),date(2018,5,2),date(2018,6,13),date(2018,8,1),date(2018,9,26),date(2018,11,8),date(2018,12,19)],
    2019: [date(2019,1,30),date(2019,3,20),date(2019,5,1),date(2019,6,19),date(2019,7,31),date(2019,9,18),date(2019,10,30),date(2019,12,11)],
    2020: [date(2020,1,29),date(2020,3,3),date(2020,3,15),date(2020,4,29),date(2020,6,10),date(2020,7,29),date(2020,9,16),date(2020,11,5),date(2020,12,16)],
    2021: [date(2021,1,27),date(2021,3,17),date(2021,4,28),date(2021,6,16),date(2021,7,28),date(2021,9,22),date(2021,11,3),date(2021,12,15)],
    2022: [date(2022,2,2),date(2022,3,16),date(2022,5,4),date(2022,6,15),date(2022,7,27),date(2022,9,21),date(2022,11,2),date(2022,12,14)],
    2023: [date(2023,2,1),date(2023,3,22),date(2023,5,3),date(2023,6,14),date(2023,7,26),date(2023,9,20),date(2023,11,1),date(2023,12,13)],
    2024: [date(2024,1,31),date(2024,3,20),date(2024,6,12),date(2024,7,31),date(2024,9,18),date(2024,11,7),date(2024,12,18)],
    2025: [date(2025,1,29),date(2025,3,19),date(2025,5,7),date(2025,6,18),date(2025,7,30),date(2025,9,17),date(2025,10,29),date(2025,12,17)],
}


# ─── Helper Functions ───

def normalize_df_index(df):
    """Normalize a yfinance DataFrame index to date-only (no timezone)."""
    if df.empty:
        return df
    df = df.copy()
    # Remove timezone THEN normalize — normalize() alone keeps timezone info
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    # Remove duplicate dates (keep last)
    df = df[~df.index.duplicated(keep='last')]
    return df


def jd_from_date(year, month, day):
    return swe.julday(year, month, day, 0.0)


def sign_and_degree(sidereal_lon):
    sign_idx = int(sidereal_lon // 30)
    return ZODIAC_SIGNS[sign_idx], round(sidereal_lon % 30, 2)


def nakshatra(sidereal_lon):
    nak_idx = int(sidereal_lon // (360 / 27))
    return NAKSHATRAS[nak_idx % 27]


def nakshatra_lord(nak_name):
    return NAKSHATRA_LORDS.get(nak_name, "")


def sidereal_position(jd_ut1, planet_id):
    flag = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, ierr = swe.calc_ut(jd_ut1, planet_id, flag)
    if ierr < 0:
        return None, None, None
    return result[0], result[3], result[2]


def elongation_from_sun(lon_planet, lon_sun):
    diff = (lon_planet - lon_sun) % 360
    if diff > 180:
        diff = 360 - diff
    return round(diff, 2)


def elongation_direction(lon_planet, lon_sun):
    diff = (lon_planet - lon_sun) % 360
    return "W" if diff > 180 else "E"


def is_combust(elong_deg, planet_name):
    if planet_name in COMBUST_ORBS:
        return elong_deg <= COMBUST_ORBS[planet_name]
    return False


def gann_calculate_levels(price):
    """Gann Square of 9 levels from price."""
    price_str = str(int(price))
    base = int(price_str[:3]) if len(price_str) >= 3 else int(price)
    scale = 10 if price >= 1000 else 1.0
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
        'base': base, 'scale': scale,
        'all_levels': all_levels,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'nearest_support_price': nearest_support['price'] if nearest_support else None,
        'nearest_resistance_price': nearest_resistance['price'] if nearest_resistance else None,
    }


def calculate_aspects(jd, include_nodes=True):
    positions = {}
    for name, pid in PLANETS.items():
        lon, speed, _ = sidereal_position(jd, pid)
        if lon is not None:
            positions[name] = lon

    if include_nodes:
        rahu_lon, _, _ = sidereal_position(jd, RAHU_NODE)
        if rahu_lon is not None:
            positions["Rahu"] = rahu_lon
            positions["Ketu"] = (rahu_lon + 180) % 360

    aspects = []
    aspect_defs = [
        ("Conjunction", 0, 5), ("Sextile", 60, 4),
        ("Square", 90, 4), ("Trine", 120, 4), ("Opposition", 180, 5),
    ]

    planet_names = list(positions.keys())
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1, p2 = planet_names[i], planet_names[j]
            diff = abs(positions[p1] - positions[p2])
            if diff > 180:
                diff = 360 - diff
            for aspect_name, angle, orb in aspect_defs:
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "planet1": p1, "planet2": p2,
                        "aspect": aspect_name,
                        "orb_deg": round(abs(diff - angle), 2)
                    })
    return aspects


def check_eclipse(jd):
    moon_lon, _, _ = sidereal_position(jd, swe.MOON)
    sun_lon, _, _ = sidereal_position(jd, swe.SUN)
    if moon_lon is None or sun_lon is None:
        return False, "", 0
    moon_phase_deg = (moon_lon - sun_lon) % 360
    new_moon_diff = min(moon_phase_deg, 360 - moon_phase_deg)
    full_moon_diff = min(abs(moon_phase_deg - 180), 360 - abs(moon_phase_deg - 180))
    if new_moon_diff < 15:
        return True, "Solar", int(new_moon_diff)
    elif full_moon_diff < 15:
        return True, "Lunar", int(full_moon_diff)
    return False, "", 0


def calculate_moon_phase(jd):
    sun_lon, _, _ = sidereal_position(jd, swe.SUN)
    moon_lon, _, _ = sidereal_position(jd, swe.MOON)
    if sun_lon is None or moon_lon is None:
        return "Unknown", 0
    phase_angle = (moon_lon - sun_lon) % 360
    illumination = round((1 - math.cos(math.radians(phase_angle))) / 2 * 100, 1)
    if phase_angle < 22.5: phase_name = "New Moon"
    elif phase_angle < 67.5: phase_name = "Waxing Crescent"
    elif phase_angle < 112.5: phase_name = "First Quarter"
    elif phase_angle < 157.5: phase_name = "Waxing Gibbous"
    elif phase_angle < 202.5: phase_name = "Full Moon"
    elif phase_angle < 247.5: phase_name = "Waning Gibbous"
    elif phase_angle < 292.5: phase_name = "Last Quarter"
    elif phase_angle < 337.5: phase_name = "Waning Crescent"
    else: phase_name = "New Moon"
    return phase_name, illumination


def get_sunrise(jd):
    flag = swe.CALC_RISE | swe.BIT_DISC_CENTER
    geopos = [GEO_LON, GEO_LAT, GEO_ALT]
    res_code, tret = swe.rise_trans(jd, swe.SUN, flag, geopos)
    if res_code >= 0 and len(tret) > 0:
        sunrise_jd = tret[0]
        hours_ut = (sunrise_jd - jd) * 24
        return round((hours_ut + TIMEZONE_OFFSET) % 24, 2)
    return 5.5


def calculate_market_reaction(row):
    open_p, close, high, low = float(row.get("Open", 0)), float(row.get("Close", 0)), float(row.get("High", 0)), float(row.get("Low", 0))
    if open_p == 0:
        return "unknown", "range", "low"
    range_pct = (high - low) / open_p * 100
    body = abs(close - open_p)
    body_pct = body / open_p * 100
    upper_wick = high - max(open_p, close)
    lower_wick = min(open_p, close) - low
    wick_ratio = (upper_wick + lower_wick) / (high - low) if (high - low) > 0 else 0

    if range_pct > 2.0: volatility = "high"
    elif range_pct > 1.0: volatility = "medium"
    else: volatility = "low"

    trend = "bullish" if close > open_p else ("bearish" if close < open_p else "neutral")

    if body_pct > 1.5 and wick_ratio < 0.3: reaction = "strong_trend"
    elif body_pct > 1.0 and wick_ratio < 0.4: reaction = "moderate_trend"
    elif wick_ratio > 0.6: reaction = "reversal_signal"
    elif range_pct < 0.5: reaction = "consolidation"
    elif body_pct > 0.5: reaction = "mild_trend"
    else: reaction = "choppy"

    return reaction, trend, volatility


def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calc_atr(df, period=14):
    """Calculate Average True Range."""
    high, low, close = df['High'], df['Low'], df['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calc_rsi(series, period=14):
    """Calculate RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ─── Economic Events Scheduling ───

def get_first_friday(year, month):
    cal = calendar.Calendar(calendar.SUNDAY)
    for week in cal.monthdatescalendar(year, month):
        for day in week:
            if day.month == month and day.weekday() == 4:
                return day
    return None


def get_first_business_day(year, month):
    for day in range(1, 8):
        d = date(year, month, day)
        if d.weekday() < 5: return d
    return None


def get_third_business_day(year, month):
    count = 0
    for day in range(1, 15):
        d = date(year, month, day)
        if d.weekday() < 5:
            count += 1
            if count == 3: return d
    return None


def get_last_tuesday(year, month):
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, 0, -1):
        d = date(year, month, day)
        if d.weekday() == 1: return d
    return None


def get_cpi_date(year, month):
    for day in range(10, 16):
        try:
            d = date(year, month, day)
            if d.weekday() < 5: return d
        except: pass
    return None


def get_pce_date(year, month):
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, last_day - 6, -1):
        try:
            d = date(year, month, day)
            if d.weekday() < 5: return d
        except: pass
    return None


def get_retail_sales_date(year, month):
    for day in range(13, 18):
        try:
            d = date(year, month, day)
            if d.weekday() < 5: return d
        except: pass
    return None


def get_gdp_dates_for_year(year):
    return [date(year, 4, 25), date(year, 7, 30), date(year, 10, 29), date(year + 1, 1, 28)]


def get_fomc_dates(year):
    return FOMC_DATES_BY_YEAR.get(year, [])


def get_economic_events_for_date(year, month, day, day_of_week):
    d = date(year, month, day)
    events = []

    first_friday = get_first_friday(year, month)
    if first_friday and d == first_friday:
        events.append(("Non-Farm Payrolls (NFP)", "high"))
        events.append(("Unemployment Rate", "high"))
        events.append(("Avg Hourly Earnings", "medium"))

    first_bd = get_first_business_day(year, month)
    if first_bd and d == first_bd:
        events.append(("ISM Manufacturing PMI", "medium"))

    third_bd = get_third_business_day(year, month)
    if third_bd and d == third_bd:
        events.append(("ISM Services PMI", "medium"))

    last_tue = get_last_tuesday(year, month)
    if last_tue and d == last_tue:
        events.append(("Consumer Confidence", "medium"))

    cpi_date = get_cpi_date(year, month)
    if cpi_date and d == cpi_date:
        events.append(("CPI (Consumer Price Index)", "high"))

    pce_date = get_pce_date(year, month)
    if pce_date and d == pce_date:
        events.append(("PCE Price Index", "high"))

    retail_date = get_retail_sales_date(year, month)
    if retail_date and d == retail_date:
        events.append(("Retail Sales", "medium"))

    # Durable goods ~23-27th
    for dy in range(23, 28):
        try:
            dd = date(year, month, dy)
            if dd.weekday() < 5 and d == dd:
                events.append(("Durable Goods Orders", "medium"))
        except: pass

    # Housing starts ~16-20th
    for dy in range(16, 21):
        try:
            dd = date(year, month, dy)
            if dd.weekday() < 5 and d == dd:
                events.append(("Housing Starts", "medium"))
        except: pass

    # Michigan sentiment ~14-17th
    for dy in range(14, 18):
        try:
            dd = date(year, month, dy)
            if dd.weekday() < 5 and d == dd:
                events.append(("Michigan Consumer Sentiment", "medium"))
        except: pass

    # ADP = 2 days before first Friday
    if first_friday:
        adp_date = first_friday - timedelta(days=2)
        if d == adp_date:
            events.append(("ADP Non-Farm Employment", "medium"))

    if day_of_week == "Thursday":
        events.append(("Initial Jobless Claims", "low"))

    if d in get_fomc_dates(year):
        events.append(("FOMC Rate Decision", "high"))

    if d in get_gdp_dates_for_year(year):
        events.append(("GDP Advance Estimate", "high"))

    return events


# ─── Data Fetching (FIXED timezone handling) ───

def fetch_and_normalize(ticker_symbol, start_str, end_str):
    """Fetch yfinance data and normalize index to date-only."""
    ticker = yf.Ticker(ticker_symbol)
    try:
        df = ticker.history(start=start_str, end=end_str, interval="1d")
        if df.empty:
            return df
        return normalize_df_index(df)
    except Exception as e:
        print(f"  ⚠️  {ticker_symbol}: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_extended_gold_data(year, month, lookback_days=200):
    """Fetch gold with lookback for EMA/ATR/RSI calculation."""
    start_dt = date(year, month, 1) - timedelta(days=lookback_days)
    if month == 12:
        end_dt = date(year + 1, 1, 1)
    else:
        end_dt = date(year, month + 1, 1)
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    return fetch_and_normalize("GC=F", start_str, end_str)


def get_dxy_data(year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    return fetch_and_normalize("DX-Y.NYB", start, end)


def get_us10y_data(year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    return fetch_and_normalize("^TNX", start, end)


def get_sp500_data(year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    return fetch_and_normalize("^GSPC", start, end)


def get_vix_data(year, month):
    start = f"{year}-{month:02d}-01"
    end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    return fetch_and_normalize("^VIX", start, end)


# ─── Main Collect ───

def collect_month(year, month, dry=False, incremental=False):
    """Collect all data for one month."""
    print(f"\n{'='*60}")
    print(f"Collecting: {year}-{month:02d} {'(DRY RUN)' if dry else ''} {'(INCREMENTAL)' if incremental else ''}")
    print(f"{'='*60}")

    # Fetch gold with lookback
    gold_df = get_extended_gold_data(year, month, lookback_days=200)
    if gold_df.empty:
        print(f"❌ No gold data for {year}-{month:02d}")
        return None

    # Calculate technical indicators on extended data
    gold_df['ema_31'] = calc_ema(gold_df['Close'], 31)
    gold_df['ema_113'] = calc_ema(gold_df['Close'], 113)
    gold_df['atr_14'] = calc_atr(gold_df, 14)
    gold_df['rsi_14'] = calc_rsi(gold_df['Close'], 14)

    # Filter to target month
    target_start = f"{year}-{month:02d}-01"
    target_end = f"{year+1}-01-01" if month == 12 else f"{year}-{month+1:02d}-01"
    gold_target = gold_df[(gold_df.index >= target_start) & (gold_df.index < target_end)]

    if gold_target.empty:
        print(f"❌ No gold data for target month {year}-{month:02d}")
        return None

    # Check existing data for incremental mode
    existing_dates = set()
    csv_path = os.path.join(DATA_DIR, f"{year}-{month:02d}.csv")
    existing_df = None
    if incremental and os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        existing_dates = set(existing_df['date'].tolist())
        print(f"  📄 Existing CSV has {len(existing_dates)} rows")

    # Fetch external data (FIXED: all normalized to date-only)
    dxy_df = get_dxy_data(year, month)
    us10y_df = get_us10y_data(year, month)
    sp500_df = get_sp500_data(year, month)
    vix_df = get_vix_data(year, month)

    # Status
    for name, df in [("DXY", dxy_df), ("US10Y", us10y_df), ("S&P500", sp500_df), ("VIX", vix_df)]:
        status = f"{len(df)} rows" if not df.empty else "⚠️ EMPTY"
        print(f"  {name}: {status}")

    # Pre-calculate DXY changes
    if not dxy_df.empty:
        dxy_df['dxy_change_pct'] = dxy_df['Close'].pct_change() * 100
        dxy_prev = dxy_df['Close'].shift(1)
        dxy_df['dxy_direction'] = 'neutral'
        dxy_df.loc[dxy_df['Close'] > dxy_prev, 'dxy_direction'] = 'bullish'
        dxy_df.loc[dxy_df['Close'] < dxy_prev, 'dxy_direction'] = 'bearish'

    # Pre-calculate S&P500 changes
    if not sp500_df.empty:
        sp500_df['sp500_change_pct'] = sp500_df['Close'].pct_change() * 100

    # Pre-calculate US10Y changes
    if not us10y_df.empty:
        us10y_df['us10y_change'] = us10y_df['Close'].diff()

    rows = []
    for ts, row in gold_target.iterrows():
        # ts is already date-only from normalize_df_index
        date_str = ts.strftime("%Y-%m-%d") if hasattr(ts, 'strftime') else str(ts)[:10]
        yr, mo, dy = ts.year, ts.month, ts.day

        # Skip existing dates in incremental mode
        if incremental and date_str in existing_dates:
            # Check if row has v2 columns already
            if existing_df is not None:
                ex_row = existing_df[existing_df['date'] == date_str]
                if len(ex_row) > 0:
                    has_v2 = all(c in ex_row.columns and pd.notna(ex_row[c].iloc[0]) and ex_row[c].iloc[0] != '' 
                                 for c in V2_NEW_COLUMNS)
                    if has_v2:
                        continue  # Fully up-to-date, skip

        jd = jd_from_date(yr, mo, dy)
        day_of_week = ts.strftime("%A")

        # ─── A. Price ───
        open_price = round(float(row.get("Open", 0)), 2)
        close = round(float(row.get("Close", 0)), 2)
        high = round(float(row.get("High", 0)), 2)
        low = round(float(row.get("Low", 0)), 2)
        range_val = round(high - low, 2)
        change_pct = round((close - open_price) / open_price * 100, 2) if open_price else 0
        bullish = close > open_price

        ema_31 = round(float(row.get('ema_31', 0)), 2) if pd.notna(row.get('ema_31')) else ""
        ema_113 = round(float(row.get('ema_113', 0)), 2) if pd.notna(row.get('ema_113')) else ""
        ema_relation = "above" if ema_31 and ema_113 and ema_31 > ema_113 else ("below" if ema_31 and ema_113 else "")

        # ─── Volume, ATR, RSI (NEW) ───
        volume = int(row.get("Volume", 0)) if pd.notna(row.get("Volume")) else ""
        atr_14 = round(float(row.get('atr_14', 0)), 2) if pd.notna(row.get('atr_14')) else ""
        rsi_14 = round(float(row.get('rsi_14', 0)), 1) if pd.notna(row.get('rsi_14')) else ""

        # ─── B. Gann/Fib ───
        swing_high, swing_low = high, low
        trend = "UP" if bullish else "DOWN"
        diff = swing_high - swing_low
        fib_levels = {}
        for ratio in FIB_RATIOS:
            price_level = swing_low + (diff * ratio) if trend == "UP" else swing_high - (diff * ratio)
            fib_levels[str(ratio)] = round(price_level, 2)

        key_held, breached, reaction = False, "", ""
        fib_sorted = sorted(fib_levels.items(), key=lambda x: x[1])
        for i in range(len(fib_sorted) - 1):
            low_f, high_f = fib_sorted[i][1], fib_sorted[i + 1][1]
            if low_f <= close <= high_f:
                if abs(close - low_f) < 3:
                    key_held, reaction, breached = True, "bounce", str(fib_sorted[i][0])
                elif abs(close - high_f) < 3:
                    key_held, reaction, breached = True, "bounce", str(fib_sorted[i + 1][0])
                break

        # Gann S/R
        gann = gann_calculate_levels(swing_high)
        gann_ns = gann['nearest_support_price'] if gann['nearest_support_price'] else ""
        gann_nr = gann['nearest_resistance_price'] if gann['nearest_resistance_price'] else ""
        gann_gap = round(float(gann_nr) - float(gann_ns), 2) if gann_ns and gann_nr else ""

        gann_held = False
        gann_breached = ""
        if gann_ns and gann_nr:
            threshold = close * 0.02
            if abs(close - float(gann_ns)) < threshold:
                gann_held = True
                gann_breached = f"support_{gann_ns}"
            elif abs(close - float(gann_nr)) < threshold:
                gann_held = True
                gann_breached = f"resistance_{gann_nr}"

        gann_levels_json = json.dumps({
            'base': gann['base'], 'scale': gann['scale'],
            'supports': [l['price'] for l in gann['all_levels'] if l['direction'] == 'support'],
            'resistances': [l['price'] for l in gann['all_levels'] if l['direction'] == 'resistance'],
        }, ensure_ascii=False)

        # ─── C. Planetary ───
        planet_data = {}
        sun_lon = None
        for name, pid in PLANETS.items():
            lon, speed, _ = sidereal_position(jd, pid)
            if lon is not None:
                sign, deg = sign_and_degree(lon)
                planet_data[f"{name.lower()}_sign"] = sign
                planet_data[f"{name.lower()}_deg"] = deg
                if speed is not None:
                    planet_data[f"{name.lower()}_retro"] = speed < 0
                if name == "Moon":
                    nak = nakshatra(lon)
                    planet_data["moon_nakshatra"] = nak
                    planet_data["moon_nakshatra_lord"] = nakshatra_lord(nak)  # NEW
                if name == "Sun":
                    sun_lon = lon

        # Rahu/Ketu
        rahu_lon, _, _ = sidereal_position(jd, RAHU_NODE)
        if rahu_lon is not None:
            rahu_sign, rahu_deg = sign_and_degree(rahu_lon)
            planet_data["rahu_sign"] = rahu_sign
            planet_data["rahu_deg"] = rahu_deg
            ketu_lon = (rahu_lon + 180) % 360
            ketu_sign, ketu_deg = sign_and_degree(ketu_lon)
            planet_data["ketu_sign"] = ketu_sign
            planet_data["ketu_deg"] = ketu_deg

        # ─── D. Elongations ───
        if sun_lon is not None:
            for pname in ["mercury", "venus", "mars", "jupiter", "saturn"]:
                psign = planet_data.get(f"{pname}_sign", "")
                pdeg = planet_data.get(f"{pname}_deg", 0)
                if psign:
                    plon_full = ZODIAC_SIGNS.index(psign) * 30 + pdeg
                    elong = elongation_from_sun(plon_full, sun_lon)
                    planet_data[f"{pname}_elong_deg"] = elong
                    if pname in ["mercury", "venus"]:
                        planet_data[f"{pname}_elong_dir"] = elongation_direction(plon_full, sun_lon)
                        planet_data[f"{pname}_combust"] = is_combust(elong, pname.capitalize())
                    elif pname == "mars":
                        planet_data[f"{pname}_combust"] = is_combust(elong, pname.capitalize())

        # ─── E. Aspects ───
        aspects = calculate_aspects(jd, include_nodes=True)
        planet_data["aspects_json"] = json.dumps(aspects, ensure_ascii=False)

        # ─── F. Eclipse ───
        eclipse_active, eclipse_type, days_away = check_eclipse(jd)

        # ─── G. Moon Phase ───
        moon_phase, moon_illum = calculate_moon_phase(jd)

        # ─── H. Economic ───
        events = get_economic_events_for_date(yr, mo, dy, day_of_week)
        econ_events = " | ".join([f"{name} ({impact})" for name, impact in events]) if events else ""
        max_impact = "none"
        for _, impact in events:
            if impact == "high":
                max_impact = "high"; break
            elif impact == "medium" and max_impact != "high":
                max_impact = "medium"

        # ─── I. Market Reaction ───
        market_reaction, trend_direction, volatility = calculate_market_reaction(row)

        # ─── J. Hora ───
        sunrise_local = get_sunrise(jd)
        dominant_hour = DAY_LORDS[day_of_week]

        # ─── K. External Data (FIXED: normalized indices) ───
        dxy_close = ""
        dxy_change = ""
        dxy_dir = ""
        if not dxy_df.empty and ts in dxy_df.index:
            dxy_row = dxy_df.loc[ts]
            # Handle potential duplicate indices
            if isinstance(dxy_row, pd.DataFrame):
                dxy_row = dxy_row.iloc[0]
            dxy_close = round(float(dxy_row['Close']), 2)
            if pd.notna(dxy_row.get('dxy_change_pct')):
                dxy_change = round(float(dxy_row['dxy_change_pct']), 2)
            dxy_dir = dxy_row.get('dxy_direction', '')

        us10y_close = ""
        us10y_change = ""
        if not us10y_df.empty and ts in us10y_df.index:
            us10y_row = us10y_df.loc[ts]
            if isinstance(us10y_row, pd.DataFrame):
                us10y_row = us10y_row.iloc[0]
            us10y_close = round(float(us10y_row['Close']), 2)
            if pd.notna(us10y_row.get('us10y_change')):
                us10y_change = round(float(us10y_row['us10y_change']), 2)

        sp500_change = ""
        if not sp500_df.empty and ts in sp500_df.index:
            sp_row = sp500_df.loc[ts]
            if isinstance(sp_row, pd.DataFrame):
                sp_row = sp_row.iloc[0]
            if pd.notna(sp_row.get('sp500_change_pct')):
                sp500_change = round(float(sp_row['sp500_change_pct']), 2)

        vix_close = ""
        if not vix_df.empty and ts in vix_df.index:
            vx_row = vix_df.loc[ts]
            if isinstance(vx_row, pd.DataFrame):
                vx_row = vx_row.iloc[0]
            vix_close = round(float(vx_row['Close']), 2)

        # ─── Build row ───
        full_row = {
            "date": date_str, "day_of_week": day_of_week,
            "gold_open": open_price, "gold_close": close, "gold_high": high, "gold_low": low,
            "gold_range": range_val, "gold_change_pct": change_pct, "gold_bullish": bullish,
            "gold_ema_31": ema_31, "gold_ema_113": ema_113, "gold_ema_relation": ema_relation,
            "gann_swing_high": swing_high, "gann_swing_low": swing_low, "gann_trend": trend,
            "fib_levels_json": json.dumps(fib_levels),
            "gann_key_level_held": key_held, "gann_breached_level": breached, "gann_reaction": reaction,
            "gann_base": gann['base'], "gann_scale": gann['scale'],
            "gann_nearest_support": gann_ns, "gann_nearest_resistance": gann_nr,
            "gann_gap": gann_gap, "gann_held": gann_held, "gann_breached": gann_breached,
            "gann_levels_json": gann_levels_json,
            "sun_sign": planet_data.get("sun_sign", ""), "sun_deg": planet_data.get("sun_deg", 0),
            "moon_sign": planet_data.get("moon_sign", ""), "moon_deg": planet_data.get("moon_deg", 0),
            "moon_nakshatra": planet_data.get("moon_nakshatra", ""),
            "moon_nakshatra_lord": planet_data.get("moon_nakshatra_lord", ""),  # NEW
            "mercury_sign": planet_data.get("mercury_sign", ""), "mercury_deg": planet_data.get("mercury_deg", 0),
            "mercury_retro": planet_data.get("mercury_retro", False),
            "venus_sign": planet_data.get("venus_sign", ""), "venus_deg": planet_data.get("venus_deg", 0),
            "venus_retro": planet_data.get("venus_retro", False),
            "mars_sign": planet_data.get("mars_sign", ""), "mars_deg": planet_data.get("mars_deg", 0),
            "mars_retro": planet_data.get("mars_retro", False),
            "jupiter_sign": planet_data.get("jupiter_sign", ""), "jupiter_deg": planet_data.get("jupiter_deg", 0),
            "jupiter_retro": planet_data.get("jupiter_retro", False),
            "saturn_sign": planet_data.get("saturn_sign", ""), "saturn_deg": planet_data.get("saturn_deg", 0),
            "saturn_retro": planet_data.get("saturn_retro", False),
            "rahu_sign": planet_data.get("rahu_sign", ""), "rahu_deg": planet_data.get("rahu_deg", 0),
            "ketu_sign": planet_data.get("ketu_sign", ""), "ketu_deg": planet_data.get("ketu_deg", 0),
            "mercury_elong_deg": planet_data.get("mercury_elong_deg", 0),
            "mercury_elong_dir": planet_data.get("mercury_elong_dir", ""),
            "mercury_combust": planet_data.get("mercury_combust", False),
            "venus_elong_deg": planet_data.get("venus_elong_deg", 0),
            "venus_elong_dir": planet_data.get("venus_elong_dir", ""),
            "venus_combust": planet_data.get("venus_combust", False),
            "mars_elong_deg": planet_data.get("mars_elong_deg", 0),
            "mars_combust": planet_data.get("mars_combust", False),
            "jupiter_elong_deg": planet_data.get("jupiter_elong_deg", 0),
            "saturn_elong_deg": planet_data.get("saturn_elong_deg", 0),
            "aspects_json": planet_data.get("aspects_json", "[]"),
            "eclipse_active": eclipse_active,
            "eclipse_type": eclipse_type if eclipse_type else "",
            "eclipse_days_away": days_away,
            "moon_phase": moon_phase, "moon_illumination_pct": moon_illum,
            "economic_events": econ_events, "economic_impact": max_impact,
            "market_reaction": market_reaction, "trend_direction": trend_direction, "volatility": volatility,
            "dominant_planet_hour": dominant_hour, "sunrise_local": sunrise_local,
            "dxy_close": dxy_close, "dxy_change_pct": dxy_change, "dxy_direction": dxy_dir,
            "us10y_close": us10y_close, "us10y_change": us10y_change,
            # ─── NEW v2 ───
            "sp500_change_pct": sp500_change, "vix_close": vix_close,
            "gold_volume": volume, "gold_atr_14": atr_14, "gold_rsi_14": rsi_14,
        }
        rows.append(full_row)

    # Build DataFrame
    df_new = pd.DataFrame(rows, columns=ALL_COLUMNS)
    df_new = df_new.fillna("")

    if dry:
        print(f"\n  Preview ({len(df_new)} rows):")
        preview_cols = ["date", "gold_close", "moon_nakshatra_lord", "us10y_close",
                        "sp500_change_pct", "vix_close", "gold_atr_14", "gold_rsi_14"]
        available = [c for c in preview_cols if c in df_new.columns]
        print(df_new[available].to_string(index=False))
        return df_new

    # Merge with existing if incremental
    if incremental and existing_df is not None:
        # Remove existing dates from new, then concat
        existing_dates_set = set(existing_df['date'].tolist())
        df_new_filtered = df_new[~df_new['date'].isin(existing_dates_set)]
        if len(df_new_filtered) == 0:
            print(f"  ✅ Already up-to-date, nothing to add")
            return existing_df

        # Ensure same columns before concat
        for col in ALL_COLUMNS:
            if col not in existing_df.columns:
                existing_df[col] = ""
        existing_df = existing_df[ALL_COLUMNS]

        df_final = pd.concat([existing_df, df_new_filtered], ignore_index=True)
        df_final = df_final.sort_values('date').reset_index(drop=True)
        print(f"  📊 Merged: {len(existing_df)} existing + {len(df_new_filtered)} new = {len(df_final)} total")
    else:
        df_final = df_new

    # Save
    filename = f"{year}-{month:02d}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    df_final.to_csv(filepath, index=False)
    print(f"  💾 Saved: {filepath} ({len(df_final)} rows)")

    # Quick validation
    us10y_filled = sum(1 for v in df_final['us10y_close'] if v != '' and v != 0)
    print(f"  ✅ Validation: DXY={sum(1 for v in df_final['dxy_close'] if v != '' and v != 0)}/{len(df_final)}, "
          f"US10Y={us10y_filled}/{len(df_final)}, "
          f"SP500={sum(1 for v in df_final['sp500_change_pct'] if v != '' and v != 0)}/{len(df_final)}, "
          f"VIX={sum(1 for v in df_final['vix_close'] if v != '' and v != 0)}/{len(df_final)}")

    return df_final


# ─── CLI ───

def backfill_all(dry=False):
    """Re-process all 120 months."""
    print("🔄 BACKFILL ALL MODE")
    success, fail = 0, 0
    for year in range(2016, 2027):
        start_month = 6 if year == 2016 else 1
        end_month = 6 if year == 2026 else 13
        for month in range(start_month, end_month):
            if year == 2026 and month > 5:
                break
            try:
                result = collect_month(year, month, dry=dry)
                if result is not None:
                    success += 1
                else:
                    fail += 1
            except Exception as e:
                print(f"❌ {year}-{month:02d}: {e}")
                fail += 1
    print(f"\n{'='*60}")
    print(f"Backfill complete: {success} success, {fail} failed")
    return success, fail


def fix_us10y_all():
    """Fix only US10Y column across all existing CSVs."""
    print("🔧 FIX US10Y MODE — patching all CSVs with corrected US10Y data")
    fixed = 0
    for year in range(2016, 2027):
        start_month = 6 if year == 2016 else 1
        end_month = 6 if year == 2026 else 13
        for month in range(start_month, end_month):
            if year == 2026 and month > 5:
                break
            csv_path = os.path.join(DATA_DIR, f"{year}-{month:02d}.csv")
            if not os.path.exists(csv_path):
                continue

            df = pd.read_csv(csv_path)
            us10y_df = get_us10y_data(year, month)

            if us10y_df.empty:
                print(f"  {year}-{month:02d}: No US10Y data available, skipping")
                continue

            us10y_df['us10y_change'] = us10y_df['Close'].diff()
            patched = 0

            for idx, row in df.iterrows():
                date_str = row['date']
                try:
                    ts = pd.to_datetime(date_str)
                    if ts in us10y_df.index:
                        us10y_row = us10y_df.loc[ts]
                        if isinstance(us10y_row, pd.DataFrame):
                            us10y_row = us10y_row.iloc[0]
                        df.at[idx, 'us10y_close'] = round(float(us10y_row['Close']), 2)
                        if pd.notna(us10y_row.get('us10y_change')):
                            df.at[idx, 'us10y_change'] = round(float(us10y_row['us10y_change']), 2)
                        patched += 1
                except Exception as e:
                    pass

            if patched > 0:
                df.to_csv(csv_path, index=False)
                print(f"  ✅ {year}-{month:02d}: Patched {patched}/{len(df)} rows")
                fixed += patched
            else:
                print(f"  ⚠️  {year}-{month:02d}: 0 rows patched (date mismatch?)")

    print(f"\n🔧 US10Y fix complete: {fixed} total rows patched")
    return fixed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 collect_v2.py YYYY-MM              # Full month collect")
        print("  python3 collect_v2.py YYYY-MM --inc        # Incremental (fill gaps)")
        print("  python3 collect_v2.py YYYY-MM --dry        # Dry run preview")
        print("  python3 collect_v2.py --backfill-all       # Re-process all 120 months")
        print("  python3 collect_v2.py --fix-us10y          # Only fix US10Y across all CSVs")
        sys.exit(1)

    arg = sys.argv[1]
    dry = "--dry" in sys.argv
    inc = "--inc" in sys.argv

    if arg == "--backfill-all":
        backfill_all(dry=dry)
    elif arg == "--fix-us10y":
        fix_us10y_all()
    else:
        try:
            year, month = map(int, arg.split("-"))
            collect_month(year, month, dry=dry, incremental=inc)
        except ValueError:
            print("Error: Use format YYYY-MM", file=sys.stderr)
            sys.exit(1)
