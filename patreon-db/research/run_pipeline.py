#!/usr/bin/env python3
"""
run_pipeline.py — Astro-Quant Pipeline for Gold (XAUUSD)

Flow:
  1. Pull LIVE data from all engines (astro, hora, gann, ta, macro, price)
  2. Run through Astro-Quant Framework scoring
  3. Find matching historical patterns similar to today
  4. Calculate SL/TP from Gann + Fib levels
  5. Output structured JSON for AI analysis

Usage:
  python3 run_pipeline.py              # today
  python3 run_pipeline.py 2026-05-22  # specific date (uses historical CSV)
"""

import sys, os, json, math
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np

# Add parent & workspace root to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # workspace root

from astro_quant_scorer import AstroQuantScorer

TZ = pytz.timezone("Asia/Ho_Chi_Minh")
DATA_DIR = Path(os.path.dirname(__file__)).parent / "data"
HCM_LAT, HCM_LON = 10.85, 106.75

# ─── CONSTANTS ───
NAKSHATRA_QUALITIES = {
    'Ashwini': 'Nhanh, đột phá, năng lượng mới',
    'Bharani': 'Chịu đựng, kiềm chế, tích lũy',
    'Krittika': 'Sắc bén, cắt giảm, thanh lọc',
    'Rohini': 'Tăng trưởng, vật chất, hưởng thụ',
    'Mrigashira': 'Tìm kiếm, do dự, phân nhánh',
    'Ardra': 'Hủy diệt, biến động, đổi mới',
    'Punarvasu': 'Phục hồi, quay lại, tái sinh',
    'Pushya': 'Nuôi dưỡng, ổn định, bảo thủ',
    'Ashlesha': 'Thao túng, đầu cơ, bẫy giá',
    'Magha': 'Quyền lực, lãnh đạo, đỉnh cao',
    'Purva Phalguni': 'Sáng tạo, hưởng thụ, nghỉ ngơi',
    'Uttara Phalguni': 'Cam kết, hợp đồng, ổn định',
    'Hasta': 'Khéo léo, chính xác, thủ công',
    'Chitra': 'Xây dựng, kiến trúc, cơ hội',
    'Swati': 'Độc lập, tự do, phân tán',
    'Vishakha': 'Mục tiêu kép, quyết đoán, đột phá',
    'Anuradha': 'Kiên nhẫn, tích lũy ngầm, chiến lược',
    'Jyeshtha': 'Cạnh tranh, quyền lực ngầm, rủi ro',
    'Mula': 'Đào sâu, phá hủy gốc rễ, tái cấu trúc',
    'Purva Ashadha': 'Chiến thắng, mở rộng, tuyên bố',
    'Uttara Ashadha': 'Chiến thắng cuối cùng, bền vững',
    'Shravana': 'Lắng nghe, học hỏi, kết nối',
    'Dhanishta': 'Giàu có, âm nhạc, nhịp điệu',
    'Shatabhisha': 'Trị liệu, ẩn giấu, bí ẩn',
    'Purva Bhadrapada': 'Tâm linh, hy sinh, biến đổi',
    'Uttara Bhadrapada': 'Từ bỏ, giải thoát, kết thúc',
    'Revati': 'Hoàn thành, khép lại, chuyển giao',
}

# ─── 1. PULL DATA FROM ENGINES ───

def pull_live_astro(now_dt):
    """Pull planetary data from Vedic API + hora engine."""
    try:
        import requests
        payload = {
            "date": now_dt.strftime("%Y-%m-%d"),
            "time": now_dt.strftime("%H:%M"),
            "timezone": "Asia/Ho_Chi_Minh",
            "latitude": HCM_LAT,
            "longitude": HCM_LON
        }
        r = requests.post("https://vedicvn-api.onrender.com/api/chart", json=payload, timeout=30)
        vedic = r.json()
        planets = {p['planet']: p for p in vedic.get('planets', [])}
    except Exception as e:
        print(f"⚠️ Vedic API failed: {e}", file=sys.stderr)
        planets = {}
    
    # Hora (only used in live mode)
    try:
        from engines.hora_engine import VedicHoraEngine
        hora_engine = VedicHoraEngine(lat=HCM_LAT, lon=HCM_LON)
        hora_now = hora_engine.calculate_hora(now_dt)
        hora_full = hora_engine.calculate_full_day_horas(now_dt)
    except ImportError:
        hora_now, hora_full = {}, {}
    
    return planets, hora_now, hora_full


