import os
import sys
import json
import requests
from datetime import datetime
import pytz

# Ensure workspace + engines are in path (works both locally and on Render)
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
for p in (WORKSPACE, os.path.join(WORKSPACE, 'engines')):
    if p not in sys.path:
        sys.path.insert(0, p)

from data_fetcher import DataFetcher
from gann_engine import GannEngine, GannDateEngine
from hora_engine import VedicHoraEngine
from ta_engine import TAEngine
from astro_engine import AstroEngine
from carmen_analyst import CarmenAnalyst
from historical_correlation import HistoricalCorrelation

def get_forex_factory_news():
    import feedparser
    try:
        feed = feedparser.parse("https://nfs.faireconomy.media/ff_calendar_thisweek.xml")
        news_items = []
        for entry in feed.entries:
            impact = getattr(entry, "impact", "Unknown")
            if impact.lower() == 'high' or 'High' in entry.title:
                news_items.append({"title": entry.title, "impact": impact})
        return news_items if news_items else [{"info": "No high impact news"}]
    except:
        return []

def _get_last_known_price():
    """Đọc giá đóng cửa gần nhất từ CSV cache — fallback khi API fail."""
    import pandas as pd
    from datetime import datetime
    data_dir = os.path.join(os.path.dirname(__file__), "patreon-db", "data")
    try:
        months = sorted([f for f in os.listdir(data_dir) if f.endswith(".csv")], reverse=True)
        for m in months:
            df = pd.read_csv(os.path.join(data_dir, m))
            last = df.iloc[-1]
            return float(last["gold_close"])
    except:
        pass
    raise RuntimeError("Không lấy được giá vàng — cả yfinance lẫn CSV cache đều fail")


def _build_ta_data(market_data, price_for_fib, label="M30"):
    """Build TA dict from candle data (works for any timeframe)."""
    if isinstance(market_data, dict) and "error" in market_data:
        return None
    if not isinstance(market_data, list) or len(market_data) < 3:
        return None
    try:
        highs = [x['high'] for x in market_data]
        lows = [x['low'] for x in market_data]
        sh = max(highs)
        sl = min(lows)
        idx_h = highs.index(sh)
        idx_l = lows.index(sl)
        trend = "UP" if idx_h > idx_l else "DOWN"

        fibs = TAEngine.calculate_fib_retracement(sh, sl, trend)
        fib_analysis = TAEngine.analyze_price_fibo(price_for_fib, fibs)

        bars_since = len(market_data) - (idx_h if trend == "DOWN" else idx_l)
        scale = 1.97
        anchor = sh if trend == "DOWN" else sl
        if trend == "UP":
            fan_1x1 = anchor + (bars_since * scale)
            fan_2x1 = anchor + (bars_since * scale * 2)
            fan_3x1 = anchor + (bars_since * scale * 3)
        else:
            fan_1x1 = anchor - (bars_since * scale)
            fan_2x1 = anchor - (bars_since * scale * 2)
            fan_3x1 = anchor - (bars_since * scale * 3)

        closes = [c['close'] for c in market_data]

        def calc_ema(prices, period):
            if len(prices) < period:
                return None
            multiplier = 2 / (period + 1)
            ema = sum(prices[:period]) / period
            for i in range(period, len(prices)):
                ema = (prices[i] - ema) * multiplier + ema
            return round(ema, 2)

        # Use shorter EMA periods for M30, longer for H4
        if label == "H4":
            ema_short = calc_ema(closes, 12)
            ema_long = calc_ema(closes, 26)
        else:
            ema_short = calc_ema(closes, 31)
            ema_long = calc_ema(closes, 113)

        ema_position = "trên" if price_for_fib > (ema_short or price_for_fib) else "dưới" if price_for_fib < (ema_short or price_for_fib) else "ngang"

        result = {
            "swing_high": sh,
            "swing_low": sl,
            "trend": trend,
            "fib_analysis": fib_analysis,
            "fib_levels": fibs,
            "fan_1x1": round(fan_1x1, 2),
            "fan_2x1": round(fan_2x1, 2),
            "fan_3x1": round(fan_3x1, 2),
            "ema_short": ema_short,
            "ema_long": ema_long,
            "ema_position": ema_position,
            "closes": closes,
            "timeframe": label
        }
        # Add EMA cross signal
        if ema_short and ema_long:
            result["ema_cross"] = "GOLDEN_CROSS" if ema_short > ema_long else "DEATH_CROSS"
            result["ema_short"] = ema_short
            result["ema_long"] = ema_long
        return result
    except:
        return None


