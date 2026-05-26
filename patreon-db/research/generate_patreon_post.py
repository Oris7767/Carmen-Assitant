#!/usr/bin/env python3
"""
generate_patreon_post.py — Astro-Quant Patreon Post Generator
Loads current day data, runs through scoring engine, finds matching
historical patterns, and generates a data-backed Patreon analysis post.

Usage:
    python3 generate_patreon_post.py                          # today
    python3 generate_patreon_post.py 2026-05-22               # specific date
    python3 generate_patreon_post.py 2026-05-22 --verbose     # full debug
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(__file__))
from astro_quant_scorer import AstroQuantScorer

DATA_DIR = Path(os.path.dirname(__file__)).parent / "data"

# ─── Config ───
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

ASPECT_NAMES_VI = {
    'Conjunction': 'Giao hội (0°)',
    'Sextile': 'Lục hợp (60°)',
    'Square': 'Góc Vuông (90°)',
    'Trine': 'Tam hợp (120°)',
    'Opposition': 'Đối đỉnh (180°)',
}

PLANET_NAMES_VI = {
    'Sun': 'Mặt Trời', 'Moon': 'Mặt Trăng', 'Mercury': 'Sao Thủy',
    'Venus': 'Sao Kim', 'Mars': 'Sao Hỏa', 'Jupiter': 'Sao Mộc',
    'Saturn': 'Sao Thổ', 'Rahu': 'Rahu', 'Ketu': 'Ketu',
}

PLANET_SYMBOLS = {
    'Sun': '☀️', 'Moon': '🌙', 'Mercury': '☿️', 'Venus': '♀️',
    'Mars': '♂️', 'Jupiter': '♃', 'Saturn': '♄', 'Rahu': '☊', 'Ketu': '☋',
}

# ─── Data Loading ───

def load_day(date_str):
    """Load a single day's data from monthly CSV."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    csv_path = DATA_DIR / f"{dt.year}-{dt.month:02d}.csv"
    
    if not csv_path.exists():
        print(f"Error: No data file for {dt.year}-{dt.month:02d}", file=sys.stderr)
        return None
    
    df = pd.read_csv(csv_path)
    row = df[df['date'] == date_str]
    
    if row.empty:
        print(f"Error: No data for {date_str}", file=sys.stderr)
        return None
    
    return row.iloc[0]


def find_similar_days(row, full_df, top_n=5):
    """
    Find historically similar days based on:
    1. Same Nakshatra + same Moon Sign (exact astro match)
    2. Similar aspect count and types
    """
    nakshatra = row['moon_nakshatra']
    moon_sign = row['moon_sign']
    vol = row['volatility']
    
    # Parse current aspects
    try:
        current_aspects = set()
        aspects_list = json.loads(str(row['aspects_json'])) if isinstance(row['aspects_json'], str) else row['aspects_json']
        for a in aspects_list:
            key = f"{a['planet1']}-{a['aspect']}-{a['planet2']}"
            current_aspects.add(key)
    except:
        current_aspects = set()
    
    # 1. Exact Nakshatra + Moon Sign matches (excluding current date)
    exact_matches = full_df[
        (full_df['moon_nakshatra'] == nakshatra) & 
        (full_df['moon_sign'] == moon_sign) &
        (full_df['date'] != row['date'])
    ].copy()
    
    # 2. Score each match by aspect overlap
    scored_matches = []
    for _, match in exact_matches.iterrows():
        try:
            match_aspects = set()
            mas_list = json.loads(str(match['aspects_json'])) if isinstance(match['aspects_json'], str) else match['aspects_json']
            for a in mas_list:
                key = f"{a['planet1']}-{a['aspect']}-{a['planet2']}"
                match_aspects.add(key)
            
            overlap = len(current_aspects & match_aspects)
            scored_matches.append({
                'date': match['date'],
                'close': match['gold_close'],
                'change': match['gold_change_pct'],
                'bullish': match['gold_bullish'],
                'range': match['gold_range'],
                'vol': match['volatility'],
                'reaction': match['market_reaction'],
                'aspect_overlap': overlap,
                'total_aspects': len(match_aspects),
            })
        except:
            continue
    
    scored_matches.sort(key=lambda x: (x['aspect_overlap'], -abs(x['change'])), reverse=True)
    
    return scored_matches[:top_n]


