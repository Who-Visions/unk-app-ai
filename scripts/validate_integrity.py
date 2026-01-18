"""
System Integrity & Import Validation Script
==========================================
Verifies that all critical Python modules for Unk (Trader) and the CLI (Dashboard)
import correctly and that dependencies are met.
"""
import sys
import os
import importlib
import traceback

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CRITICAL_MODULES = [
    "services.brokers.robinhood_crypto",
    "services.cloud_sync",
    "services.governor",
    "services.trading_memory",
    "services.loredb",
    "services.llm.gemini_agent",
    "services.llm.unk_agent",
    "services.llm.trading_tools",
    "services.llm.reasoning_agent",
    "scripts.unk_trader_cli"
]

EXTERNAL_DEPS = [
    "rich",
    "dotenv",
    "google.genai",
    "vertexai",
    "aiosqlite",
    "firebase_admin",
    "google.cloud.firestore",
    "google.cloud.bigquery"
]

def validate():
    print("=" * 60)
    print("🚀 UNK SYSTEM INTEGRITY CHECK")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    print("\n📦 Checking External Dependencies...")
    for dep in EXTERNAL_DEPS:
        try:
            importlib.import_module(dep)
            print(f"  ✅ {dep:<30} OK")
            success_count += 1
        except ImportError as e:
            print(f"  ❌ {dep:<30} FAILED: {e}")
            fail_count += 1

    print("\n🧠 Checking Unk & CLI Modules...")
    for mod in CRITICAL_MODULES:
        try:
            print(f"  🔄 Importing {mod}...", end="\r")
            importlib.import_module(mod)
            print(f"  ✅ {mod:<30} OK")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {mod:<30} FAILED")
            print("-" * 40)
            traceback.print_exc()
            print("-" * 40)
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {success_count} Passed, {fail_count} Failed")
    print("=" * 60)
    
    if fail_count > 0:
        sys.exit(1)
    else:
        print("\n✨ All systems green. Unk is ready to make money.")
        sys.exit(0)

if __name__ == "__main__":
    validate()
