"""Check Robinhood order history - detailed"""
import os
import json
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

print("=== ROBINHOOD ORDER HISTORY ===")
print()

# Get recent orders
orders = api._request('GET', '/api/v1/crypto/trading/orders/')

results = orders.get('results', [])
print(f"Total orders: {len(results)}")
print()

# Print raw JSON for first 5 orders
for i, order in enumerate(results[:10]):
    print(f"--- Order {i+1} ---")
    print(json.dumps(order, indent=2))
    print()