def get_report_data():
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)

    # 1. Price — Twelve Data (realtime) → MetalpriceAPI → yfinance close → CSV cache
    #    Không hardcode. Không bịa số.
    twelvedata_price = DataFetcher.get_gold_spot_price_twelvedata()
    if twelvedata_price is None:
        twelvedata_price = DataFetcher.get_gold_spot_price_metalprice()

    # 2. TA data — Twelve Data time_series (ưu tiên) → yfinance M30
    #    Dùng Twelve Data vì cho spot gold, realtime hơn yfinance futures
    ts_data = DataFetcher.get_gold_time_series_twelvedata(interval="30min", output=150)
    if isinstance(ts_data, dict) and "error" in ts_data:
        market_data = DataFetcher.get_gold_price_m30(limit=150)
    else:
        market_data = ts_data

    # 2b. H4 data — multi-timeframe context
    #     Twelve Data 4h → yfinance fallback
    h4_raw = DataFetcher.get_gold_time_series_twelvedata(interval="4h", output=100)
    if isinstance(h4_raw, dict) and "error" in h4_raw:
        # yfinance fallback for H4
        try:
            import yfinance as yf
            ticker = yf.Ticker("GC=F")
            df_h4 = ticker.history(interval="1h", period="10d")
            if not df_h4.empty:
                h4_raw = DataFetcher._df_to_candles(df_h4, limit=100)
            else:
                h4_raw = []
        except Exception:
            h4_raw = []

    # Xác định price cuối cùng
    if twelvedata_price is not None:
        price = twelvedata_price
    elif isinstance(market_data, list) and len(market_data) > 0:
        price = market_data[-1]['close']
    else:
        price = _get_last_known_price()

    # Xây TA data với price hiện tại
    ta_data = _build_ta_data(market_data, price, label="M30")
    h4_ta_data = _build_ta_data(h4_raw, price, label="H4") if isinstance(h4_raw, list) and len(h4_raw) >= 3 else None

    # Backward compat: map ema_short/ema_long to ema_31/ema_113 for M30
    if ta_data:
        if 'ema_short' in ta_data:
            ta_data['ema_31'] = ta_data['ema_short']
            ta_data['ema_113'] = ta_data['ema_long']

    # 2. Gann Price & Date
    base_num = GannEngine.extract_base_number(price)
    gann_levels = GannEngine.calculate_gann_levels(base_num, scale_factor=10)
    
    # Confluence: Fibo levels near Gann Square levels (needs both ta_data and gann_levels)
    if ta_data:
        fib_levels_dict = ta_data.get('fib_levels', {})
        all_gann = ([r['price'] for r in gann_levels['resistances']] +
                    [s['price'] for s in gann_levels['supports']])
        confluence_zones = []
        threshold = max(5, price * 0.001)
        for ratio_str, fib_price in fib_levels_dict.items():
            for gan_price in all_gann:
                if abs(fib_price - gan_price) <= threshold:
                    side = "kháng cự" if gan_price >= price else "hỗ trợ"
                    confluence_zones.append({
                        "fib_level": ratio_str,
                        "fib_price": fib_price,
                        "gann_price": gan_price,
                        "diff": round(abs(fib_price - gan_price), 2),
                        "side": side,
                        "label": f"Fibo {ratio_str} @ ${fib_price:.1f} ≡ Gann ${gan_price:.1f}"
                    })
        ta_data['confluence_zones'] = sorted(confluence_zones, key=lambda z: abs(z['fib_price'] - price))[:5]
    
    anchor_date = "2024-11-14" # Mốc anchor gốc theo Kim Ssa
    gann_dates = GannDateEngine.calculate_dates_from_anchor(anchor_date)
    nearest_gann_date = GannDateEngine.find_nearest_future_date(gann_dates)
    nearest_gann_date = GannDateEngine.find_nearest_future_date(gann_dates)
    
    # 3. Hora — always available (no external API needed)
    hora_engine = VedicHoraEngine()
    hora_info = hora_engine.calculate_hora(now)
    hora_forecast = hora_engine.calculate_full_day_horas(now)

    # 4. Vedic Transits + Deep Astro Analysis (with retry + fallback)
    planets_info = {}
    astro_report = None
    astro_analysis = None
    vedic_api_error = None

    for attempt in range(3):
        try:
            payload = {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M"),
                "timezone": "Asia/Ho_Chi_Minh",
                "latitude": 10.8510238,
                "longitude": 106.7548953
            }
            r = requests.post("https://vedicvn-api.onrender.com/api/chart", json=payload, timeout=60)
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")
            vedic_data = r.json()
            planets = vedic_data.get('planets', [])
            if not planets:
                raise Exception("No planets data in response")
            for p in planets:
                if p['planet'] in ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN']:
                    planets_info[p['planet']] = f"{p['sign']['name']} ({round(p['longitude'], 2)}°)"

            # 4b. Deep Astro Analysis (AI-powered interpretation)
            astro_engine = AstroEngine(planets, hora_info, now)
            astro_report = astro_engine.format_report()
            astro_analysis = astro_engine.get_gold_specific_analysis()
            break  # Success — exit retry loop
        except Exception as e:
            vedic_api_error = str(e)
            if attempt < 2:
                import time
                time.sleep(3)  # Wait before retry
            else:
                planets_info = {"error": f"Vedic API failed after 3 attempts: {vedic_api_error}"}

    # If Vedic API failed, build fallback astro report from Hora only
    if astro_report is None:
        astro_report = f"⚠️ Không lấy được dữ liệu Vedic API ({vedic_api_error}). Báo cáo dựa trên Hora engine."
        astro_analysis = None

    # 5. Macro News & Market News
    macro_news = get_forex_factory_news()
    market_news = DataFetcher.get_gold_market_news(limit=3)

    output = {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "price": price,
        "ta_data": ta_data,
        "h4_ta_data": h4_ta_data,
        "gann_base": base_num,
        "gann_resistances": gann_levels['resistances'],
        "gann_supports": gann_levels['supports'],
        "gann_dates": gann_dates,
        "nearest_gann_date": nearest_gann_date,
        "gann_anchor_date": anchor_date,
        "hora": hora_info,
        "hora_forecast": hora_forecast,
        "vedic_planets": planets_info,
        "astro_report": astro_report,
        "astro_analysis": astro_analysis,
        "macro_calendar": macro_news[:2] if isinstance(macro_news, list) else macro_news,
        "market_news": market_news
    }
    return output

