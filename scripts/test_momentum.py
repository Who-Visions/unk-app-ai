
import requests
import json
import time

WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD',
    'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'ETC-USD',
    'XLM-USD', 'HBAR-USD', 'UNI-USD', 'AAVE-USD', 'COMP-USD'
]

def fetch_momentum_data():
    """
    Fetches 24h % Change from CryptoCompare for ALL Watchlist items.
    """
    print("Fetching momentum data...")
    try:
        # Build CSV of symbols (BTC,ETH,etc)
        syms = ",".join([s.split('-')[0] for s in WATCHLIST])
        url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={syms}&tsyms=USD"
        
        res = requests.get(url, timeout=5)
        data = res.json()
        
        found = 0
        if "RAW" in data:
            print(f"{'COIN':<8} | {'24h %':<8} | {'TREND'}")
            print("-" * 30)
            for sym in WATCHLIST:
                coin = sym.split('-')[0]
                if coin in data["RAW"]:
                    try:
                        # Extract 24h Change %
                        pct = data["RAW"][coin]["USD"]["CHANGEPCT24HOUR"]
                        trend = "🌊 UP" if pct > 1.0 else "📉 DOWN"
                        print(f"{coin:<8} | {pct:>7.2f}% | {trend}")
                        found += 1
                    except:
                        pass
        print("-" * 30)
        print(f"Momentum Data Updated. Found {found} coins.")
            
    except Exception as e:
        print(f"Momentum Fetch Error: {e}")

if __name__ == "__main__":
    fetch_momentum_data()
