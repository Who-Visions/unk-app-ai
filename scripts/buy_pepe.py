"""
Quick PEPE Buy - It's already down 4.87%!
"""
import sys
sys.path.insert(0, 'c:/Users/super/Watchtower/unk-app-ai')

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
import uuid

API_KEY = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
PRIVATE_KEY = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)

# Check buying power
acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
cash = float(acc.get('buying_power', 0))
print(f"Buying power: ${cash:.2f}")

# Get PEPE price
p = api._request('GET', '/api/v1/crypto/marketdata/best_bid_ask/?symbol=PEPE-USD')
price = float(p['results'][0]['ask_inclusive_of_buy_spread'])
print(f"PEPE price: ${price:.10f}")

# Calculate how much PEPE we can buy with $2.50 (half the cash)
buy_amount = 2.50
pepe_quantity = buy_amount / price
print(f"$2.50 buys: {pepe_quantity:,.0f} PEPE")

# Place order
print("\nPlacing buy order...")
order_id = str(uuid.uuid4())
body = {
    "client_order_id": order_id,
    "side": "buy",
    "symbol": "PEPE-USD",
    "type": "market",
    "market_order_config": {
        "quote_amount": "2.50"
    }
}
result = api._request('POST', '/api/v1/crypto/trading/orders/', body)
print(f"Order result: {result}")

# Check new balance
acc2 = api._request('GET', '/api/v1/crypto/trading/accounts/')
new_cash = float(acc2.get('buying_power', 0))
print(f"\nNew buying power: ${new_cash:.2f}")
