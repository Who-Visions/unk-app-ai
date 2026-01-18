"""
Correction: Buy AAVE
====================
Allocates $9.40 to AAVE with 5-decimal precision.
"""
import os
import sys
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

def buy_aave():
    BUDGET = 9.40
    PAIR = "AAVE-USD"
    
    print(f"🛠️ RE-TRYING AAVE BUY (Budget: ${BUDGET:.2f})...")
    
    try:
        quote = api.get_best_bid_ask(PAIR)
        ask = float(quote[PAIR]['ask_price'])
        
        # Calc + Round
        raw_qty = (BUDGET * 0.995) / ask
        
        # AAVE constraint: 0.00001
        safe_qty = float(f"{raw_qty:.5f}")
        
        print(f"📉 Placing Order: {safe_qty} AAVE @ ${ask:.2f}...")
        order = api.place_market_order(PAIR, "buy", asset_quantity=safe_qty)
        
        if order:
            print(f"✅ BOUGHT AAVE")
        else:
            print(f"❌ Failed: {api.last_error}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    buy_aave()
