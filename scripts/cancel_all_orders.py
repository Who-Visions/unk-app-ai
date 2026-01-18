"""
Cancel All Open Orders
======================
Fetches all orders with state='open' and cancels them.
"""
import os
import sys
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()

api = RobinhoodCryptoAPI()

def cancel_all():
    print("🗑️ Fetching Open Orders...")
    try:
        orders = api.get_orders(state="open")
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
        return

    if not orders:
        print("✅ No open orders found.")
        return

    print(f"⚠️ Found {len(orders)} open orders. Cancelling...")
    
    count = 0
    for o in orders:
        print(f"   ❌ Cancelling {o.side.upper()} {o.symbol} (ID: {o.order_id})...")
        try:
            success = api.cancel_order(o.order_id)
            if success:
                print(f"      ✅ Cancelled.")
                count += 1
            else:
                print(f"      ❌ Failed to cancel.")
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            
    print(f"🏁 Done. Cancelled {count} orders.")

if __name__ == "__main__":
    cancel_all()