def format_aspect_vi(aspect_dict):
    """Format aspect in Vietnamese."""
    p1 = PLANET_NAMES_VI.get(aspect_dict['planet1'], aspect_dict['planet1'])
    p2 = PLANET_NAMES_VI.get(aspect_dict['planet2'], aspect_dict['planet2'])
    asp = ASPECT_NAMES_VI.get(aspect_dict['aspect'], aspect_dict['aspect'])
    orb = aspect_dict.get('orb_deg', '')
    return f"{p1} {asp} {p2}" + (f" (orb {orb}°)" if orb else "")


def classify_setup(nakshatra, moon_sign, score):
    """Classify setup quality based on framework data."""
    # Top nakshatras (from backtest)
    top_naks = ['Mula', 'Purva Ashadha', 'Ashwini']
    bearish_naks = ['Uttara Bhadrapada', 'Anuradha', 'Dhanishta', 'Mrigashira']
    top_moons = ['Sagittarius', 'Libra', 'Leo']
    bearish_moons = ['Scorpio', 'Capricorn', 'Aquarius']
    
    quality = 'C'
    if nakshatra in top_naks and moon_sign in top_moons:
        quality = 'A+'
    elif nakshatra in top_naks or (moon_sign in top_moons and score >= 3):
        quality = 'A'
    elif nakshatra in bearish_naks and moon_sign in bearish_moons:
        quality = 'F'
    elif nakshatra in bearish_naks:
        quality = 'D'
    elif score >= 3:
        quality = 'B'
    elif score <= -3:
        quality = 'D'
    
    return quality


# ─── Post Generation ───

