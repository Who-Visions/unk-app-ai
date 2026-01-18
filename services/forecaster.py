
"""
Forecaster AI Module
====================
Provides statistical edge through:
1. Seasonality Analysis (Monthly Win Rates)
2. Pattern Matching (Correlation with Historical Price Action)
"""
import requests
import datetime
import statistics
import math
import time

class Forecaster:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {} # symbol -> timestamp
        
    def _fetch_history(self, symbol, limit=2000):
        """Fetch daily OHLCV from CryptoCompare"""
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&limit={limit}"
            res = requests.get(url, timeout=10)
            data = res.json()
            if data['Response'] == 'Success':
                return data['Data']['Data']
        except Exception as e:
            print(f"[Forecaster] Fetch Error {symbol}: {e}")
        return []

    def _fetch_hourly(self, symbol, limit=24):
        """Fetch hourly OHLCV for recent session data"""
        try:
            url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym=USD&limit={limit}"
            res = requests.get(url, timeout=10)
            data = res.json()
            if data['Response'] == 'Success':
                return data['Data']['Data']
        except Exception as e:
            print(f"[Forecaster] Hourly Fetch Error {symbol}: {e}")
        return []

    def check_seasonality(self, symbol):
        """
        Returns (Score, WinRate, AvgReturn, Recommendation)
        Score: -1 (Avoid), 0 (Neutral), 1 (Good)
        """
        # Check Cache
        cache_key = f"{symbol}_seasonality"
        if cache_key in self.cache:
            # Monthly cache is fine
            if time.time() - self.cache_expiry.get(cache_key, 0) < 86400:
                return self.cache[cache_key]

        data = self._fetch_history(symbol)
        if not data:
            return 0, 0, 0, "No Data"

        current_month = datetime.datetime.now().month
        years = {}
        
        for day in data:
            dt = datetime.datetime.fromtimestamp(day['time'])
            if dt.month == current_month:
                y = dt.year
                if y not in years:
                    years[y] = {'open': 0, 'close': 0, 'first_day': 32, 'last_day': 0}
                
                if dt.day < years[y]['first_day']:
                    years[y]['open'] = day['open']
                    years[y]['first_day'] = dt.day
                if dt.day > years[y]['last_day']:
                    years[y]['close'] = day['close']
                    years[y]['last_day'] = dt.day

        monthly_returns = []
        wins = 0
        total = 0
        
        for y, stats in years.items():
            if stats['open'] > 0:
                ret = (stats['close'] - stats['open']) / stats['open'] * 100
                monthly_returns.append(ret)
                if ret > 0: wins += 1
                total += 1
        
        if total == 0:
            return 0, 0, 0, "Insufficient Data"

        avg_ret = statistics.mean(monthly_returns) if monthly_returns else 0
        win_rate = (wins / total) * 100
        
        # Scoring Logic
        # > 70% WR = Good
        # < 40% WR = Bad
        score = 0
        if win_rate >= 60: score = 1
        if win_rate <= 40: score = -1
        
        result = (score, win_rate, avg_ret, "Bullish" if score > 0 else "Bearish" if score < 0 else "Neutral")
        
        # Cache
        self.cache[cache_key] = result
        self.cache_expiry[cache_key] = time.time()
        
        return result

    def find_patterns(self, symbol, lookback=30):
        """
        Simulated Pattern Matcher.
        Real Pearson correlation is computationally heavy for a CLI loop.
        Simple substitute: Compare recent trend vs historical trend of chart segments.
        
        Returns: (CorrelationScore, PredictedMove)
        """
        # Placeholder for complex pattern matching
        # For now, we return a Neutral signal to avoid blocking valid trades
        # until the heavy math engine is ready.
        return 0, 0.0

    def get_fabio_metrics(self, symbol):
        """
        Calculates Fabio Scalper Metrics:
        1. Range Position (0.0 - 1.0): Proxy for Value Area.
           - < 0.25: Value Area Low (BUY Zone if Momentum)
           - > 0.75: Value Area High (SELL Zone or Breakout Watch)
        2. Volatility State: 'Squeeze' or 'Expansion'
        """
        data = self._fetch_hourly(symbol, limit=24)
        if not data:
            return None

        closes = [d['close'] for d in data]
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        
        # 1. Calculate Daily Range Position
        day_high = max(highs)
        day_low = min(lows)
        current_price = closes[-1]
        
        range_size = day_high - day_low
        if range_size == 0: range_position = 0.5
        else: range_position = (current_price - day_low) / range_size
        
        # 2. Detect Absorption / Consolidation (Low Volatility)
        # Using StdDev of last 6 hours
        recent_closes = closes[-6:]
        if len(recent_closes) > 1:
            std_dev = statistics.stdev(recent_closes)
            mean_price = statistics.mean(recent_closes)
            volatility_pct = (std_dev / mean_price) * 100
        else:
            volatility_pct = 1.0

        is_squeeze = volatility_pct < 0.5 # Arbitrary low vol threshold
        
        return {
            "range_position": range_position,
            "is_squeeze": is_squeeze,
            "day_high": day_high,
            "day_low": day_low,
            "volatility_pct": volatility_pct
        }

    def get_timeframe_stats(self, symbol):
        """
        Returns % Change for: 1H, 24H, 7D
        """
        # 1. 24H & 7D from Daily Data
        daily = self._fetch_history(symbol, limit=8) # Need 7 days back
        stats = {"1h": 0.0, "24h": 0.0, "7d": 0.0}
        
        if daily and len(daily) >= 8:
            curr = daily[-1]['close']
            prev_24h = daily[-2]['close']
            prev_7d = daily[-8]['close']
            
            if prev_24h > 0: stats["24h"] = (curr - prev_24h) / prev_24h * 100
            if prev_7d > 0: stats["7d"] = (curr - prev_7d) / prev_7d * 100
            
        # 2. 1H from Hourly Data
        hourly = self._fetch_hourly(symbol, limit=2)
        if hourly and len(hourly) >= 2:
            curr_h = hourly[-1]['close']
            prev_h = hourly[-2]['close']
            if prev_h > 0: stats["1h"] = (curr_h - prev_h) / prev_h * 100
            
        return stats

# Singleton
forecaster = Forecaster()
