
import json
import os

STATE_FILE = r"c:\Users\super\Watchtower\unk-app-ai\trading_state.json"

def fix_entries():
    if not os.path.exists(STATE_FILE):
        print("State file not found!")
        return

    with open(STATE_FILE, 'r') as f:
        data = json.load(f)

    start_positions = data.get("positions", {})
    prices = data.get("prices", {})
    
    updates = 0
    
    print(f"Checking {len(start_positions)} positions for zero entries...")
    
    for sym, pos in start_positions.items():
        entry = float(pos.get("entry", 0.0))
        qty = float(pos.get("qty", 0.0))
        
        if entry == 0.0:
            # FIX: Use current price as new basis
            curr_price = prices.get(sym, 0.0)
            if curr_price > 0:
                print(f"🛠️ REPAIRING {sym}: Entry $0.00 -> ${curr_price:.4f}")
                pos["entry"] = curr_price
                updates += 1
            else:
                print(f"⚠️ CANNOT REPAIR {sym}: Price is also zero.")
    
    if updates > 0:
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Repaired {updates} positions. Restart bot to apply.")
    else:
        print("✅ No repairs needed.")

if __name__ == "__main__":
    fix_entries()
