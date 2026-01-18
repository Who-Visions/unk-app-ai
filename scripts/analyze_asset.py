
import os
import sys
import argparse
import requests
import statistics
import time
from rich.console import Console
from rich.panel import Panel

def calculate_rsi(prices, period=14):
    """Calculate RSI from a list of closing prices."""
    if len(prices) < period + 1:
        return 50.0  # Not enough data
    
    gains = []
    losses = []
    
    pass_prices = prices[-(period+1):] # Take just enough for simple calc or all
    # Standard Wilders Smoothing usually needs more history, 
    # but for simple 14-period avg gain/loss:
    
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Simple Moving Average RSI (Smoother one needs recursion)
    # Using Simple for robustness with limited data
    recent_changes = changes[-period:]
    
    avg_gain = sum([x for x in recent_changes if x > 0]) / period
    avg_loss = abs(sum([x for x in recent_changes if x < 0])) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

    return rsi

def fetch_with_retry(url, retries=3, backoff=2):
    """Fetch URL with retry logic for Rate Limits."""
    console = Console()
    for i in range(retries):
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('Response') == 'Error' and 'rate limit' in res.get('Message', '').lower():
                wait = backoff ** (i + 1)
                console.print(f"[yellow]⚠️ Rate Limit Hit. Cooling down for {wait}s...[/]")
                time.sleep(wait)
                continue
            return res
        except Exception as e:
            console.print(f"[red]Request failed: {e}[/]")
            time.sleep(1)
    return {'Response': 'Error', 'Message': 'Max retries reached'}

def analyze_asset(symbol):
    console = Console()
    symbol = symbol.upper().split('-')[0] # Clean "ARB-USD" -> "ARB"
    
    console.print(f"[bold blue]🔍 Analyzing {symbol} Technicals...[/]")
    
    try:
        # Fetch 60 minutes of minute-data (for Volatility) and 24 hours of hourly (for RSI/Trend)
        # Using 15-minute candles for RSI
        url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={symbol}&tsym=USD&limit=60&aggregate=15"
        res = fetch_with_retry(url)
        # res = requests.get(url, timeout=10).json() # OLD
        
        if res['Response'] == 'Error':
            console.print(f"[red]Error fetching data: {res.get('Message')}[/]")
            return

        candles = res['Data']['Data']
        closes = [c['close'] for c in candles]
        
        if not closes:
            console.print("[red]No price data found.[/]")
            return
            
        current_price = closes[-1]
        
        # --- TECHNICAL INDICATORS ---
        
        # 1. RSI (14 period on 15m candles)
        # We need more data for accurate RSI. The initial fetch was limit=60 aggregate=15 which is 15 hours?
        # Actually logic above fetched limit=60 mins? No, aggregate=15 means 60*15 mins = 900 mins = 15 hours.
        # Sufficient for recent RSI.
        rsi = calculate_rsi(closes, period=14)
        
        # 2. Volatility (StdDev of last 20 candles)
        recent_closes = closes[-20:]
        mean_price = statistics.mean(recent_closes)
        stdev = statistics.stdev(recent_closes)
        volatility_pct = (stdev / mean_price) * 100
        
        # 3. Trend (Last 5 candles)
        trend_start = closes[-5]
        trend_diff = (current_price - trend_start) / trend_start * 100

        # 4. FIBONACCI RETRACEMENT (Using 7-day hourly data)
        # We need a separate fetch for Swing High/Low context
        fib_url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym=USD&limit=168"
        fib_res = fetch_with_retry(fib_url)
        # fib_res = requests.get(fib_url, timeout=10).json() # OLD
        fib_levels_str = ""
        fib_status = ""
        
        if fib_res['Response'] == 'Success':
            f_data = fib_res['Data']['Data']
            f_highs = [d['high'] for d in f_data]
            f_lows = [d['low'] for d in f_data]
            
            swing_h = max(f_highs)
            swing_l = min(f_lows)
            
            # Simple Trend Direction over period: 
            # If Peak index > Valley index => Uptrend (Retracing from High)
            # If Peak index < Valley index => Downtrend (Retracing from Low) -> actually usually we just care about range
            # Standard Fib Retracement tool draws from Swing Low to Swing High (for Uptrend Support) 
            # or Swing High to Swing Low (for Downtrend Resistance).
            
            # Let's assume we want to support lines below current price and resistance above.
            # Range = High - Low
            diff = swing_h - swing_l
            
            # Helper to fmt
            def fmt_lvl(p): return f"${p:,.4f}"
            
            # Calculating Standard Levels
            # We display where current price sits relative to range
            fib_0   = swing_l          # Low
            fib_236 = swing_l + (diff * 0.236)
            fib_382 = swing_l + (diff * 0.382)
            fib_500 = swing_l + (diff * 0.500)
            fib_618 = swing_l + (diff * 0.618)
            fib_786 = swing_l + (diff * 0.786)
            fib_100 = swing_h          # High
            
            # Find nearest levels
            levels = [
                ("0% (Low)", fib_0),
                ("23.6%", fib_236),
                ("38.2%", fib_382),
                ("50.0%", fib_500),
                ("61.8%", fib_618),
                ("78.6%", fib_786),
                ("100% (High)", fib_100)
            ]
            
            # Identify Zone
            above = None
            below = None
            for name, price in levels:
                if price <= current_price:
                    below = (name, price)
                else:
                    above = (name, price)
                    break # Found the first one above
            
            fib_levels_str = f"""
[bold]7-Day Swing[/]: {fmt_lvl(swing_l)} - {fmt_lvl(swing_h)}
[dim]Resistance[/]: {above[0] + ' @ ' + fmt_lvl(above[1]) if above else 'None (ATH?)'}
[dim]Support[/]:    {below[0] + ' @ ' + fmt_lvl(below[1]) if below else 'None (ATL?)'}
"""
            # Highlight Golden Zone
            if below and (below[0] == "61.8%" or below[0] == "50.0%"):
                fib_status = "[bold green]🧪 IN GOLDEN ZONE (50-61.8%)[/]"
            elif above and above[0] == "23.6%":
                 fib_status = "[bold yellow]⚠️ NEAR RESISTANCE[/]"
        
        # Display
        color = "green"
        signal = "NEUTRAL"
        
        if rsi > 70:
            color = "red"
            signal = "OVERBOUGHT (Wait)"
        elif rsi < 30:
            color = "green"
            signal = "OVERSOLD (Buy Dip)"
        else:
            if trend_diff > 0.5:
                color = "green"
                signal = "BULLISH MOMENTUM"
            elif trend_diff < -0.5:
                color = "yellow"
                signal = "BEARISH MOMENTUM"
                
        # Override High Volatility
        if volatility_pct > 2.0:
            signal += " + HIGH VOLATILITY"
            
        # RAW PRINT FOR LOGS
        print(f"DEBUG_RAW: Symbol={symbol} Price={current_price} RSI={rsi} Vol={volatility_pct} Trend={trend_diff}")

        panel_content = f"""
[bold]Price[/]: ${current_price:,.4f}
[bold]RSI (15m)[/]: {rsi:.1f}
[bold]Volatility[/]: {volatility_pct:.2f}%
[bold]Trend (1h)[/]: {trend_diff:+.2f}%
{fib_levels_str}
[bold {color}]SIGNAL: {signal}[/]
{fib_status}
"""
        console.print(Panel(panel_content, title=f"{symbol} Analysis", border_style=color))
        
    except Exception as e:
        console.print_exception()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Ticker symbol (e.g. ARB)")
    args = parser.parse_args()
    analyze_asset(args.symbol)
