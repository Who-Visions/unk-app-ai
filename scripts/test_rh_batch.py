
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
import time

API_KEY = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
PRIVATE_KEY = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='
WATCHLIST = ['PEPE-USD', 'BONK-USD', 'SHIB-USD', 'ETH-USD']

def test():
    print("Initializing API...")
    api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)
    
    print(f"Fetching batch prices for {WATCHLIST}...")
    
    # DEBUG: call _request directly to see raw fields
    print("DEBUG: Checking raw response fields for batch...")
    params = "&".join([f"symbol={s}" for s in WATCHLIST])
    path = f"/api/v1/crypto/marketdata/best_bid_ask/?{params}"
    raw = api._request("GET", path)
    if raw and 'results' in raw and len(raw['results']) > 0:
        first = raw['results'][0]
        print(f"Sample Item Keys: {list(first.keys())}")
        print(f"Sample Item: {first}")
    
    try:
        prices = api.get_best_bid_ask(*WATCHLIST)
        print(f"Result Type: {type(prices)}")
        print(f"Result Keys: {list(prices.keys())}")
        for sym, data in prices.items():
            print(f"{sym}: {data['ask_price']}")
            
        if not prices:
            print("❌ Empty response!")
            # Try single to see if it works
            print("Trying single fetch...")
            p = api.get_best_bid_ask("BTC-USD")
            print(f"Single BTC fetch: {p}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test()
