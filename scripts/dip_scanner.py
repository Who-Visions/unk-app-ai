"""
Meme Coin Dip Scanner
======================
Watches penny cryptos for dips to buy.
Uses Pattern Scalp logic: wait for manipulation, then reversal.
"""
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
import time
from datetime import datetime

api = RobinhoodCryptoAPI(
    api_key='rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814',
    private_key_base64='bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='
)

# Penny cryptos to watch
WATCHLIST = ['PEPE-USD', 'BONK-USD', 'SHIB-USD', 'FLOKI-USD', 'PENGU-USD', 'PNUT-USD']

# Store initial prices
baseline = {}

def get_price(symbol):
    """Get current bid price."""
    try:
        p = api._request('GET', f'/api/v1/crypto/marketdata/best_bid_ask/?symbol={symbol}')
        if p and p.get('results'):
            return float(p['results'][0].get('bid_inclusive_of_sell_spread', 0))
    except:
        pass
    return None

def format_price(price):
    """Format price based on magnitude."""
    if price < 0.0001:
        return f"${price:.10f}"
    elif price < 0.01:
        return f"${price:.8f}"
    elif price < 1:
        return f"${price:.6f}"
    else:
        return f"${price:.4f}"

print("=== MEME COIN DIP SCANNER ===")
print("Strategy: Wait for -3% dip, then buy the reversal")
print()

# Get baseline prices
print("Getting baseline prices...")
for sym in WATCHLIST:
    price = get_price(sym)
    if price:
        baseline[sym] = price
        print(f"  {sym}: {format_price(price)}")

print()
print("Watching for dips... (Ctrl+C to stop)")
print("-" * 60)

scan_count = 0
try:
    while True:
        scan_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        
        alerts = []
        for sym in WATCHLIST:
            price = get_price(sym)
            if price and sym in baseline:
                change = (price - baseline[sym]) / baseline[sym] * 100
                
                if change <= -3.0:
                    alerts.append((sym, price, change, "DIP ALERT"))
                elif change <= -5.0:
                    alerts.append((sym, price, change, "BIG DIP"))
                elif change >= 3.0:
                    alerts.append((sym, price, change, "PUMP"))
        
        if alerts:
            print(f"\n[{now}] ALERTS:")
            for sym, price, change, alert_type in alerts:
                emoji = "🔴" if "DIP" in alert_type else "🟢"
                print(f"  {emoji} {alert_type}: {sym} {change:+.2f}% @ {format_price(price)}")
        else:
            # Show status every 10 scans
            if scan_count % 10 == 0:
                print(f"[{now}] Scan #{scan_count} - No alerts (waiting for -3% dip)")
        
        time.sleep(5)  # Check every 5 seconds
        
except KeyboardInterrupt:
    print("\n\nScanner stopped.")
    print("Final prices:")
    for sym in WATCHLIST:
        price = get_price(sym)
        if price and sym in baseline:
            change = (price - baseline[sym]) / baseline[sym] * 100
            print(f"  {sym}: {format_price(price)} ({change:+.2f}%)")
