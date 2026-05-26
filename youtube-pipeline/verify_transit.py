#!/usr/bin/env python3
"""
Swiss Ephemeris Transit Verifier
Usage: python3 verify_transit.py <planet> <target_sign> <year> [month]

Examples:
  python3 verify_transit.py JUPITER Cancer 2026
  python3 verify_transit.py SATURN Aries 2025
  python3 verify_transit.py MARS Leo 2026 6

Output: Exact ingress date, time, and degree (sidereal Lahiri).
MUST be run before publishing ANY calendar-based content.
"""

import swisseph as swe
from datetime import datetime, timedelta
import pytz
import sys

swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

PLANETS = {
    'SUN': swe.SUN, 'MOON': swe.MOON, 'MERCURY': swe.MERCURY,
    'VENUS': swe.VENUS, 'MARS': swe.MARS, 'JUPITER': swe.JUPITER,
    'SATURN': swe.SATURN, 'RAHU': swe.MEAN_NODE, 'KETU': None,
}

SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

SIGNS_VI = {
    'Aries': 'Bạch Dương', 'Taurus': 'Kim Ngưu', 'Gemini': 'Song Tử',
    'Cancer': 'Cự Giải', 'Leo': 'Sư Tử', 'Virgo': 'Xử Nữ',
    'Libra': 'Thiên Bình', 'Scorpio': 'Bọ Cạp', 'Sagittarius': 'Nhân Mã',
    'Capricorn': 'Ma Kết', 'Aquarius': 'Bảo Bình', 'Pisces': 'Song Ngư'
}

tz = pytz.timezone('Asia/Saigon')

