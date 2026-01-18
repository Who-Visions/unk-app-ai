"""Check actual Robinhood holdings"""
import os
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

print("=== ACTUAL ROBINHOOD ACCOUNT ===")
print()

# Get account info
acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
print(f"Buying Power: ${acc.get('buying_power', 'N/A')}")
print()

# Get all holdings
print("=== HOLDINGS WITH VALUE ===")
holdings = api.get_holdings()
for h in holdings:
    qty = float(h.total_quantity)
    if qty > 0:
        print(f"  {h.asset_code}: {qty}")

print()
print("=== ALL HOLDINGS (including zero) ===")
for h in holdings:
    print(f"  {h.asset_code}: {h.total_quantity}")
