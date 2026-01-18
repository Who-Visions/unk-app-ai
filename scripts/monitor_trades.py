
import time
import json
import sys
import os
from datetime import datetime

# Adjust path to import services
sys.path.append(os.getcwd())
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def monitor_trades(iterations=100):
    print(f"MONITORING ACTIVE TRADES ({iterations} Iterations)")
    
    # INJECT CREDENTIALS
    os.environ["ROBINHOOD_API_KEY"] = "rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814"
    os.environ["ROBINHOOD_PRIVATE_KEY"] = "bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0="
    
    print("Loading API...")
    try:
        api = RobinhoodCryptoAPI()
    except Exception as e:
        print(f"API Init Failed: {e}")
        return

    watchlist = ["BTC-USD", "ETH-USD", "DOGE-USD", "SHIB-USD", "PEPE-USD", "BONK-USD"]
    
    for i in range(1, iterations + 1):
        try:
            # 1. Load Bot State
            if not os.path.exists("trading_state.json"):
                print("trading_state.json not found! Is the bot running?")
                time.sleep(2)
                continue

            with open("trading_state.json", "r") as f:
                state = json.load(f)
            
            positions = state.get("positions", {})
            targets = state.get("targets", {})
            sell_target = targets.get("sell", 8.0)
            
            # 2. Fetch Live Prices
            try:
                pricing = api.get_best_bid_ask(*watchlist)
            except Exception as e:
                print(f"API Error: {e}")
                time.sleep(2)
                continue
            
            print(f"\n[{i}/{iterations}] {datetime.now().strftime('%H:%M:%S')} | Target: +{sell_target}% | Stop: -10%")
            print(f"{'ASSET':<10} {'ENTRY':<12} {'CURRENT':<12} {'PNL %':<10} {'STATUS'}")
            print("-" * 65)
            
            active_count = 0
            
            for sym in watchlist:
                if sym not in pricing: continue
                price = pricing[sym]['ask_price']
                
                if sym in positions:
                    active_count += 1
                    pos = positions[sym]
                    entry = pos['entry']
                    qty = pos['qty']
                    pnl = (price - entry) / entry * 100
                    
                    status = "HODL"
                    if pnl >= sell_target:
                        status = "SELLING NOW!"
                    elif pnl <= -10.0:
                        status = "STOP LOSS!"
                    
                    print(f"{sym:<10} ${entry:<11.6f} ${price:<11.6f} {pnl:>+6.2f}%    {status}")
            
            if active_count == 0:
                print("No active trades. Scanning for dips...")
                
            time.sleep(5) 
            
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor_trades()
