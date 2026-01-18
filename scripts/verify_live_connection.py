
import os
import sys
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.getcwd())

# Load Env
env_path = r"c:\Users\super\Watchtower\unk-app-ai\.env"
print(f"DEBUG: Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path, verbose=True)

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

API_KEY = os.getenv('ROBINHOOD_API_KEY', '')
PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
print(f"DEBUG: Loaded API_KEY length: {len(API_KEY)}")

def check_live_status():
    print("🔌 Connecting to Robinhood API (Live)...")
    
    if not API_KEY or not PRIVATE_KEY:
        print("❌ CRITICAL: Missing API Credentials in Environment.")
        return

    try:
        api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)
        
        # 1. Fetch Account (Buying Power)
        print("   -> Fetching Account Info...")
        account = api.get_account()
        if not account:
            print("❌ Failed to fetch account.")
            return

        buying_power = float(account.get('buying_power', 0))
        print(f"✅ CONNECTED. Buying Power: ${buying_power:.2f}")
        
        # 2. Fetch Live Quote (DOGE)
        print(f"   -> Fetching Real-Time Quote for DOGE-USD...")
        quotes = api.get_best_bid_ask("DOGE-USD")
        if quotes and "DOGE-USD" in quotes:
            price = quotes["DOGE-USD"]["ask_price"]
            print(f"✅ LIVE DATA: DOGE-USD @ ${price:.6f}")
        else:
            print(f"⚠️ Failed to fetch quote: {quotes}")
            
        # 3. Explain "No Emails"
        print("-" * 50)
        if buying_power < 1.0:
            print(f"🚫 TRADING STATUS: PAUSED")
            print(f"   Reason: Insufficient Buying Power (${buying_power:.2f} < $1.00)")
            print(f"   Action: Waiting for existing positions to hit +1.1% profit to sell.")
        else:
            print(f"🟢 TRADING STATUS: ACTIVE")
            
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    check_live_status()
