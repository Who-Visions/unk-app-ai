"""
Massive (Polygon) Portfolio Scanner
===================================
Scans all active positions in trading_state.json using Massive API indicators.
"""
import json
import os
import time
from services.massive_api import MassiveAPI

STATE_FILE = "trading_state.json"

def scan_portfolio():
    print("🦅 MASSIVE API: PORTFOLIO WIDE SCAN")
    print("=" * 40)
    
    # 1. Load Positions
    if not os.path.exists(STATE_FILE):
        print("❌ No trading state found.")
        return
        
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
        
    positions = state.get("positions", {})
    api = MassiveAPI()
    
    print(f"🔍 Scanning {len(positions)} positions...")
    print("-" * 40)
    
    for symbol, data in positions.items():
        qty = float(data.get("qty", 0))
        entry = float(data.get("entry", 0))
        
        # Skip dust logic (very small amounts might be residue, but user asked for ALL)
        if qty <= 0:
            continue
            
        print(f"💎 Analyzing {symbol} (Qty: {qty:.6f} | Entry: ${entry:.4f})")
        
        # Rate Limit Sleep (Basic Plan has 5 calls/min)
        # We need to be careful. 1 position = ~3 calls (Price, RSI, MACD)
        # 5 positions = 15 calls.
        # We must sleep ~15s between positions to be safe-ish or expect slow scan.
        # Actually, let's just run it and handle errors or sleep a bit.
        # "5 calls / minute" is strict.
        # We might need to space this out significantly.
        # Let's do 12s sleep between assets.
        
        analyze_asset(api, symbol)
        print("-" * 40)
        # API wrapper now handles 429 backoff automatically

def analyze_asset(api, ticker):
    # Normalize ticker (e.g. BTC-USD -> X:BTCUSD)
    poly_ticker = ticker
    if "-" in ticker and "X:" not in ticker:
         parts = ticker.split('-')
         poly_ticker = f"X:{parts[0]}{parts[1]}"

    # A. Price (Fallback Logic)
    price = 0
    source = "Unknown"
    
    # Try Prev Close (Reliable)
    prev = api.get_previous_close(poly_ticker)
    if prev and "results" in prev and len(prev["results"]) > 0:
        res = prev["results"][0]
        price = res.get("c", 0)
        source = "Prev Close"
        
    print(f"   Price: ${price:.4f} ({source})")
    
    # B. RSI
    rsi_val = 50
    try:
        rsi_data = api.get_rsi(poly_ticker, timespan="hour", window=14)
        if rsi_data and "results" in rsi_data:
             vals = rsi_data.get("results", {}).get("values", [])
             if vals: rsi_val = vals[0].get("value", 50)
        print(f"   RSI (1H): {rsi_val:.2f}")
    except:
        print("   RSI: n/a")

    # C. MACD
    histo = 0
    try:
        macd_data = api.get_macd(poly_ticker, timespan="hour")
        if macd_data and "results" in macd_data:
             vals = macd_data.get("results", {}).get("values", [])
             if vals: histo = vals[0].get("histogram", 0)
        print(f"   MACD Histo: {histo:.6f}")
    except:
        print("   MACD: n/a")
        
    # Analysis
    trend = "NEUTRAL"
    if rsi_val < 30: trend = "OVERSOLD (BUY?)"
    elif rsi_val > 70: trend = "OVERBOUGHT (SELL?)"
    elif histo > 0: trend = "BULLISH MOMENTUM"
    elif histo < 0: trend = "BEARISH MOMENTUM"
    
    print(f"   🧠 VERDICT: {trend}")

if __name__ == "__main__":
    scan_portfolio()
