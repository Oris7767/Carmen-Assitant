import yfinance as yf
import feedparser
import pandas as pd
from datetime import datetime
import json
import os

# ── API Config ──
METALPRICE_KEY = os.environ.get("METALPRICE_API_KEY", "a6d36e7104ed3b7107ab66a7fd684b65")
METALPRICE_URL = "https://api.metalpriceapi.com/v1"
TWELVEDATA_KEY = os.environ.get("TWELVEDATA_API_KEY", "b08dc46f82a84431b93d1db653ce075c")
TWELVEDATA_URL = "https://api.twelvedata.com"


class DataFetcher:
    @staticmethod
    def get_gold_spot_price_twelvedata():
        """
        Lấy giá vàng spot realtime từ Twelve Data.
        Free plan: ~1 phút delay, 800 req/ngày.
        Returns: float (USD/oz) hoặc None nếu fail.
        """
        import requests as req
        try:
            url = f"{TWELVEDATA_URL}/price?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "price" in data:
                    return round(float(data["price"]), 2)
        except Exception:
            pass
        return None

    @staticmethod
    def get_gold_quote_twelvedata():
        """
        Lấy full quote vàng spot từ Twelve Data.
        Returns: dict {open, high, low, close, change, percent_change, timestamp}
                 hoặc None nếu fail.
        """
        import requests as req
        try:
            url = f"{TWELVEDATA_URL}/quote?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if "close" in data:
                    return {
                        "price": round(float(data.get("close", 0)), 2),
                        "open": round(float(data.get("open", 0)), 2),
                        "high": round(float(data.get("high", 0)), 2),
                        "low": round(float(data.get("low", 0)), 2),
                        "change_pct": round(float(data.get("percent_change", 0)), 2),
                        "is_market_open": data.get("is_market_open", False),
                        "timestamp": data.get("timestamp", 0),
                    }
        except Exception:
            pass
        return None

    @staticmethod
    def get_gold_time_series_twelvedata(interval="30min", output=100):
        """
        Lấy dữ liệu nến intraday vàng spot từ Twelve Data.
        Dùng thay thế cho yfinance M30 khi cần realtime hơn.
        Args:
            interval: "1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h"
            output: số nến trả về (max 5000 free)
        Returns: list of candles hoặc error dict
        """
        import requests as req
        try:
            url = f"{TWELVEDATA_URL}/time_series?symbol=XAU/USD&interval={interval}&outputsize={output}&apikey={TWELVEDATA_KEY}"
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "ok" and "values" in data:
                    candles = []
                    for v in data["values"]:
                        candles.append({
                            "time": v["datetime"],
                            "open": round(float(v["open"]), 2),
                            "high": round(float(v["high"]), 2),
                            "low": round(float(v["low"]), 2),
                            "close": round(float(v["close"]), 2),
                        })
                    return candles[-output:]
        except Exception:
            pass
        return {"error": "Twelve Data API failed"}

    @staticmethod
    def get_gold_spot_price_metalprice():
        """
        Lấy giá vàng spot hiện tại từ MetalpriceAPI.
        Free plan: daily delay — vẫn đủ dùng cho phân tích.
        Returns: float (giá USD/oz) hoặc None nếu fail.
        """
        import requests as req
        try:
            url = f"{METALPRICE_URL}/latest?api_key={METALPRICE_KEY}&base=XAU&currencies=USD"
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and "USD" in data.get("rates", {}):
                    price = float(data["rates"]["USD"])
                    return round(price, 2)
        except Exception:
            pass
        return None

    @staticmethod
    def get_gold_ohlc_metalprice(date_str: str):
        """
        Lấy OHLC hàng ngày từ MetalpriceAPI cho collect.py.
        Args:
            date_str: "YYYY-MM-DD"
        Returns: dict {open, high, low, close} hoặc None
        """
        import requests as req
        try:
            url = f"{METALPRICE_URL}/ohlc?api_key={METALPRICE_KEY}&base=XAU&currency=USD&date={date_str}"
            r = req.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and "rate" in data:
                    return {
                        "open": round(float(data["rate"]["open"]), 2),
                        "high": round(float(data["rate"]["high"]), 2),
                        "low": round(float(data["rate"]["low"]), 2),
                        "close": round(float(data["rate"]["close"]), 2),
                    }
        except Exception:
            pass
        return None

    @staticmethod
    def get_gold_price_m30(limit=5):
        """
        Get gold price M30 candles.
        Primary: yfinance, Fallback: direct Yahoo Finance API
        """
        # Try yfinance first
        try:
            ticker = yf.Ticker("GC=F")
            df = ticker.history(interval="30m", period="5d")
            if not df.empty:
                return DataFetcher._df_to_candles(df, limit)
        except Exception:
            pass

        # Fallback: direct Yahoo Finance API
        try:
            import requests as req
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF"
            params = {"interval": "30m", "range": "5d"}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            r = req.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                result = data.get("chart", {}).get("result", [{}])[0]
                timestamps = result.get("timestamp", [])
                quotes = result.get("indicators", {}).get("quote", [{}])[0]
                opens = quotes.get("open", [])
                highs = quotes.get("high", [])
                lows = quotes.get("low", [])
                closes = quotes.get("close", [])

                candles = []
                for i in range(len(timestamps)):
                    if closes[i] is not None:
                        candles.append({
                            "time": pd.Timestamp(timestamps[i], unit='s').strftime("%Y-%m-%d %H:%M:%S"),
                            "open": round(opens[i], 2) if opens[i] else 0,
                            "high": round(highs[i], 2) if highs[i] else 0,
                            "low": round(lows[i], 2) if lows[i] else 0,
                            "close": round(closes[i], 2)
                        })
                if candles:
                    return candles[-limit:]
        except Exception:
            pass

        return {"error": "All gold price APIs failed"}

    @staticmethod
    def get_forex_factory_news():
        feed_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
        try:
            feed = feedparser.parse(feed_url)
            news_items = []
            for entry in feed.entries:
                impact = getattr(entry, "impact", "Unknown")
                if impact.lower() == 'high' or 'High' in entry.title:
                     news_items.append({
                         "title": entry.title,
                         "country": getattr(entry, "country", ""),
                         "impact": impact
                     })
            return news_items if news_items else [{"info": "No high impact news"}]
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_gold_market_news(limit=3):
        """
        Lấy tin tức định tính trực tiếp từ mảng tài chính (Yahoo Finance News cho Vàng)
        """
        try:
            ticker = yf.Ticker("GC=F")
            news_data = ticker.news
            parsed_news = []
            for n in news_data[:limit]:
                content = n.get('content', {})
                if content:
                    parsed_news.append({
                        "title": content.get('title', ''),
                        "summary": content.get('summary', ''),
                        "time": content.get('pubDate', '')
                    })
            return parsed_news
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _df_to_candles(df, limit=5):
        """Convert yfinance DataFrame to candle list."""
        recent = df.tail(limit)
        result = []
        for idx, row in recent.iterrows():
            # Handle timezone-aware index
            if hasattr(idx, 'tz') and idx.tz is not None:
                ts = idx.tz_localize(None) if idx.tz else idx
            else:
                ts = idx
            timestamp_str = pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            result.append({
                "time": timestamp_str,
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2)
            })
        return result


if __name__ == "__main__":
    print(json.dumps(DataFetcher.get_gold_market_news(2), indent=2))
