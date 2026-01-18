"""
PANIC SELL SCRIPT
=================
Liquidates ALL crypto holdings immediately.
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ROBINHOOD_API_KEY')
priv_key = os.getenv('ROBINHOOD_PRIVATE_KEY')

if not api_key or not priv_key:
    print("❌ Credentials missing.")
    sys.exit(1)

api = RobinhoodCryptoAPI(api_key=api_key, private_key_base64=priv_key)

def panic_sell():
    print("🚨 INITIATING EMERGENCY LIQUIDATION 🚨")
    
    try:
        holdings = api.get_holdings()
    except Exception as e:
        print(f"❌ Failed to fetch holdings: {e}")
        return

    sold_count = 0
    
    for h in holdings:
        qty = float(h.total_quantity)
        sym = f"{h.asset_code}-USD"
        
        if qty > 0:
            # Check value rough estimate (to skip dust if needed, but we try all)
            # We don't have price handy easily without another call, so just TRY selling.
            
            print(f"📉 Selling {qty} {h.asset_code}...")
            
            try:
                # Max precision logic from CLI
                prec = 6
                if h.asset_code in ['DOGE', 'ADA', 'XRP']: prec = 1
                if h.asset_code in ['SHIB', 'PEPE', 'BONK']: prec = 0
                
                safe_qty = float(f"{qty:.{prec}f}")
                
                if safe_qty <= 0:
                    print(f"   ⚠️ Quantity too small after rounding: {safe_qty}")
                    continue

                order = api.place_market_order(sym, "sell", asset_quantity=safe_qty)
                
                if order:
                    print(f"   ✅ SOLD {h.asset_code}")
                    sold_count += 1
                else:
                    print(f"   ❌ Failed to place order for {h.asset_code}")
                    
            except Exception as e:
                print(f"   ❌ Error selling {h.asset_code}: {e}")
                
    print(f"🏁 Liquidation Complete. Sold {sold_count} positions.")
    
    # Show Cash
    try:
        acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
        cash = float(acc.get('buying_power', 0))
        print(f"💰 Final Cash Balance: ${cash:.2f}")
    except:
        pass

if __name__ == "__main__":
    panic_sell()
