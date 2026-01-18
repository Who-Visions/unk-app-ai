"""
Strategic Re-entry: XTZ Limit Buy
=================================
Places a Limit Buy Order for XTZ-USD @ $0.617.
Locks capital to prevent bot from spending it elsewhere.
"""
import os
import sys
import time
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

api = RobinhoodCryptoAPI()

def place_reentry_order():
    TARGET_PRICE = 0.617
    PAIR = "XTZ-USD"
    
    print(f"🎯 Preparing Re-entry: {PAIR} @ Limit ${TARGET_PRICE}")
    
    # 1. Get Cash
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    cash = float(acc.get('buying_power', 0))
    print(f"💰 Available Capital: ${cash:.2f}")
    
    if cash < 1.00:
        print("❌ Insufficient funds.")
        return

    # 2. Calculate Qty
    # Use 99% of cash to cover potential fees/buffer
    buy_amount = cash * 0.99
    qty = buy_amount / TARGET_PRICE
    
    # Round to 2 decimals for XTZ
    safe_qty = float(f"{qty:.2f}")
    
    print(f"📉 Placing LIMIT BUY: {safe_qty} XTZ @ ${TARGET_PRICE:.4f}...")
    
    try:
        order = api.place_limit_order(
            symbol=PAIR,
            side="buy",
            limit_price=TARGET_PRICE,
            asset_quantity=safe_qty
        )
        
        if order:
            print(f"✅ LIMIT ORDER SET. Capital locked.")
            print(f"   Waiting for price to slide to ${TARGET_PRICE}...")
        else:
            print("❌ Order Placement Failed (API returned None).")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    place_reentry_order()
