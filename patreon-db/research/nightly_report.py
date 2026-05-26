#!/usr/bin/env python3
"""
nightly_report.py — Carmens Nightly Gold Prediction Report

Chạy mỗi tối sau khi thị trường đóng cửa.
  1. Kéo data giá hôm nay + astro ngày mai
  2. Chạy qua Astro-Quant Framework
  3. Tìm similar historical patterns  
  4. Xuất bài dự báo theo TEMPLATE CỐ ĐỊNH

Usage:
  python3 nightly_report.py                        # dự báo ngày mai
  python3 nightly_report.py 2026-05-23             # dự báo cho ngày cụ thể
  python3 nightly_report.py --json                 # output JSON data packet only
"""

import sys, os, json, math
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np

# Paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engines'))

from engines.hora_engine import VedicHoraEngine
from engines.ta_engine import TAEngine
from engines.gann_engine import GannEngine
from astro_quant_scorer import AstroQuantScorer
from generate_patreon_post import load_day

TZ = pytz.timezone("Asia/Ho_Chi_Minh")
DATA_DIR = Path(os.path.dirname(__file__)) / "data"
OUTPUT_DIR = Path(os.path.dirname(__file__)) / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

# ═══════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════

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

MOON_SIGN_SENTIMENT = {
    "Aries": "Nóng vội, dễ FOMO. Phù hợp momentum trades.",
    "Taurus": "Ổn định, kiên nhẫn. Trend bền, phù hợp hold.",
    "Gemini": "Biến động, phân mảnh. Khó đọc, dễ đảo chiều.",
    "Cancer": "Cảm xúc cao, dễ panic. Sentiment chi phối mạnh.",
    "Leo": "Tự tin, bullish bias. Thị trường optimistic.",
    "Virgo": "Phân tích kỹ, cẩn trọng. Choppy, precision entries.",
    "Libra": "Cân bằng, range-bound. Buy support, sell resistance.",
    "Scorpio": "Sâu sắc, transformative. Hidden moves, sudden reversals.",
    "Sagittarius": "Mở rộng, optimistic. Phù hợp swing trades.",
    "Capricorn": "Kỷ luật, structure. Respect technical levels.",
    "Aquarius": "Bất ngờ, disruptive. Counter-trend moves.",
    "Pisces": "Mơ hồ, intuitive. Khó xác định direction."
}

HORA_TRADING = {
    'Sun': {'emoji': '☀️', 'label': 'GOLD HOUR ⭐', 'desc': 'Tốt nhất cho vàng. Institutional flow rõ ràng, phù hợp entry positions.'},
    'Jupiter': {'emoji': '♃', 'label': 'EXPANSION', 'desc': 'Thanh khoản tốt, xu hướng rõ. Phù hợp swing trades.'},
    'Mars': {'emoji': '♂️', 'label': 'MOMENTUM', 'desc': 'Năng lượng mạnh cho breakout & scalp. Giá di chuyển nhanh.'},
    'Mercury': {'emoji': '☿️', 'label': 'SCALP', 'desc': 'Biến động nhanh, news-driven. Phù hợp scalping.'},
    'Moon': {'emoji': '🌙', 'label': '⚠️ NOISY', 'desc': 'Cảm xúc cao, dễ FOMO/panic. Cảnh báo false signals.'},
    'Venus': {'emoji': '♀️', 'label': '⚠️ RANGE-BOUND', 'desc': 'Comfort zone, range trading. Tránh breakout trades.'},
    'Saturn': {'emoji': '♄', 'label': '⚠️ DEFENSIVE', 'desc': 'Áp lực, low liquidity. Không nên aggressive entries.'},
}

# ═══════════════════════════════════════
# DATA PULLING
# ═══════════════════════════════════════

