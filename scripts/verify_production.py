
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.thread_runner.models import Thread, ThreadStatus
from services.thread_runner.persistence import store
from services.thread_runner.runner import ThreadRunner
from skills.notion_skill import NotionSkill, DB_AI_TRAINING

async def test_persistence():
    print("\n--- Testing Persistence ---")
    t = Thread(goal="Test Persistence", context_refs=["check-1"])
    await store.save_thread(t)
    print(f"✅ Saved Thread: {t.thread_id}")
    
    loaded = await store.load_thread(t.thread_id)
    if loaded and loaded.goal == "Test Persistence":
        print(f"✅ Loaded Thread: {loaded.thread_id}")
    else:
        print("❌ Persistence Failed!")

async def test_notion_integration():
    print("\n--- Testing Notion Integration ---")
    # Only test if we have credentials
    if not os.environ.get("NOTION_WHO_VISIONS_SECRET"):
         print("⚠️ Skipping Notion test (No credentials in env)")
         return

    skill = NotionSkill(token=os.environ.get("NOTION_WHO_VISIONS_SECRET"))
    
    # 1. Check Search
    res = skill.search_observatory("Studio OS")
    print(f"Search Result len: {len(res)}")
    
    # 2. Check Metric Logging (if DB_AI_TRAINING is set)
    if DB_AI_TRAINING and "placeholder" not in DB_AI_TRAINING.lower():
         log_res = skill.log_training_metric("TestModel", "verification_check", 1.0)
         print(f"Metric Log: {log_res}")
    else:
         print("⚠️ Skipping Metric Log (No DB ID)")

async def test_thread_execution():
    print("\n--- Testing Thread Execution (Notification) ---")
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("⚠️ Skipping Execution (No GCP Project)")
        return

    runner = ThreadRunner(project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    t = Thread(goal="Read the first 5 lines of README.md", context_refs=["test-read"])
    
    # Run fully
    print("Running thread (Refactoring Tool Check)...")
    try:
        res = await runner.run_thread(t)
        print(f"✅ Thread Finished: {res.status}")
        if "Unk App Agent" in (res.final_summary or "") or "Introduction" in (res.final_summary or ""):
             print("✅ Tool Verification: Agent successfully read file properties.")
    except Exception as e:
        print(f"❌ Thread Execution Failed: {e}")

async def main():
    print("🚀 Starting Production Verification")
    await test_persistence()
    await test_notion_integration()
    await test_thread_execution() 
    print("\n✅ Verification Complete")

if __name__ == "__main__":
    asyncio.run(main())
