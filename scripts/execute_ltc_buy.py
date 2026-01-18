"""
Manual Buy Script: LTC-USD
==========================
Executes user command: "Buy LTC" with available cash.
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

def run_buy():
    print("🚀 Starting LTC Buy...")
    
    # 1. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    print(f"💰 Available Cash: ${cash:.2f}")
    
    if cash < 1.00:
        print("❌ Insufficient cash to buy LTC (Need > $1.00).")
        return

    # 2. Buy LTC
    target_pair = "LTC-USD"
    
    # Get Price first
    price_info = api.get_best_bid_ask(target_pair)
    if not price_info or target_pair not in price_info:
        print(f"❌ Could not fetch {target_pair} price.")
        return
        
    ask_price = float(price_info[target_pair]["ask_price"])
    print(f"ℹ️ {target_pair} Ask Price: ${ask_price:.2f}")
    
    # Calculate Qty (99% of cash to cover spread/fees)
    buy_amount = cash * 0.99
    qty = buy_amount / ask_price
    
    # Round to 8 decimals (LTC supports high precision)
    qty = float(f"{qty:.8f}")
    
    print(f"📈 Buying {qty:.8f} LTC with ${buy_amount:.2f}...")
    
    try:
        # Use asset_quantity
        buy_order = api.place_market_order(target_pair, "buy", asset_quantity=qty)
        
        if buy_order:
            print("✅ LTC Buy Order Placed Successfully!")
            print(f"🎉 Trade Complete: Bought {qty} LTC")
        else:
            print("❌ LTC Buy Failed (API returned None).")
    except Exception as e:
        print(f"❌ Buy Exception: {e}")

if __name__ == "__main__":
    run_buy()
