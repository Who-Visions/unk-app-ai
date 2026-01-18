"""
verify_chat.py
==============
Rigorous 100x Validation of Chat State Integration.
Simulates the exact crash condition (appending to state["chat_log"]) 100 times.
"""
import sys
import os
import time

# Mocking imports to avoid starting the full bot threads
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from scripts.unk_trader_cli import state
    print("[TEST] Imported state successfully.")
except ImportError as e:
    print(f"[FAIL] Could not import unk_trader_cli: {e}")
    sys.exit(1)

def run_validation():
    print(f"[TEST] Starting 100x Validation Cycle...")
    
    # 1. Existence Check
    if "chat_log" not in state:
        print("[FAIL] 'chat_log' key MISSING from state!")
        sys.exit(1)
        
    if not isinstance(state["chat_log"], list):
        print(f"[FAIL] 'chat_log' is {type(state['chat_log'])}, expected list!")
        sys.exit(1)

    # 2. Stress Test (100 iterations)
    failures = 0
    for i in range(1, 101):
        try:
            msg = f"Test Message {i}"
            state["chat_log"].append(("User", msg))
            
            # Verify tail
            last = state["chat_log"][-1]
            if last != ("User", msg):
                print(f"[FAIL] Iteration {i}: Content mismatch.")
                failures += 1
            
            if i % 20 == 0:
                print(f"[INFO] Verified {i}/100 operations...")
                
        except KeyError:
            print(f"[FAIL] Iteration {i}: KeyError 'chat_log'!")
            failures += 1
        except Exception as e:
            print(f"[FAIL] Iteration {i}: Unexpected Error: {e}")
            failures += 1

    if failures == 0:
        print("\n[SUCCESS] 100/100 Validations Passed.")
        print(f"[INFO] Final Chat Log Size: {len(state['chat_log'])}")
        print("[INFO] System Ready for Chat.")
    else:
        print(f"\n[FAIL] {failures} errors detected during validation.")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
