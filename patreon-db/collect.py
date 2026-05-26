#!/usr/bin/env python3
"""
patreon-db/collect.py
FULLY AUTO — no manual input needed.
Collects daily data for one month:
- Price (yfinance)
- Gann/Fib levels
- Planetary positions (Swiss Ephemeris, sidereal/Vedic, Lahiri)
- Elongation, combust, aspects, eclipse
- Moon phase (8-phase system)
- DXY (Dollar Index)
- EMA 31 / EMA 113 on gold
- Real yield proxy (US 10Y Treasury)
- Economic events (hardcoded major US releases schedule)
- Market reaction (computed from OHLC)
- Planetary Hora (sunrise + Chaldean order)

Usage:
    python3 collect.py 2025-05        # collect May 2025
    python3 collect.py 2025-05 --dry  # preview only
"""

import sys
import os
import json
import math
import calendar
import pandas as pd
import yfinance as yf
import swisseph as swe

# ─── Swiss Ephemeris config ───
swe.set_ephe_path(None)
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ─── Config ───
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Location for sunrise (Saigon timezone)
GEO_LON = 106.7
GEO_LAT = 10.78
GEO_ALT = 0
TIMEZONE_OFFSET = 7  # GMT+7

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}

# Rahu (North Node / Mean Node) and Ketu (South Node = opposite)
RAHU_NODE = swe.MEAN_NODE
# Ketu = Rahu + 180° (always exact opposite in Vedic astrology)

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

FIB_RATIOS = [0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874]

# ─── Gann Square of 9 ───
GANN_CRITICAL_ANGLES = [45, 90, 135, 180, 225, 270, 315, 360]

def gann_extract_base(price):
    """Extract 3-digit base number from price.
    E.g., 2453.50 -> 245, 1900 -> 190"""
    price_str = str(int(price))
    if len(price_str) >= 3:
        return int(price_str[:3])
    return int(price)

def gann_scale_factor(price):
    """Determine scale factor to convert base back to price.
    4-digit price (1000-9999) -> scale 10
    3-digit price (100-999) -> scale 1"""
    return 10 if price >= 1000 else 1.0

def gann_calculate_levels(price):
    """Calculate Gann Square of 9 support/resistance levels.
    Formula: Target = (sqrt(Base) +/- (Angle/180))^2 * scale
    Returns dict with 'nearest_support', 'nearest_resistance', 'all_levels'."""
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
    
    # Find nearest support below and resistance above
    below = [l for l in all_levels if l['price'] <= price]
    above = [l for l in all_levels if l['price'] > price]
    
    nearest_support = max(below, key=lambda x: x['price']) if below else None
    nearest_resistance = min(above, key=lambda x: x['price']) if above else None
    
    return {
        'base': base,
        'scale': scale,
        'all_levels': all_levels,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'nearest_support_price': nearest_support['price'] if nearest_support else None,
        'nearest_resistance_price': nearest_resistance['price'] if nearest_resistance else None,
    }

def gann_check_held(close, nearest_support_price, nearest_resistance_price, threshold_pct=0.02):
    """Check if price is holding near a Gann level.
    Uses relative threshold (% of close price, not gap).
    Default 2% = ~$60 at $3000 gold.
    Returns (held: bool, nearest_level: float, distance: float, direction: str)."""
    if nearest_support_price is None or nearest_resistance_price is None:
        return False, None, None, None
    
    threshold = close * threshold_pct  # e.g., 2% of close price
    
    dist_to_support = abs(close - nearest_support_price)
    dist_to_resistance = abs(close - nearest_resistance_price)
    
    if dist_to_support < threshold:
        return True, nearest_support_price, dist_to_support, 'support'
    elif dist_to_resistance < threshold:
        return True, nearest_resistance_price, dist_to_resistance, 'resistance'
    else:
        return False, None, None, None

COMBUST_ORBS = {
    "Mars": 8, "Saturn": 8, "Jupiter": 8,
    "Venus": 4, "Mercury": 2
}

# Chaldean order for Hora calculation
CHALDEAN_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Day lords (planetary rulers of days)
DAY_LORDS = {
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
    "Sunday": "Sun",
}

