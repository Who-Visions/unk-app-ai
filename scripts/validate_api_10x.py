"""
Quick Robinhood API Validation Script - 10 Live Calls
Run: python scripts/validate_api_10x.py
"""
import sys
import os
import time

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI

def main():
    print("=" * 60)
    print("ROBINHOOD API VALIDATION - 10 LIVE CALLS")
    print("=" * 60)
    
    api = RobinhoodCryptoAPI(api_version=2)
    
    results = []
    
    # Test 1: Get Account
    print("\n[1/10] GET Account...")
    try:
        res = api.get_account()
        if res and "account_number" in res:
            print(f"  ✓ SUCCESS: Account #{res['account_number']}")
            results.append(("Account", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("Account", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Account", False))
    time.sleep(1)
    
    # Test 2: Get Trading Pairs (BTC only)
    print("\n[2/10] GET Trading Pairs (BTC-USD)...")
    try:
        res = api.get_trading_pairs("BTC-USD")
        if res and len(res) > 0:
            print(f"  ✓ SUCCESS: Got {len(res)} pair(s)")
            results.append(("TradingPairs", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("TradingPairs", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("TradingPairs", False))
    time.sleep(1)
    
    # Test 3: Get Best Bid/Ask (BTC)
    print("\n[3/10] GET Best Bid/Ask (BTC-USD)...")
    try:
        res = api.get_best_bid_ask("BTC-USD")
        if res and "BTC-USD" in res:
            btc = res["BTC-USD"]
            print(f"  ✓ SUCCESS: Bid=${btc['bid_price']:,.2f} Ask=${btc['ask_price']:,.2f}")
            results.append(("BidAsk_BTC", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("BidAsk_BTC", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("BidAsk_BTC", False))
    time.sleep(1)
    
    # Test 4: Get Best Bid/Ask (ETH)
    print("\n[4/10] GET Best Bid/Ask (ETH-USD)...")
    try:
        res = api.get_best_bid_ask("ETH-USD")
        if res and "ETH-USD" in res:
            eth = res["ETH-USD"]
            print(f"  ✓ SUCCESS: Bid=${eth['bid_price']:,.2f} Ask=${eth['ask_price']:,.2f}")
            results.append(("BidAsk_ETH", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("BidAsk_ETH", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("BidAsk_ETH", False))
    time.sleep(1)
    
    # Test 5: Get Best Bid/Ask (DOGE)
    print("\n[5/10] GET Best Bid/Ask (DOGE-USD)...")
    try:
        res = api.get_best_bid_ask("DOGE-USD")
        if res and "DOGE-USD" in res:
            doge = res["DOGE-USD"]
            print(f"  ✓ SUCCESS: Bid=${doge['bid_price']:.6f} Ask=${doge['ask_price']:.6f}")
            results.append(("BidAsk_DOGE", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("BidAsk_DOGE", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("BidAsk_DOGE", False))
    time.sleep(1)
    
    # Test 6: Get Holdings
    print("\n[6/10] GET Holdings...")
    try:
        res = api.get_holdings()
        print(f"  ✓ SUCCESS: {len(res)} holdings found")
        for h in res[:3]:  # Show first 3
            print(f"     - {h.asset_code}: {h.total_quantity:.6f}")
        results.append(("Holdings", True))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Holdings", False))
    time.sleep(1)
    
    # Test 7: Get Orders (open)
    print("\n[7/10] GET Orders (open)...")
    try:
        res = api.get_orders(state="open")
        print(f"  ✓ SUCCESS: {len(res)} open orders")
        results.append(("Orders_Open", True))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("Orders_Open", False))
    time.sleep(1)
    
    # Test 8: Get Estimated Price (BTC, 0.001)
    print("\n[8/10] GET Estimated Price (BTC-USD, 0.001)...")
    try:
        res = api.get_estimated_price("BTC-USD", "ask", "0.001")
        if res and len(res) > 0:
            print(f"  ✓ SUCCESS: {res[0]}")
            results.append(("EstPrice", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("EstPrice", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("EstPrice", False))
    time.sleep(1)
    
    # Test 9: Batch Bid/Ask (3 symbols)
    print("\n[9/10] GET Batch Bid/Ask (BTC, ETH, SOL)...")
    try:
        res = api.get_best_bid_ask("BTC-USD", "ETH-USD", "SOL-USD")
        if res and len(res) >= 3:
            print(f"  ✓ SUCCESS: Got {len(res)} prices")
            results.append(("BatchBidAsk", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("BatchBidAsk", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("BatchBidAsk", False))
    time.sleep(1)
    
    # Test 10: Get All Trading Pairs
    print("\n[10/10] GET All Trading Pairs...")
    try:
        res = api.get_trading_pairs()
        if res and len(res) > 0:
            tradable = sum(1 for p in res if p.get("is_api_tradable"))
            print(f"  ✓ SUCCESS: {len(res)} pairs, {tradable} API tradable")
            results.append(("AllPairs", True))
        else:
            print(f"  ✗ FAILED: {res}")
            results.append(("AllPairs", False))
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        results.append(("AllPairs", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed
    print(f"Passed: {passed}/10")
    print(f"Failed: {failed}/10")
    
    if failed > 0:
        print("\nFailed Tests:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
    
    if api.last_error:
        print(f"\nLast Error: {api.last_error[:200]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