def get_full_report_data(include_carmen=True):
    """
    Get report data with optional Carmen AI analysis.
    This is the main entry point for the Telegram bot.
    
    Args:
        include_carmen: If True, run Carmen AI analysis before returning.
                       Falls back gracefully if Gemini API key not set.
    
    Returns:
        dict with all raw data + carmen_analysis field
    """
    data = get_report_data()

    # ── Compute historical correlation BEFORE Carmen AI (so AI can use it) ──
    try:
        hc = HistoricalCorrelation()
        # Extract moon data for correlation query
        planets = data.get('vedic_planets', {})
        moon = planets.get('Moon', {}) if isinstance(planets.get('Moon'), dict) else {}
        nak = moon.get('nakshatra', '')
        sign = moon.get('sign', '')
        ta = data.get('ta_data') or {}
        vol = 'high' if abs(ta.get('swing_high', 0) - ta.get('swing_low', 0)) > 50 else ('medium' if abs(ta.get('swing_high', 0) - ta.get('swing_low', 0)) > 25 else 'low')
        trend = ta.get('trend', '')
        hora_curr = (data.get('hora') or {}).get('hora', '')

        # Parse nakshatra from astro_report if not in planets dict
        if not nak:
            import re
            ar = data.get('astro_report', '')
            nak_match = re.search(r'—\s*(\w+(?:\s+\w+)?)\s*\(chủ tinh', ar)
            moon_match = re.search(r'Moon:\s*\S+\s+(\S+(?:\s+\S+)?)\s*\(', ar)
            if nak_match:
                nak = nak_match.group(1)
            if moon_match and not sign:
                sign = moon_match.group(1)

        corr = hc.correlate(
            moon_nakshatra=nak,
            moon_sign=sign,
            dominant_hora=hora_curr,
            volatility=vol,
            trend=trend,
        )
        data['correlation_data'] = corr
        print(f"📊 Correlation: {nak} + {sign} — {corr.get('combined_stats', {}).get('bullish_pct', '?')}% bullish ({corr.get('combined_stats', {}).get('total_days', 0)} days)", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Correlation skipped: {e}", file=sys.stderr)
        data['correlation_data'] = None

    if include_carmen:
        try:
            analyst = CarmenAnalyst()
            print(f"🪐 Carmen AI analyzing... ({analyst.model_name})", file=sys.stderr)
            carmen_analysis = analyst.analyze(data)
            data['carmen_analysis'] = carmen_analysis
            print(f"🪐 Carmen analysis complete. Bias: {carmen_analysis.get('bias', 'N/A')} | Confidence: {carmen_analysis.get('confidence', 0)}", file=sys.stderr)
        except ValueError as e:
            # Gemini API key not set — fallback gracefully
            print(f"⚠️ Carmen AI skipped: {e}", file=sys.stderr)
            data['carmen_analysis'] = None
        except Exception as e:
            print(f"⚠️ Carmen AI error: {e}", file=sys.stderr)
            data['carmen_analysis'] = None
    else:
        data['carmen_analysis'] = None
    
    return data

def run_pipeline():
    data = get_report_data()
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    run_pipeline()
