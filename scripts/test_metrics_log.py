
import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from skills.notion_skill import NotionSkill, DB_METRICS_LOG

def test_metrics_write():
    print(f"🧪 Testing Write to Metrics Log ({DB_METRICS_LOG})...")
    notion = NotionSkill()
    
    if not notion.client:
        print("❌ Notion Client not initialized.")
        print("Init Skill...")
        notion = NotionSkill() # Re-initialize if client was not set initially
    
    try:
        me = notion.get_me()
        print(f"✅ Skill Connected per: {me.get('name') or me.get('bot', {}).get('owner', {}).get('user', {}).get('name')}")
    except Exception as e:
        print(f"❌ Skill Init Failed: {e}")
        return

    run_id = str(uuid.uuid4())[:8]
    
    # Prepare parameters for logging
    params = {
        "model_name": "Test-Model-v1",
        "run_id": run_id,
        "session_id": f"test-session-{run_id}",
        "user_id": "verifier-bot",
        "latency": 123.45,
        "token_count": 100,
        "cost": 0.002,
        "success": True,
        "feedback": "Final Verification: Full Schema Fidelity Check",
        "rating": 5,
        "environment": "Test"
    }

    print("Running Test...") # Added this print statement
    try:
        # Assuming 'notion' is the 'agent' here based on context
        if notion.log_training_metric(**params):
            print(f"✅ Success! Logged metric with Run ID: {run_id}")
        else:
            print("❌ Failed to log metric (returned False).Check Skill logs.")
    except Exception as e:
        print(f"❌ Exception during call: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_metrics_write()
