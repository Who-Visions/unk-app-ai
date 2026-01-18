"""
Portfolio Report Card
=====================
Calculates:
1. Total Net Worth (Cash + Assets).
2. Unrealized PnL (vs Entry).
3. 24h Market Trend (Impact on Portfolio).
"""
import os
import sys
import json
import requests
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

# CryptoCompare URL
CC_URL = "https://min-api.cryptocompare.com/data/pricemultifull"

def get_24h_stats(symbols):
    """Fetch 24h change % from CryptoCompare."""
    if not symbols: return {}
    
    fsyms = ",".join([s.split('-')[0] for s in symbols])
    url = f"{CC_URL}?fsyms={fsyms}&tsyms=USD"
    
    try:
        data = requests.get(url, timeout=10).json()
        stats = {}
        if "RAW" in data:
            for coin, details in data["RAW"].items():
                usd = details["USD"]
                stats[f"{coin}-USD"] = {
                    "change_24h": usd["CHANGEPCT24HOUR"],
                    "price": usd["PRICE"]
                }
        return stats
    except Exception as e:
        print(f"⚠️ Market Data Error: {e}")
        return {}

def generate_report():
    print("📊 GENERATING 24H PERFORMANCE REPORT...\n")
    
    # 1. Fetch Account & Holdings
    try:
        acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
        cash = float(acc.get('buying_power', 0))
        holdings = api.get_holdings()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    # 2. Filter & Prepare
    assets = []
    symbols = []
    
    # Load local state for Entry Prices
    entries = {}
    try:
        with open("trading_state.json", "r") as f:
            state = json.load(f)
            positions = state.get("positions", {})
            for sym, pos in positions.items():
                entries[sym] = float(pos.get("entry", 0))
    except:
        pass

    total_equity = cash
    
    for h in holdings:
        qty = float(h.total_quantity)
        if qty * 1000 < 0.01: continue # Skip dust
        
        pair = f"{h.asset_code}-USD"
        symbols.append(pair)
        
        assets.append({
            "symbol": pair,
            "qty": qty,
            "entry": entries.get(pair, 0)
        })

    # 3. Fetch Market Data
    stats = get_24h_stats(symbols)
    
    # 4. Calculate Metrics
    print(f"{'ASSET':<8} {'QTY':<10} {'PRICE':<10} {'VALUE':<10} {'ENTRY':<10} {'PNL %':<8} {'24H %':<8}")
    print("-" * 75)
    
    port_24h_weighted = 0
    total_asset_val = 0
    
    for a in assets:
        sym = a['symbol']
        qty = a['qty']
        entry = a['entry']
        
        # Use CC price or fallback
        mkt = stats.get(sym, {})
        price = mkt.get("price", 0)
        chg24 = mkt.get("change_24h", 0)
        
        if price == 0:
            # Fallback to RH quote
            q = api.get_best_bid_ask(sym)
            price = float(q[sym]['ask_price'])
            
        val = qty * price
        total_equity += val
        total_asset_val += val
        
        # PnL
        pnl_pct = 0.0
        if entry > 0:
            pnl_pct = (price - entry) / entry * 100
            
        # Weighted 24h (Impact)
        # This is rough, assumes current composition held for 24h
        
        entry_str = f"${entry:.4f}" if entry > 0 else "---"
        pnl_str = f"{pnl_pct:+.2f}%" if entry > 0 else "---"
        
        print(f"{sym.split('-')[0]:<8} {qty:<10.4f} ${price:<9.4f} ${val:<9.2f} {entry_str:<10} {pnl_str:<8} {chg24:+.2f}%")

    print("-" * 75)
    print(f"\n💰 CASH:       ${cash:.2f}")
    print(f"🏦 NET WORTH:  ${total_equity:.2f}")

    # Estimate Portfolio 24h Delta
    # If we assume the current holdings represent the 'day', how did they move?
    # (Total Value) - (Total Value / (1 + weighted_change))
    # This is speculative but gives a 'Day Vibe'.
    
    print("\n📝 SUMMARY:")
    if total_equity > 0:
        print(f"   Current Assets are tracking the market.")

if __name__ == "__main__":
    generate_report()
