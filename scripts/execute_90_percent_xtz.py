"""
Aggressive Rotation: 90% ALL IN XTZ
===================================
Strategy:
1. Sell 100% LTC
2. Sell 100% remaining ETH
3. Wait for settlement
4. Buy XTZ with 100% of proceeds
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

best_api_key = os.getenv('ROBINHOOD_API_KEY')
best_priv_key = os.getenv('ROBINHOOD_PRIVATE_KEY')

api = RobinhoodCryptoAPI(api_key=best_api_key, private_key_base64=best_priv_key)

def run_all_in():
    print("🚀 EXECUTING 90% XTZ CONVICTION PLAY...")
    
    # 1. LIQUIDATE SOURCES (LTC, ETH)
    holdings = api.get_holdings()
    
    for h in holdings:
        sym = f"{h.asset_code}-USD"
        qty = float(h.total_quantity)
        
        if h.asset_code in ['LTC', 'ETH'] and qty > 0:
            print(f"📉 Liquidating {h.asset_code} ({qty})...")
            try:
                # Use max precision allowed
                prec = 6 if h.asset_code == 'ETH' else 6
                safe_qty = float(f"{qty:.{prec}f}")
                
                api.place_market_order(sym, "sell", asset_quantity=safe_qty)
                print(f"✅ Sold {h.asset_code}")
            except Exception as e:
                print(f"❌ Error selling {h.asset_code}: {e}")
    
    print("⏳ Waiting 15s for settlement...")
    time.sleep(15)
    
    # 2. SWEEP CASH INTO XTZ
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    print(f"💰 Total Cash Sweep: ${cash:.2f}")
    
    if cash < 1.00:
        print("❌ Not enough cash generated.")
        return

    # 3. BUY XTZ
    target_pair = "XTZ-USD"
    price_info = api.get_best_bid_ask(target_pair)
    ask_price = float(price_info[target_pair]["ask_price"])
    
    # Use 98% of cash to be safe on fees/spread
    buy_amount = cash * 0.98 
    qty = buy_amount / ask_price
    
    # Round to 2 decimals for XTZ (Safety)
    safe_qty = float(f"{qty:.2f}")
    
    print(f"📈 Buying {safe_qty} XTZ @ ${ask_price:.4f}...")
    
    try:
        order = api.place_market_order(target_pair, "buy", asset_quantity=safe_qty)
        if order:
            print(f"🎉 CONVICTION TRADE COMPLETE. WE ARE ALL IN XTZ.")
        else:
            print("❌ Buy Failed.")
    except Exception as e:
        print(f"❌ Buy Error: {e}")

if __name__ == "__main__":
    run_all_in()
