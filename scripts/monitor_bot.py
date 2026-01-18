import time
import json
import os
from datetime import datetime

LOG_FILE = "trader_activity.log"
STATE_FILE = "trading_state.json"

print(f"=== MONITOR STARTED: {datetime.now()} ===")
print("Checking every 15 seconds for 1 hour...")
start_time = time.time()
last_pos_count = -1
last_log_line = ""

while time.time() - start_time < 3600: # 1 hour
    try:
        current_ts = datetime.now().strftime('%H:%M:%S')
        
        # 1. Check State (Cash & Positions)
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                try:
                    state = json.load(f)
                    pos = state.get("positions", {})
                    cash = state.get("cash", 0)
                    
                    # Detect Position Changes
                    if len(pos) != last_pos_count and last_pos_count != -1:
                        print(f"\n[{current_ts}] 🚨 POSITION CHANGE: {last_pos_count} -> {len(pos)} held")
                        # Detailed diff could go here
                    
                    last_pos_count = len(pos)
                    
                    # Status Line
                    print(f"[{current_ts}] Cash: ${cash:.2f} | Positions: {len(pos)} | Running...", end="\r")
                    
                except json.JSONDecodeError:
                    pass # Race condition with write
                    
        # 2. Check Log for new entries
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    newest_line = lines[-1].strip()
                    if newest_line != last_log_line:
                        print(f"\n[{current_ts}] 📜 LOG: {newest_line}")
                        last_log_line = newest_line

    except Exception as e:
        print(f"\nMonitor Error: {e}")
        
    time.sleep(15)

print("\n=== MONITOR FINISHED ===")
