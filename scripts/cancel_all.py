#!/usr/bin/env python3
"""
Cancel ALL open Robinhood crypto orders to release withheld funds.
"""
import sys
import os
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI

def main():
    load_dotenv()
    
    # Initialize API
    try:
        api = RobinhoodCryptoAPI()
    except Exception as e:
        print(f"❌ Error initializing API: {e}")
        return

    print("=== 💸 RELEASING WITHHELD FUNDS 💸 ===")
    
    # 1. Check initial buying power
    try:
        account = api.get_account()
        initial_bp = float(account.get("buying_power", 0))
        print(f"💰 Initial Buying Power: ${initial_bp:.2f}")
    except Exception as e:
        print(f"⚠️ Could not fetch buying power: {e}")
        initial_bp = 0

    # 2. Fetch open orders
    print("\n🔍 Scanning for open orders...")
    try:
        orders = api.get_orders(state="open")
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        return

    if not orders:
        print("✅ No open orders found! Your funds are not withheld in orders.")
        return

    print(f"⚠️ Found {len(orders)} open orders. Cancelling now...")

    # 3. Cancel all open orders
    cancelled_count = 0
    total_value_freed = 0.0

    for order in orders:
        print(f"   ❌ Cancelling {order.side.upper()} {order.symbol} ({order.order_type})...", end=" ")
        try:
            success = api.cancel_order(order.order_id)
            if success:
                print("✅")
                cancelled_count += 1
                # Estimate value (rough approximation)
                if order.side == "buy" and (order.order_type == "limit" or order.order_type == "stop_limit"):
                    # We verify against the returned object but for now just count
                    pass
            else:
                print("FAILED ❌")
        except Exception as e:
            print(f"ERROR: {e}")
            
    # 4. Check final buying power
    print("\n⏳ Verifying released funds...")
    time.sleep(2)  # Give API a moment to update
    try:
        account = api.get_account()
        final_bp = float(account.get("buying_power", 0))
        released = final_bp - initial_bp
        
        print("\n=== SUMMARY ===")
        print(f"🗑️  Cancelled: {cancelled_count}/{len(orders)} orders")
        print(f"💰 Final Buying Power: ${final_bp:.2f}")
        if released > 0:
            print(f"💸 RELEASED: ${released:.2f}")
        else:
            print(f"ℹ️  No change in buying power detected (yet).")
            
    except Exception as e:
        print(f"⚠️ Could not fetch final buying power: {e}")

if __name__ == "__main__":
    main()