def verify_transit(planet_name, target_sign, year, month_start=1):
    """Find exact ingress of planet into target_sign in given year."""
    
    planet_id = PLANETS.get(planet_name.upper())
    if planet_id is None:
        print(f"❌ Unknown planet: {planet_name}")
        print(f"   Valid: {', '.join(PLANETS.keys())}")
        sys.exit(1)
    
    target_sign = target_sign.capitalize()
    if target_sign not in SIGNS:
        print(f"❌ Unknown sign: {target_sign}")
        print(f"   Valid: {', '.join(SIGNS)}")
        sys.exit(1)
    
    target_sign_num = SIGNS.index(target_sign)
    
    # Special case: Ketu is opposite Rahu
    if planet_name.upper() == 'KETU':
        return verify_ketu(target_sign, year, month_start)
    
    print(f"🔍 Verifying: {planet_name.capitalize()} → {target_sign} ({SIGNS_VI[target_sign]}) in {year}")
    print(f"   Method: Swiss Ephemeris (sidereal Lahiri, GMT+7)")
    print()
    
    # Scan hourly
    start_date = datetime(year, month_start, 1, tzinfo=tz)
    end_date = datetime(year + 1, 1, 1, tzinfo=tz) if month_start > 1 else datetime(year, 12, 31, 23, 59, tzinfo=tz)
    
    prev_sign = None
    found = False
    
    current = start_date
    while current <= end_date:
        jd = swe.julday(current.year, current.month, current.day, 
                        current.hour + current.minute/60.0)
        lon, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        sign_num = int(lon[0] / 30)
        sign_deg = lon[0] % 30
        
        if prev_sign is not None and prev_sign != sign_num:
            if sign_num == target_sign_num:
                print(f"✅ VERIFIED: {planet_name.capitalize()} enters {target_sign}")
                print(f"   Date: {current.strftime('%Y-%m-%d %H:%M GMT+7')}")
                print(f"   Position: {target_sign} {sign_deg:.4f}°")
                print(f"   Exact longitude: {lon[0]:.4f}°")
                print(f"   Previous sign: {SIGNS[prev_sign]}")
                
                # Also check next day positions for context
                for d in [1, 2, 3, 7]:
                    next_dt = current + timedelta(days=d)
                    jd2 = swe.julday(next_dt.year, next_dt.month, next_dt.day,
                                     next_dt.hour + next_dt.minute/60.0)
                    lon2, _ = swe.calc_ut(jd2, planet_id, swe.FLG_SIDEREAL)
                    sd2 = lon2[0] % 30
                    print(f"   +{d}d ({next_dt.strftime('%m/%d')}): {target_sign} {sd2:.2f}°")
                
                # Retrograde check
                jd_retro = swe.julday(current.year, current.month, current.day,
                                      current.hour + current.minute/60.0)
                _, ret = swe.calc_ut(jd_retro, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                speed = ret  # degrees/day
                if speed < 0:
                    print(f"   ⚠️  Planet is RETROGRADE (speed: {speed:.4f}°/day)")
                else:
                    print(f"   ▶ Direct motion (speed: {speed:.4f}°/day)")
                
                found = True
                return
            else:
                # Ingressed into wrong sign
                print(f"⚠️  Planet entered {SIGNS[sign_num]}, NOT {target_sign}")
                print(f"   Date: {current.strftime('%Y-%m-%d %H:%M GMT+7')}")
                print(f"   This means {planet_name.capitalize()} will enter {target_sign} at a different time.")
                print(f"   Scanning further...")
        
        prev_sign = sign_num
        current += timedelta(hours=1)
    
    if not found:
        print(f"❌ NOT FOUND: {planet_name.capitalize()} does NOT enter {target_sign} in {year}")
        print(f"   (or the ingress happens outside the scanned range)")
        
        # Show current position at start of year
        jd_start = swe.julday(year, 1, 1, 0)
        lon_start, _ = swe.calc_ut(jd_start, planet_id, swe.FLG_SIDEREAL)
        sn_start = int(lon_start[0] / 30)
        print(f"   Position at {year}-01-01: {SIGNS[sn_start]} {lon_start[0] % 30:.2f}°")
        
        jd_end = swe.julday(year, 12, 31, 0)
        lon_end, _ = swe.calc_ut(jd_end, planet_id, swe.FLG_SIDEREAL)
        sn_end = int(lon_end[0] / 30)
        print(f"   Position at {year}-12-31: {SIGNS[sn_end]} {lon_end[0] % 30:.2f}°")
        sys.exit(1)

def verify_ketu(target_sign, year, month_start=1):
    """Ketu is always opposite Rahu (180° away)."""
    rahu_id = swe.MEAN_NODE
    target_sign_num = SIGNS.index(target_sign)
    rahu_target = SIGNS[(target_sign_num + 6) % 12]  # opposite sign
    
    print(f"🔍 Ketu → {target_sign} = Rahu → {rahu_target} (opposite)")
    print(f"   Method: Swiss Ephemeris (sidereal Lahiri, GMT+7)")
    print()
    
    start_date = datetime(year, month_start, 1, tzinfo=tz)
    end_date = datetime(year + 1, 1, 1, tzinfo=tz)
    
    prev_sign = None
    current = start_date
    while current <= end_date:
        jd = swe.julday(current.year, current.month, current.day,
                        current.hour + current.minute/60.0)
        lon, _ = swe.calc_ut(jd, rahu_id, swe.FLG_SIDEREAL)
        sign_num = int(lon[0] / 30)
        
        if prev_sign is not None and prev_sign != sign_num:
            if sign_num == SIGNS.index(rahu_target):
                ketu_sign = SIGNS[(sign_num + 6) % 12]
                print(f"✅ VERIFIED: Ketu enters {ketu_sign}")
                print(f"   Date: {current.strftime('%Y-%m-%d %H:%M GMT+7')}")
                return
        
        prev_sign = sign_num
        current += timedelta(hours=1)
    
    print(f"❌ NOT FOUND")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    
    planet = sys.argv[1]
    sign = sys.argv[2]
    year = int(sys.argv[3])
    month = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    verify_transit(planet, sign, year, month)
