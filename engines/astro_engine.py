"""
astro_engine.py — Deep Vedic Astrology Analysis for Gold (XAUUSD) Trading

Analyzes raw planetary transit data and produces professional-grade astrological
interpretations specifically tailored for gold price analysis.

Follows Kim Ssa's framework:
- Moon sign + nakshatra → market sentiment & trading style
- Lunar phase → bullish/bearish bias
- Planetary hour → current energy for trading
- Aspects (tight orb) → key volatility signals
- Combust analysis → weakened planetary signals
- Next hora → forward-looking timing
"""

import math
from datetime import datetime, timedelta
import pytz


# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────

# Zodiac signs (sidereal, with ayanamsa already applied by API)
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
}

# Vietnamese sign names
SIGN_NAMES_VI = {
    "Aries": "Bạch Dương", "Taurus": "Kim Ngưu", "Gemini": "Song Tử", "Cancer": "Cự Giải",
    "Leo": "Sư Tử", "Virgo": "Xử Nữ", "Libra": "Thiên Bình", "Scorpio": "Thiên Yết",
    "Sagittarius": "Nhân Mã", "Capricorn": "Ma Kết", "Aquarius": "Bảo Bình", "Pisces": "Song Ngư"
}

# Nakshatra lord → trading personality
NAKSHATRA_LORD_TRADING = {
    "Sun": "Quyết đoán, trend-following, phù hợp breakout trades. Vàng được hỗ trợ bởi chính sách/chính phủ.",
    "Moon": "Cảm xúc cao, dễ FOMO/panic. Phù hợp fade trades tại extreme sentiment.",
    "Mars": "Mạnh mẽ, aggressive momentum. Phù hợp breakout & scalp. Cảnh báo sharp reversals.",
    "Mercury": "Biến động nhanh, news-driven. Phù hợp short-term trading, scalping.",
    "Jupiter": "Mở rộng, liquidity cao. Phù hợp swing trades, hold positions. Xu hướng bullish.",
    "Venus": "Định giá, comfort zone. Phù hợp range trading. Cảnh báo complacency.",
    "Saturn": "Phòng thủ, bảo toàn vốn. Phù hợp hold hơn trade aggressive. Slow grind.",
    "Rahu": "Bất ngờ, disruptive, extreme moves. Phù hợp counter-trend. Cảnh báo fakeouts.",
    "Ketu": "Tâm linh, detachment. Thị trường thiếu direction rõ ràng. Phù hợp wait-and-see.",
}

# Aspect type → gold trading interpretation
ASPECT_MEANINGS = {
    "Conjunction": {
        "symbol": "☌",
        "description": "Năng lượng hành tinh hợp nhất — tác động nhân lên, rất mạnh.",
        "gold_impact": "Hợp nhất với Sun (ruler vàng) = tác động trực tiếp lên giá vàng. Hợp nhất với các hành tinh khác = năng lượng kết hợp chi phối thị trường."
    },
    "Opposition": {
        "symbol": "☍",
        "description": "Đối kháng — căng thẳng cực đại, dễ có sudden reversal hoặc flash event.",
        "gold_impact": "Opposition với Moon = biến động cảm xúc cực đoan (panic buying/selling). Opposition với Sun = áp lực ngược chiều lên vàng."
    },
    "Square": {
        "symbol": "□",
        "description": "Thách thức — ma sát, khó khăn, cần hành động để vượt qua.",
        "gold_impact": "Square tạo áp lực lên giá vàng, dễ có false breakouts và whipsaw. Cần cảnh giác với stop hunts."
    },
    "Trine": {
        "symbol": "⚹",
        "description": "Hài hòa — năng lượng chảy mượt, hỗ trợ xu hướng hiện tại.",
        "gold_impact": "Trine hỗ trợ trend-following. Vàng có thể di chuyển ổn định theo xu hướng. Tuy nhiên, trine quá dễ dãi có thể tạo 'ảo tưởng' về xu hướng."
    },
    "Sextile": {
        "symbol": "⚺",
        "description": "Cơ hội — hợp tác nhẹ nhàng, mở cửa cho trades có tính toán.",
        "gold_impact": "Sextile tạo cơ hội entry tốt. Vàng có nhịp điều chỉnh lành mạnh, phù hợp buy the dip / sell the rally."
    },
}

# Combust thresholds (degrees from Sun)
COMBUST_THRESHOLDS = {
    "MERCURY": 2,    # Combust within 2° of Sun
    "VENUS": 4,      # Combust within 4° of Sun
    "MARS": 8,       # Combust within 8° of Sun
    "JUPITER": 8,    # Combust within 8° of Sun
    "SATURN": 8,     # Combust within 8° of Sun
}

