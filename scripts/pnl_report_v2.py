"""
PnL Report V2 (Simple)
======================
Just the facts: Qty, Entry, Price, Value.
"""
import sys
import json
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

def simple_pnl():
    print("📊 HOLDINGS REPORT")
    print("-" * 60)
    print(f"{'ASSET':<8} {'QTY':<10} {'ENTRY':<10} {'PRICE':<10} {'VALUE':<10} {'PNL':<8}")
    print("-" * 60)
    
    # 1. Get Holdings
    try:
        holdings = api.get_holdings()
        acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
        cash = float(acc.get('buying_power', 0))
    except:
        print("❌ API Error")
        return

    # 2. Get Entries
    entries = {}
    try:
        with open("trading_state.json", "r") as f:
            state = json.load(f)
            for s, p in state.get("positions", {}).items():
                entries[s.split('-')[0]] = float(p.get("entry", 0))
    except:
        pass

    total = cash
    
    for h in holdings:
        qty = float(h.total_quantity)
        sym = h.asset_code
        if qty < 0.001 and sym != 'BTC': continue
        
        # Get Price
        pair = f"{sym}-USD"
        try:
            q = api.get_best_bid_ask(pair)
            price = float(q[pair]['ask_price'])
        except:
            price = 0
            
        val = qty * price
        total += val
        
        entry = entries.get(sym, 0)
        pnl_pct = 0.0
        if entry > 0:
            pnl_pct = (price - entry) / entry * 100
            
        entry_s = f"${entry:.4f}" if entry > 0 else "---"
        pnl_s = f"{pnl_pct:+.1f}%" if entry > 0 else "---"
            
        print(f"{sym:<8} {qty:<10.4f} {entry_s:<10} ${price:<9.4f} ${val:<9.2f} {pnl_s:<8}")

    print("-" * 60)
    print(f"💰 CASH:      ${cash:.2f}")
    print(f"🏦 NET WORTH: ${total:.2f}")

if __name__ == "__main__":
    simple_pnl()