# ─── Economic Events Schedule ───
ECONOMIC_EVENTS_DB = {
    "nfp": {
        "name": "Non-Farm Payrolls (NFP)",
        "schedule": "first_friday",
        "time_et": "08:30",
        "impact": "high",
    },
    "unemployment": {
        "name": "Unemployment Rate",
        "schedule": "first_friday",
        "time_et": "08:30",
        "impact": "high",
    },
    "avg_hourly_earnings": {
        "name": "Average Hourly Earnings",
        "schedule": "first_friday",
        "time_et": "08:30",
        "impact": "medium",
    },
    "cpi": {
        "name": "CPI (Consumer Price Index)",
        "schedule": "cpi_window",
        "time_et": "08:30",
        "impact": "high",
    },
    "pce": {
        "name": "PCE Price Index",
        "schedule": "pce_window",
        "time_et": "08:30",
        "impact": "high",
    },
    "fomc": {
        "name": "FOMC Rate Decision",
        "schedule": "fomc_dates",
        "time_et": "14:00",
        "impact": "high",
    },
    "fomc_minutes": {
        "name": "FOMC Minutes",
        "schedule": "fomc_minutes",
        "time_et": "14:00",
        "impact": "medium",
    },
    "gdp": {
        "name": "GDP (Advance Estimate)",
        "schedule": "gdp_windows",
        "time_et": "08:30",
        "impact": "high",
    },
    "retail_sales": {
        "name": "Retail Sales",
        "schedule": "retail_window",
        "time_et": "08:30",
        "impact": "medium",
    },
    "ism_mfg": {
        "name": "ISM Manufacturing PMI",
        "schedule": "first_business_day",
        "time_et": "10:00",
        "impact": "medium",
    },
    "ism_services": {
        "name": "ISM Services PMI",
        "schedule": "third_business_day",
        "time_et": "10:00",
        "impact": "medium",
    },
    "jobless_claims": {
        "name": "Initial Jobless Claims",
        "schedule": "weekly_thursday",
        "time_et": "08:30",
        "impact": "low",
    },
    "adp": {
        "name": "ADP Non-Farm Employment",
        "schedule": "mid_month",
        "time_et": "08:15",
        "impact": "medium",
    },
    "consumer_confidence": {
        "name": "Consumer Confidence",
        "schedule": "last_tuesday",
        "time_et": "10:00",
        "impact": "medium",
    },
    "michigan_sentiment": {
        "name": "University of Michigan Consumer Sentiment",
        "schedule": "michigan_window",
        "time_et": "10:00",
        "impact": "medium",
    },
    "trade_balance": {
        "name": "Trade Balance",
        "schedule": "monthly",
        "time_et": "08:30",
        "impact": "low",
    },
    "durable_goods": {
        "name": "Durable Goods Orders",
        "schedule": "durable_window",
        "time_et": "08:30",
        "impact": "medium",
    },
    "housing_starts": {
        "name": "Housing Starts",
        "schedule": "housing_window",
        "time_et": "08:30",
        "impact": "medium",
    },
    "existing_home_sales": {
        "name": "Existing Home Sales",
        "schedule": "housing_window",
        "time_et": "10:00",
        "impact": "low",
    },
    "new_home_sales": {
        "name": "New Home Sales",
        "schedule": "durable_window",
        "time_et": "10:00",
        "impact": "medium",
    },
}


def get_first_friday(year, month):
    """Get the first Friday of a month."""
    cal = calendar.Calendar(calendar.SUNDAY)
    for week in cal.monthdatescalendar(year, month):
        for day in week:
            if day.month == month and day.weekday() == 4:
                return day
    return None


def get_first_business_day(year, month):
    """Get the first business day (Mon-Fri) of a month."""
    for day in range(1, 8):
        import datetime
        d = datetime.date(year, month, day)
        if d.weekday() < 5:
            return d
    return None


def get_third_business_day(year, month):
    """Get the third business day of a month."""
    import datetime
    count = 0
    for day in range(1, 15):
        d = datetime.date(year, month, day)
        if d.weekday() < 5:
            count += 1
            if count == 3:
                return d
    return None


def get_last_tuesday(year, month):
    """Get the last Tuesday of a month."""
    import datetime
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, 0, -1):
        d = datetime.date(year, month, day)
        if d.weekday() == 1:
            return d
    return None


def get_cpi_date(year, month):
    """CPI typically released 10th-15th."""
    import datetime
    for day in range(10, 16):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_pce_date(year, month):
    """PCE typically released 25th-30th or 1st-5th of next month."""
    import datetime
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, last_day - 6, -1):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_retail_sales_date(year, month):
    """Retail Sales typically around 13th-17th."""
    import datetime
    for day in range(13, 18):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_gdp_dates(year):
    """GDP advance estimates."""
    import datetime
    return [
        datetime.date(year, 4, 25),
        datetime.date(year, 7, 30),
        datetime.date(year, 10, 29),
        datetime.date(year + 1, 1, 28),
    ]


