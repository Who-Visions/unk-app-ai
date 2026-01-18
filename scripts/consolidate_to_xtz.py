"""
Consolidate to XTZ (Preserve BTC, ETH, LTC)
=============================================
Liquidates all assets EXCEPT BTC, ETH, LTC, and XTZ.
Sweeps all resulting cash into XTZ.
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

PROTECTED = ['BTC', 'ETH', 'LTC', 'XTZ']
TARGET_PAIR = "XTZ-USD"

def consolidate():
    print("🚜 STARTING CONSOLIDATION TO XTZ...")
    print(f"🛡️  Protected Assets: {PROTECTED}")
    
    # 1. LIQUIDATE NON-PROTECTED
    try:
        holdings = api.get_holdings()
    except Exception as e:
        print(f"❌ Failed to get holdings: {e}")
        return

    sold_count = 0
    
    for h in holdings:
        if h.asset_code in PROTECTED:
            continue
            
        qty = float(h.total_quantity)
        if qty <= 0: continue
        
        pair = f"{h.asset_code}-USD"
        print(f"📉 Liquidating {h.asset_code} ({qty})...")
        
        try:
            # Precision logic
            prec = 6
            if h.asset_code in ['BONK', 'SHIB', 'PEPE']: prec = 0
            if h.asset_code in ['DOGE', 'ADA', 'XRP', 'AERO']: prec = 1
            
            safe_qty = float(f"{qty:.{prec}f}")
            
            if safe_qty <= 0:
                print(f"   ⚠️ Qty too small to sell: {safe_qty}")
                continue

            order = api.place_market_order(pair, "sell", asset_quantity=safe_qty)
            if order:
                print(f"   ✅ SOLD {h.asset_code}")
                sold_count += 1
            else:
                print(f"   ❌ Failed to sell {h.asset_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    print(f"✓ Liquidation phase complete. Sold {sold_count} positions.")
    time.sleep(5) # Allow for settlement/updates
    
    # 2. SWEEP CASH INTO XTZ
    try:
        acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
        cash = float(acc.get('buying_power', 0))
    except:
        print("❌ Failed to fetch cash.")
        return

    print(f"💰 Available Cash: ${cash:.2f}")
    
    if cash < 1.00:
        print("⚠️ Not enough cash to buy XTZ.")
        return

    print(f"📈 Sweeping ${cash:.2f} into XTZ...")
    
    try:
        quote = api.get_best_bid_ask(TARGET_PAIR)
        ask = float(quote[TARGET_PAIR]['ask_price'])
        
        # 99% of cash
        buy_amt = cash * 0.99
        qty = buy_amt / ask
        safe_qty = float(f"{qty:.2f}") # XTZ 2 decimals
        
        print(f"   Buying {safe_qty} XTZ @ ${ask:.4f}...")
        order = api.place_market_order(TARGET_PAIR, "buy", asset_quantity=safe_qty)
        
        if order:
            print("   ✅ BOUGHT XTZ. Consolidation Complete.")
        else:
            print(f"   ❌ Buy Failed: {api.last_error}")
            
    except Exception as e:
        print(f"   ❌ Error buying XTZ: {e}")

if __name__ == "__main__":
    consolidate()
