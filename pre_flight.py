import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

print("Testing imports...")
try:
    from rich.markup import escape
    from services.llm.reasoning_agent import ReasoningAgent
    from services.llm.unk_agent import UnkAiAgent
    from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI
    from trading.core.shared import enterprise_throttle
    from trading.integrations.memory import TradingMemory
    print("Imports OK.")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

print("Testing NY Time Sync...")
now_ny = datetime.datetime.now()
print(f"Local NY Time: {now_ny.strftime('%Y-%m-%d %I:%M:%S %p')}")

print("Diagnostic Complete.")
