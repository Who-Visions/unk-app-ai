
import os
import sys
import json
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def debug_holdings():
    load_dotenv()
    print("🔍 Inspecting Robinhood Holdings Raw Data (V2)...")
    
    api = RobinhoodCryptoAPI(api_version=2)
    # V2 needs account number
    api.get_account()
    
    # We need to access the raw request to see the fields, 
    # but the current class wraps it. 
    # Let's use the private _request method to get raw JSON.
    
    path = api._get_api_path("trading/holdings/")
    if api.api_version == 2 and api.account_number:
         path += f"?account_number={api.account_number}"
         
    res = api._request("GET", path)
    
    if res and "results" in res:
        for i, h in enumerate(res["results"]):
            code = h.get('asset_code')
            qty = h.get('quantity') or h.get('total_quantity')
            
            # Print potentially useful fields
            print(f"\n--- Asset: {code} (Qty: {qty}) ---")
            print(f"Keys found: {list(h.keys())}")
            
            if 'cost_basis' in h:
                print(f"Cost Basis: {h['cost_basis']}")
            if 'average_buy_price' in h:
                print(f"Avg Buy Price: {h['average_buy_price']}")
                
            # Dump full first item for reference
            if i < 2: 
                print(f"Full JSON: {json.dumps(h, indent=2)}")
                
    else:
        print("No results found or error.")
        print(res)

if __name__ == "__main__":
    debug_holdings()