FOMC_DATES_BY_YEAR = {
    2022: [
        __import__('datetime').date(2022, 2, 2),
        __import__('datetime').date(2022, 3, 16),
        __import__('datetime').date(2022, 5, 4),
        __import__('datetime').date(2022, 6, 15),
        __import__('datetime').date(2022, 7, 27),
        __import__('datetime').date(2022, 9, 21),
        __import__('datetime').date(2022, 11, 2),
        __import__('datetime').date(2022, 12, 14),
    ],
    2023: [
        __import__('datetime').date(2023, 2, 1),
        __import__('datetime').date(2023, 3, 22),
        __import__('datetime').date(2023, 5, 3),
        __import__('datetime').date(2023, 6, 14),
        __import__('datetime').date(2023, 7, 26),
        __import__('datetime').date(2023, 9, 20),
        __import__('datetime').date(2023, 11, 1),
        __import__('datetime').date(2023, 12, 13),
    ],
    2024: [
        __import__('datetime').date(2024, 1, 31),
        __import__('datetime').date(2024, 3, 20),
        __import__('datetime').date(2024, 6, 12),
        __import__('datetime').date(2024, 7, 31),
        __import__('datetime').date(2024, 9, 18),
        __import__('datetime').date(2024, 11, 7),
        __import__('datetime').date(2024, 12, 18),
    ],
    2025: [
        __import__('datetime').date(2025, 1, 29),
        __import__('datetime').date(2025, 3, 19),
        __import__('datetime').date(2025, 5, 7),
        __import__('datetime').date(2025, 6, 18),
        __import__('datetime').date(2025, 7, 30),
        __import__('datetime').date(2025, 9, 17),
        __import__('datetime').date(2025, 10, 29),
        __import__('datetime').date(2025, 12, 17),
    ],
}


def get_fomc_dates(year):
    return FOMC_DATES_BY_YEAR.get(year, [])


def get_durable_goods_date(year, month):
    import datetime
    for day in range(23, 28):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_housing_starts_date(year, month):
    import datetime
    for day in range(16, 21):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_michigan_sentiment_date(year, month):
    import datetime
    for day in range(14, 18):
        try:
            d = datetime.date(year, month, day)
            if d.weekday() < 5:
                return d
        except ValueError:
            pass
    return None


def get_adp_date(year, month):
    import datetime
    first_fri = get_first_friday(year, month)
    if first_fri:
        return first_fri - datetime.timedelta(days=2)
    return None


def get_economic_events_for_date(year, month, day, day_of_week):
    import datetime
    d = datetime.date(year, month, day)
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

    durable_date = get_durable_goods_date(year, month)
    if durable_date and d == durable_date:
        events.append(("Durable Goods Orders", "medium"))

    housing_date = get_housing_starts_date(year, month)
    if housing_date and d == housing_date:
        events.append(("Housing Starts", "medium"))

    michigan_date = get_michigan_sentiment_date(year, month)
    if michigan_date and d == michigan_date:
        events.append(("Michigan Consumer Sentiment", "medium"))

    adp_date = get_adp_date(year, month)
    if adp_date and d == adp_date:
        events.append(("ADP Non-Farm Employment", "medium"))

    if day_of_week == "Thursday":
        events.append(("Initial Jobless Claims", "low"))

    fomc_dates = get_fomc_dates(year)
    if d in fomc_dates:
        events.append(("FOMC Rate Decision", "high"))

    gdp_dates = get_gdp_dates(year)
    if d in gdp_dates:
        events.append(("GDP Advance Estimate", "high"))

    return events


# ─── Swiss Ephemeris helpers ───

def sidereal_position(jd_ut1, planet_id):
    flag = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, ierr = swe.calc_ut(jd_ut1, planet_id, flag)
    if ierr < 0:
        return None, None, None
    return result[0], result[3], result[2]


def jd_from_date(year, month, day):
    return swe.julday(year, month, day, 0.0)


