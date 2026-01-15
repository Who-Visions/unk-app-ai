
import os
import sys
import logging
sys.path.append(os.getcwd())
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

logging.basicConfig(level=logging.DEBUG)

def test_buy_precision():
    print("Testing Buy Precision...")
    os.environ["ROBINHOOD_API_KEY"] = "rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814"
    os.environ["ROBINHOOD_PRIVATE_KEY"] = "bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0="
    
    api = RobinhoodCryptoAPI()
    
    sym = "DOGE-USD"
    # Try safe precision (1 decimal)
    qty = 6.8 
    
    print(f"Placing Buy for {sym} ({qty} Coins)...")
    order = api.place_market_order(sym, "buy", asset_quantity=qty)
    
    if order:
        print(f"SUCCESS: {order}")
    else:
        print("FAILURE.")

if __name__ == "__main__":
    test_buy_precision()
