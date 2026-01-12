
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
    print("🤖 Initializing Notion Refactoring Agent...")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT not set.")
        return

    runner = ThreadRunner(project_id=project_id)
    
    # Define the Job
    goal = (
        "Refactor 'skills/notion_skill.py'. "
        "1. Improve error handling for missing databases (catch APIResponseError). "
        "2. Add full Type Hints. "
        "3. Ensure 'Metrics Log' (d1700...) ID is used correctly. "
        "4. Run 'python scripts/test_notion_skill.py' to verify."
    )
    
    thread = Thread(
        goal=goal,
        type="refactor",
        context_refs=["skills/notion_skill.py", "scripts/test_notion_skill.py"]
    )
    
    print(f"🎯 Goal: {goal}")
    print("⏳ Starting Loop (Target: Notion Skill)...")
    
    # Run
    result = await runner.run_thread(thread)
    
    print(f"\n✅ Job Complete. Status: {result.status}")
    print(f"📝 Final Summary: {result.final_summary}")

if __name__ == "__main__":
    asyncio.run(main())