def sign_and_degree(sidereal_lon):
    sign_idx = int(sidereal_lon // 30)
    deg_in_sign = sidereal_lon % 30
    return ZODIAC_SIGNS[sign_idx], round(deg_in_sign, 2)


def nakshatra(sidereal_lon):
    nak_idx = int(sidereal_lon // (360 / 27))
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha",
        "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
        "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    return nakshatras[nak_idx % 27]


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


def calculate_aspects(jd, include_nodes=False):
    positions = {}
    for name, pid in PLANETS.items():
        lon, speed, _ = sidereal_position(jd, pid)
        if lon is not None:
            positions[name] = lon
    
    # Add Rahu/Ketu if requested
    if include_nodes:
        rahu_lon, _, _ = sidereal_position(jd, RAHU_NODE)
        if rahu_lon is not None:
            positions["Rahu"] = rahu_lon
            ketu_lon = (rahu_lon + 180) % 360
            positions["Ketu"] = ketu_lon

    aspects = []
    aspect_defs = [
        ("Conjunction", 0, 5),
        ("Sextile", 60, 4),
        ("Square", 90, 4),
        ("Trine", 120, 4),
        ("Opposition", 180, 5),
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
                        "planet1": p1,
                        "planet2": p2,
                        "aspect": aspect_name,
                        "orb_deg": round(abs(diff - angle), 2)
                    })
    return aspects


def check_eclipse(jd):
    moon_lon, _, _ = sidereal_position(jd, swe.MOON)
    sun_lon, _, _ = sidereal_position(jd, swe.SUN)

    if moon_lon is None or sun_lon is None:
        return False, None, 0

    moon_phase_deg = (moon_lon - sun_lon) % 360
    new_moon_diff = min(moon_phase_deg, 360 - moon_phase_deg)
    full_moon_diff = min(abs(moon_phase_deg - 180), 360 - abs(moon_phase_deg - 180))

    if new_moon_diff < 15:
        return True, "Solar", int(new_moon_diff)
    elif full_moon_diff < 15:
        return True, "Lunar", int(full_moon_diff)

    return False, None, 0


# ─── Moon Phase (8-phase system) ───

def calculate_moon_phase(jd):
    """
    Calculate moon phase from Swiss Ephemeris data.
    Returns phase name (8-phase) and illumination %.
    
    Phase angle 0° = New Moon
    Phase angle 90° = First Quarter
    Phase angle 180° = Full Moon
    Phase angle 270° = Last Quarter
    """
    sun_lon, _, _ = sidereal_position(jd, swe.SUN)
    moon_lon, _, _ = sidereal_position(jd, swe.MOON)
    
    if sun_lon is None or moon_lon is None:
        return "Unknown", 0
    
    # Phase angle: angle of Moon from Sun (0-360)
    phase_angle = (moon_lon - sun_lon) % 360
    
    # Illumination: fraction of moon illuminated (0-100%)
    illumination = round((1 - math.cos(math.radians(phase_angle))) / 2 * 100, 1)
    
    # 8-phase system
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


# ─── EMA calculation ───

def calc_ema(series, period):
    """Calculate EMA for a pandas Series."""
    return series.ewm(span=period, adjust=False).mean()


# ─── Hora ───

def get_sunrise(jd):
    flag = swe.CALC_RISE | swe.BIT_DISC_CENTER
    geopos = [GEO_LON, GEO_LAT, GEO_ALT]
    res_code, tret = swe.rise_trans(jd, swe.SUN, flag, geopos)
    if res_code >= 0 and len(tret) > 0:
        sunrise_jd = tret[0]
        hours_ut = (sunrise_jd - jd) * 24
        hours_local = (hours_ut + TIMEZONE_OFFSET) % 24
        return round(hours_local, 2)
    return 5.5


def calculate_planetary_hour(jd, date_str):
    sunrise_hours = get_sunrise(jd)
    day_of_week = date_str.strftime("%A")
    day_lord = DAY_LORDS[day_of_week]
    dominant = day_lord
    trading_hours = {
        "dominant_hour": dominant,
        "sunrise_local": round(sunrise_hours, 2),
    }
    return dominant, trading_hours


# ─── Market Reaction ───

def calculate_market_reaction(row):
    open_price = float(row.get("Open", 0))
    close = float(row.get("Close", 0))
    high = float(row.get("High", 0))
    low = float(row.get("Low", 0))

    if open_price == 0:
        return "unknown", "range", "low"

    range_pct = (high - low) / open_price * 100
    body = abs(close - open_price)
    body_pct = body / open_price * 100
    upper_wick = high - max(open_price, close)
    lower_wick = min(open_price, close) - low
    total_wicks = upper_wick + lower_wick
    wick_ratio = total_wicks / (high - low) if (high - low) > 0 else 0

    if range_pct > 2.0:
        volatility = "high"
    elif range_pct > 1.0:
        volatility = "medium"
    else:
        volatility = "low"

    if close > open_price:
        trend = "bullish"
    elif close < open_price:
        trend = "bearish"
    else:
        trend = "neutral"

    if body_pct > 1.5 and wick_ratio < 0.3:
        reaction = "strong_trend"
    elif body_pct > 1.0 and wick_ratio < 0.4:
        reaction = "moderate_trend"
    elif wick_ratio > 0.6:
        reaction = "reversal_signal"
    elif range_pct < 0.5:
        reaction = "consolidation"
    elif body_pct > 0.5:
        reaction = "mild_trend"
    else:
        reaction = "choppy"

    return reaction, trend, volatility


# ─── Data Fetching ───

def get_extended_gold_data(year, month, lookback_days=200):
    """
    Fetch gold data with lookback for EMA calculation.
    Returns (extended_df, target_mask) where target_mask selects the target month.
    """
    import datetime
    # Start lookback_days before the target month
    start_dt = datetime.date(year, month, 1) - datetime.timedelta(days=lookback_days)
    if month == 12:
        end_dt = datetime.date(year + 1, 1, 1)
    else:
        end_dt = datetime.date(year, month + 1, 1)
    
    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    
    ticker = yf.Ticker("GC=F")
    try:
        df = ticker.history(start=start_str, end=end_str, interval="1d")
        return df
    except Exception as e:
        print(f"Warning: Could not fetch gold data: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_dxy_data(year, month):
    """Fetch DXY (DX-Y.NYB) for the month."""
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    
    ticker = yf.Ticker("DX-Y.NYB")
    try:
        df = ticker.history(start=start, end=end, interval="1d")
        return df
    except Exception as e:
        print(f"Warning: Could not fetch DXY data: {e}", file=sys.stderr)
        return pd.DataFrame()


def get_us10y_data(year, month):
    """Fetch US 10Y Treasury yield (^TNX) for the month."""
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year+1}-01-01"
    else:
        end = f"{year}-{month+1:02d}-01"
    
    ticker = yf.Ticker("^TNX")
    try:
        df = ticker.history(start=start, end=end, interval="1d")
        return df
    except Exception as e:
        print(f"Warning: Could not fetch US10Y data: {e}", file=sys.stderr)
        return pd.DataFrame()


def collect_month(year, month, dry=False):
    """Collect all data for one month — FULLY AUTO."""
    # Fetch extended gold data (with lookback for EMA)
    gold_df = get_extended_gold_data(year, month, lookback_days=200)
    
    if gold_df.empty:
        print(f"Error: No gold data found for {year}-{month:02d}", file=sys.stderr)
        return None
    
    # Calculate EMAs on full extended dataset BEFORE filtering
    gold_df['ema_31'] = calc_ema(gold_df['Close'], 31)
    gold_df['ema_113'] = calc_ema(gold_df['Close'], 113)
    
    # Filter to target month only (now includes EMA columns)
    target_start = f"{year}-{month:02d}-01"
    if month == 12:
        target_end = f"{year+1}-01-01"
    else:
        target_end = f"{year}-{month+1:02d}-01"
    gold_df_target = gold_df[(gold_df.index >= target_start) & (gold_df.index < target_end)]
    
    if gold_df_target.empty:
        print(f"Error: No gold data for target month {year}-{month:02d}", file=sys.stderr)
        return None
    
    # Fetch DXY
    dxy_df = get_dxy_data(year, month)
    
    # Fetch US 10Y
    us10y_df = get_us10y_data(year, month)
    
    # Calculate DXY values
    if not dxy_df.empty:
        dxy_df['dxy_change_pct'] = dxy_df['Close'].pct_change() * 100
        dxy_prev = dxy_df['Close'].shift(1)
        dxy_df['dxy_direction'] = 'neutral'
        dxy_df.loc[dxy_df['Close'] > dxy_prev, 'dxy_direction'] = 'bullish'
        dxy_df.loc[dxy_df['Close'] < dxy_prev, 'dxy_direction'] = 'bearish'
    
    # Calculate US10Y changes
    if not us10y_df.empty:
        us10y_df['us10y_change'] = us10y_df['Close'].diff()
    
    rows = []
    for date_str, row in gold_df_target.iterrows():
        yr = date_str.year
        mo = date_str.month
        dy = date_str.day
        jd = jd_from_date(yr, mo, dy)
        day_of_week = date_str.strftime("%A")
        
        # ─── A. Price Data ───
        open_price = round(float(row.get("Open", 0)), 2)
        close = round(float(row.get("Close", 0)), 2)
        high = round(float(row.get("High", 0)), 2)
        low = round(float(row.get("Low", 0)), 2)
        range_val = round(high - low, 2)
        change_pct = round((close - open_price) / open_price * 100, 2) if open_price else 0
        bullish = close > open_price
        
        # EMA values
        ema_31 = round(float(row.get('ema_31', 0)), 2) if pd.notna(row.get('ema_31')) else ""
        ema_113 = round(float(row.get('ema_113', 0)), 2) if pd.notna(row.get('ema_113')) else ""
        # EMA relationship
        if ema_31 and ema_113:
            ema_relation = "above" if ema_31 > ema_113 else "below"
        else:
            ema_relation = ""
        
        # ─── B. Gann/Fib ───
        # Fib levels (daily swing-based, for volatility analysis)
        swing_high = high
        swing_low = low
        trend = "UP" if bullish else "DOWN"
        
        fib_levels = {}
        diff = swing_high - swing_low
        for ratio in FIB_RATIOS:
            if trend == "UP":
                price_level = swing_low + (diff * ratio)
            else:
                price_level = swing_high - (diff * ratio)
            fib_levels[str(ratio)] = round(price_level, 2)
        
        key_held = False
        breached = ""
        reaction = ""
        fib_sorted = sorted(fib_levels.items(), key=lambda x: x[1])
        for i in range(len(fib_sorted) - 1):
            low_f = fib_sorted[i][1]
            high_f = fib_sorted[i + 1][1]
            if low_f <= close <= high_f:
                dist_low = abs(close - low_f)
                dist_high = abs(close - high_f)
                if dist_low < 3:
                    key_held = True
                    reaction = "bounce"
                    breached = str(fib_sorted[i][0])
                elif dist_high < 3:
                    key_held = True
                    reaction = "bounce"
                    breached = str(fib_sorted[i + 1][0])
                break
        
        # ─── B2. Gann Square of 9 (structural S/R levels) ───
        # Calculate Gann from SWING HIGH (structural anchor), not close
        gann = gann_calculate_levels(swing_high)
        gann_nearest_support = gann['nearest_support_price'] if gann['nearest_support_price'] else ""
        gann_nearest_resistance = gann['nearest_resistance_price'] if gann['nearest_resistance_price'] else ""
        gann_gap = ""
        if gann_nearest_support and gann_nearest_resistance:
            gann_gap = round(float(gann_nearest_resistance) - float(gann_nearest_support), 2)
        
        # Gann held/breached: is close within 2% of price from nearest Gann level?
        gann_held = False
        gann_breached = ""
        if gann_nearest_support and gann_nearest_resistance:
            threshold = close * 0.02  # 2% of close price (~$60 at $3000)
            dist_sup = abs(close - float(gann_nearest_support))
            dist_res = abs(close - float(gann_nearest_resistance))
            if dist_sup < threshold:
                gann_held = True
                gann_breached = f"support_{gann_nearest_support}"
            elif dist_res < threshold:
                gann_held = True
                gann_breached = f"resistance_{gann_nearest_resistance}"
        
        gann_levels_json = json.dumps({
            'base': gann['base'],
            'scale': gann['scale'],
            'supports': [l['price'] for l in gann['all_levels'] if l['direction'] == 'support'],
            'resistances': [l['price'] for l in gann['all_levels'] if l['direction'] == 'resistance'],
        }, ensure_ascii=False)
        
        # ─── C. Planetary Positions ───
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
                    planet_data["moon_nakshatra"] = nakshatra(lon)
                if name == "Sun":
                    sun_lon = lon
        
        # Rahu (North Node / Mean Node)
        rahu_lon, rahu_speed, _ = sidereal_position(jd, RAHU_NODE)
        if rahu_lon is not None:
            rahu_sign, rahu_deg = sign_and_degree(rahu_lon)
            planet_data["rahu_sign"] = rahu_sign
            planet_data["rahu_deg"] = rahu_deg
            # Ketu = opposite point (always retrograde)
            ketu_lon = (rahu_lon + 180) % 360
            ketu_sign, ketu_deg = sign_and_degree(ketu_lon)
            planet_data["ketu_sign"] = ketu_sign
            planet_data["ketu_deg"] = ketu_deg
        
        # ─── D. Elongations ───
        if sun_lon is not None:
            for pname in ["mercury", "venus", "mars", "jupiter", "saturn"]:
                plon = planet_data.get(f"{pname}_deg", 0)
                psign = planet_data.get(f"{pname}_sign", "")
                if psign:
                    sign_idx = ZODIAC_SIGNS.index(psign)
                    plon_full = sign_idx * 30 + plon
                    elong = elongation_from_sun(plon_full, sun_lon)
                    planet_data[f"{pname}_elong_deg"] = elong
                    if pname in ["mercury", "venus"]:
                        planet_data[f"{pname}_elong_dir"] = elongation_direction(plon_full, sun_lon)
                        planet_data[f"{pname}_combust"] = is_combust(elong, pname.capitalize())
                    elif pname == "mars":
                        planet_data[f"{pname}_combust"] = is_combust(elong, pname.capitalize())
            
            # Rahu/Ketu position only (no elongation/combust — shadow planets)
        
        # ─── E. Aspects ───
        aspects = calculate_aspects(jd, include_nodes=True)
        planet_data["aspects_json"] = json.dumps(aspects, ensure_ascii=False)
        
        # ─── F. Eclipse ───
        eclipse_active, eclipse_type, days_away = check_eclipse(jd)
        planet_data["eclipse_active"] = eclipse_active
        planet_data["eclipse_type"] = eclipse_type if eclipse_type else ""
        planet_data["eclipse_days_away"] = days_away
        
        # ─── G. Moon Phase (NEW) ───
        moon_phase, moon_illumination = calculate_moon_phase(jd)
        planet_data["moon_phase"] = moon_phase
        planet_data["moon_illumination_pct"] = moon_illumination
        
        # ─── H. Economic Events ───
        events = get_economic_events_for_date(yr, mo, dy, day_of_week)
        econ_events = " | ".join([f"{name} ({impact})" for name, impact in events]) if events else ""
        max_impact = "none"
        for _, impact in events:
            if impact == "high":
                max_impact = "high"
                break
            elif impact == "medium" and max_impact != "high":
                max_impact = "medium"
        
        # ─── I. Market Reaction ───
        market_reaction, trend_direction, volatility = calculate_market_reaction(row)
        
        # ─── J. Planetary Hora ───
        dominant_hour, hora_info = calculate_planetary_hour(jd, date_str)
        
        # ─── K. DXY (NEW) ───
        dxy_close = ""
        dxy_change = ""
        dxy_dir = ""
        if not dxy_df.empty and date_str in dxy_df.index:
            dxy_row = dxy_df.loc[date_str]
            dxy_close = round(float(dxy_row['Close']), 2)
            if pd.notna(dxy_row.get('dxy_change_pct')):
                dxy_change = round(float(dxy_row['dxy_change_pct']), 2)
            dxy_dir = dxy_row.get('dxy_direction', '')
        
        # ─── L. Real Yield Proxy — US 10Y (NEW) ───
        us10y_close = ""
        us10y_change = ""
        if not us10y_df.empty and date_str in us10y_df.index:
            us10y_row = us10y_df.loc[date_str]
            us10y_close = round(float(us10y_row['Close']), 2)
            if pd.notna(us10y_row.get('us10y_change')):
                us10y_change = round(float(us10y_row['us10y_change']), 2)
        
        # ─── Combine all ───
        full_row = {
            # A. Date & Price
            "date": date_str.strftime("%Y-%m-%d"),
            "day_of_week": day_of_week,
            "gold_open": open_price,
            "gold_close": close,
            "gold_high": high,
            "gold_low": low,
            "gold_range": range_val,
            "gold_change_pct": change_pct,
            "gold_bullish": bullish,
            # A+. EMA
            "gold_ema_31": ema_31,
            "gold_ema_113": ema_113,
            "gold_ema_relation": ema_relation,
            # B. Gann/Fib
            "gann_swing_high": swing_high,
            "gann_swing_low": swing_low,
            "gann_trend": trend,
            "fib_levels_json": json.dumps(fib_levels),
            "gann_key_level_held": key_held,
            "gann_breached_level": breached,
            "gann_reaction": reaction,
            # B2. Gann Square of 9
            "gann_base": gann['base'],
            "gann_scale": gann['scale'],
            "gann_nearest_support": gann_nearest_support,
            "gann_nearest_resistance": gann_nearest_resistance,
            "gann_gap": gann_gap,
            "gann_held": gann_held,
            "gann_breached": gann_breached,
            "gann_levels_json": gann_levels_json,
            # C. Planetary
            "sun_sign": planet_data.get("sun_sign", ""),
            "sun_deg": planet_data.get("sun_deg", 0),
            "moon_sign": planet_data.get("moon_sign", ""),
            "moon_deg": planet_data.get("moon_deg", 0),
            "moon_nakshatra": planet_data.get("moon_nakshatra", ""),
            "mercury_sign": planet_data.get("mercury_sign", ""),
            "mercury_deg": planet_data.get("mercury_deg", 0),
            "mercury_retro": planet_data.get("mercury_retro", False),
            "venus_sign": planet_data.get("venus_sign", ""),
            "venus_deg": planet_data.get("venus_deg", 0),
            "venus_retro": planet_data.get("venus_retro", False),
            "mars_sign": planet_data.get("mars_sign", ""),
            "mars_deg": planet_data.get("mars_deg", 0),
            "mars_retro": planet_data.get("mars_retro", False),
            "jupiter_sign": planet_data.get("jupiter_sign", ""),
            "jupiter_deg": planet_data.get("jupiter_deg", 0),
            "jupiter_retro": planet_data.get("jupiter_retro", False),
            "saturn_sign": planet_data.get("saturn_sign", ""),
            "saturn_deg": planet_data.get("saturn_deg", 0),
            "saturn_retro": planet_data.get("saturn_retro", False),
            # C+. Rahu & Ketu (Shadow Planets)
            "rahu_sign": planet_data.get("rahu_sign", ""),
            "rahu_deg": planet_data.get("rahu_deg", 0),
            "ketu_sign": planet_data.get("ketu_sign", ""),
            "ketu_deg": planet_data.get("ketu_deg", 0),
            # D. Elongations
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
            # E. Aspects
            "aspects_json": planet_data.get("aspects_json", "[]"),
            # F. Eclipse
            "eclipse_active": eclipse_active,
            "eclipse_type": eclipse_type if eclipse_type else "",
            "eclipse_days_away": days_away,
            # G. Moon Phase (NEW)
            "moon_phase": planet_data.get("moon_phase", ""),
            "moon_illumination_pct": planet_data.get("moon_illumination_pct", 0),
            # H. Economic
            "economic_events": econ_events,
            "economic_impact": max_impact,
            # I. Market Reaction
            "market_reaction": market_reaction,
            "trend_direction": trend_direction,
            "volatility": volatility,
            # J. Hora
            "dominant_planet_hour": dominant_hour,
            "sunrise_local": hora_info.get("sunrise_local", 0),
            # K. DXY (NEW)
            "dxy_close": dxy_close,
            "dxy_change_pct": dxy_change,
            "dxy_direction": dxy_dir,
            # L. US 10Y Real Yield Proxy (NEW)
            "us10y_close": us10y_close,
            "us10y_change": us10y_change,
        }
        
        rows.append(full_row)
    
    # Create DataFrame with explicit column order
    columns = [
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
        "moon_sign", "moon_deg", "moon_nakshatra",
        "mercury_sign", "mercury_deg", "mercury_retro",
        "venus_sign", "venus_deg", "venus_retro",
        "mars_sign", "mars_deg", "mars_retro",
        "jupiter_sign", "jupiter_deg", "jupiter_retro",
        "saturn_sign", "saturn_deg", "saturn_retro",
        # C+. Rahu & Ketu (Shadow Planets / Lunar Nodes — always retrograde)
        "rahu_sign", "rahu_deg",
        "ketu_sign", "ketu_deg",
        "mercury_elong_deg", "mercury_elong_dir", "mercury_combust",
        "venus_elong_deg", "venus_elong_dir", "venus_combust",
        "mars_elong_deg", "mars_combust",
        "jupiter_elong_deg",
        "saturn_elong_deg",
        "aspects_json",
        "eclipse_active", "eclipse_type", "eclipse_days_away",
        "moon_phase", "moon_illumination_pct",
        "economic_events", "economic_impact",
        "market_reaction", "trend_direction", "volatility",
        "dominant_planet_hour", "sunrise_local",
        "dxy_close", "dxy_change_pct", "dxy_direction",
        "us10y_close", "us10y_change",
    ]
    
    df = pd.DataFrame(rows, columns=columns)
    df = df.astype(object)
    df = df.fillna("")
    
    if dry:
        print(f"\n{'='*100}")
        print(f"DRY RUN: {year}-{month:02d}")
        print(f"Rows: {len(df)}")
        print(f"{'='*100}")
        print(df[["date", "gold_close", "gold_ema_31", "gold_ema_113", "gold_ema_relation",
                   "moon_phase", "moon_illumination_pct", "dxy_close", "dxy_direction",
                   "us10y_close", "economic_events", "economic_impact",
                   "market_reaction", "trend_direction", "volatility",
                   "dominant_planet_hour", "mercury_combust", "venus_combust",
                   "rahu_sign", "rahu_deg", "ketu_sign", "ketu_deg"]].to_string(index=False))
        return df
    
    # Save
    filename = f"{year}-{month:02d}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"Saved: {filepath} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 collect.py YYYY-MM [--dry]")
        sys.exit(1)
    
    arg = sys.argv[1]
    dry = "--dry" in sys.argv
    
    try:
        year, month = map(int, arg.split("-"))
    except ValueError:
        print("Error: Use format YYYY-MM", file=sys.stderr)
        sys.exit(1)
    
    collect_month(year, month, dry=dry)
