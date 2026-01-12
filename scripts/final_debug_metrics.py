
import os
import sys
import uuid
import traceback
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from skills.notion_skill import NotionSkill, DB_METRICS_LOG

def final_debug():
    print("🚀 Starting Final Debug")
    print(f"📌 DB_METRICS_LOG Constant: '{DB_METRICS_LOG}'")
    
    if DB_METRICS_LOG != "d17006d5c557416688cfd3a7df1f8d8c":
        print("❌ CRITICAL: DB_METRICS_LOG is NOT the correct Database ID!")
        return

    notion = NotionSkill()
    me = notion.get_me()
    print(f"✅ Connected as: {me.get('bot', {}).get('owner', {}).get('user', {}).get('name')}")

    params = {
        "model_name": "Debug-Model-Final",
        "run_id": str(uuid.uuid4())[:8],
        "latency": 99.9,
        "token_count": 50,
        "cost": 0.001,
        "success": True,
        "feedback": "Final Check",
        "rating": 5,
        "environment": "Test"
    }

    print("📝 Calling log_training_metric...")
    try:
        result = notion.log_training_metric(**params)
        print(f"✅ Result: {result}")
    except Exception as e:
        print("❌ EXCEPTION CAUGHT:")
        traceback.print_exc()

if __name__ == "__main__":
    final_debug()