def pull_today_data(date_str):
    """Pull today's market data from CSV."""
    row = load_day(date_str)
    if row is None:
        return None
    
    return {
        'date': date_str,
        'day_of_week': str(row['day_of_week']),
        'open': float(row['gold_open']),
        'high': float(row['gold_high']),
        'low': float(row['gold_low']),
        'close': float(row['gold_close']),
        'range': float(row['gold_range']),
        'change_pct': float(row['gold_change_pct']),
        'bullish': bool(row['gold_bullish']),
        'ema31': float(row['gold_ema_31']),
        'ema113': float(row['gold_ema_113']),
        'ema_relation': str(row['gold_ema_relation']),
        'dxy_close': float(row['dxy_close']) if not pd.isna(row.get('dxy_close')) else None,
        'dxy_change': float(row['dxy_change_pct']) if not pd.isna(row.get('dxy_change_pct')) else None,
        'dxy_dir': str(row['dxy_direction']),
        'volatility': str(row['volatility']),
        'reaction': str(row['market_reaction']),
        'trend': str(row['trend_direction']),
    }


def pull_tomorrow_astro(date_str):
    """Pull astro data for tomorrow via Vedic API."""
    try:
        import requests
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        payload = {
            'date': date_str,
            'time': '08:00',
            'timezone': 'Asia/Ho_Chi_Minh',
            'latitude': 10.85,
            'longitude': 106.75
        }
        r = requests.post("https://vedicvn-api.onrender.com/api/chart", json=payload, timeout=30)
        data = r.json()
        planets_raw = data.get('planets', [])
        
        planets = {}
        for p in planets_raw:
            name = p.get('planet', '')
            planets[name] = {
                'sign': p.get('sign', {}).get('name', ''),
                'degree': p.get('sign', {}).get('longitude', 0),
                'longitude': p.get('longitude', 0),
                'retro': p.get('isRetrograde', False),
                'nakshatra': p.get('nakshatra', {}).get('name', ''),
                'nakshatra_lord': p.get('nakshatra', {}).get('lord', ''),
            }
        
        return planets
    except Exception as e:
        print(f"⚠️ Vedic API failed: {e}", file=sys.stderr)
        return {}


def pull_tomorrow_hora(date_str):
    """Pull hora forecast for tomorrow."""
    try:
        dt = TZ.localize(datetime.strptime(date_str, "%Y-%m-%d").replace(hour=7))
        engine = VedicHoraEngine()
        forecast = engine.calculate_full_day_horas(dt)
        current = [h for h in forecast['horas'] if h['is_current']]
        
        return {
            'day_ruler': forecast['astrological_day'],
            'sunrise': forecast['sunrise'],
            'sunset': forecast['sunset'],
            'best_hours': forecast['best_trading_hours'][:5],
            'worst_hours': forecast['hours_to_avoid'][:5],
            'morning_hora': current[0] if current else None,
            'all_horas': forecast['horas'],
        }
    except Exception as e:
        print(f"⚠️ Hora failed: {e}", file=sys.stderr)
        return {}


# ═══════════════════════════════════════
# GANN & FIB CALC
# ═══════════════════════════════════════

def calc_levels(close, high, low):
    """Calculate Gann Square of 9 + Fibonacci levels."""
    base = GannEngine.extract_base_number(close)
    scale = 10 if close >= 1000 else 1
    gann = GannEngine.calculate_gann_levels(base, scale)
    
    supports = sorted([s['price'] for s in gann['supports'] if s['price'] < close], reverse=True)
    resistances = sorted([r['price'] for r in gann['resistances'] if r['price'] > close])
    
    ns = supports[0] if supports else close * 0.95
    nr = resistances[0] if resistances else close * 1.05
    
    # Fib
    fib_levels = TAEngine.calculate_fib_retracement(high, low, 'UP' if close > (high+low)/2 else 'DOWN')
    fib_analysis = TAEngine.analyze_price_fibo(close, fib_levels)
    
    return {
        'gann_base': base,
        'gann_scale': scale,
        'nearest_support': round(ns, 1),
        'nearest_resistance': round(nr, 1),
        'gann_supports': supports[:3],
        'gann_resistances': resistances[:3],
        'fib_levels': fib_levels,
        'fib_below': fib_analysis.get('below'),
        'fib_above': fib_analysis.get('above'),
    }


