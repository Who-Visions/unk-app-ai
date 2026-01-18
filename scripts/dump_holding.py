"""Dump first holding raw dict"""
import os
import json
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

try:
    resp = api._request('GET', '/api/v1/crypto/trading/holdings/')
    if resp and 'results' in resp and resp['results']:
        with open('raw_holding.json', 'w') as f:
            json.dump(resp['results'][0], f, indent=2)
        print("Done dumping")
    else:
        print("No results found")
except Exception as e:
    print(e)
