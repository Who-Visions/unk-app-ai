"""
Manual Rotation Script: XTZ -> DASH
===================================
Executes user command: "Sell Half XTZ, Buy DASH"
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ROBINHOOD_API_KEY')
PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY')

if not API_KEY or not PRIVATE_KEY:
    print("❌ Error: Credentials missing.")
    sys.exit(1)

api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)

def run_rotation():
    print("🚀 Starting XTZ -> DASH Rotation...")
    
    # 1. Get XTZ Holdings
    holdings = api.get_holdings()
    xtz_qty = 0.0
    for h in holdings:
        if h.asset_code == 'XTZ':
            xtz_qty = float(h.total_quantity)
            break
            
    if xtz_qty <= 0:
        print("❌ No XTZ holdings found.")
        return

    # 2. Sell Half - SKIPPED (ALREADY EXECUTED)
    # sell_qty = xtz_qty * 0.5
    # print(f"📉 Selling 50% XTZ: {sell_qty:.6f} coins...")
    # order = api.place_market_order("XTZ-USD", "sell", asset_quantity=sell_qty)
    
    # 3. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    print(f"💰 Available Cash: ${cash:.2f}")
    
    if cash < 1.00:
        print("❌ Insufficient cash to buy DASH (Need > $1.00).")
        return

    # 4. Buy DASH
    # Get Price first
    price_info = api.get_best_bid_ask("DASH-USD")
    if not price_info or "DASH-USD" not in price_info:
        print("❌ Could not fetch DASH price.")
        return
        
    ask_price = float(price_info["DASH-USD"]["ask_price"])
    print(f"ℹ️ DASH Ask Price: ${ask_price:.2f}")
    
    # Calculate Qty (98% of cash to cover spread/fees)
    buy_amount = cash * 0.98
    qty = buy_amount / ask_price
    
    # Round to 6 decimals (DASH supports high precision, but safe side)
    qty = float(f"{qty:.6f}")
    
    print(f"📈 Buying {qty:.6f} DASH with ${buy_amount:.2f}...")
    
    # Use asset_quantity, which we know works
    try:
        buy_order = api.place_market_order("DASH-USD", "buy", asset_quantity=qty)
        
        if buy_order:
            print("✅ DASH Buy Order Placed Successfully!")
            print(f"🎉 Rotation Complete: Bought {qty} DASH")
        else:
            print("❌ DASH Buy Failed (API returned None).")
    except Exception as e:
        print(f"❌ Buy Exception: {e}")
        # Try fallback: place_order directly if wrapper fails
        print("⚠️ Attempting raw place_order fallback...")
        try:
            api.place_order("DASH-USD", "buy", "market", quantity=str(qty), side="buy")
            print("✅ Fallback Order Sent.")
        except Exception as e2:
            print(f"❌ Fallback Failed: {e2}")

if __name__ == "__main__":
    run_rotation()
