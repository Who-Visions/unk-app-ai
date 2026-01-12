
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.thread_runner.runner import ThreadRunner
from services.thread_runner.models import Thread

async def main():
    print("🧪 Testing Thread Runner...")
    
    # Needs auth (mock or real) - assuming default credentials or .env
    # For now, let's assume it initializes (or fails on auth, which is a success for code loading)
    try:
        runner = ThreadRunner("unk-app-480102")
        t = Thread(goal="Fix the login page typo", context_refs=["ticket-123"])
        
        print(f"Created Thread Request: {t.json()}")
        
        # Execute run (will trigger telemetry and evals)
        result = await runner.run_thread(t)
        
        print("\n📊 Verification Output:")
        print(f"Status: {result.status}")
        print(f"Metrics: {result.metrics}")
        print(f"Validations: {[v.dict() for v in result.validations]}")
        
    except Exception as e:
        print(f"⚠️ Runner Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
