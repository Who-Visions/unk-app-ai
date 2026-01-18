
import json
import sys
import os
import logging

# Adjust path to import services
sys.path.append(os.getcwd())
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

logging.basicConfig(level=logging.INFO)

def reconcile_state():
    print("RECONCILING BOT STATE WITH BROKER...")
    
    # INJECT CREDENTIALS
    os.environ["ROBINHOOD_API_KEY"] = "rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814"
    os.environ["ROBINHOOD_PRIVATE_KEY"] = "bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0="
    
    try:
        api = RobinhoodCryptoAPI()
        
        # 1. Get Live Holdings
        print("Fetching Broker Holdings...")
        holdings = api.get_holdings()
        
        # 2. Get Current Prices (for Entry est. if missing)
        watchlist = ["BTC-USD", "ETH-USD", "DOGE-USD", "SHIB-USD", "PEPE-USD", "BONK-USD", "LTC-USD", "XRP-USD", "ADA-USD", "HBAR-USD", "SOL-USD", "LINK-USD"]
        pricing = api.get_best_bid_ask(*watchlist)
        
        # 3. Load Local State
        if os.path.exists("trading_state.json"):
            with open("trading_state.json", "r") as f:
                state = json.load(f)
        else:
            state = {"highs": {}, "positions": {}, "cash": 0.0, "targets": {}}
            
        print(f"Local Positions: {list(state['positions'].keys())}")
        
        # 4. Sync Logic
        updated_positions = {}
        
        for h in holdings:
            # Fix: CryptoHolding uses asset_code (e.g. "DOGE") not symbol
            symbol = f"{h.asset_code}-USD" 
            qty = float(h.available_quantity) # Use available qty
            
            if qty > 0:
                print(f"Found Broker Position: {symbol} ({qty})")
                
                # Check if already in state to preserve Entry Price
                if symbol in state["positions"]:
                    existing_entry = state["positions"][symbol]['entry']
                    print(f"  -> Keeping existing entry: ${existing_entry}")
                    entry = existing_entry
                else:
                    # New/Ghost position caught! Estimate entry from current price
                    current_price = pricing.get(symbol, {}).get('ask_price', 0.0)
                    
                    # Inspect holding for cost basis if available
                    # Note: Original dataclass might not have cost_basis, check safely
                    if hasattr(h, 'cost_basis') and h.cost_basis:
                         try:
                             cost_basis = float(h.cost_basis)
                             if cost_basis > 0:
                                entry = cost_basis / qty
                                print(f"  -> Recovered cost basis: ${entry}")
                             else:
                                entry = current_price
                         except:
                             entry = current_price
                    else:
                         entry = current_price
                         print(f"  -> resetting entry to market: ${entry}")

                updated_positions[symbol] = {
                    "qty": qty,
                    "entry": entry
                }
        
        # 5. Save Reconciled State
        state["positions"] = updated_positions
        
        with open("trading_state.json", "w") as f:
            json.dump(state, f)
            
        print("STATE RECONCILED.")
        print(f"Active Managed Positions: {list(updated_positions.keys())}")
        
    except Exception as e:
        print(f"Reconciliation Failed: {e}")

if __name__ == "__main__":
    reconcile_state()