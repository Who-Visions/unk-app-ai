"""
Green Scalper Mode 💸 (ROTATION v3)
====================================
Sell anything > +0.3% gain -> Flip into dips.
Reads entry prices from trading_state.json (shared with main bot).
"""
import time
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Setup paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

# Load Env
load_dotenv()
API_KEY = os.getenv('ROBINHOOD_API_KEY')
PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY')

# Config
TARGETS = ['ETH-USD', 'ADA-USD', 'ETC-USD']
SELL_TARGET = 0.3  # Sell if PnL > 0.3%
POLL_INTERVAL = 10 # seconds (fast loop)
STATE_FILE = "trading_state.json"

def load_entries():
    """Load entry prices from main bot's state file."""
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('positions', {})
    except:
        return {}

def main():
    if not API_KEY or not PRIVATE_KEY:
        print("❌ Missing Robinhood Credentials!")
        return

    api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)
    
    print("🚀 GREEN SCALPER v3 - ROTATION MODE")
    print(f"Targets: {', '.join(TARGETS)}")
    print(f"Sell Target: +{SELL_TARGET}%")
    print("-" * 50)

    while True:
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Load entries from main bot state
            positions = load_entries()
            
            # Get Current Prices
            quotes = api.get_best_bid_ask(*TARGETS)
            if not quotes:
                print(f"[{timestamp}] ⚠️ No quotes")
                time.sleep(5)
                continue
            
            # Get Buying Power
            acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
            buying_power = float(acc.get('buying_power', 0))
            
            print(f"\n[{timestamp}] 💰 BP: ${buying_power:.2f}")
            
            # Get actual holdings from API
            holdings = api.get_holdings()
            actual_holdings = {}
            for h in holdings:
                if float(h.total_quantity) > 0:
                    actual_holdings[f"{h.asset_code}-USD"] = float(h.total_quantity)
            
            # Process Each Target
            for sym in TARGETS:
                if sym not in quotes:
                    continue
                    
                price = quotes[sym]['ask_price']
                
                # Check ACTUAL holdings from API (not stale state file)
                actual_qty = actual_holdings.get(sym, 0)
                
                # Check if we have this position with entry price in state
                if sym in positions and actual_qty > 0:
                    pos = positions[sym]
                    entry = float(pos.get('entry', 0))
                    
                    if entry > 0:
                        pnl_pct = ((price - entry) / entry) * 100
                        
                        status = f"  {sym}: ${price:.4f} | Entry: ${entry:.4f} | PnL: {pnl_pct:+.2f}%"
                        
                        # SELL CONDITION: > 0.3%
                        if pnl_pct >= SELL_TARGET:
                            print(f"{status} -> 💰 SELLING!")
                            order = api.place_market_order(sym, "sell", asset_quantity=actual_qty)
                            if order:
                                print(f"     ✅ Sold {actual_qty:.6f} @ ${price:.4f}")
                            else:
                                print(f"     ❌ Sell failed")
                        else:
                            print(status)
                    else:
                        print(f"  {sym}: ${price:.4f} | Qty: {actual_qty:.6f} | NO ENTRY DATA")
                elif actual_qty > 0:
                    print(f"  {sym}: ${price:.4f} | HOLDING (no entry data)")
                else:
                    # We don't hold this - potential BUY target
                    print(f"  {sym}: ${price:.4f} | FLAT")
                    
                    # BUY CONDITION: We have freed cash
                    if buying_power > 1.0:
                        spend = buying_power * 0.95
                        qty_to_buy = spend / price
                        
                        print(f"     ♻️ ROTATING INTO {sym}...")
                        order = api.place_market_order(sym, "buy", asset_quantity=qty_to_buy)
                        if order:
                            print(f"     ✅ Bought {qty_to_buy:.6f} @ ${price:.4f}")
                            buying_power = 0
                        else:
                            print(f"     ❌ Buy failed")
            
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    main()
