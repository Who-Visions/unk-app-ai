"""Debug Robinhood API - Raw Responses"""
import os
import json
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

print("=== RAW ACCOUNT RESPONSE ===")
try:
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    print(json.dumps(acc, indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== RAW HOLDINGS RESPONSE ===")
try:
    # Try different endpoints
    holdings_raw = api._request('GET', '/api/v1/crypto/trading/holdings/')
    print(json.dumps(holdings_raw, indent=2))
except Exception as e:
    print(f"Holdings Error: {e}")

print("\n=== PARSED HOLDINGS ===")
try:
    holdings = api.get_holdings()
    for h in holdings:
        print(f"  {h.asset_code}: total={h.total_quantity}, available={h.available_quantity}")
except Exception as e:
    print(f"Error: {e}")
