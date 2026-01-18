"""
Market Scanner: Trend Hunter (> +2%)
====================================
Fetches 24h change for all Robinhood-supported assets.
Filters for gains > +2.0%.
"""
import requests
import sys

# Full Robinhood Tradable List
WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD',
    'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'ETC-USD',
    'XLM-USD', 'HBAR-USD', 'UNI-USD', 'AAVE-USD', 'COMP-USD', 'XTZ-USD',
    'DOT-USD', 'SUI-USD', 'OP-USD', 'ARB-USD', 'SEI-USD', 'CRV-USD', 
    'LDO-USD', 'ENA-USD', 'WIF-USD', 'VIRTUAL-USD', 'AERO-USD', 'SYRUP-USD', 'XCN-USD'
]

def scan_market():
    print("🔍 Scanning Market for Momentum (> +2.0%)...")
    
    # 1. Build Query
    syms = ",".join([s.split('-')[0] for s in WATCHLIST])
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={syms}&tsyms=USD"
    
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    if "RAW" not in data:
        print("❌ No data returned.")
        return

    # 2. Process & Filter
    results = []
    
    for sym in WATCHLIST:
        coin = sym.split('-')[0]
        if coin in data["RAW"]:
            try:
                raw = data["RAW"][coin]["USD"]
                price = raw["PRICE"]
                pct_24h = raw["CHANGEPCT24HOUR"]
                
                if pct_24h >= 2.0:
                    results.append({
                        "symbol": sym,
                        "price": price,
                        "change": pct_24h
                    })
            except:
                pass

    # 3. Sort & Display
    results.sort(key=lambda x: x['change'], reverse=True)
    
    if not results:
        print("❄️ No assets found matching criteria (> +2%). Market is cold.")
        return

    print(f"\n✅ FOUND {len(results)} ASSETS ON THE MOVE:\n")
    print(f"{'ASSET':<10} {'PRICE':<12} {'24H CHG':<10}")
    print("-" * 35)
    
    for r in results:
        sym = r['symbol'].split('-')[0]
        print(f"{sym:<10} ${r['price']:<11.4f} +{r['change']:.2f}%")

if __name__ == "__main__":
    scan_market()
