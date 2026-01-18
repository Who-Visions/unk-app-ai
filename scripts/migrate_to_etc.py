
"""
scripts/migrate_to_etc.py

EMERGENCY MIGRATION SCRIPT
1. Cancels all open orders.
2. Liquidates ALL non-ETC assets.
3. Buys ETC-USD with essentially 100% of buying power.
4. Verifies Entry Price.

Usage:
  & c:/Users/super/Watchtower/unk-app-ai/venv/Scripts/python.exe scripts/migrate_to_etc.py
"""
import sys
import os
import time
import math
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def run_migration():
    load_dotenv()
    print("🚀 STARTING ASSET MIGRATION TO ETC-USD...")
    
    api = RobinhoodCryptoAPI()
    
    # 1. CANCEL ALL ORDERS
    print("--- Step 1: Cancelling Open Orders ---")
    orders = api.get_orders(state="open")
    for o in orders:
        print(f"Cancelling {o.side} {o.symbol}...")
        api.cancel_order(o.order_id)
    time.sleep(2)
    
    # 2. LIQUIDATE NON-ETC
    print("--- Step 2: Liquidating Non-ETC Assets ---")
    holdings = api.get_holdings()
    sold_any = False
    
    for h in holdings:
        if h.asset_code == "ETC":
            continue
            
        if h.available_quantity > 0:
            pair = f"{h.asset_code}-USD"
            print(f"Selling {h.available_quantity} {pair}...")
            # Use market sell
            res = api.place_market_order(pair, "sell", asset_quantity=h.available_quantity)
            if res:
                print(f"  > Order Placed: {res.state}")
                sold_any = True
            else:
                print(f"  > Failed to sell {pair}")
    
    if sold_any:
        print("Waiting 10 seconds for settlements...")
        time.sleep(10)
    else:
        print("Nothing to sell.")
        
    # 3. BUY ETC
    print("--- Step 3: Buying ETC-USD ---")
    
    # Refresh Buying Power
    acct = api.get_account()
    bp = float(acct.get("buying_power", 0))
    print(f"Available Buying Power: ${bp:.2f}")
    
    if bp < 1.0:
        print("Not enough funds to buy meaningful amount.")
        return
        
    # Safety buffer for market buy (fees + slippage) -> Use 98%
    amount_to_spend = bp * 0.98
    
    print(f"Placing Buy Order for ${amount_to_spend:.2f} of ETC-USD...")
    res = api.place_market_order("ETC-USD", "buy", quote_amount=amount_to_spend)
    
    if res:
        print(f"  > Buy Order Placed: {res.state}")
        # Wait for fill
        for _ in range(10):
            time.sleep(2)
            o = api.get_order(res.order_id)
            if o.state == "filled":
                print("  > FILLED!")
                break
            print(f"  > Status: {o.state}...")
    else:
        print("  > Buy Failed.")
        
    # 4. VERIFY ENTRY
    print("--- Step 4: Verification ---")
    time.sleep(3)
    holdings = api.get_holdings("ETC")
    for h in holdings:
        if h.asset_code == "ETC":
            print(f"✅ ETC POSITION SECURED")
            print(f"   Qty:   {h.total_quantity}")
            print(f"   Entry: ${h.average_buy_price} (Target ~$13.08)")
            
    print("DONE. Please restart unk_trader_cli.py now.")

if __name__ == "__main__":
    run_migration()
