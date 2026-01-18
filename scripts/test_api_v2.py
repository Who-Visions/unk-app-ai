
import os
import sys
from decimal import Decimal
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI

def main():
    api_key = os.getenv('ROBINHOOD_API_KEY', '')
    priv_key = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
    api = RobinhoodCryptoAPI(api_key=api_key, private_key_base64=priv_key)

    print("--- TESTING API ---")
    try:
        print("Testing get_trading_pairs()...")
        pairs = api.get_trading_pairs()
        print(f"Found {len(pairs)} pairs.")
        if pairs:
            print(f"Keys in first pair: {list(pairs[0].keys())}")
            print(f"Sample pair: {pairs[0]}")
            
        print("\nTesting get_holdings()...")
        holdings = api.get_holdings()
        print(f"Found {len(holdings)} holdings.")
        if holdings:
            print(f"First holding: {holdings[0]}")
            
        print("\nTesting get_best_bid_ask('BTC-USD') 10 times...")
        for i in range(1, 11):
            prices = api.get_best_bid_ask("BTC-USD")
            print(f"[{i}] BTC-USD Price: {prices.get('BTC-USD', {}).get('bid_price')}")
            import time
            time.sleep(0.5)
        
        print("\nTesting UnkAiAgent...")
        from services.llm.unk_agent import UnkAiAgent
        agent = UnkAiAgent()
        # Test the run method (sync wrapper)
        resp = agent.run("Hello Unk, give me a one sentence trading tip.")
        print(f"Agent Response: {resp}")
        
    except Exception as e:
        print(f"DIAGNOSTIC FAILED: {e}")

if __name__ == "__main__":
    main()
