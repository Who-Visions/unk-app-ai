import os
import sys
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from dotenv import load_dotenv

load_dotenv()
api = RobinhoodCryptoAPI()

# Fetch Pairs
pairs = api.get_trading_pairs()
dash_found = False
print("--- CLEAN SYMBOL LIST ---")
for p in pairs:
    sym = p.get('symbol')
    code = p.get('asset_code')
    print(f"{sym} ({code})")
    if 'DASH' in sym or 'DASH' in code:
        dash_found = True
        print(f"!!! FOUND DASH: {sym} !!!")

if not dash_found:
    print("❌ DASH NOT FOUND IN API PAIRS.")
