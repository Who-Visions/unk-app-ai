import os
import sys
import logging
sys.path.append(os.getcwd())
from services.trading_memory import TradingMemory

def test_sync():
    logging.basicConfig(level=logging.INFO)
    print("--- Testing Notion Triple Sync ---")
    
    tm = TradingMemory()
    
    # 1. Test Trade Sync
    print("\n[1] Testing Trade Sync...")
    trade_id = tm.log_trade(
        symbol="DOGE-USD",
        side="buy",
        quantity=100.0,
        price=0.35,
        strategy="War Mode",
        reason="Testing Notion Triple Sync Integration"
    )
    print(f"Trade logged locally: {trade_id}")
    
    # 2. Test Snapshot Sync
    print("\n[2] Testing Snapshot Sync...")
    snapshot_id = tm.log_portfolio_snapshot(
        holdings={"DOGE-USD": {"quantity": 100.0, "value": 35.0, "pnl_percent": 0.0}},
        buying_power=500.0,
        total_value=535.0
    )
    print(f"Snapshot logged locally: {snapshot_id}")
    
    print("\nCheck the console logs for 'Synced ... to Notion' messages.")

if __name__ == "__main__":
    test_sync()
