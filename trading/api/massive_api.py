"""
Massive (Polygon) API Client
============================
Wrapper for accessing Massive/Polygon market data.
Docs: https://polygon.io/docs/crypto/getting-started
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class MassiveAPI:
    def __init__(self):
        self.api_key = os.getenv("MASSIVE_API_KEY") or os.getenv("POLYGON_API_KEY")
        self.base_url = "https://api.polygon.io"
        
        if not self.api_key:
            print("⚠️ WARNING: MASSIVE_API_KEY not found in env.")

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        if not params:
            params = {}
        params["apiKey"] = self.api_key
        
        max_retries = 3
        backoff_sec = 15 # Start with 15s (since limit is 5/min)

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 429:
                    print(f"⚠️ Massive API Rate Limit (429). Cooling down {backoff_sec}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(backoff_sec)
                    backoff_sec *= 2 # Exponential backoff
                    continue # Retry
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                # If we exhausted retries or it's another error, we accept it (but print 429 final fail)
                if response.status_code == 429:
                     print(f"❌ Massive API Rate Limit Exceeded (Final).")
                else:
                     print(f"❌ Massive API Error: {e}")
                return {}
            except Exception as e:
                print(f"❌ Request Failed: {e}")
                return {}
        
        return {}

    def list_crypto_tickers(self, limit=100, search=None):
        """
        GET /v3/reference/tickers?market=crypto
        """
        params = {
            "market": "crypto",
            "active": "true",
            "limit": limit,
            "sort": "ticker"
        }
        if search:
            params["search"] = search
            
        data = self._get("/v3/reference/tickers", params)
        return data.get("results", [])

    def get_snapshot(self, ticker):
        """
        GET /v2/snapshot/locale/global/markets/crypto/tickers/{ticker}
        Note: Ticker format usually 'X:BTCUSD'
        """
        # Massive uses specific ticker formats for crypto snapshots
        # e.g. X:BTCUSD
        # We might need to map 'BTC-USD' -> 'X:BTCUSD'
        
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
            # Map 'BTC-USD' to 'X:BTCUSD' (Simple heuristic)
            parts = ticker.split('-')
            fmt_ticker = f"X:{parts[0]}{parts[1]}"
            
        endpoint = f"/v2/snapshot/locale/global/markets/crypto/tickers/{fmt_ticker}"
        return self._get(endpoint)

    def get_aggregates(self, ticker, multiplier, timespan, from_date, to_date):
        """
        GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        e.g. get_aggregates("X:XTZUSD", 1, "hour", "2025-01-01", "2025-01-02")
        """
        # Ensure ticker format X:SYMBOLUSD
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"


        endpoint = f"/v2/aggs/ticker/{fmt_ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        return self._get(endpoint)

    def get_daily_grouped_prices(self, date=None):
        """
        GET /v2/aggs/grouped/locale/global/market/crypto/{date}
        Returns ALL crypto tickers for a single date.
        date format: YYYY-MM-DD (Defaults to yesterday if None)
        """
        if not date:
            import datetime
            date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            
        endpoint = f"/v2/aggs/grouped/locale/global/market/crypto/{date}"
        return self._get(endpoint)

    def get_daily_open_close(self, from_symbol, to_symbol, date):
        """
        GET /v1/open-close/crypto/{from}/{to}/{date}
        e.g. get_daily_open_close("BTC", "USD", "2025-01-01")
        """
        endpoint = f"/v1/open-close/crypto/{from_symbol}/{to_symbol}/{date}"
        return self._get(endpoint)

    def get_previous_close(self, ticker):
        """
        GET /v2/aggs/ticker/{cryptoTicker}/prev
        Retrieve previous day's OHLC.
        """
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
             
        endpoint = f"/v2/aggs/ticker/{fmt_ticker}/prev"
        return self._get(endpoint)

    def get_full_market_snapshot(self):
        """
        GET /v2/snapshot/locale/global/markets/crypto/tickers
        Returns snapshot for ALL crypto tickers.
        """
        endpoint = "/v2/snapshot/locale/global/markets/crypto/tickers"
        return self._get(endpoint)

    def get_sma(self, ticker, timespan="day", window=50, limit=10):
        """
        GET /v1/indicators/sma/{cryptoTicker}
        e.g. get_sma("X:BTCUSD", timespan="day", window=50)
        """
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
             
        params = {
            "timespan": timespan,
            "window": window,
            "limit": limit,
            "order": "desc"
        }
        endpoint = f"/v1/indicators/sma/{fmt_ticker}"
        return self._get(endpoint, params)

    def get_ema(self, ticker, timespan="day", window=50, limit=10):
        """
        GET /v1/indicators/ema/{cryptoTicker}
        e.g. get_ema("X:BTCUSD", timespan="day", window=21)
        """
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
             
        params = {
            "timespan": timespan,
            "window": window,
            "limit": limit,
            "order": "desc"
        }
        endpoint = f"/v1/indicators/ema/{fmt_ticker}"
        return self._get(endpoint, params)

    def get_macd(self, ticker, timespan="day", short_window=12, long_window=26, signal_window=9, limit=10):
        """
        GET /v1/indicators/macd/{cryptoTicker}
        """
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
             
        params = {
            "timespan": timespan,
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "limit": limit,
            "order": "desc"
        }
        endpoint = f"/v1/indicators/macd/{fmt_ticker}"
        return self._get(endpoint, params)
        
    def get_rsi(self, ticker, timespan="day", window=14, limit=10):
        """
        GET /v1/indicators/rsi/{cryptoTicker}
        """
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
        
        params = {
            "timespan": timespan,
            "window": window,
            "limit": limit,
            "order": "desc"
        }
        endpoint = f"/v1/indicators/rsi/{fmt_ticker}"
        return self._get(endpoint, params)

    def get_last_trade(self, from_symbol, to_symbol):
        """
        GET /v1/last/crypto/{from}/{to}
        e.g. get_last_trade("BTC", "USD")
        """
        endpoint = f"/v1/last/crypto/{from_symbol}/{to_symbol}"
        return self._get(endpoint)

    def get_latest_trades(self, ticker, limit=1):
        """
        GET /v3/trades/{cryptoTicker}?limit={limit}&sort=timestamp&order=desc
        Attempts to fetch the most recent trade ticks.
        """
        # Ensure ticker format X:SYMBOLUSD
        fmt_ticker = ticker
        if "-" in ticker and "X:" not in ticker:
             parts = ticker.split('-')
             fmt_ticker = f"X:{parts[0]}{parts[1]}"
             
        params = {
            "limit": limit,
            "sort": "timestamp",
            "order": "desc"
        }
        endpoint = f"/v3/trades/{fmt_ticker}"
        return self._get(endpoint, params)

if __name__ == "__main__":
    # Simple Self-Test
    m = MassiveAPI()
    print("🔍 Testing Massive API Connection...")
    tickers = m.list_crypto_tickers(limit=5)
    print(f"✅ Found {len(tickers)} tickers:")
    for t in tickers:
        print(f"   - {t['ticker']}: {t['name']}")
