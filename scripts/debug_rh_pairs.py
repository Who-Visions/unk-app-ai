
import os
import sys
import json
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def debug_pairs():
    load_dotenv()
    print("🔍 Testing Robinhood Asset Discovery...")
    
    try:
        api = RobinhoodCryptoAPI()
        # Ensure account is initialized (good practice now)
        api.get_account()
        
        print("Calling get_trading_pairs() with no args...")
        pairs = api.get_trading_pairs()
        
        if pairs:
            print(f"✅ Found {len(pairs)} trading pairs.")
            # Print first 5
            for p in pairs[:5]:
                print(f" - {p.get('symbol')} ({p.get('asset_code')})")
            
            # Dump all symbols to a list for reference
            all_syms = [p.get('symbol') for p in pairs]
            print(f"\nAll Symbols: {json.dumps(all_syms)}")
        else:
            print("❌ No pairs returned (Empty list).")

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_pairs()
