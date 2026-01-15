
import time
import json
import sys
import os
from datetime import datetime

# Adjust path to import services
sys.path.append(os.getcwd())
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def validate_buys(iterations=25):
    print(f"🕵️ VALIDATING TRADING LOGIC ({iterations} Iterations)")
    
    # INJECT CREDENTIALS BEFORE INIT
    os.environ["ROBINHOOD_API_KEY"] = "rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814"
    os.environ["ROBINHOOD_PRIVATE_KEY"] = "bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0="
    
    print("Loading State & API...")
    try:
        api = RobinhoodCryptoAPI()
    except Exception as e:
        print(f"❌ API Init Failed: {e}")
        return

    watchlist = ["BTC-USD", "ETH-USD", "DOGE-USD", "SHIB-USD", "PEPE-USD", "BONK-USD"]
    
    for i in range(1, iterations + 1):
        try:
            # 1. Load Bot State
            if not os.path.exists("trading_state.json"):
                print("❌ trading_state.json not found! Is the bot running?")
                # Create dummy state if missing for test?
                # No, we want to validate live state.
                time.sleep(2)
                continue

            with open("trading_state.json", "r") as f:
                state = json.load(f)
            
            highs = state.get("highs", {})
            targets = state.get("targets", {})
            buy_trigger = targets.get("buy", -1.5)
            positions = state.get("positions", {})
            
            # 2. Fetch Live Prices
            try:
                pricing = api.get_best_bid_ask(*watchlist)
            except Exception as e:
                print(f"API Error: {e}")
                time.sleep(2)
                continue
            
            print(f"\n[{i}/{iterations}] {datetime.now().strftime('%H:%M:%S')} | Trigger: {buy_trigger}%")
            print(f"{'ASSET':<10} {'HIGH':<12} {'CURRENT':<12} {'DIP %':<10} {'STATUS'}")
            print("-" * 65)
            
            for sym in watchlist:
                if sym not in pricing: continue
                
                price = pricing[sym]['ask_price']
                high = highs.get(sym, 0)
                
                status = ""
                dip = 0.0
                
                if high == 0:
                    status = "⚠️ No High (Learning)"
                else:
                    dip = (price - high) / high * 100
                    
                    if sym in positions:
                        entry = positions[sym]['entry']
                        pnl = (price - entry) / entry * 100
                        status = f"✅ HODL ({pnl:+.2f}%)"
                    elif dip <= buy_trigger:
                        status = "🚀 BUY ZONE!" 
                    else:
                        miss = dip - buy_trigger
                        status = f"⏳ Waiting ({miss:+.2f}%)"
                
                print(f"{sym:<10} ${high:<11.4f} ${price:<11.4f} {dip:>6.2f}%    {status}")
                
            time.sleep(2) # Wait 2s between checks
            
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    validate_buys()