def pull_live_price():
    """Pull gold price from yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker("GC=F")
        df = ticker.history(period="2d")
        if len(df) >= 1:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else latest
            return {
                'open': round(latest['Open'], 1),
                'high': round(latest['High'], 1),
                'low': round(latest['Low'], 1),
                'close': round(latest['Close'], 1),
                'range': round(latest['High'] - latest['Low'], 1),
                'change_pct': round((latest['Close'] - latest['Open']) / latest['Open'] * 100, 2),
                'bullish': latest['Close'] > latest['Open'],
                'prev_close': round(prev['Close'], 1),
            }
    except Exception as e:
        print(f"⚠️ yfinance failed: {e}", file=sys.stderr)
    return None


def pull_live_macro():
    """Pull DXY + US10Y from yfinance."""
    macro = {'dxy_close': None, 'dxy_change': None, 'dxy_dir': None, 'us10y_close': None, 'us10y_change': None}
    try:
        import yfinance as yf
        # DXY
        dxy = yf.Ticker("DX-Y.NYB")
        dxy_df = dxy.history(period="2d")
        if len(dxy_df) >= 1:
            macro['dxy_close'] = round(dxy_df.iloc[-1]['Close'], 2)
            macro['dxy_change'] = round((dxy_df.iloc[-1]['Close'] - dxy_df.iloc[-1]['Open']) / dxy_df.iloc[-1]['Open'] * 100, 2)
            macro['dxy_dir'] = 'bullish' if macro['dxy_change'] > 0 else 'bearish'
        # US10Y
        us10y = yf.Ticker("^TNX")
        us10y_df = us10y.history(period="2d")
        if len(us10y_df) >= 1:
            macro['us10y_close'] = round(us10y_df.iloc[-1]['Close'], 2)
            if len(us10y_df) >= 2:
                macro['us10y_change'] = round(us10y_df.iloc[-1]['Close'] - us10y_df.iloc[-2]['Close'], 2)
    except Exception as e:
        print(f"⚠️ Macro fetch failed: {e}", file=sys.stderr)
    return macro


# ─── 2. GANN + FIB CALCULATIONS ───

def calc_gann_fib(price_data):
    """Calculate Gann Square of 9 and Fib levels from price."""
    from engines.gann_engine import GannEngine
    from engines.ta_engine import TAEngine
    
    close = price_data['close']
    high = price_data['high']
    low = price_data['low']
    
    # Gann Square of 9
    base = GannEngine.extract_base_number(close)
    scale = 10 if close >= 1000 else 1
    gann_levels = GannEngine.calculate_gann_levels(base, scale)
    
    # Find nearest S/R
    supports = sorted([s['price'] for s in gann_levels['supports'] if s['price'] < close], reverse=True)
    resistances = sorted([r['price'] for r in gann_levels['resistances'] if r['price'] > close])
    
    nearest_support = supports[0] if supports else None
    nearest_resistance = resistances[0] if resistances else None
    
    # Check if close is near a Gann level (within 2%)
    gann_held = False
    held_level = None
    if nearest_support and abs(close - nearest_support) / close * 100 < 2:
        gann_held = True
        held_level = nearest_support
    elif nearest_resistance and abs(close - nearest_resistance) / close * 100 < 2:
        gann_held = True
        held_level = nearest_resistance
    
    # Fib retracement (daily swing)
    trend = 'UP' if price_data['bullish'] else 'DOWN'
    fib_levels = TAEngine.calculate_fib_retracement(high, low, trend)
    fib_analysis = TAEngine.analyze_price_fibo(close, fib_levels)
    
    return {
        'gann_base': base,
        'gann_scale': scale,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'gann_held': gann_held,
        'held_at_level': held_level,
        'gann_gap': round(nearest_resistance - nearest_support, 1) if nearest_support and nearest_resistance else None,
        'fib_levels': fib_levels,
        'fib_below': fib_analysis.get('below'),
        'fib_above': fib_analysis.get('above'),
        'swing_high': high,
        'swing_low': low,
    }


# ─── 3. HISTORICAL PATTERN MATCH ───

def find_similar_patterns(current_data, full_df, top_n=5):
    """Find historically similar days based on astro pattern overlap."""
    nakshatra = current_data.get('moon_nakshatra')
    moon_sign = current_data.get('moon_sign')
    hora = current_data.get('hora')
    moon_phase = current_data.get('moon_phase')
    
    # Current aspects set
    current_aspects = set()
    for asp in current_data.get('aspects', []):
        current_aspects.add(f"{asp['planet1']}-{asp['aspect']}-{asp['planet2']}")
    
    # 1. Same Nakshatra + Moon Sign
    matches = full_df[
        (full_df['moon_nakshatra'] == nakshatra) &
        (full_df['moon_sign'] == moon_sign)
    ].copy()
    
    scored = []
    for _, m in matches.iterrows():
        try:
            m_aspects = set()
            for a in json.loads(str(m['aspects_json'])):
                m_aspects.add(f"{a['planet1']}-{a['aspect']}-{a['planet2']}")
            overlap = len(current_aspects & m_aspects)
            scored.append({
                'date': m['date'],
                'close': float(m['gold_close']),
                'change': float(m['gold_change_pct']),
                'bullish': bool(m['gold_bullish']),
                'range': float(m['gold_range']),
                'reaction': str(m['market_reaction']),
                'vol': str(m['volatility']),
                'aspect_overlap': overlap,
                'total_aspects': len(m_aspects),
            })
        except:
            continue
    
    scored.sort(key=lambda x: (x['aspect_overlap'], -abs(x['change'])), reverse=True)
    return scored[:top_n] if scored else []


# ─── 4. MAIN PIPELINE ───

def run_pipeline(date_str=None, use_live=True):
    """Run the full pipeline and output structured data packet."""
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    
    if date_str:
        target_dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    else:
        target_dt = datetime.now(tz)
    
    # ── Pull data ──
    if use_live:
        planets, hora_now, hora_full = pull_live_astro(target_dt)
        price = pull_live_price()
        macro = pull_live_macro()
    else:
        # Fallback to CSV
        planets, hora_now, hora_full = {}, {}, {}
        price, macro = None, {}
    
    # ── If no live data, use CSV ──
    if not price:
        csv_path = DATA_DIR / f"{target_dt.year}-{target_dt.month:02d}.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            row = df[df['date'] == target_dt.strftime("%Y-%m-%d")]
            if not row.empty:
                r = row.iloc[0]
                price = {
                    'open': float(r['gold_open']), 'high': float(r['gold_high']),
                    'low': float(r['gold_low']), 'close': float(r['gold_close']),
                    'range': float(r['gold_range']), 'change_pct': float(r['gold_change_pct']),
                    'bullish': bool(r['gold_bullish']),
                }
                hora_now = {'hora': str(r['dominant_planet_hour']), 'astrological_day': ''}
                macro = {
                    'dxy_close': float(r['dxy_close']) if not pd.isna(r.get('dxy_close')) else None,
                    'dxy_change': float(r['dxy_change_pct']) if not pd.isna(r.get('dxy_change_pct')) else None,
                    'dxy_dir': str(r['dxy_direction']),
                }
    
    if not price:
        return {"error": "No price data available"}
    
    # ── Gann & Fib ──
    gann_fib = calc_gann_fib(price)
    
    # ── Build astro packet from CSV if no live ──
    csv_row = None
    csv_path = DATA_DIR / f"{target_dt.year}-{target_dt.month:02d}.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        row_match = df[df['date'] == target_dt.strftime("%Y-%m-%d")]
        if not row_match.empty:
            csv_row = row_match.iloc[0]
    
    # ── Extract aspects ──
    aspects = []
    if csv_row is not None:
        try:
            aspects = json.loads(str(csv_row['aspects_json']))
        except:
            pass
    
    # ── Astro data from CSV row ──
    astro_data = {}
    if csv_row is not None:
        astro_data = {
            'sun_sign': str(csv_row['sun_sign']), 'sun_deg': float(csv_row['sun_deg']),
            'moon_sign': str(csv_row['moon_sign']), 'moon_deg': float(csv_row['moon_deg']),
            'moon_nakshatra': str(csv_row['moon_nakshatra']),
            'moon_phase': str(csv_row['moon_phase']),
            'moon_illumination': float(csv_row['moon_illumination_pct']) if not pd.isna(csv_row.get('moon_illumination_pct')) else 0,
            'hora': str(csv_row['dominant_planet_hour']),
            'mercury_sign': str(csv_row['mercury_sign']), 'mercury_deg': float(csv_row['mercury_deg']),
            'mercury_retro': bool(csv_row['mercury_retro']),
            'mercury_elong_deg': float(csv_row['mercury_elong_deg']) if not pd.isna(csv_row.get('mercury_elong_deg')) else None,
            'mercury_elong_dir': str(csv_row['mercury_elong_dir']) if not pd.isna(csv_row.get('mercury_elong_dir')) else None,
            'mercury_combust': bool(csv_row['mercury_combust']),
            'venus_sign': str(csv_row['venus_sign']), 'venus_deg': float(csv_row['venus_deg']),
            'venus_retro': bool(csv_row['venus_retro']),
            'venus_elong_deg': float(csv_row['venus_elong_deg']) if not pd.isna(csv_row.get('venus_elong_deg')) else None,
            'venus_elong_dir': str(csv_row['venus_elong_dir']) if not pd.isna(csv_row.get('venus_elong_dir')) else None,
            'venus_combust': bool(csv_row['venus_combust']),
            'mars_sign': str(csv_row['mars_sign']), 'mars_deg': float(csv_row['mars_deg']),
            'mars_retro': bool(csv_row['mars_retro']),
            'mars_combust': bool(csv_row['mars_combust']) if not pd.isna(csv_row.get('mars_combust')) else False,
            'jupiter_sign': str(csv_row['jupiter_sign']), 'jupiter_deg': float(csv_row['jupiter_deg']),
            'jupiter_retro': bool(csv_row['jupiter_retro']),
            'saturn_sign': str(csv_row['saturn_sign']), 'saturn_deg': float(csv_row['saturn_deg']),
            'saturn_retro': bool(csv_row['saturn_retro']),
            'rahu_sign': str(csv_row['rahu_sign']), 'rahu_deg': float(csv_row['rahu_deg']),
            'ketu_sign': str(csv_row['ketu_sign']), 'ketu_deg': float(csv_row['ketu_deg']),
            'aspects': aspects,
            'eclipse_active': bool(csv_row['eclipse_active']) if not pd.isna(csv_row.get('eclipse_active')) else False,
            'eclipse_days_away': int(csv_row['eclipse_days_away']) if not pd.isna(csv_row.get('eclipse_days_away')) else 0,
        }
    
    # ── Run Astro-Quant Scorer ──
    scorer_row = {
        'gold_range': price['range'],
        'volatility': csv_row['volatility'] if csv_row is not None else 'medium',
        'moon_nakshatra': astro_data.get('moon_nakshatra'),
        'moon_sign': astro_data.get('moon_sign'),
        'mercury_retro': astro_data.get('mercury_retro', False),
        'venus_retro': astro_data.get('venus_retro', False),
        'mars_retro': astro_data.get('mars_retro', False),
        'jupiter_retro': astro_data.get('jupiter_retro', False),
        'saturn_retro': astro_data.get('saturn_retro', False),
        'mercury_combust': astro_data.get('mercury_combust', False),
        'venus_combust': astro_data.get('venus_combust', False),
        'mars_combust': astro_data.get('mars_combust', False),
        'dominant_planet_hour': astro_data.get('hora'),
        'moon_phase': astro_data.get('moon_phase'),
        'aspects_json': json.dumps(aspects) if aspects else '[]',
        'gann_key_level_held': gann_fib['gann_held'],
        'gann_held': gann_fib['gann_held'],
        'gold_ema_relation': csv_row['gold_ema_relation'] if csv_row is not None else 'above',
        'dxy_direction': macro.get('dxy_dir', ''),
        'us10y_change': macro.get('us10y_change', 0) or 0,
        'economic_impact': csv_row['economic_impact'] if csv_row is not None else '',
    }
    
    score_result = AstroQuantScorer.score(scorer_row)
    
    # ── Historical similar patterns ──
    # Load full dataset
    full_df = pd.concat([pd.read_csv(f) for f in sorted(DATA_DIR.glob("*.csv"))], ignore_index=True)
    similar = find_similar_patterns(astro_data, full_df)
    
    # ── Build SL/TP ──
    close = price['close']
    sl_tp = {}
    
    if gann_fib['nearest_support'] and gann_fib['nearest_resistance']:
        support = gann_fib['nearest_support']
        resistance = gann_fib['nearest_resistance']
        
        # LONG setup
        sl_tp['long'] = {
            'entry': round(close, 1),
            'sl': round(support - (resistance - support) * 0.15, 1),
            'tp1': round(close + (resistance - close) * 0.5, 1),
            'tp2': round(resistance, 1),
            'risk': round(close - (support - (resistance - support) * 0.15), 1),
            'reward_tp1': round((resistance - close) * 0.5, 1),
            'reward_tp2': round(resistance - close, 1),
            'rr_tp1': round(((resistance - close) * 0.5) / (close - (support - (resistance - support) * 0.15)), 1),
            'rr_tp2': round((resistance - close) / (close - (support - (resistance - support) * 0.15)), 1),
        }
        
        # SHORT setup
        sl_tp['short'] = {
            'entry': round(close, 1),
            'sl': round(resistance + (resistance - support) * 0.15, 1),
            'tp1': round(close - (close - support) * 0.5, 1),
            'tp2': round(support, 1),
            'risk': round((resistance + (resistance - support) * 0.15) - close, 1),
            'reward_tp1': round((close - support) * 0.5, 1),
            'reward_tp2': round(close - support, 1),
        }
    
    # ── Compile output packet ──
    packet = {
        'meta': {
            'date': target_dt.strftime("%Y-%m-%d"),
            'day_of_week': target_dt.strftime("%A"),
            'generated_at': datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
            'data_source': 'live' if use_live else 'csv',
        },
        'price': price,
        'macro': macro,
        'astro': astro_data,
        'gann_fib': gann_fib,
        'sl_tp': sl_tp,
        'framework_score': score_result,
        'similar_history': similar,
        # For AI analysis
        'signals_active': {
            'nakshatra': astro_data.get('moon_nakshatra'),
            'nakshatra_quality': NAKSHATRA_QUALITIES.get(astro_data.get('moon_nakshatra', ''), ''),
            'moon_sign': astro_data.get('moon_sign'),
            'moon_phase': astro_data.get('moon_phase'),
            'hora': astro_data.get('hora'),
            'aspects': aspects,
            'retro_planets': [
                p for p in ['mercury', 'venus', 'mars', 'jupiter', 'saturn']
                if astro_data.get(f'{p}_retro', False)
            ],
            'combust_planets': [
                p for p in ['mercury', 'venus', 'mars']
                if astro_data.get(f'{p}_combust', False)
            ],
            'eclipse': astro_data.get('eclipse_active', False),
            'dxy_direction': macro.get('dxy_dir'),
            'gann_held': gann_fib['gann_held'],
            'ema_relation': csv_row['gold_ema_relation'] if csv_row is not None else 'N/A',
        }
    }
    
    return packet


# ─── MAIN ───
if __name__ == "__main__":
    date_arg = None
    for a in sys.argv[1:]:
        if not a.startswith('--') and len(a) == 10:
            date_arg = a
    
    packet = run_pipeline(date_str=date_arg, use_live=False)  # Use CSV for reliability
    
    if 'error' in packet:
        print(json.dumps(packet, indent=2))
        sys.exit(1)
    
    # Output structured data packet for AI analysis
    print(json.dumps(packet, indent=2, ensure_ascii=False, default=str))
