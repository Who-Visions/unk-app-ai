"""Quick order check"""
import os
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

orders = api._request('GET', '/api/v1/crypto/trading/orders/')
results = orders.get('results', [])

print(f"TOTAL ORDERS: {len(results)}")
print()
print("SIDE  | SYMBOL       | STATE      | QTY          | PRICE")
print("-" * 70)

for o in results[:20]:
    side = o.get('side', '?')
    sym = o.get('symbol', '?')
    state = o.get('state', '?')
    qty = o.get('filled_asset_quantity') or o.get('quantity') or '?'
    price = o.get('average_price') or '?'
    print(f"{side:5} | {sym:12} | {state:10} | {str(qty):12} | {price}")
