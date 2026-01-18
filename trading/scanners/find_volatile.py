
import os
import sys
import json
import urllib.request
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD',
    'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'ETC-USD',
    'XLM-USD', 'HBAR-USD', 'UNI-USD', 'AAVE-USD', 'COMP-USD', 'XTZ-USD',
    'DOT-USD', 'SUI-USD', 'OP-USD', 'ARB-USD', 'SEI-USD', 'CRV-USD', 
    'LDO-USD', 'ENA-USD', 'WIF-USD', 'VIRTUAL-USD', 'AERO-USD', 'SYRUP-USD', 'XCN-USD'
]

def find_volatility():
    print(f"--- Scanning Top Market Assets for Volatile Momentum ---")
    
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=50&tsym=USD"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.loads(res.read().decode())
        
        if data.get("Response") == "Error":
             print(f"Error: {data.get('Message')}")
             return

        results = []
        for item in data.get("Data", []):
            coin = item.get("CoinInfo", {}).get("Name")
            raw = item.get("RAW", {}).get("USD", {})
            
            change_24h = raw.get("CHANGEPCT24HOUR", 0)
            vol_24h = raw.get("VOLUME24HOUR", 0)
            price = raw.get("PRICE", 0)
            
            results.append({
                "symbol": f"{coin}-USD",
                "change_24h": change_24h,
                "abs_change": abs(change_24h),
                "vol_24h": vol_24h,
                "price": price
            })
        
        # Sort by absolute volatility
        results.sort(key=lambda x: x["abs_change"], reverse=True)
        
        print(f"\n{'SYMBOL':<12} | {'24H CHANGE':<12} | {'VOLUME (USD)':<15} | {'PRICE':<10}")
        print("-" * 55)
        for r in results[:15]:
            print(f"{r['symbol']:<12} | {r['change_24h']:>10.2f}% | ${r['vol_24h']:>13,.0f} | ${r['price']:>9.4f}")
            
        if results:
            winner = results[0]
            print(f"\n🏆 MOST VOLATILE: {winner['symbol']} at {winner['change_24h']:.2f}% change.")
        
    except Exception as e:
        print(f"Scan failed: {e}")

if __name__ == "__main__":
    find_volatility()
