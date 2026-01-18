#!/usr/bin/env python3
"""Quick validation of all Robinhood API endpoints."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI

def main():
    api = RobinhoodCryptoAPI(
        api_key=os.getenv('ROBINHOOD_API_KEY'),
        private_key_base64=os.getenv('ROBINHOOD_PRIVATE_KEY')
    )

    print("=== ROBINHOOD API VALIDATION ===")
    print()

    # 1. Account
    print("[1] GET Account...")
    try:
        acc = api.get_account()
        if acc:
            print(f"    ✓ Account: {acc.get('account_number')}")
            print(f"    ✓ Buying Power: ${acc.get('buying_power', 0)}")
            print(f"    ✓ Status: {acc.get('status')}")
        else:
            print("    ✗ No account data")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # 2. Trading Pairs
    print("[2] GET Trading Pairs...")
    try:
        pairs = api.get_trading_pairs()
        print(f"    ✓ Found {len(pairs)} trading pairs")
        tradable = [p for p in pairs if p.get('tradability') == 'tradable']
        print(f"    ✓ Tradable: {len(tradable)}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # 3. Best Bid/Ask
    print("[3] GET Best Bid/Ask (BTC, ETH, SOL)...")
    try:
        prices = api.get_best_bid_ask('BTC-USD', 'ETH-USD', 'SOL-USD')
        for sym, data in prices.items():
            bid = float(data.get('bid_price', 0))
            ask = float(data.get('ask_price', 0))
            spread = ((ask - bid) / bid * 100) if bid > 0 else 0
            print(f"    ✓ {sym}: bid=${bid:.2f} ask=${ask:.2f} spread={spread:.3f}%")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # 4. Holdings
    print("[4] GET Holdings...")
    try:
        holdings = api.get_holdings()
        print(f"    ✓ Found {len(holdings)} holdings")
        for h in holdings[:5]:
            print(f"      - {h.asset_code}: {h.total_quantity:.8f}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # 5. Orders
    print("[5] GET Orders...")
    try:
        orders = api.get_orders()
        print(f"    ✓ Found {len(orders)} orders")
        open_orders = [o for o in orders if o.state in ('open', 'pending')]
        print(f"    ✓ Open orders: {len(open_orders)}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # 6. Estimated Price
    print("[6] GET Estimated Price (BTC-USD, 0.001)...")
    try:
        est = api.get_estimated_price('BTC-USD', 'ask', '0.001')
        if est:
            print(f"    ✓ Estimated: {est}")
        else:
            print("    ✓ No estimate returned")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    print()
    print("=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    main()