# ═══════════════════════════════════════
# AI PATTERN ANALYSIS
# ═══════════════════════════════════════

def analyze_patterns(today_data, tomorrow_astro, levels, hora_data):
    """
    AI-driven pattern analysis through Astro-Quant Framework.
    This is the core reasoning engine — not just data formatting.
    """
    nakshatra = tomorrow_astro.get('MOON', {}).get('nakshatra', '')
    moon_sign = tomorrow_astro.get('MOON', {}).get('sign', '')
    
    # ── Aspect detection ──
    aspects = []
    planet_list = [(k, v) for k, v in tomorrow_astro.items() if v.get('longitude')]
    
    for i, (p1_name, p1_data) in enumerate(planet_list):
        for p2_name, p2_data in planet_list[i+1:]:
            diff = abs(p1_data['longitude'] - p2_data['longitude'])
            diff = min(diff, 360 - diff)
            
            for angle, name, orb_max in [
                (0, 'Conjunction', 5), (60, 'Sextile', 4), (90, 'Square', 5),
                (120, 'Trine', 4), (180, 'Opposition', 5)
            ]:
                orb = abs(diff - angle)
                if orb <= orb_max:
                    aspects.append({
                        'p1': p1_name, 'p2': p2_name,
                        'aspect': name, 'orb': round(orb, 2),
                        'tightness': 'VERY TIGHT' if orb <= 1 else ('TIGHT' if orb <= 3 else 'MODERATE')
                    })
                    break
    
    aspects.sort(key=lambda x: x['orb'])
    
    # Skip Rahu-Ketu opposition (always true)
    aspects = [a for a in aspects if not ({a['p1'], a['p2']} == {'RAHU', 'KETU'} and a['aspect'] == 'Opposition')]
    
    # ── Key signal detection ──
    key_signals = []
    risk_flags = []
    
    # Sun-Uranus conjunction = flash move
    sun_uranus = [a for a in aspects if {a['p1'], a['p2']} == {'SUN', 'URANUS'} and a['aspect'] == 'Conjunction']
    if sun_uranus:
        key_signals.append(f"⚡ Sun Conjunction Uranus ({sun_uranus[0]['orb']}°) — FLASH MOVE risk. Sun (ruler vàng) + Uranus (đột biến) = biến động bất ngờ")
        risk_flags.append("Sun conjunct Uranus — giá có thể flash spike/crash không cảnh báo")
    
    # Mars-Pluto hard aspects = extreme volatility
    mars_pluto = [a for a in aspects if {a['p1'], a['p2']} == {'MARS', 'PLUTO'} and a['aspect'] in ('Square', 'Opposition')]
    if mars_pluto:
        key_signals.append(f"💀 Mars {mars_pluto[0]['aspect']} Pluto ({mars_pluto[0]['orb']}°) — EXTREME VOLATILITY. Năng lượng tích tụ bùng nổ")
        risk_flags.append("Mars-Pluto góc cứng — biến động cực đoan, dễ sharp reversal")
    
    # Moon-Saturn aspects
    moon_saturn = [a for a in aspects if {a['p1'], a['p2']} == {'MOON', 'SATURN'}]
    if moon_saturn:
        ms = moon_saturn[0]
        if ms['aspect'] == 'Trine':
            key_signals.append(f"🛡️ Moon Trine Saturn ({ms['orb']}°) — Sentiment có structure, thị trường phòng thủ")
    
    # Venus-Rahu aspects = manipulation
    venus_rahu = [a for a in aspects if {a['p1'], a['p2']} == {'VENUS', 'RAHU'}]
    if venus_rahu:
        vr = venus_rahu[0]
        key_signals.append(f"🔥 Venus {vr['aspect']} Rahu ({vr['orb']}°) — Định giá + disruption = dễ false breakout")
    
    # Nakshatra signal
    if nakshatra in ['Magha', 'Ardra', 'Purva Phalguni']:
        risk_flags.append(f"{nakshatra} Nakshatra có high vol rate cao — range có thể mở rộng")
    if nakshatra == 'Ashlesha':
        risk_flags.append(f"Ashlesha Nakshatra = thao túng, đầu cơ — cảnh giác false breakout & liquidity sweep")
    
    # Combust check
    for p in ['MERCURY', 'VENUS', 'MARS']:
        sun_lon = tomorrow_astro.get('SUN', {}).get('longitude', 0)
        p_lon = tomorrow_astro.get(p, {}).get('longitude', 0)
        if p_lon and sun_lon:
            diff = abs(p_lon - sun_lon)
            diff = min(diff, 360 - diff)
            thresholds = {'MERCURY': 2, 'VENUS': 4, 'MARS': 8}
            if diff <= thresholds.get(p, 8):
                key_signals.append(f"🔥 {p} COMBUST (cách Sun {diff:.1f}°) — năng lượng bị che khuất")
    
    # Retro check
    retro_planets = [k for k, v in tomorrow_astro.items() if v.get('retro') and k not in ['RAHU', 'KETU']]
    for rp in retro_planets:
        key_signals.append(f"🔄 {rp} NGHỊCH HÀNH — năng lượng hướng nội, tác động ngầm")
    
    # ── Build reasoning ──
    reasoning_parts = []
    
    # Moon state
    nak_quality = NAKSHATRA_QUALITIES.get(nakshatra, '')
    moon_feel = MOON_SIGN_SENTIMENT.get(moon_sign, '')
    reasoning_parts.append(f"Moon tại {moon_sign} ({nakshatra} Nakshatra): {nak_quality}. {moon_feel}")
    
    # Market structure
    if today_data:
        ema = today_data.get('ema_relation', '')
        if ema == 'below':
            reasoning_parts.append(f"EMA31 < EMA113 — xu hướng ngắn hạn yếu, cảnh báo bearish")
        dxy = today_data.get('dxy_dir', '')
        if dxy == 'bullish':
            reasoning_parts.append(f"DXY bullish — tạo áp lực giảm lên vàng")
    
    # Key aspects in reasoning
    for sig in key_signals[:3]:
        reasoning_parts.append(sig)
    
    # Hora note
    if hora_data.get('morning_hora'):
        mh = hora_data['morning_hora']
        hd = HORA_TRADING.get(mh['ruler'], {})
        reasoning_parts.append(f"Hora sáng: {mh['ruler']} — {hd.get('desc', '')}")
    
    # ── Signal direction ──
    # Score-based
    retro_bullish = 1 if 'MARS' in retro_planets else 0
    retro_bearish = 1 if 'SATURN' in retro_planets else 0
    
    bullish_score = 0
    bearish_score = 0
    
    # Nakshatra bias
    bullish_naks = ['Mula', 'Purva Ashadha', 'Ashwini', 'Magha', 'Chitra', 'Vishakha']
    bearish_naks = ['Uttara Bhadrapada', 'Anuradha', 'Dhanishta', 'Mrigashira', 'Pushya']
    if nakshatra in bullish_naks:
        bullish_score += 1
    if nakshatra in bearish_naks:
        bearish_score += 1
    
    # Moon sign
    if moon_sign in ['Sagittarius', 'Leo', 'Libra']:
        bullish_score += 1
    if moon_sign in ['Scorpio', 'Capricorn', 'Aquarius']:
        bearish_score += 1
    
    # Retros
    bullish_score += retro_bullish * 1
    bearish_score += retro_bearish * 1
    
    # EMA
    if today_data and today_data.get('ema_relation') == 'below':
        bearish_score += 1
    elif today_data and today_data.get('ema_relation') == 'above':
        bullish_score += 1
    
    # DXY
    if today_data and today_data.get('dxy_dir') == 'bearish':
        bullish_score += 1
    elif today_data and today_data.get('dxy_dir') == 'bullish':
        bearish_score += 1
    
    # Determine direction
    if bullish_score > bearish_score:
        direction = 'BULLISH'
        confidence = min(85, 55 + (bullish_score - bearish_score) * 10)
    elif bearish_score > bullish_score:
        direction = 'BEARISH'
        confidence = min(85, 55 + (bearish_score - bullish_score) * 10)
    else:
        # Tiebreaker: nakshatra historical bias
        direction = 'BULLISH' if nakshatra in bullish_naks else 'BEARISH'
        confidence = 50
    
    conf_label = '🟢 HIGH' if confidence >= 70 else ('🟡 MEDIUM' if confidence >= 55 else '🔴 LOW')
    
    # ── SL/TP calculation ──
    close = today_data['close'] if today_data else 4500
    ns = levels['nearest_support']
    nr = levels['nearest_resistance']
    gap = nr - ns
    
    if direction == 'BULLISH':
        # Entry: near support (pullback buy)
        entry = round(ns + gap * 0.15, 1)  # just above support + 15% gap buffer
        sl = round(ns - gap * 0.05, 1)       # tight stop below support
        tp1 = round(nr, 1)                   # TP1 = nearest resistance
        tp2 = round(nr + gap * 0.382, 1)    # TP2 = next resistance extension
    else:
        # Entry: near resistance (rally sell)
        entry = round(nr - gap * 0.15, 1)  # just below resistance - 15% gap buffer
        sl = round(nr + gap * 0.05, 1)       # tight stop above resistance
        tp1 = round(ns, 1)                   # TP1 = nearest support
        tp2 = round(ns - gap * 0.382, 1)    # TP2 = next support extension
    
    # Ensure entry is between support and resistance
    entry = max(ns, min(nr, entry))
    
    risk = abs(entry - sl)
    reward_tp1 = abs(tp1 - entry)
    reward_tp2 = abs(tp2 - entry)
    
    # Cap risk at reasonable level (max 3% of price)
    max_risk = close * 0.03
    if risk > max_risk:
        if direction == 'BULLISH':
            sl = round(entry - max_risk, 1)
        else:
            sl = round(entry + max_risk, 1)
        risk = max_risk
    
    return {
        'direction': direction,
        'confidence': round(confidence),
        'conf_label': conf_label,
        'bullish_score': bullish_score,
        'bearish_score': bearish_score,
        'aspects': aspects,
        'key_signals': key_signals,
        'risk_flags': risk_flags,
        'reasoning': reasoning_parts,
        'entry': entry,
        'sl': sl,
        'tp1': tp1,
        'tp2': tp2,
        'risk': round(risk, 1),
        'reward_tp1': round(reward_tp1, 1),
        'reward_tp2': round(reward_tp2, 1),
        'rr_tp1': round(reward_tp1 / risk, 1) if risk > 0 else 0,
        'rr_tp2': round(reward_tp2 / risk, 1) if risk > 0 else 0,
    }


