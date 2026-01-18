"""
Smart Rotation: AAVE, XTZ, LTC
==============================
Allocates 20% of total cash to each of the 3 targets.
Total Invested: 60%.
Cash Reserve: 40%.
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

api = RobinhoodCryptoAPI()

TARGETS = ['AAVE-USD', 'XTZ-USD', 'LTC-USD']
ALLOCATION_PCT = 0.20  # 20% each

def smart_rotate():
    print("🧠 EXECUTING SMART ROTATION...")
    
    # 1. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    total_cash = float(acc.get('buying_power', 0))
    
    if total_cash < 5.00:
        print(f"❌ Cash too low (${total_cash:.2f}) for 3-way split.")
        return

    print(f"💰 Total Capital: ${total_cash:.2f}")
    
    # 2. Calculate Per-Asset Budget
    # We base off INITIAL cash to ensure equal checking, 
    # but we need to verify cash remains for each step (in case of drift).
    budget_per_coin = total_cash * ALLOCATION_PCT
    print(f"🎯 Allocation Target: ${budget_per_coin:.2f} per coin ({ALLOCATION_PCT*100}%)")
    print(f"🛡️  Reserve Cash:     ${total_cash * (1 - (ALLOCATION_PCT * len(TARGETS))):.2f}")
    
    print("-" * 40)
    
    for pair in TARGETS:
        symbol = pair.split('-')[0]
        print(f"📉 Allocating {symbol}...")
        
        try:
            # Fetch Price
            quote = api.get_best_bid_ask(pair)
            ask = float(quote[pair]['ask_price'])
            
            # Calc Qty
            # Safety buffer 0.5% on price/fees
            safe_budget = budget_per_coin * 0.995 
            qty = safe_budget / ask
            
            # Precision Check (Naive but functional for majors)
            prec = 6
            if symbol in ['XTZ']: prec = 2 # XTZ usually safe at 2
            if symbol in ['LTC', 'AAVE']: prec = 6 
            
            safe_qty = float(f"{qty:.{prec}f}")
            
            # Min Notional Check ($1.00)
            if (safe_qty * ask) < 1.00:
                print(f"   ⚠️ Amount too small (${safe_qty*ask:.2f}). Skipping.")
                continue

            # Execute
            print(f"   Buying {safe_qty} {symbol} @ ${ask:.4f}...")
            order = api.place_market_order(pair, "buy", asset_quantity=safe_qty)
            
            if order:
                print(f"   ✅ BOUGHT {symbol}")
            else:
                print(f"   ❌ FAILED to buy {symbol}")
                
            time.sleep(1) # Pace API
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("-" * 40)
    print("🏁 Rotation Complete.")

if __name__ == "__main__":
    smart_rotate()
