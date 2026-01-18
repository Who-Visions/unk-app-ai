"""
Manual Rotation Script: ETH -> XTZ
==================================
Executes user command: "Move 30% ETH to XTZ"
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
    print("🚀 Starting ETH -> XTZ Rotation (30%)...")
    
    # 1. Get ETH Holdings
    holdings = api.get_holdings()
    eth_qty = 0.0
    for h in holdings:
        if h.asset_code == 'ETH':
            eth_qty = float(h.total_quantity)
            break
            
    if eth_qty <= 0:
        print("❌ No ETH holdings found.")
        return

    print(f"ℹ️ Current ETH Holdings: {eth_qty:.8f}")

    # 2. Sell 30% - SKIPPED (ALREADY DONE)
    # sell_qty = eth_qty * 0.30
    # sell_qty = float(f"{sell_qty:.6f}")
    # print(f"📉 Selling 30% ETH: {sell_qty:.6f} coins...")
    
    # try:
    #     order = api.place_market_order("ETH-USD", "sell", asset_quantity=sell_qty)
    #     if not order:
    #          print("❌ Sell Order Failed (API returned None).")
    #          return
    # except Exception as e:
    #     print(f"❌ Sell Order Error: {e}")
    #     return
        
    # print(f"✅ Sell Placed. Waiting for settlement (10s)...")
    # time.sleep(10)
    
    # 3. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    print(f"💰 Available Cash: ${cash:.2f}")
    
    if cash < 1.00:
        print("❌ Insufficient cash to buy XTZ (Need > $1.00).")
        return

    # 4. Buy XTZ
    target_pair = "XTZ-USD"
    
    # Get Price
    price_info = api.get_best_bid_ask(target_pair)
    if not price_info or target_pair not in price_info:
        print(f"❌ Could not fetch {target_pair} price.")
        return
        
    ask_price = float(price_info[target_pair]["ask_price"])
    print(f"ℹ️ {target_pair} Ask Price: ${ask_price:.4f}")
    
    # Calculate Qty (99% of cash to cover spread/fees)
    buy_amount = cash * 0.99
    xtz_qty = buy_amount / ask_price
    
    # Round to 2 decimals (Ultra safe)
    xtz_qty = float(f"{xtz_qty:.2f}")
    
    print(f"📈 Buying {xtz_qty:.6f} XTZ with ${buy_amount:.2f}...")
    
    try:
        buy_order = api.place_market_order(target_pair, "buy", asset_quantity=xtz_qty)
        
        if buy_order:
            print("✅ XTZ Buy Order Placed Successfully!")
            print(f"🎉 Rotation Complete: Sold ETH -> Bought XTZ")
        else:
            print("❌ XTZ Buy Failed.")
    except Exception as e:
        print(f"❌ Buy Exception: {e}")

if __name__ == "__main__":
    run_rotation()
