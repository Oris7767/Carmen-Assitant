from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, timedelta
import pytz

class VedicHoraEngine:
    # Chaldean order: slowest to fastest
    CHALDEAN_ORDER = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
    
    # Python datetime.weekday() -> 0: Monday, 6: Sunday
    DAY_RULERS = {
        0: 'Moon',    # Monday
        1: 'Mars',    # Tuesday
        2: 'Mercury', # Wednesday
        3: 'Jupiter', # Thursday
        4: 'Venus',   # Friday
        5: 'Saturn',  # Saturday
        6: 'Sun'      # Sunday
    }

    # Trading quality for each planet hora (1=worst, 5=best)
    TRADING_QUALITY = {
        'Sun': 5,      # Sun = ruler of Gold → BEST for XAUUSD
        'Jupiter': 4,  # Expansion, liquidity → good for swing
        'Mars': 4,     # Momentum, volatility → good for breakout/scalp
        'Mercury': 3,  # News-driven, fast → ok for scalping
        'Moon': 2,     # Emotional, noisy → avoid
        'Venus': 2,    # Valuation, comfort → range-bound, avoid breakout
        'Saturn': 1,   # Pressure, resistance → avoid aggressive trades
    }

    # Hora emoji
    HORA_EMOJI = {
        'Sun': '☀️',
        'Moon': '🌙',
        'Mars': '♂️',
        'Mercury': '☿️',
        'Jupiter': '♃',
        'Venus': '♀️',
        'Saturn': '♄',
    }

    # Trading recommendation per hora
    TRADING_RECOMMENDATION = {
        'Sun': {
            'emoji': '☀️',
            'label': 'GOLD HOUR ⭐',
            'recommendation': 'TỐT NHẤT CHO VÀNG. Sun = ruler của Gold. Entry positions, follow institutional flow.',
            'style': 'Trend-following, institutional moves',
            'caution': 'Luôn dùng stop loss.',
        },
        'Jupiter': {
            'emoji': '♃',
            'label': 'EXPANSION',
            'recommendation': 'Thanh khoản tốt, xu hướng rõ. Phù hợp swing trades, hold positions.',
            'style': 'Swing trading, position building',
            'caution': 'Watch for FOMO tops.',
        },
        'Mars': {
            'emoji': '♂️',
            'label': 'MOMENTUM',
            'recommendation': 'Năng lượng mạnh cho breakout & scalp. Giá di chuyển nhanh.',
            'style': 'Aggressive momentum, breakout trading',
            'caution': 'Dễ sharp reversal — tight stops, không hold quá lâu.',
        },
        'Mercury': {
            'emoji': '☿️',
            'label': 'SCALP',
            'recommendation': 'Biến động nhanh, news-driven. Phù hợp scalping, quick entries/exits.',
            'style': 'Scalping, news trading',
            'caution': 'Signal noise cao — không hold qua Mercury Hora.',
        },
        'Moon': {
            'emoji': '🌙',
            'label': '⚠️ NOISY',
            'recommendation': 'CẢM XÚC CAO — thị trường dễ FOMO/panic. Chỉ fade extremes, KHÔNG chase trend.',
            'style': 'Counter-sentiment, fade extremes',
            'caution': 'Tránh trade nếu không có clear plan.',
        },
        'Venus': {
            'emoji': '♀️',
            'label': '⚠️ RANGE-BOUND',
            'recommendation': 'Thị trường trong comfort zone — range trading, TRÁNH breakout trades.',
            'style': 'Range trading, mean-reversion',
            'caution': 'Dễ false breakouts.',
        },
        'Saturn': {
            'emoji': '♄',
            'label': '⚠️ DEFENSIVE',
            'recommendation': 'Áp lực & kháng cự — thị trường kìm nén, low liquidity. HOLD, tránh aggressive entries.',
            'style': 'Defensive, wait for clarity',
            'caution': 'Thị trường có thể "đóng băng" — không force trades.',
        },
    }

    def __init__(self, lat=10.85, lon=106.75, tz_name="Asia/Ho_Chi_Minh"):
        self.location = LocationInfo("Ho Chi Minh", "Vietnam", tz_name, lat, lon)
        self.tz = pytz.timezone(tz_name)

    def calculate_hora(self, target_dt: datetime) -> dict:
        """
        Calculate the current Planetary Hora for a given datetime.
        """
        # Ensure target_dt is timezone aware
        if target_dt.tzinfo is None:
            target_dt = self.tz.localize(target_dt)

        # Get sun info for today
        s = sun(self.location.observer, date=target_dt.date(), tzinfo=self.tz)
        sunrise = s['sunrise']
        sunset = s['sunset']

        # Determine the Astrological Day (which started at the most recent sunrise)
        if target_dt < sunrise:
            # We are in the pre-dawn hours, so the astrological day is yesterday
            astro_date = target_dt.date() - timedelta(days=1)
            # Recalculate sun info for yesterday to get yesterday's sunrise and sunset
            s_yest = sun(self.location.observer, date=astro_date, tzinfo=self.tz)
            start_time = s_yest['sunset']
            end_time = sunrise # today's sunrise
            is_daytime = False
            astro_day_index = astro_date.weekday()
            
            # Hora length (night)
            total_seconds = (end_time - start_time).total_seconds()
            hora_length = total_seconds / 12.0
            elapsed = (target_dt - start_time).total_seconds()
            hora_index_in_period = int(elapsed // hora_length)
            # Night horas start from index 12 internally (12 to 23)
            hora_index_total = 12 + hora_index_in_period
            
        else:
            astro_date = target_dt.date()
            astro_day_index = astro_date.weekday()
            
            if target_dt < sunset:
                # Daytime
                start_time = sunrise
                end_time = sunset
                is_daytime = True
                total_seconds = (end_time - start_time).total_seconds()
                hora_length = total_seconds / 12.0
                elapsed = (target_dt - start_time).total_seconds()
                hora_index_total = int(elapsed // hora_length)
            else:
                # Nighttime after sunset
                start_time = sunset
                # Get tomorrow's sunrise
                s_tom = sun(self.location.observer, date=astro_date + timedelta(days=1), tzinfo=self.tz)
                end_time = s_tom['sunrise']
                is_daytime = False
                total_seconds = (end_time - start_time).total_seconds()
                hora_length = total_seconds / 12.0
                elapsed = (target_dt - start_time).total_seconds()
                hora_index_total = 12 + int(elapsed // hora_length)

        # 1st Hora of the day = Lord of the Day
        ruler_of_day = self.DAY_RULERS[astro_day_index]
        start_index = self.CHALDEAN_ORDER.index(ruler_of_day)
        
        # Calculate current Hora ruler
        # Move forward in the Chaldean order array (which naturally represents the downward sequence when looped)
        current_hora_index = (start_index + hora_index_total) % 7
        ruler_of_hora = self.CHALDEAN_ORDER[current_hora_index]

        # Calculate exact start and end of this specific hora
        period_start = start_time if is_daytime else start_time
        if is_daytime:
             hora_start = sunrise + timedelta(seconds=hora_index_total * hora_length)
        else:
             hora_start = sunset + timedelta(seconds=(hora_index_total - 12) * hora_length)
             
        hora_end = hora_start + timedelta(seconds=hora_length)

        return {
            "current_time": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "astrological_day": ruler_of_day,
            "hora": ruler_of_hora,
            "is_daytime": is_daytime,
            "hora_start": hora_start.strftime("%H:%M:%S"),
            "hora_end": hora_end.strftime("%H:%M:%S"),
            "hora_length_mins": round(hora_length / 60, 2)
        }

    def calculate_full_day_horas(self, target_dt: datetime) -> dict:
        """
        Calculate ALL 24 planetary hours for a full astrological day.
        Returns structured data for trading hour forecast.
        
        An astrological day runs from sunrise to next sunrise (24 horas total):
        - Horas 0-11: Daytime (sunrise → sunset)
        - Horas 12-23: Nighttime (sunset → next sunrise)
        """
        if target_dt.tzinfo is None:
            target_dt = self.tz.localize(target_dt)

        # Get sun info for today and tomorrow
        s_today = sun(self.location.observer, date=target_dt.date(), tzinfo=self.tz)
        sunrise_today = s_today['sunrise']
        sunset_today = s_today['sunset']

        s_tom = sun(self.location.observer, date=target_dt.date() + timedelta(days=1), tzinfo=self.tz)
        sunrise_tom = s_tom['sunrise']

        astro_day_index = target_dt.date().weekday()
        ruler_of_day = self.DAY_RULERS[astro_day_index]
        start_index = self.CHALDEAN_ORDER.index(ruler_of_day)

        horas = []

        # ── DAYTIME HORAS (0-11) ──
        day_total_seconds = (sunset_today - sunrise_today).total_seconds()
        day_hora_length = day_total_seconds / 12.0

        for i in range(12):
            hora_start = sunrise_today + timedelta(seconds=i * day_hora_length)
            hora_end = sunrise_today + timedelta(seconds=(i + 1) * day_hora_length)
            
            # Calculate ruler using Chaldean order
            ruler_index = (start_index + i) % 7
            ruler = self.CHALDEAN_ORDER[ruler_index]
            
            quality = self.TRADING_QUALITY.get(ruler, 3)
            rec = self.TRADING_RECOMMENDATION.get(ruler, {})
            
            horas.append({
                "hora_number": i,
                "period": "day",
                "ruler": ruler,
                "emoji": self.HORA_EMOJI.get(ruler, ''),
                "start": hora_start.strftime("%H:%M"),
                "end": hora_end.strftime("%H:%M"),
                "quality": quality,
                "quality_label": ["", "RẤT XẤU", "XẤU", "TRUNG BÌNH", "TỐT", "TỐT NHẤT"][quality],
                "label": rec.get('label', ''),
                "recommendation": rec.get('recommendation', ''),
                "style": rec.get('style', ''),
                "caution": rec.get('caution', ''),
                "is_current": False,  # Will be set below
            })

        # ── NIGHTTIME HORAS (12-23) ──
        night_total_seconds = (sunrise_tom - sunset_today).total_seconds()
        night_hora_length = night_total_seconds / 12.0

        for i in range(12):
            hora_start = sunset_today + timedelta(seconds=i * night_hora_length)
            hora_end = sunset_today + timedelta(seconds=(i + 1) * night_hora_length)
            
            # Night horas continue from index 12 in Chaldean sequence
            ruler_index = (start_index + 12 + i) % 7
            ruler = self.CHALDEAN_ORDER[ruler_index]
            
            quality = self.TRADING_QUALITY.get(ruler, 3)
            rec = self.TRADING_RECOMMENDATION.get(ruler, {})
            
            horas.append({
                "hora_number": 12 + i,
                "period": "night",
                "ruler": ruler,
                "emoji": self.HORA_EMOJI.get(ruler, ''),
                "start": hora_start.strftime("%H:%M"),
                "end": hora_end.strftime("%H:%M"),
                "quality": quality,
                "quality_label": ["", "RẤT XẤU", "XẤU", "TRUNG BÌNH", "TỐT", "TỐT NHẤT"][quality],
                "label": rec.get('label', ''),
                "recommendation": rec.get('recommendation', ''),
                "style": rec.get('style', ''),
                "caution": rec.get('caution', ''),
                "is_current": False,
            })

        # Mark current hora
        current_now = target_dt
        for h in horas:
            h_start = datetime.strptime(f"{target_dt.strftime('%Y-%m-%d')} {h['start']}", "%Y-%m-%d %H:%M")
            h_start = self.tz.localize(h_start)
            h_end_dt = datetime.strptime(f"{target_dt.strftime('%Y-%m-%d')} {h['end']}", "%Y-%m-%d %H:%M")
            h_end_dt = self.tz.localize(h_end_dt)
            
            # Handle overnight hora (night horas cross midnight)
            if h['period'] == 'night' and h['start'] > h['end']:
                h_end_dt = h_end_dt + timedelta(days=1)
            
            if h_start <= current_now < h_end_dt:
                h['is_current'] = True
                break

        # Build forecast: top recommended hours + hours to avoid
        day_horas = [h for h in horas if h['period'] == 'day']
        night_horas = [h for h in horas if h['period'] == 'night']

        # Top trading hours (quality >= 4)
        best_hours = sorted([h for h in horas if h['quality'] >= 4], key=lambda x: -x['quality'])
        # Worst hours (quality <= 2)
        worst_hours = sorted([h for h in horas if h['quality'] <= 2], key=lambda x: x['quality'])

        return {
            "date": target_dt.strftime("%Y-%m-%d"),
            "astrological_day": ruler_of_day,
            "sunrise": sunrise_today.strftime("%H:%M"),
            "sunset": sunset_today.strftime("%H:%M"),
            "day_hora_length_mins": round(day_hora_length / 60, 2),
            "night_hora_length_mins": round(night_hora_length / 60, 2),
            "horas": horas,
            "best_trading_hours": best_hours[:5],
            "hours_to_avoid": worst_hours[:5],
        }


if __name__ == "__main__":
    engine = VedicHoraEngine()
    
    # Test with current time
    now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
    
    print("=== CURRENT HORA ===")
    result = engine.calculate_hora(now)
    for k, v in result.items():
        print(f"  {k.replace('_', ' ').title()}: {v}")
    
    print("\n=== FULL DAY HORA FORECAST ===")
    forecast = engine.calculate_full_day_horas(now)
    print(f"  Date: {forecast['date']}")
    print(f"  Astrological Day: {forecast['astrological_day']}")
    print(f"  Sunrise: {forecast['sunrise']} | Sunset: {forecast['sunset']}")
    
    print(f"\n  ⭐ GIỜ TRADING TỐT NHẤT:")
    for h in forecast['best_trading_hours']:
        print(f"    {h['emoji']} {h['start']}-{h['end']} | {h['ruler']} Hora | {h['quality_label']} | {h['label']}")
    
    print(f"\n  ⚠️ GIỜ NÊN TRÁNH:")
    for h in forecast['hours_to_avoid']:
        print(f"    {h['emoji']} {h['start']}-{h['end']} | {h['ruler']} Hora | {h['quality_label']} | {h['label']}")
    
    print(f"\n  📋 TOÀN BỘ 24 GIỜ:")
    for h in forecast['horas']:
        marker = " ◀ HIỆN TẠI" if h['is_current'] else ""
        print(f"    {h['emoji']} [{h['hora_number']:2d}] {h['start']}-{h['end']} | {h['ruler']:8s} | Q{h['quality']}: {h['quality_label']:10s} | {h['label']}{marker}")
