"""
Massive (Polygon) Technical Analysis Suite
==========================================
Diagnoses XTZ trend using server-side indicators.
"""
import sys
from services.massive_api import MassiveAPI

def analyze_xtz():
    print("🔬 MASSIVE API: DEEP SCAN (XTZ-USD)")
    api = MassiveAPI()
    ticker = "X:XTZUSD"
    
    # 1. Price Check
    # 1. Price Check (Basic Plan Compatible)
    price = 0
    open_price = 0
    source = "Unknown"
    
    # Plan A: Try v2/Prev Close (Most reliable on Basic)
    if price == 0:
        prev = api.get_previous_close(ticker)
        if prev and "results" in prev and len(prev["results"]) > 0:
            res = prev["results"][0]
            price = res.get("c", 0)
            open_price = res.get("o", 0)
            source = "Previous Close (v2)"

    # Plan B: Try Real-Time (Bonus, if available)
    # We suppress errors here because we expect 403s on Basic
    try:
        # Just a quick check, don't print errors inside api wrapper if possible
        pass 
        # For now, we rely on Prev Close which is sufficient for "Trend" analysis
        # If we really need live price, we'd use the WebSocket (Next Step)
    except:
        pass

    if price == 0:
        print("❌ Data Unavailable (Check Connectivity).")
        return

    print(f"   Price: ${price:.4f} (Source: {source} - Basic Plan Limit)")
    
    # Context (Daily Open)
    if open_price == 0:
        # Approximate from prev close
        open_price = price 
    
    # 2. RSI (14)
    print("   Fetching RSI...")
    rsi_data = api.get_rsi(ticker, timespan="hour", window=14) # Hourly RSI for shorter term
    rsi_val = rsi_data.get("results", {}).get("values", [{}])[0].get("value", 50)
    print(f"   RSI (1H): {rsi_val:.2f}")

    # 3. MACD
    print("   Fetching MACD...")
    macd_data = api.get_macd(ticker, timespan="hour")
    macd_vals = macd_data.get("results", {}).get("values", [{}])[0]
    histo = macd_vals.get("histogram", 0)
    print(f"   MACD Histo: {histo:.6f}")

    # 4. SMA (50)
    print("   Fetching SMA (50)...")
    sma_data = api.get_sma(ticker, timespan="hour", window=50)
    sma_val = sma_data.get("results", {}).get("values", [{}])[0].get("value", 0)
    print(f"   SMA (50, 1H): ${sma_val:.4f}")
    
    print("-" * 30)
    print("🧠 SYNTHESIS:")
    
    # Trend
    trend = "FAIL"
    if price > sma_val: trend = "BULLISH (Above SMA)"
    else: trend = "BEARISH (Below SMA)"
    
    # Momentum
    mom = "NEUTRAL"
    if rsi_val < 30: mom = "OVERSOLD"
    elif rsi_val > 70: mom = "OVERBOUGHT"
    
    # Direction
    direction = "FLAT"
    if histo > 0: direction = "EXPANDING UP"
    elif histo < 0: direction = "CONTRACTING/DOWN"
    
    print(f"   Trend:    {trend}")
    print(f"   Momentum: {mom} ({rsi_val:.1f})")
    print(f"   Energy:   {direction} ({histo:.6f})")
    
    # Verdict
    score = 0
    if price > sma_val: score += 1
    if rsi_val < 30: score += 2 # Buy dip
    if histo > 0: score += 1
    
    print(f"   Score:    {score}/4")
    if score >= 3: print("   🚀 VERDICT: STRONG BUY")
    elif score >= 1: print("   🛡️ VERDICT: HOLD / CONSOLIDATING")
    else: print("   ⚠️ VERDICT: WEAK / SELL RALLY")

if __name__ == "__main__":
    analyze_xtz()