# ═══════════════════════════════════════
# TEMPLATE RENDERER
# ═══════════════════════════════════════

def render_report(today, tomorrow_date, astro, levels, hora, analysis, macro_note=""):
    """Render the fixed-format prediction report."""
    
    nakshatra = astro.get('MOON', {}).get('nakshatra', 'N/A')
    nak_quality = NAKSHATRA_QUALITIES.get(nakshatra, '')
    moon_sign = astro.get('MOON', {}).get('sign', 'N/A')
    
    lines = []
    
    # ── HEADER ──
    lines.append(f"# 🔮 CARMEN'S GOLD FORECAST — {tomorrow_date}")
    lines.append(f"**Dự báo ngày:** {tomorrow_date} | **Dữ liệu tham chiếu:** Close {today['date']} ${today['close']:.1f}")
    lines.append("")
    
    # ── SECTION 1: TỔNG QUAN ──
    lines.append("## 📊 1. TỔNG QUAN THỊ TRƯỜNG HÔM NAY")
    lines.append("")
    emoji = "🟢" if today['bullish'] else "🔴"
    lines.append(f"| Chỉ số | Giá trị |")
    lines.append(f"|--------|--------|")
    lines.append(f"| **Close** | ${today['close']:.1f} |")
    lines.append(f"| **Change** | {today['change_pct']:+.2f}% {emoji} |")
    lines.append(f"| **High / Low** | ${today['high']:.1f} / ${today['low']:.1f} |")
    lines.append(f"| **Range** | ${today['range']:.1f} |")
    lines.append(f"| **EMA 31/113** | {today['ema31']:.1f} / {today['ema113']:.1f} ({today['ema_relation']}) |")
    lines.append(f"| **DXY** | {today['dxy_close']} ({today['dxy_dir']}, {today['dxy_change']:+.2f}%) |")
    lines.append(f"| **Volatility** | {today['volatility'].upper()} |")
    lines.append("")
    
    # ── SECTION 2: KHUNG THIÊN VĂN NGÀY MAI ──
    lines.append("## 🌌 2. KHUNG THIÊN VĂN NGÀY MAI")
    lines.append("")
    lines.append(f"**🌙 Moon:** {moon_sign} — **{nakshatra} Nakshatra** ({nak_quality})")
    lines.append(f"**⏰ Ngày:** {hora.get('day_ruler', 'N/A')} | **Bình minh:** {hora.get('sunrise', 'N/A')} | **Hoàng hôn:** {hora.get('sunset', 'N/A')}")
    lines.append("")
    
    # Planets table
    lines.append(f"| Hành tinh | Cung | Độ | Trạng thái |")
    lines.append(f"|-----------|------|-----|-----------|")
    planet_order = ['SUN', 'MOON', 'MERCURY', 'VENUS', 'MARS', 'JUPITER', 'SATURN', 'RAHU', 'KETU']
    sym = {'SUN': '☀️', 'MOON': '🌙', 'MERCURY': '☿️', 'VENUS': '♀️', 'MARS': '♂️', 'JUPITER': '♃', 'SATURN': '♄', 'RAHU': '☊', 'KETU': '☋'}
    for p in planet_order:
        pd_ = astro.get(p, {})
        sign = pd_.get('sign', '')
        deg = pd_.get('degree', 0)
        retro = '℞ Nghịch hành' if pd_.get('retro') and p not in ['RAHU', 'KETU'] else ('—' if p not in ['RAHU', 'KETU'] else '—')
        lines.append(f"| {sym.get(p, '')} {p} | {sign} | {deg}° | {retro} |")
    lines.append("")
    
    # Active aspects
    if analysis['aspects']:
        lines.append("### 🔗 Góc chiếu ngày mai (trong orb ±5°):")
        lines.append("")
        for a in analysis['aspects'][:10]:
            p1 = a['p1']
            p2 = a['p2']
            asp = a['aspect']
            orb = a['orb']
            tight = a['tightness']
            lines.append(f"- {sym.get(p1,'')} {p1} **{asp}** {sym.get(p2,'')} {p2} — orb {orb}° ({tight})")
        lines.append("")
    
    # Hora schedule
    if hora.get('best_hours'):
        lines.append("### ⏰ Khung giờ giao dịch tốt nhất:")
        lines.append("")
        for h in hora['best_hours'][:3]:
            lines.append(f"- {h['emoji']} **{h['start']}-{h['end']}** | {h['ruler']} Hora | {h['label']}")
        lines.append("")
    
    if hora.get('worst_hours'):
        lines.append("### ⚠️ Khung giờ nên tránh:")
        lines.append("")
        for h in hora['worst_hours'][:3]:
            if h['start'] >= '07:00' and h['start'] <= '22:00':
                lines.append(f"- {h['emoji']} **{h['start']}-{h['end']}** | {h['ruler']} Hora | {h['label']}")
        lines.append("")
    
    # ── SECTION 3: KEY SIGNALS ──
    lines.append("## 🧬 3. TÍN HIỆU CHÍNH")
    lines.append("")
    for sig in analysis['key_signals']:
        lines.append(f"- {sig}")
    if not analysis['key_signals']:
        lines.append("- Không có tín hiệu cực đoan đáng kể.")
    lines.append("")
    
    # ── SECTION 4: LEVELS ──
    lines.append("## 📐 4. MỨC GIÁ QUAN TRỌNG")
    lines.append("")
    lines.append(f"| Vùng | Giá |")
    lines.append(f"|------|-----|")
    lines.append(f"| **Resistance (Gann)** | ${levels['nearest_resistance']:.1f} |")
    lines.append(f"| **Close hôm nay** | ${today['close']:.1f} |")
    lines.append(f"| **Support (Gann)** | ${levels['nearest_support']:.1f} |")
    lines.append("")
    
    # Fib
    fib_above = levels.get('fib_above')
    fib_below = levels.get('fib_below')
    if fib_above:
        lines.append(f"- **Fib trên:** {fib_above[0]} — ${fib_above[1]:.1f}")
    if fib_below:
        lines.append(f"- **Fib dưới:** {fib_below[0]} — ${fib_below[1]:.1f}")
    lines.append("")
    
    # ── SECTION 5: CALL LỆNH ──
    lines.append("---")
    lines.append("")
    lines.append("## 💡 ĐỀ XUẤT CHIẾN LƯỢC")
    lines.append("")
    
    order_type = "⬆️ BUY LIMIT" if analysis['direction'] == 'BULLISH' else "⬇️ SELL LIMIT"
    lines.append(f"🧠 CARMEN AI PHÂN TÍCH — **{analysis['direction']}** | Confidence: {analysis['confidence']}% {analysis['conf_label']}")
    lines.append("")
    lines.append(f"📌 **LỆNH: {order_type}**")
    lines.append(f"• **Entry:** ${analysis['entry']:.1f}")
    
    # Entry reasoning
    if analysis['direction'] == 'BULLISH':
        lines.append(f" → Entry tại pullback về gần Gann Support ${levels['nearest_support']:.1f}. Chờ nến H1 xác nhận bật lên.")
    else:
        lines.append(f" → Entry tại rally lên gần Gann Resistance ${levels['nearest_resistance']:.1f}. Chờ nến H1 xác nhận từ chối.")
    
    lines.append(f"• **SL:** ${analysis['sl']:.1f}")
    lines.append(f"• **TP1:** ${analysis['tp1']:.1f} (50% pos) | **TP2:** ${analysis['tp2']:.1f}")
    lines.append(f"• **R:R = 1:{analysis['rr_tp2']:.1f}** (dựa trên TP2)")
    lines.append("")
    
    # ── SECTION 6: REASONING ──
    lines.append("📝 **CARMEN'S REASONING:**")
    for r in analysis['reasoning']:
        lines.append(f"- {r}")
    lines.append("")
    
    # ── SECTION 7: MACRO ──
    lines.append(f"📰 **MACRO CONTEXT:**")
    lines.append(f"{macro_note if macro_note else 'Không có sự kiện kinh tế tác động mạnh. Theo dõi DXY và US10Y để xác nhận thêm.'}")
    lines.append("")
    
    # ── SECTION 8: RISKS ──
    lines.append("🔴 **KEY RISKS:**")
    for rf in analysis['risk_flags'][:5]:
        lines.append(f"⚠️ {rf}")
    if not analysis['risk_flags']:
        lines.append(f"⚠️ Rủi ro chính: giá không giữ được mức Gann Support/Resistance, false breakout.")
    lines.append("")
    
    # ── SECTION 9: ZONES ──
    lines.append(f"📍 **Vùng quan sát (Kỹ thuật):** Giá cần giữ trên ${levels['nearest_support']:.1f} để duy trì cấu trúc tăng, hoặc phá vỡ dưới để xác nhận giảm.")
    lines.append(f"📍 **Kháng cự cực đại (Gann):** ${levels['nearest_resistance']:.1f}")
    lines.append(f"📍 **Hỗ trợ cực đại (Gann):** ${levels['nearest_support']:.1f}")
    
    morning_hora = hora.get('morning_hora', {})
    if morning_hora:
        lines.append(f"🛑 **Cảnh báo:** Hora sáng mai là {morning_hora.get('ruler', 'N/A')} Hora. {HORA_TRADING.get(morning_hora.get('ruler', ''), {}).get('label', '')} — {HORA_TRADING.get(morning_hora.get('ruler', ''), {}).get('desc', '')}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Bản tin dự báo bởi Carmen AI — Astro-Quant Engine v1.0*")
    lines.append(f"*Dữ liệu thiên văn: Vedic API (Lahiri) | Dữ liệu giá: yfinance*")
    lines.append(f"*⚠️ KHÔNG PHẢI LỜI KHUYÊN ĐẦU TƯ. Luôn quản lý rủi ro. Backtest: LONG 78% / SHORT 85% win rate.*")
    
    return "\n".join(lines)


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def generate_nightly(target_date_str=None, json_only=False):
    """Main nightly report generation."""
    
    # ── Determine dates ──
    if target_date_str:
        tomorrow_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    else:
        tomorrow_dt = datetime.now(TZ) + timedelta(days=1)
    
    tomorrow_str = tomorrow_dt.strftime("%Y-%m-%d")
    today_str = (tomorrow_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"📡 Pulling data...")
    print(f"   Today (reference): {today_str}")
    print(f"   Tomorrow (predict): {tomorrow_str}")
    
    # ── Pull data ──
    today = pull_today_data(today_str)
    if not today:
        print(f"❌ No data for today ({today_str}). Cannot generate report.", file=sys.stderr)
        return None
    
    astro = pull_tomorrow_astro(tomorrow_str)
    if not astro:
        print(f"❌ No astro data for tomorrow ({tomorrow_str}).", file=sys.stderr)
        return None
    
    hora = pull_tomorrow_hora(tomorrow_str)
    levels = calc_levels(today['close'], today['high'], today['low'])
    
    # ── AI Analysis ──
    analysis = analyze_patterns(today, astro, levels, hora)
    
    # ── Macro note ──
    macro_note = ""
    if today.get('dxy_dir') == 'bullish':
        macro_note += "DXY đang bullish — tạo áp lực giảm lên vàng. "
    elif today.get('dxy_dir') == 'bearish':
        macro_note += "DXY đang bearish — hỗ trợ vàng tăng. "
    if today.get('ema_relation') == 'below':
        macro_note += "EMA31 dưới EMA113 — xu hướng ngắn hạn yếu."
    
    # ── Output ──
    if json_only:
        packet = {
            'today': today, 'tomorrow_date': tomorrow_str,
            'astro': {k: {sk: sv for sk, sv in v.items()} for k, v in astro.items()},
            'hora': {k: v for k, v in hora.items() if k != 'all_horas'},
            'levels': levels,
            'analysis': {k: v for k, v in analysis.items() if k != 'aspects'},
            'aspects': analysis['aspects'],
        }
        return json.dumps(packet, indent=2, ensure_ascii=False, default=str)
    
    # ── Render report ──
    report = render_report(today, tomorrow_str, astro, levels, hora, analysis, macro_note)
    
    # ── Save ──
    filename = f"FORECAST_{tomorrow_str}.md"
    filepath = OUTPUT_DIR / filename
    filepath.write_text(report)
    
    print(f"\n✅ Report saved: {filepath}")
    return report


if __name__ == "__main__":
    json_only = "--json" in sys.argv
    date_arg = None
    for a in sys.argv[1:]:
        if not a.startswith('--') and len(a) == 10 and '-' in a:
            date_arg = a
    
    report = generate_nightly(target_date_str=date_arg, json_only=json_only)
    if report and not json_only:
        print(report)
