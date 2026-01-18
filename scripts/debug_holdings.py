import os
import sys
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

print("--- RAW HOLDINGS ---")
holdings = api.get_holdings()
for h in holdings:
    if float(h.total_quantity) > 0:
        print(f"{h.asset_code}: {h.total_quantity} (Available: {h.available_quantity})")
