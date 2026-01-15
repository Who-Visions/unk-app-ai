
import os
import sys
import logging
sys.path.append(os.getcwd())
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

# Setup Logging to Console
logging.basicConfig(level=logging.DEBUG)

def test_buy():
    print("Testing Buy Order...")
    os.environ["ROBINHOOD_API_KEY"] = "rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814"
    os.environ["ROBINHOOD_PRIVATE_KEY"] = "bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0="
    
    api = RobinhoodCryptoAPI()
    
    # Try buying $1.00 DOGE
    sym = "DOGE-USD"
    amount = 1.00
    
    print(f"Placing Buy for {sym} ($ {amount})...")
    order = api.place_market_order(sym, "buy", quote_amount=amount)
    
    if order:
        print(f"SUCCESS: {order}")
    else:
        print("FAILURE.")

if __name__ == "__main__":
    test_buy()
