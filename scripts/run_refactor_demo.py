import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env before imports
load_dotenv()

from services.thread_runner.runner import ThreadRunner
from services.thread_runner.models import Thread

async def main():
    print("🤖 Initializing Refactoring Agent...")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT not set.")
        return

    runner = ThreadRunner(project_id=project_id)
    
    # Define the Job
    goal = (
        "Refactor 'examples/inefficient_code.py'. "
        "1. Add Type Hints. 2. Use list comprehension or faster loop. 3. Remove artificial sleep."
    )
    
    thread = Thread(
        goal=goal,
        type="refactor",
        context_refs=["examples/inefficient_code.py"]
    )
    
    print(f"🎯 Goal: {goal}")
    print("⏳ Starting 100-Turn Loop (Output filtered)...")
    
    # Run
    result = await runner.run_thread(thread)
    
    print(f"\n✅ Job Complete. Status: {result.status}")
    print(f"📝 Final Summary: {result.final_summary}")
    
    # Show the result file
    print("\n--- Content of examples/inefficient_code.py ---")
    with open("examples/inefficient_code.py", "r") as f:
        print(f.read())
    print("-----------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