def generate_post(date_str, verbose=False):
    """Generate a complete Patreon analysis post."""
    row = load_day(date_str)
    if row is None:
        return None
    
    # ═══ SCORE THROUGH FRAMEWORK ═══
    result = AstroQuantScorer.score(row)
    
    # ═══ LOAD FULL DATASET FOR SIMILARITY ═══
    dfs = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            dfs.append(pd.read_csv(f))
        except:
            pass
    full_df = pd.concat(dfs, ignore_index=True)
    
    # ═══ FIND SIMILAR DAYS ═══
    similar = find_similar_days(row, full_df, top_n=5)
    
    # ═══ CLASSIFY SETUP ═══
    setup_quality = classify_setup(
        row['moon_nakshatra'], 
        row['moon_sign'], 
        result['composite_score']
    )
    
    # ═══ BUILD POST ═══
    lines = []
    
    # Header
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_vi = {
        'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư',
        'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy', 'Sunday': 'Chủ Nhật'
    }
    
    lines.append(f"# 🔬 BẢN TIN ASTRO-QUANT GOLD — {day_vi.get(row['day_of_week'], row['day_of_week'])} {dt.day}/{dt.month}/{dt.year}")
    lines.append("")
    
    # ─── SECTION 1: TỔNG QUAN THỊ TRƯỜNG ───
    lines.append("## 📊 1. TỔNG QUAN THỊ TRƯỜNG")
    lines.append("")
    
    direction = "TĂNG" if row['gold_bullish'] else "GIẢM"
    emoji = "🟢" if row['gold_bullish'] else "🔴"
    lines.append(f"| Chỉ số | Giá trị |")
    lines.append(f"|--------|--------|")
    lines.append(f"| **Open** | ${row['gold_open']:.1f} |")
    lines.append(f"| **Close** | ${row['gold_close']:.1f} |")
    lines.append(f"| **High** | ${row['gold_high']:.1f} |")
    lines.append(f"| **Low** | ${row['gold_low']:.1f} |")
    lines.append(f"| **Range** | ${row['gold_range']:.1f} |")
    lines.append(f"| **Change** | {row['gold_change_pct']:+.2f}% {emoji} |")
    lines.append(f"| **EMA 31/113** | {row['gold_ema_31']:.1f} / {row['gold_ema_113']:.1f} ({row['gold_ema_relation']}) |")
    lines.append(f"| **DXY** | {row['dxy_close']} ({row['dxy_direction']}, {row['dxy_change_pct']:+.2f}%) |")
    lines.append(f"| **Volatility** | {row['volatility'].upper()} (range ${row['gold_range']:.1f}) |")
    lines.append(f"| **Market Reaction** | {row['market_reaction']} |")
    lines.append("")
    
    # ─── SECTION 2: KHUNG THIÊN VĂN ───
    lines.append("## 🌌 2. KHUNG THIÊN VĂN HÔM NAY")
    lines.append("")
    
    # State
    state_emoji = {'expansion': '🟢', 'compression': '🟡', 'exhaustion': '🔴', 'fear': '💀'}
    state_name = {'expansion': 'MỞ RỘNG', 'compression': 'NÉN GIÁ', 'exhaustion': 'KIỆT SỨC/THAO TÚNG', 'fear': 'HOẢNG LOẠN'}
    lines.append(f"**Trạng thái thị trường:** {state_emoji.get(result['market_state'], '⚪')} **{state_name.get(result['market_state'], result['market_state']).upper()}**")
    lines.append(f"**Composite Score:** {result['composite_score']:+.1f}/10")
    lines.append(f"**Tín hiệu:** {result['signal']} (độ tin cậy: {result['confidence']})")
    lines.append("")
    
    # Moon
    nak_quality = NAKSHATRA_QUALITIES.get(row['moon_nakshatra'], '')
    lines.append(f"### 🌙 Mặt Trăng")
    lines.append(f"- **Cung:** {row['moon_sign']} ({row['moon_deg']}°)")
    lines.append(f"- **Nakshatra:** {row['moon_nakshatra']} — *{nak_quality}*")
    lines.append(f"- **Pha:** {row['moon_phase']} (illumination {row['moon_illumination_pct']}%)")
    lines.append(f"- **Hora chủ đạo:** {row['dominant_planet_hour']}")
    lines.append("")
    
    # Nakshatra historical stats
    nak_stats = full_df[full_df['moon_nakshatra'] == row['moon_nakshatra']]
    nak_bull = nak_stats['gold_bullish'].sum() / len(nak_stats) * 100 if len(nak_stats) > 0 else 0
    nak_avg_chg = nak_stats['gold_change_pct'].mean() if len(nak_stats) > 0 else 0
    lines.append(f"**📈 Lịch sử {row['moon_nakshatra']} Nakshatra:** {len(nak_stats)} ngày → **{nak_bull:.1f}% bullish**, avgΔ {nak_avg_chg:+.2f}%")
    lines.append("")
    
    # Planets
    lines.append(f"### 🪐 Hành Tinh")
    lines.append(f"| Hành tinh | Cung | Độ | Trạng thái |")
    lines.append(f"|-----------|------|----|-----------|")
    for planet in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']:
        sign = row.get(f'{planet}_sign', '')
        deg = row.get(f'{planet}_deg', 0)
        retro = row.get(f'{planet}_retro', False) if f'{planet}_retro' in row.index else False
        combust = row.get(f'{planet}_combust', False) if f'{planet}_combust' in row.index else False
        elong = row.get(f'{planet}_elong_deg', '') if f'{planet}_elong_deg' in row.index else ''
        
        status = []
        if planet in ['mercury', 'venus']:
            elong_dir = row.get(f'{planet}_elong_dir', '')
            if elong_dir == 'W':
                status.append('Morning Star ⭐')
            elif elong_dir == 'E':
                status.append('Evening Star 🌅')
        if retro:
            status.append('Nghịch hành ℞')
        if combust:
            status.append('Bốc cháy 🔥')
        
        sym = PLANET_SYMBOLS.get(planet.capitalize(), '')
        name = PLANET_NAMES_VI.get(planet.capitalize(), planet.capitalize())
        status_str = ', '.join(status) if status else '—'
        lines.append(f"| {sym} **{name}** | {sign} | {deg}° | {status_str} |")
    lines.append("")
    
    # Active Aspects
    lines.append(f"### 🔗 Góc Chiếu Chính (trong orb ±5°)")
    lines.append("")
    try:
        aspects = json.loads(str(row['aspects_json'])) if isinstance(row['aspects_json'], str) else row['aspects_json']
        if aspects:
            for asp in aspects:
                p1 = asp['planet1']
                p2 = asp['planet2']
                asp_type = asp['aspect']
                key = f"{p1} {asp_type} {p2}"
                
                # Lookup historical stats for this aspect
                score_info = ""
                if key in AstroQuantScorer.ASPECT_SCORES:
                    sc = AstroQuantScorer.ASPECT_SCORES[key]
                    score_info = f" → Score: {sc:+.1f}"
                
                lines.append(f"- {format_aspect_vi(asp)}{score_info}")
        else:
            lines.append("- Không có góc chiếu lớn nào trong ngày")
    except Exception as e:
        lines.append(f"- (error parsing aspects: {e})")
    lines.append("")
    
    # Eclipse
    if row.get('eclipse_active'):
        lines.append(f"⚠️ **ECLIPSE ACTIVE:** {row['eclipse_type']} — days away: {row['eclipse_days_away']}")
        lines.append("")
    
    # ─── SECTION 3: PHÂN TÍCH KHUNG ASTRO-QUANT ───
    lines.append("## 🧬 3. PHÂN TÍCH THEO KHUNG ASTRO-QUANT")
    lines.append("")
    
    # Signal breakdown from scorer details
    details = result.get('details', {})
    
    lines.append("### Tín hiệu TĂNG (Bullish Signals)")
    lines.append("")
    bull_signals = []
    bear_signals = []
    neutral_signals = []
    
    for cat, data in details.items():
        if cat == 'aspects':
            for ad in data.get('details', []):
                if ad['score'] > 0:
                    bull_signals.append((ad['aspect'], ad['score']))
                elif ad['score'] < 0:
                    bear_signals.append((ad['aspect'], ad['score']))
        elif cat in ['high_vol_alert', 'mars_combust_alert', 'eco_impact']:
            bear_signals.append((data, -1.0) if isinstance(data, str) else (cat, -0.5))
        elif isinstance(data, dict) and 'score' in data:
            s = data['score']
            # Get display value from various possible keys
            v = data.get('value', data.get('held', data.get('relation', data.get('direction', ''))))
            label = f"{cat}"
            if v and str(v).strip():
                label = f"{cat}: {v}"
            if s > 0:
                bull_signals.append((label, s))
            elif s < 0:
                bear_signals.append((label, s))
            else:
                neutral_signals.append((label, s))
    
    if bull_signals:
        lines.append("| Tín hiệu | Điểm |")
        lines.append("|----------|------|")
        for sig, sc in sorted(bull_signals, key=lambda x: x[1], reverse=True):
            lines.append(f"| ✅ {sig} | {sc:+.1f} |")
        lines.append("")
    else:
        lines.append("Không có tín hiệu tăng đáng kể nào.")
        lines.append("")
    
    lines.append("### Tín hiệu GIẢM (Bearish Signals)")
    lines.append("")
    if bear_signals:
        lines.append("| Tín hiệu | Điểm |")
        lines.append("|----------|------|")
        for sig, sc in sorted(bear_signals, key=lambda x: x[1]):
            lines.append(f"| ❌ {sig} | {sc:+.1f} |")
        lines.append("")
    else:
        lines.append("Không có tín hiệu giảm đáng kể nào.")
        lines.append("")
    
    lines.append(f"**→ Điểm tổng hợp:** {result['composite_score']:+.1f}/10")
    lines.append(f"**→ Tín hiệu:** **{result['signal']}**")
    lines.append("")
    
    # ─── SECTION 4: SO SÁNH LỊCH SỬ ───
    lines.append("## 📜 4. NGÀY LỊCH SỬ TƯƠNG ĐỒNG")
    lines.append("")
    lines.append(f"Các ngày có cùng Nakshatra **{row['moon_nakshatra']}** + Moon **{row['moon_sign']}**:")
    lines.append("")
    
    if similar:
        lines.append("| Ngày | Close | Δ% | Range | Phản ứng | Khớp Aspects |")
        lines.append("|------|-------|----|-------|----------|-------------|")
        for s in similar:
            em = "🟢" if s['bullish'] else "🔴"
            lines.append(f"| {s['date']} | ${s['close']:.1f} | {s['change']:+.2f}% {em} | ${s['range']:.1f} | {s['reaction']} | {s['aspect_overlap']}/{s['total_aspects']} |")
        lines.append("")
        
        # Summary stats
        bull_count = sum(1 for s in similar if s['bullish'])
        bear_count = len(similar) - bull_count
        lines.append(f"**Kết quả:** {bull_count}/{len(similar)} ngày bullish ({bull_count/len(similar)*100:.0f}%)")
        lines.append("")
    else:
        lines.append("Không tìm thấy ngày lịch sử tương đồng trong database.")
        lines.append("")
    
    # ─── SECTION 5: GANN & FIB ───
    lines.append("## 📐 5. GANN & FIBONACCI")
    lines.append("")
    
    try:
        gann_levels = json.loads(str(row['gann_levels_json'])) if isinstance(row['gann_levels_json'], str) else row['gann_levels_json']
        supports = gann_levels.get('supports', [])
        resistances = gann_levels.get('resistances', [])
        
        lines.append(f"**Gann Base:** {gann_levels.get('base', 'N/A')} | **Scale:** {gann_levels.get('scale', 'N/A')}")
        lines.append(f"**Nearest Support:** ${row['gann_nearest_support']}")
        lines.append(f"**Nearest Resistance:** ${row['gann_nearest_resistance']}")
        lines.append(f"**Gann Gap:** ${row['gann_gap']}")
        
        held_status = "✅ HELD" if row.get('gann_held', False) else "❌ NOT HELD"
        lines.append(f"**Key Level Status:** {held_status}")
        if row.get('gann_breached'):
            lines.append(f"**Breached:** {row['gann_breached']}")
        lines.append("")
        
        lines.append("### Gann Support Levels")
        lines.append("| Level | Price |")
        lines.append("|-------|-------|")
        for s in supports[-4:]:
            marker = " ← CLOSE" if abs(float(s) - float(row['gold_close'])) < float(row['gold_close']) * 0.02 else ""
            lines.append(f"| Support | ${s}{marker} |")
        lines.append("")
        
        lines.append("### Gann Resistance Levels")
        lines.append("| Level | Price |")
        lines.append("|-------|-------|")
        for r in resistances[:4]:
            marker = " ← CLOSE" if abs(float(r) - float(row['gold_close'])) < float(row['gold_close']) * 0.02 else ""
            lines.append(f"| Resistance | ${r}{marker} |")
        lines.append("")
    except Exception as e:
        lines.append(f"(Gann data parse error: {e})")
        lines.append("")
    
    # ─── SECTION 6: KẾT LUẬN & KHUYẾN NGHỊ ───
    lines.append("## 🎯 6. KẾT LUẬN & CHIẾN LƯỢC")
    lines.append("")
    
    lines.append(f"**Setup Quality:** {setup_quality}")
    lines.append(f"**Market State:** {state_name.get(result['market_state'], 'Unknown')}")
    lines.append("")
    
    # Strategy based on state
    if result['market_state'] == 'expansion':
        lines.append("### Chiến lược hôm nay:")
        lines.append("- Thị trường đang trong pha **Mở Rộng** — trend rõ ràng, thanh khoản tốt")
        lines.append("- Vào lệnh theo pullback về Gann Support")
        lines.append("- Trailing stop theo EMA31")
        lines.append(f"- Target: Fib 1.2126 - 1.618")
    elif result['market_state'] == 'compression':
        lines.append("### Chiến lược hôm nay:")
        lines.append("- Thị trường đang trong pha **Nén Giá** — sideway biên độ hẹp")
        lines.append("- Trade range giữa Gann Support và Resistance")
        lines.append("- Giảm size còn 0.5x, chờ breakout xác nhận")
        lines.append("- Scalp target: Fib 0.5 - 0.618")
    elif result['market_state'] == 'exhaustion':
        lines.append("### Chiến lược hôm nay:")
        lines.append("- Thị trường đang trong pha **Kiệt Sức / Thao Túng**")
        lines.append("- ⚠️ Cảnh giác false breakout — fade the move")
        lines.append("- Chờ 2 nến đóng cửa quay lại range trước khi vào lệnh")
        lines.append("- Stop rộng hơn: 1.5x ATR")
    elif result['market_state'] == 'fear':
        lines.append("### Chiến lược hôm nay:")
        lines.append("- ⚠️ Thị trường trong pha **HOẢNG LOẠN** — vol cực đại")
        lines.append("- 🛑 Giảm size xuống 0.25x hoặc đứng ngoài")
        lines.append("- Nếu trade: stop 2x ATR, tìm capitulation wick")
        lines.append("- Không hold qua đêm nếu eclipse window đang mở")
    lines.append("")
    
    # Risk levels
    lines.append("### Mức giá quan trọng:")
    close = float(row['gold_close'])
    
    # Calculate key levels
    try:
        gann_ns = float(row['gann_nearest_support'])
        gann_nr = float(row['gann_nearest_resistance'])
        lines.append(f"| Vùng | Giá |")
        lines.append(f"|------|-----|")
        lines.append(f"| **Resistance** | ${gann_nr:.1f} |")
        lines.append(f"| **Close** | ${close:.1f} |")
        lines.append(f"| **Support** | ${gann_ns:.1f} |")
        
        # Calc risk
        risk_long = close - gann_ns
        reward_long = gann_nr - close
        lines.append(f"| **Risk (Long)** | ${risk_long:.1f} |")
        lines.append(f"| **Reward (Long)** | ${reward_long:.1f} |")
        if risk_long > 0:
            lines.append(f"| **R:R (Long)** | {reward_long/risk_long:.1f}:1 |")
    except:
        pass
    
    lines.append("")
    
    # ─── FOOTER ───
    lines.append("---")
    lines.append("")
    lines.append(f"*Bản tin được tạo tự động bởi Astro-Quant Engine — {date_str}*")
    lines.append(f"*Framework v1.0 | Backtest: 1,103 ngày | Win rate: LONG 78% / SHORT 85%*")
    lines.append(f"*⚠️ Không phải lời khuyên đầu tư. Luôn quản lý rủi ro.*")
    
    post = "\n".join(lines)
    
    if verbose:
        # Print additional debug info
        print("\n" + "="*80)
        print("DEBUG: Scorer Details")
        print("="*80)
        print(json.dumps(result['details'], indent=2, ensure_ascii=False))
        print(f"\nRaw Score: {result['raw_score']}/{result['max_possible']}")
        print(f"Regime: {result['volatility_regime']}")
    
    return post


# ─── MAIN ───
if __name__ == "__main__":
    verbose = "--verbose" in sys.argv
    
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('--'):
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    post = generate_post(date_str, verbose=verbose)
    
    if post:
        # Write to file
        out_path = Path(os.path.dirname(__file__)) / f"PATREON_POST_{date_str}.md"
        out_path.write_text(post)
        
        # Print to console
        print(post)
        print(f"\n✅ Post saved to: {out_path}")
    else:
        print(f"Error: Could not generate post for {date_str}", file=sys.stderr)
        sys.exit(1)