COMBUST_MEANINGS = {
    "MERCURY": "Tín hiệu ngắn hạn (news, data, volatility) bị yếu đi. Dễ có mispricing, gap, hoặc slippage. Không nên trade dựa trên tin tức ngắn hạn.",
    "VENUS": "Định giá thị trường bị méo. Dễ có extreme greed/fear không phản ánh fundamentals. Cảnh báo valuation traps.",
    "MARS": "Năng lượng đột biến bị kiềm tỏa. Khi Mars combust, thị trường có thể 'tích lũy' năng lượng và bùng nổ bất ngờ.",
    "JUPITER": "Thanh khoản và mở rộng bị suy yếu. Thị trường thiếu liquidity, dễ có gaps. Không nên kỳ vọng trend mạnh.",
    "SATURN": "Áp lực và kháng cự bị ẩn. Khó nhìn thấy阻力 rõ ràng, dễ bị bất ngờ bởi các level break.",
}

# Moon sign → market sentiment
MOON_SIGN_SENTIMENT = {
    "Aries": "Cảm xúc thị trường nóng vội, dễ FOMO. Phù hợp momentum trades nhưng cảnh báo burnout nhanh.",
    "Taurus": "Ổn định, kiên nhẫn. Thị trường có xu hướng trend bền. Phù hợp hold positions.",
    "Gemini": "Biến động, phân mảnh. Thị trường khó đọc, dễ switch direction nhanh. Phù hợp range trading.",
    "Cancer": "Cảm xúc cao, dễ panic selling và buying mạnh. Moon trong Cancer = market sentiment chi phối price action.",
    "Leo": "Tự tin, bullish bias. Thị trường có xu hướng optimistic. Phù hợp trend-following.",
    "Virgo": "Phân tích kỹ, cẩn trọng. Thị trường choppy, detail-oriented. Phù hợp precision entries.",
    "Libra": "Cân bằng, range-bound. Thị trường tìm equilibrium. Phù hợp buy support / sell resistance.",
    "Scorpio": "Sâu sắc, transformative. Thị trường có thể có hidden moves, sudden reversals. Phù hợp contrarian.",
    "Sagittarius": "Mở rộng, optimistic. Thị trường có xu hướng expand. Phù hợp swing trades.",
    "Capricorn": "Kỷ luật, structure. Thị trường respect technical levels. Phù hợp systematic trading.",
    "Aquarius": "Bất ngờ, disruptive. Thị trường có thể có moves không theo pattern. Phù hợp counter-trend.",
    "Pisces": "Mơ hồ, intuitive. Thị trường khó xác định direction rõ ràng. Cảnh báo false signals.",
}

# Chaldean order for hora
CHALDEAN_ORDER = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']

# Hora trading implications
HORA_TRADING = {
    "Sun": {
        "emoji": "☀️",
        "gold_impact": "TỐT CHO VÀNG. Sun = ruler của Gold. Sun Hora = năng lượng vàng mạnh nhất. Phù hợp entry positions, stable trades, follow institutional flow.",
        "trading_style": "Trend-following, institutional moves. Giá vàng thường có nhịp mạnh và rõ direction.",
        "caution": "Có thể quá self-confident — luôn dùng stop loss."
    },
    "Moon": {
        "emoji": "🌙",
        "gold_impact": "CẢM XÚC CAO. Moon = sentiment. Moon Hora = thị trường dễ bị FOMO/panic. Phù hợp fade extremes, không nên chase trend.",
        "trading_style": "Counter-sentiment, fade extremes. Watch for emotional overreactions.",
        "caution": "Rất dễ bị nhiễu tâm lý. Tránh trade nếu không có clear plan."
    },
    "Mars": {
        "emoji": "♂️",
        "gold_impact": "MẠNH & VOLATILE. Mars = đột biến, kim loại. Mars Hora = năng lượng mạnh cho momentum trading. Phù hợp breakout & scalp.",
        "trading_style": "Aggressive momentum, breakout trading. Giá có thể di chuyển nhanh.",
        "caution": "Dễ bị sharp reversals. Tight stops, không hold quá lâu."
    },
    "Mercury": {
        "emoji": "☿️",
        "gold_impact": "BIẾN ĐỘNG NGẮN HẠN. Mercury = news, data, speed. Mercury Hora = thị trường nhạy với tin tức. Phù hợp scalping, short-term trades.",
        "trading_style": "Scalping, news trading, quick entries/exits.",
        "caution": "Signal noise cao. Không nên hold qua Mercury Hora."
    },
    "Jupiter": {
        "emoji": "♃",
        "gold_impact": "MỞ RỘNG & THANH KHOẢN. Jupiter = expansion, liquidity. Jupiter Hora = thị trường có liquidity tốt, xu hướng rõ. Phù hợp swing trades, hold.",
        "trading_style": "Swing trading, position building. Xu hướng thường bền.",
        "caution": "Có thể quá optimistic — watch for FOMO tops."
    },
    "Venus": {
        "emoji": "♀️",
        "gold_impact": "ĐỊNH GIÁ & COMFORT. Venus = valuation, greed/fear. Venus Hora = thị trường trong comfort zone. Phù hợp range trading, avoid breakout trades.",
        "trading_style": "Range trading, mean-reversion. Giá thường oscillate.",
        "caution": "Dễ bị false breakouts. Tránh breakout trading trong Venus Hora."
    },
    "Saturn": {
        "emoji": "♄",
        "gold_impact": "ÁP LỰC & KHÁNG CỰ. Saturn = resistance, karma. Saturn Hora = thị trường bị kìm nén, low liquidity. Phù hợp hold, avoid aggressive entries.",
        "trading_style": "Defensive, hold positions, wait for clarity. Slow grind.",
        "caution": "Thị trường có thể 'đóng băng' — không nên force trades."
    },
}


# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────

def normalize_angle(deg):
    """Normalize angle to 0-360 range."""
    return deg % 360


def angular_distance(a, b):
    """Calculate the shortest angular distance between two angles (0-180)."""
    diff = abs(normalize_angle(a) - normalize_angle(b))
    return min(diff, 360 - diff)


def is_combust(planet_name, planet_longitude, sun_longitude):
    """Check if a planet is combust (too close to the Sun)."""
    threshold = COMBUST_THRESHOLDS.get(planet_name)
    if threshold is None:
        return False, 0
    distance = angular_distance(planet_longitude, sun_longitude)
    return distance <= threshold, distance


def calculate_lunar_phase(sun_longitude, moon_longitude):
    """
    Calculate lunar phase based on angular distance between Sun and Moon.
    Returns phase name, emoji, and trading bias.
    """
    elongation = normalize_angle(moon_longitude - sun_longitude)

    if elongation < 22.5:
        return "🌑 New Moon", "Bullish setup — khởi đầu chu kỳ mới. Buy dips, build positions."
    elif elongation < 67.5:
        return "🌒 Waxing Crescent", "Bullish — Buy dips. Xu hướng tăng đang tích lũy năng lượng."
    elif elongation < 112.5:
        return "🌓 First Quarter", "Crisis/Action — Thị trường cần quyết định. Breakout hoặc reversal."
    elif elongation < 157.5:
        return "🌔 Waxing Gibbous", "Bullish nhưng caution — Thị trường đang ở đỉnh, watch for exhaustion."
    elif elongation < 202.5:
        return "🌕 Full Moon", "Extreme sentiment — Dấu hiệu đỉnh chu kỳ. Cảnh báo reversal hoặc climax."
    elif elongation < 247.5:
        return "🌖 Waning Gibbous", "Bearish setup — Sell rallies. Xu hướng giảm đang tích lũy."
    elif elongation < 292.5:
        return "🌗 Last Quarter", "Crisis/Re-evaluation — Thị trường reconsider direction."
    elif elongation < 337.5:
        return "🌘 Waning Crescent", "Bearish — Thị trường yếu, avoid new longs. Wait for New Moon."
    else:
        return "🌑 New Moon", "Bullish setup — khởi đầu chu kỳ mới. Buy dips, build positions."


