
import os
import sys
import json
from dotenv import load_dotenv

# Load Env
load_dotenv()
sys.path.append(os.getcwd())

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def calculate_floating():
    # 1. Load State
    try:
        with open("trading_state.json", "r") as f:
            state = json.load(f)
    except:
        print("❌ Could not load trading_state.json")
        return

    positions = state.get("positions", {})
    if not positions:
        print("No active positions.")
        return

    # 2. Connect API
    api_key = os.getenv('ROBINHOOD_API_KEY')
    private_key = os.getenv('ROBINHOOD_PRIVATE_KEY')
    
    if not api_key:
        print("❌ Missing API Keys")
        return

    api = RobinhoodCryptoAPI(api_key=api_key, private_key_base64=private_key)
    
    # 3. Get Quotes
    symbols = list(positions.keys())
    print(f"📊 Analyzing {len(symbols)} Positions...")
    
    quotes = api.get_best_bid_ask(*symbols)
    if not quotes:
        print("❌ Failed to fetch quotes.")
        return

    total_entry_val = 0
    total_curr_val = 0
    
    print(f"\n{'ASSET':<10} {'ENTRY':<10} {'CURRENT':<10} {'P&L %':<10} {'VALUE':<10}")
    print("-" * 60)

    for sym, pos in positions.items():
        qty = float(pos['qty'])
        entry = float(pos['entry'])
        
        if sym in quotes:
            # Use BID price (what we would sell for)
            curr = quotes[sym]['bid_price']
        else:
            curr = entry # Fallback

        entry_val = qty * entry
        curr_val = qty * curr
        
        pnl_pct = ((curr - entry) / entry) * 100
        pnl_color = "🟢" if pnl_pct >= 0 else "🔴"
        
        total_entry_val += entry_val
        total_curr_val += curr_val
        
        # Format
        p_fmt = f"${curr:.6f}" if curr < 1 else f"${curr:.2f}"
        e_fmt = f"${entry:.6f}" if entry < 1 else f"${entry:.2f}"
        
        print(f"{sym:<10} {e_fmt:<10} {p_fmt:<10} {pnl_color} {pnl_pct:>6.2f}%  ${curr_val:.2f}")

    # SUMMARY
    if total_entry_val > 0:
        total_pnl_val = total_curr_val - total_entry_val
        total_pnl_pct = (total_pnl_val / total_entry_val) * 100
        
        print("-" * 60)
        print(f"💵 CASH:          ${state.get('cash', 0):.2f}")
        print(f"💼 PORTFOLIO:     ${total_curr_val:.2f}")
        print(f"📉 UNREALIZED P&L: {total_pnl_pct:+.2f}% (${total_pnl_val:+.2f})")
    else:
        print("No value invested.")

if __name__ == "__main__":
    calculate_floating()
