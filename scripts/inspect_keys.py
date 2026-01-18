"""Inspect API keys"""
import os
import json
# os.environ['ROBINHOOD_API_KEY'] = os.getenv('ROBINHOOD_API_KEY', 'default_key')
# os.environ['ROBINHOOD_PRIVATE_KEY'] = os.getenv('ROBINHOOD_PRIVATE_KEY', 'default_private_key')

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

try:
    resp = api._request('GET', '/api/v1/crypto/trading/holdings/')
    if resp and 'results' in resp:
        results = resp['results']
        if results:
            print("KEYS FOUND IN HOLDING OBJECT:")
            for k in results[0].keys():
                print(f"  {k}: {results[0][k]}")
        else:
            print("No holdings found in results")
    else:
        print("No results key in response")
        print(json.dumps(resp, indent=2))
except Exception as e:
    print(f"Error: {e}")