def calculate_next_hora(current_dt, hora_info, lat=10.85, lon=106.75, tz_name="Asia/Ho_Chi_Minh"):
    """
    Calculate the next planetary hour after the current one.
    Returns hora name and start time.
    """
    from astral import LocationInfo
    from astral.sun import sun

    tz = pytz.timezone(tz_name)
    location = LocationInfo("Ho Chi Minh", "Vietnam", tz_name, lat, lon)

    if current_dt.tzinfo is None:
        current_dt = tz.localize(current_dt)

    s = sun(location.observer, date=current_dt.date(), tzinfo=tz)
    sunrise = s['sunrise']
    sunset = s['sunset']

    # Determine if current time is in day or night period
    if current_dt < sunrise:
        # Pre-dawn: in yesterday's night period
        yesterday = current_dt.date() - timedelta(days=1)
        s_yest = sun(location.observer, date=yesterday, tzinfo=tz)
        period_start = s_yest['sunset']
        period_end = sunrise
        is_daytime = False
        astro_day_index = yesterday.weekday()
    elif current_dt < sunset:
        period_start = sunrise
        period_end = sunset
        is_daytime = True
        astro_day_index = current_dt.date().weekday()
    else:
        period_start = sunset
        s_tom = sun(location.observer, date=current_dt.date() + timedelta(days=1), tzinfo=tz)
        period_end = s_tom['sunrise']
        is_daytime = False
        astro_day_index = current_dt.date().weekday()

    total_seconds = (period_end - period_start).total_seconds()
    hora_length = total_seconds / 12.0

    ruler_of_day = VedicHoraEngine.DAY_RULERS[astro_day_index]
    start_index = CHALDEAN_ORDER.index(ruler_of_day)

    if is_daytime:
        elapsed = (current_dt - sunrise).total_seconds()
    else:
        elapsed = (current_dt - period_start).total_seconds()

    current_hora_index = int(elapsed // hora_length)
    next_hora_index = current_hora_index + 1

    if next_hora_index >= 12:
        # Next period — we'd need to calculate, but for simplicity return "next period"
        next_hora_index = 0
        if is_daytime:
            next_start = sunset
        else:
            next_start = sunrise  # today's sunrise (we're in night, next day starts at sunrise)
    else:
        if is_daytime:
            next_start = sunrise + timedelta(seconds=next_hora_index * hora_length)
        else:
            next_start = period_start + timedelta(seconds=next_hora_index * hora_length)

    next_hora_total = next_hora_index if is_daytime else 12 + next_hora_index
    next_ruler_index = (start_index + next_hora_total) % 7
    next_ruler = CHALDEAN_ORDER[next_ruler_index]

    return {
        "next_hora": next_ruler,
        "next_hora_start": next_start.strftime("%H:%M UTC+7"),
    }


class VedicHoraEngine:
    """Minimal hora engine reference for next_hora calculation."""
    CHALDEAN_ORDER = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
    DAY_RULERS = {
        0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter',
        4: 'Venus', 5: 'Saturn', 6: 'Sun'
    }


# ──────────────────────────────────────────────
# MAIN ANALYSIS ENGINE
# ──────────────────────────────────────────────

class AstroEngine:
    """
    Deep Vedic astrology analysis for gold trading.
    Takes raw planetary data from Vedic API and produces professional analysis.
    """

    def __init__(self, planets_data, hora_info, current_dt):
        """
        planets_data: list of planet dicts from Vedic API
        hora_info: dict from VedicHoraEngine.calculate_hora()
        current_dt: datetime object
        """
        self.planets = {p['planet']: p for p in planets_data}
        self.hora_info = hora_info
        self.current_dt = current_dt
        self.sun_longitude = self.planets.get('SUN', {}).get('longitude', 0)

    def analyze_moon(self):
        """Deep Moon analysis: sign, nakshatra, phase, trading implications."""
        moon = self.planets.get('MOON')
        if not moon:
            return {"error": "No Moon data"}

        sign_name = moon['sign']['name']
        sign_deg = moon['sign']['longitude']
        sign_mins = moon['sign']['minutes']
        nakshatra = moon['nakshatra']
        nak_lord = nakshatra['lord']
        nak_pada = nakshatra['pada']
        nak_name = nakshatra['name']

        # Lunar phase
        sun_lon = self.sun_longitude
        moon_lon = moon['longitude']
        phase_name, phase_bias = calculate_lunar_phase(sun_lon, moon_lon)

        # Build analysis
        analysis = {
            "moon_sign": f"{ZODIAC_SYMBOLS.get(sign_name, '')} {SIGN_NAMES_VI.get(sign_name, sign_name)} ({sign_deg}°{sign_mins}'')",
            "nakshatra": f"{nak_name} (chủ tinh {nak_lord}) — Pada {nak_pada}",
            "lunar_phase": phase_name,
            "lunar_bias": phase_bias,
            "sentiment": MOON_SIGN_SENTIMENT.get(sign_name, ""),
            "nakshatra_trading": NAKSHATRA_LORD_TRADING.get(nak_lord, ""),
            "trading_summary": (
                f"Moon trong {SIGN_NAMES_VI.get(sign_name, sign_name)} → {MOON_SIGN_SENTIMENT.get(sign_name, '')}\n"
                f"{nak_name} Nakshatra (chủ tinh {nak_lord}): {NAKSHATRA_LORD_TRADING.get(nak_lord, '')}\n"
                f"Lunar Phase {phase_name} → {phase_bias}"
            )
        }
        return analysis

    def analyze_hora(self):
        """Analyze current and next planetary hour."""
        current_hora = self.hora_info.get('hora', '')
        hora_data = HORA_TRADING.get(current_hora, {})

        # Next hora
        next_info = calculate_next_hora(self.current_dt, self.hora_info)
        next_hora = next_info.get('next_hora', '')
        next_hora_data = HORA_TRADING.get(next_hora, {})

        return {
            "current_hora": current_hora,
            "current_hora_emoji": hora_data.get('emoji', ''),
            "current_hora_impact": hora_data.get('gold_impact', ''),
            "current_hora_style": hora_data.get('trading_style', ''),
            "current_hora_caution": hora_data.get('caution', ''),
            "next_hora": next_hora,
            "next_hora_emoji": next_hora_data.get('emoji', ''),
            "next_hora_start": next_info.get('next_hora_start', ''),
            "next_hora_impact": next_hora_data.get('gold_impact', ''),
        }

    def analyze_aspects(self):
        """
        Analyze all planetary aspects, filtered by orb tightness.
        Prioritize tight aspects (≤3°), then moderate (3-5°).
        Focus on aspects involving Sun, Moon, Mars, Mercury, Venus, Jupiter, Saturn.
        """
        key_planets = {'SUN', 'MOON', 'MARS', 'MERCURY', 'VENUS', 'JUPITER', 'SATURN', 'URANUS', 'NEPTUNE', 'PLUTO', 'RAHU', 'KETU'}
        planet_symbols = {
            'SUN': '☀️', 'MOON': '🌙', 'MARS': '♂️', 'MERCURY': '☿️',
            'VENUS': '♀️', 'JUPITER': '♃', 'SATURN': '♄', 'URANUS': '♅',
            'NEPTUNE': '♆', 'PLUTO': '♇', 'RAHU': '☊', 'KETU': '☋'
        }
        planet_names_vi = {
            'SUN': 'Mặt Trời', 'MOON': 'Mặt Trăng', 'MARS': 'Sao Hỏa', 'MERCURY': 'Sao Thủy',
            'VENUS': 'Sao Kim', 'JUPITER': 'Sao Mộc', 'SATURN': 'Sao Thổ', 'URANUS': 'Sao Thiên Vương',
            'NEPTUNE': 'Sao Hải Vương', 'PLUTO': 'Sao Diêm Vương', 'RAHU': 'La Hầu', 'KETU': 'Ketu'
        }

        all_aspects = []

        for planet_name, planet_data in self.planets.items():
            if planet_name not in key_planets:
                continue
            aspects = planet_data.get('aspects', [])
            for aspect in aspects:
                target = aspect['planet']
                if target not in key_planets:
                    continue
                # Avoid duplicates (A aspects B = B aspects A)
                if planet_name > target:
                    continue

                orb = aspect['orb']
                aspect_type = aspect['aspect']

                # Only include aspects within 8° orb
                if orb > 8:
                    continue

                # Skip Rahu-Ketu opposition (they're always 180° apart — always true, no trading signal)
                if {planet_name, target} == {'RAHU', 'KETU'} and aspect_type == 'Opposition':
                    continue

                all_aspects.append({
                    "planet1": planet_name,
                    "planet2": target,
                    "aspect_type": aspect_type,
                    "orb": orb,
                    "tightness": "VERY TIGHT" if orb <= 1 else ("TIGHT" if orb <= 3 else ("MODERATE" if orb <= 5 else "WIDE")),
                })

        # Sort by orb (tightest first)
        all_aspects.sort(key=lambda x: x['orb'])

        return all_aspects

    def analyze_combust(self):
        """Check which planets are combust (too close to the Sun)."""
        combust_planets = []
        for planet_name, threshold in COMBUST_THRESHOLDS.items():
            planet_data = self.planets.get(planet_name)
            if not planet_data:
                continue
            planet_lon = planet_data.get('longitude', 0)
            is_c, distance = is_combust(planet_name, planet_lon, self.sun_longitude)
            if is_c:
                combust_planets.append({
                    "planet": planet_name,
                    "distance": round(distance, 2),
                    "threshold": threshold,
                    "meaning": COMBUST_MEANINGS.get(planet_name, ""),
                })
        return combust_planets

    def analyze_retrograde(self):
        """Check for retrograde planets."""
        retro = []
        for planet_name, planet_data in self.planets.items():
            if planet_data.get('isRetrograde', False):
                sign = planet_data['sign']['name']
                deg = planet_data['sign']['longitude']
                mins = planet_data['sign']['minutes']
                retro.append({
                    "planet": planet_name,
                    "position": f"{SIGN_NAMES_VI.get(sign, sign)} {deg}°{mins}'",
                    "note": self._retrograde_meaning(planet_name),
                })
        return retro

    def _retrograde_meaning(self, planet_name):
        meanings = {
            "MERCURY": "Mercury nghịch hành → communication, data, news có thể bị nhiễu. Cảnh báo mispricing.",
            "VENUS": "Venus nghịch hành → valuation bị đảo ngược. Market sentiment trái với fundamentals.",
            "MARS": "Mars nghịch hành → năng lượng bị hướng nội, dễ có sudden bursts khi Mars thuận hành lại.",
            "JUPITER": "Jupiter nghịch hành → expansion bị chậm lại, liquidity giảm.",
            "SATURN": "Saturn nghịch hành → áp lực tích lũy, resistance có thể break bất ngờ.",
            "PLUTO": "Pluto nghịch hành → transformation chậm, power shifts dưới surface.",
            "RAHU": "Rahu nghịch hành → disruption bị hướng nội, năng lượng shadow tăng. Cảnh báo hidden risks, shadow moves.",
            "KETU": "Ketu nghịch hành → detachment bị hướng nội, spiritual energy tăng. Thị trường thiếu clear direction.",
        }
        return meanings.get(planet_name, f"{planet_name} nghịch hành → năng lượng bị hướng nội.")

    def get_gold_specific_analysis(self):
        """
        Synthesize all analysis into gold-specific trading implications.
        This is the core output — how ALL factors combine to affect XAUUSD.
        """
        moon = self.analyze_moon()
        hora = self.analyze_hora()
        aspects = self.analyze_aspects()
        combust = self.analyze_combust()
        retro = self.analyze_retrograde()

        # Sun is ruler of gold — check Sun aspects
        sun_aspects = [a for a in aspects if a['planet1'] == 'SUN' or a['planet2'] == 'SUN']
        moon_aspects = [a for a in aspects if a['planet1'] == 'MOON' or a['planet2'] == 'MOON']

        # Check if Sun is conjunct Uranus (disruption to gold)
        sun_uranus = [a for a in aspects if ('SUN' in [a['planet1'], a['planet2']]) and
                      ('URANUS' in [a['planet1'], a['planet2']]) and a['aspect_type'] == 'Conjunction']

        # Check Moon-Pluto opposition (extreme volatility)
        moon_pluto = [a for a in aspects if ('MOON' in [a['planet1'], a['planet2']]) and
                      ('PLUTO' in [a['planet1'], a['planet2']]) and a['aspect_type'] == 'Opposition']

        return {
            "moon": moon,
            "hora": hora,
            "aspects": aspects,
            "combust": combust,
            "retrograde": retro,
            "sun_aspects": sun_aspects,
            "moon_aspects": moon_aspects,
            "sun_uranus_conjunction": len(sun_uranus) > 0,
            "moon_pluto_opposition": len(moon_pluto) > 0,
        }

    def format_report(self):
        """
        Generate the full professional astrological analysis report.
        Format matches the reference sample from the other channel.
        """
        analysis = self.get_gold_specific_analysis()
        moon = analysis['moon']
        hora = analysis['hora']
        aspects = analysis['aspects']
        combust = analysis['combust']
        retro = analysis['retrograde']

        # ── Moon Section ──
        # Get moon sign name for display
        moon_data = self.planets.get('MOON', {})
        moon_sign_name = moon_data.get('sign', {}).get('name', '')

        report = "🌌 PHÂN TÍCH THIÊN VĂN (VEDIC ASTROLOGY)\n"
        report += f"• Moon: {moon.get('moon_sign', 'N/A')} — {moon.get('nakshatra', 'N/A')}\n\n"

        report += f"• Moon trong {SIGN_NAMES_VI.get(moon_sign_name, moon_sign_name)} → {moon.get('sentiment', '')}\n"
        # Extract nakshatra lord for description
        nak_info = moon.get('nakshatra', '')
        report += f"• {nak_info} → {moon.get('nakshatra_trading', '')}\n"

        report += f"• Lunar Phase: {moon.get('lunar_phase', 'N/A')} — \"{moon.get('lunar_bias', '')}\"\n"

        # ── Hora Section ──
        report += f"• Planetary Hour hiện tại: {hora.get('current_hora_emoji', '')} {hora.get('current_hora', 'N/A')} — {hora.get('current_hora_impact', '')}\n"
        report += f"• Sắp tới: {hora.get('next_hora_emoji', '')} {hora.get('next_hora', 'N/A')} hour ({hora.get('next_hora_start', '')}) — {hora.get('next_hora_impact', '')}\n"

        # ── Aspects Section ──
        # Show only Conjunction, Opposition, Square (skip Sextile — too common)
        important_aspects = [a for a in aspects if a['orb'] <= 5 and a['aspect_type'] in ('Conjunction', 'Opposition', 'Square')]
        if important_aspects:
            report += "\n⚡ Aspects quan trọng:\n"
            for a in important_aspects:
                p1 = a['planet1']
                p2 = a['planet2']
                aspect_type = a['aspect_type']
                orb = a['orb']
                tightness = a['tightness']

                symbol = ASPECT_MEANINGS.get(aspect_type, {}).get('symbol', '')
                p1_sym = {'SUN': '☀️', 'MOON': '🌙', 'MARS': '♂️', 'MERCURY': '☿️',
                          'VENUS': '♀️', 'JUPITER': '♃', 'SATURN': '♄', 'URANUS': '♅',
                          'NEPTUNE': '♆', 'PLUTO': '♇', 'RAHU': '☊', 'KETU': '☋'}.get(p1, p1)
                p2_sym = {'SUN': '☀️', 'MOON': '🌙', 'MARS': '♂️', 'MERCURY': '☿️',
                          'VENUS': '♀️', 'JUPITER': '♃', 'SATURN': '♄', 'URANUS': '♅',
                          'NEPTUNE': '♆', 'PLUTO': '♇', 'RAHU': '☊', 'KETU': '☋'}.get(p2, p2)

                orb_desc = f"orb {orb:.2f}° — {tightness}"

                # Gold-specific interpretation
                interpretation = self._interpret_aspect_for_gold(p1, p2, aspect_type, orb, tightness)

                report += f"• {symbol} {p1_sym} {aspect_type} {p2_sym} ({orb_desc}) → {interpretation[:180]}\n"

        # ── Combust Section ──
        if combust:
            report += "\n🔥 Combust (Hành tinh quá gần Mặt Trời):\n"
            for c in combust:
                planet_sym = {'SUN': '☀️', 'MOON': '🌙', 'MARS': '♂️', 'MERCURY': '☿️',
                              'VENUS': '♀️', 'JUPITER': '♃', 'SATURN': '♄'}.get(c['planet'], c['planet'])
                planet_vi = {'MERCURY': 'Sao Thủy', 'VENUS': 'Sao Kim', 'MARS': 'Sao Hỏa',
                             'JUPITER': 'Sao Mộc', 'SATURN': 'Sao Thổ'}.get(c['planet'], c['planet'])
                report += f"• {planet_sym} {planet_vi} Combust (cách Sun {c['distance']}°) → {c['meaning']}\n"

        # ── Retrograde Section ──
        # Skip Rahu (always retrograde by definition) — only show other retrograde planets
        retro = [r for r in retro if r['planet'] != 'RAHU']
        if retro:
            report += "\n🔄 Hành tinh nghịch hành:\n"
            for r in retro:
                planet_sym = {'MERCURY': '☿️', 'VENUS': '♀️', 'MARS': '♂️',
                              'JUPITER': '♃', 'SATURN': '♄', 'PLUTO': '♇'}.get(r['planet'], r['planet'])
                planet_vi = {'MERCURY': 'Sao Thủy', 'VENUS': 'Sao Kim', 'MARS': 'Sao Hỏa',
                             'JUPITER': 'Sao Mộc', 'SATURN': 'Sao Thổ', 'PLUTO': 'Sao Diêm Vương',
                             'RAHU': 'Rahu', 'KETU': 'Ketu'}.get(r['planet'], r['planet'])
                report += f"• {planet_sym} {planet_vi} nghịch hành ở {r['position']} → {r['note']}\n"

        # ── Position Summary ──
        # Show key trading planets + Rahu/Ketu
        report += "\n📍 Vị trí Hành Tinh (Transits):\n"
        planet_order = ['SUN', 'MOON', 'MERCURY', 'VENUS', 'MARS', 'JUPITER', 'SATURN', 'RAHU', 'KETU']
        planet_symbols_short = {
            'SUN': '☀️', 'MOON': '🌙', 'MERCURY': '☿️', 'VENUS': '♀️',
            'MARS': '♂️', 'JUPITER': '♃', 'SATURN': '♄', 'RAHU': '☊', 'KETU': '☋'
        }
        planet_rolerships = {
            'SUN': 'Vàng', 'MOON': 'Cảm xúc', 'MERCURY': 'Biến động ngắn hạn', 'VENUS': 'Định giá',
            'MARS': 'Đột biến', 'JUPITER': 'Thanh khoản', 'SATURN': 'Áp lực',
            'RAHU': 'Disruption', 'KETU': 'Detachment'
        }
        for p in planet_order:
            if p in self.planets:
                pd = self.planets[p]
                sign = pd['sign']['name']
                deg = pd['sign']['longitude']
                mins = pd['sign']['minutes']
                retro_mark = " (R)" if pd.get('isRetrograde') else ""
                sym = planet_symbols_short.get(p, '')
                role = planet_rolerships.get(p, '')
                report += f"• {sym} {p} ({role}): {SIGN_NAMES_VI.get(sign, sign)} {deg}°{mins}'{retro_mark}\n"

        return report

    def _interpret_aspect_for_gold(self, p1, p2, aspect_type, orb, tightness):
        """
        Generate gold-specific interpretation for any aspect combination.
        This is the AI reasoning layer — connecting planetary geometry to XAUUSD price action.
        """
        p1_role = {
            'SUN': 'ruler của vàng',
            'MOON': 'cảm xúc thị trường',
            'MARS': 'biến động đột biến',
            'MERCURY': 'tin tức, dữ liệu ngắn hạn',
            'VENUS': 'định giá thị trường',
            'JUPITER': 'thanh khoản, mở rộng',
            'SATURN': 'kháng cự, áp lực',
            'URANUS': 'bất ngờ, disruption',
            'NEPTUNE': 'ảo tưởng, signal noise',
            'PLUTO': 'transformation, power shift',
            'RAHU': 'disruption, extreme moves',
            'KETU': 'detachment, thiếu direction',
        }

        p1_desc = p1_role.get(p1, p1)
        p2_desc = p1_role.get(p2, p2)

        # Key gold combinations
        if p1 == 'SUN' and p2 == 'URANUS' and aspect_type == 'Conjunction':
            return f"Vàng chịu ảnh hưởng bởi biến động bất ngờ, sudden spikes. Sun = {p1_desc}, Uranus = {p2_desc}. Aspect này tạo sudden price action — dễ có flash rally/crash."

        if (p1 == 'MOON' and p2 == 'PLUTO' and aspect_type == 'Opposition') or \
           (p1 == 'PLUTO' and p2 == 'MOON' and aspect_type == 'Opposition'):
            return f"Dấu hiệu biến động cực mạnh, dễ có sudden reversal hoặc flash crash/rally. Moon = {p1_desc}, Pluto = {p2_desc}. Đây là aspect NGUY HIỂM nhất."

        if p1 == 'MOON' and p2 == 'PLUTO' and aspect_type == 'Opposition':
            return f"Biến động cực mạnh — cảm xúc thị trường bị transformation. Dễ có panic selling/buying."

        if (p1 == 'MOON' and p2 == 'SATURN' and aspect_type == 'Trine') or \
           (p1 == 'SATURN' and p2 == 'MOON' and aspect_type == 'Trine'):
            return f"Hỗ trợ sentiment phòng thủ, thị trường có structure. Phù hợp hold hơn trade aggressive."

        if (p1 == 'MOON' and p2 == 'NEPTUNE' and aspect_type == 'Trine') or \
           (p1 == 'NEPTUNE' and p2 == 'MOON' and aspect_type == 'Trine'):
            return f"Hỗ trợ sentiment tích cực, nhưng cũng dễ 'ảo tưởng' về xu hướng. Neptune = {p2_desc}."

        if (p1 == 'MOON' and p2 == 'MERCURY' and aspect_type == 'Sextile') or \
           (p1 == 'MERCURY' and p2 == 'MOON' and aspect_type == 'Sextile'):
            return f"Thông tin và cảm xúc hỗ trợ nhau. Cơ hội entry tốt khi có news catalyst."

        if (p1 == 'VENUS' and p2 == 'NEPTUNE' and aspect_type == 'Square') or \
           (p1 == 'NEPTUNE' and p2 == 'VENUS' and aspect_type == 'Square'):
            return f"Tín hiệu giả, dễ bị lừa bởi false breakouts. Venus = {p1_desc}, Neptune = {p2_desc}."

        if (p1 == 'VENUS' and p2 == 'MARS' and aspect_type == 'Sextile') or \
           (p1 == 'MARS' and p2 == 'VENUS' and aspect_type == 'Sextile'):
            return f"Năng lượng tích cực cho gold — Venus (định giá) hỗ trợ Mars (momentum). Cơ hội cho momentum trades."

        if (p1 == 'SUN' and p2 == 'RAHU' and aspect_type == 'Square') or \
           (p1 == 'RAHU' and p2 == 'SUN' and aspect_type == 'Square'):
            return f"Áp lực disruption lên vàng. Rahu = {p2_desc}. Dễ có moves bất ngờ, counter-trend."

        if (p1 == 'MARS' and p2 == 'PLUTO' and aspect_type == 'Square') or \
           (p1 == 'PLUTO' and p2 == 'MARS' and aspect_type == 'Square'):
            return f"Áp lực biến động cực mạnh. Mars + Pluto = năng lượng tích tụ, dễ bùng nổ. Cảnh báo sharp moves."

        if (p1 == 'SUN' and p2 == 'NEPTUNE' and aspect_type == 'Sextile') or \
           (p1 == 'NEPTUNE' and p2 == 'SUN' and aspect_type == 'Sextile'):
            return f"Vàng có nhịp hỗ trợ từ sentiment mơ hồ. Neptune = {p2_desc}. Có thể có safe-haven flow."

        if (p1 == 'SUN' and p2 == 'PLUTO' and aspect_type == 'Trine') or \
           (p1 == 'PLUTO' and p2 == 'SUN' and aspect_type == 'Trine'):
            return f"Vàng trong quá trình transformation nhưng hài hòa. Power shift chậm nhưng bền. Phù hợp hold positions."

        if (p1 == 'MERCURY' and p2 == 'SATURN' and aspect_type == 'Sextile') or \
           (p1 == 'SATURN' and p2 == 'MERCURY' and aspect_type == 'Sextile'):
            return f"Thông tin được filter qua lăng kính thận trọng. Thị trường chậm nhưng có structure."

        if (p1 == 'MERCURY' and p2 == 'URANUS' and aspect_type == 'Conjunction') or \
           (p1 == 'URANUS' and p2 == 'MERCURY' and aspect_type == 'Conjunction'):
            return f"Thông tin bất ngờ, sudden data releases. Mercury + Uranus = news-driven volatility."

        if (p1 == 'NEPTUNE' and p2 == 'PLUTO' and aspect_type == 'Sextile') or \
           (p1 == 'PLUTO' and p2 == 'NEPTUNE' and aspect_type == 'Sextile'):
            return f"Transformation dưới surface, gradual shift. Không có sudden moves nhưng trend thay đổi chậm."

        if (p1 == 'MERCURY' and p2 == 'PLUTO' and aspect_type == 'Trine') or \
           (p1 == 'PLUTO' and p2 == 'MERCURY' and aspect_type == 'Trine'):
            return f"Thông tin sâu, institutional insight. Mercury + Pluto = data-driven precision."

        if (p1 == 'MARS' and p2 == 'RAHU' and aspect_type == 'Sextile') or \
           (p1 == 'RAHU' and p2 == 'MARS' and aspect_type == 'Sextile'):
            return f"Năng lượng disruption được channel tốt. Mars + Rahu = aggressive nhưng có direction."

        # Generic fallback
        aspect_meaning = ASPECT_MEANINGS.get(aspect_type, {})
        return f"{aspect_meaning.get('description', '')} {p1} ({p1_desc}) {aspect_type.lower()} {p2} ({p2_desc}). Orb {orb:.2f}° ({tightness})."


# ──────────────────────────────────────────────
# Standalone test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import requests

    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)

    # Fetch Vedic data
    payload = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "timezone": "Asia/Ho_Chi_Minh",
        "latitude": 10.8510238,
        "longitude": 106.7548953
    }
    r = requests.post("https://vedicvn-api.onrender.com/api/chart", json=payload, timeout=60)
    vedic_data = r.json()
    planets = vedic_data.get('planets', [])

    # Calculate hora
    from hora_engine import VedicHoraEngine
    hora_engine = VedicHoraEngine()
    hora_info = hora_engine.calculate_hora(now)

    # Run astro analysis
    engine = AstroEngine(planets, hora_info, now)
    report = engine.format_report()
    print(report)
