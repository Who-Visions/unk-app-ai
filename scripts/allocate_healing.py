"""
Healing Allocator: BONK, AERO, SHIB
===================================
Allocates remaining reserve (~$18.90) into 3 healing assets.
Budget: ~$6.30 each.
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

TARGETS = ['BONK-USD', 'AERO-USD', 'SHIB-USD']

def allocate_healing():
    print("🩹 INITIALIZING HEALING STRATEGY POSITIONS...")
    
    # 1. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    
    if cash < 3.00:
        print(f"❌ Cash too low (${cash:.2f}).")
        return

    print(f"💰 Reserve Capital: ${cash:.2f}")
    budget_per_coin = cash / 3.0
    print(f"🎯 Budget: ${budget_per_coin:.2f} per coin")
    
    for pair in TARGETS:
        symbol = pair.split('-')[0]
        print(f"📉 Buying {symbol}...")
        
        try:
            quote = api.get_best_bid_ask(pair)
            ask = float(quote[pair]['ask_price'])
            
            # 99% of budget to safe-guard fees
            raw_qty = (budget_per_coin * 0.99) / ask
            
            # Precision
            prec = 6
            if symbol in ['SHIB', 'BONK']: prec = 0 # Integer qty for memes usually safest or 0 decimals
            # Wait, SHIB is cheap, so qty is large. BONK too. 
            # Robinhood API often accepts many decimals but let's be safe with 0 for memes if huge qty, 
            # or 1. Actually SHIB < 0.001, so quantity is huge. Integers are safe.
            
            if symbol == 'AERO': prec = 2
            
            safe_qty = float(f"{raw_qty:.{prec}f}")
            
            print(f"   Qty: {safe_qty} @ ${ask:.8f}")
            order = api.place_market_order(pair, "buy", asset_quantity=safe_qty)
            
            if order:
                print(f"   ✅ BOUGHT {symbol}")
            else:
                print(f"   ❌ FAILED: {api.last_error}")
            
            time.sleep(1)

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    allocate_healing()
