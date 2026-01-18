"""
XTZ Technical Analysis (RSI) using Massive API
==============================================
Calculates RSI-14 to diagnose 'The Slide'.
"""
import sys
import pandas as pd
import datetime
from services.massive_api import MassiveAPI

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_technicals():
    print("📈 ANALYZING XTZ TECHNICALS (MASSIVE API)...")
    
    api = MassiveAPI()
    
    # Range: Last 48 hrs
    to_date = datetime.datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    
    # Fetch Hourly Candles
    # Multiplyer 1, Timespan hour
    print(f"   Fetching hourly data for X:XTZUSD ({from_date} to {to_date})...")
    data = api.get_aggregates("X:XTZUSD", 1, "hour", from_date, to_date)
    
    results = data.get("results", [])
    if not results:
        print("❌ No data returned.")
        return

    # Create DataFrame
    df = pd.DataFrame(results)
    df['t'] = pd.to_datetime(df['t'], unit='ms')
    df.set_index('t', inplace=True)
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['c'], period=14)
    
    last_close = df['c'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]
    
    print("\n📊 RECENT CANDLES:")
    print(df[['o', 'h', 'l', 'c', 'rsi']].tail(5))
    
    # Fetch Daily Open/Close for context
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"   Fetching Daily Open/Close for {today_str}...")
    daily = api.get_daily_open_close("XTZ", "USD", today_str)
    
    daily_open = daily.get("open", 0)
    day_trend = ""
    
    if daily_open > 0:
        pct_chg = ((last_close - daily_open) / daily_open) * 100
        day_trend = f"{pct_chg:+.2f}% vs Open (${daily_open:.4f})"
    
    print("-" * 40)
    print(f"🎯 CURRENT PRICE: ${last_close:.4f}")
    if day_trend:
         print(f"☀️ DAY TREND:     {day_trend}")
    print(f"🌊 CURRENT RSI:   {last_rsi:.1f}")
    
    # Interpretation
    signal = "NEUTRAL"
    bias = "Hold"
    
    if last_rsi < 30:
        signal = "OVERSOLD"
        bias = "Accumulate"
    elif last_rsi > 70:
        signal = "OVERBOUGHT"
        bias = "Trim"
        
    print(f"🚦 SIGNAL:        {signal} ({bias})")
    
    # User Heuristic: "If XTZ drops off movers list AND price stays below entry"
    # Entry is $0.627
    entry_price = 0.627014
    if last_close < entry_price:
        dist = ((last_close - entry_price) / entry_price) * 100
        print(f"⚠️  WARNING: Below Entry by {dist:.2f}%")
        if last_rsi < 40:
             print("   -> Weak Momentum. 'Real Fade' risk increasing.")
        else:
             print("   -> RSI Neutral. Likely 'Noise'.")

if __name__ == "__main__":
    check_technicals()
