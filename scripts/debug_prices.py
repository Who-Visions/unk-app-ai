
import os
import sys
import json
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def debug_prices():
    load_dotenv()
    print("🔍 Testing Price Fetch (get_best_bid_ask)...")
    
    # Try both V1 and V2 just in case, though get_best_bid_ask usually uses V1
    print("\n--- Initializing API (Default) ---")
    api = RobinhoodCryptoAPI()
    
    symbols = ["BTC-USD", "ETH-USD"]
    print(f"Requesting prices for: {symbols}")
    
    try:
        prices = api.get_best_bid_ask(*symbols)
        print(f"Result: {json.dumps(prices, indent=2)}")
        
        if not prices:
             print("❌ No prices returned! Checking raw request...")
             # Manually inspect the underlying call if we can, 
             # but for now let's just see if this works.
             
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_prices()
