
import os
import sys
import datetime
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_ID = "d17006d5c557416688cfd3a7df1f8d8c"
TEST_RUN_ID = "debug-run-123"

def debug_all_fields():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🧪 Comprehensive Field Test on {DB_ID}\n")
    
    # Base is just Title + Date (assuming these work)
    base_props = {
        "Name": {"title": [{"text": {"content": "Comprehensive Debug"}}]},
        "Date": {"date": {"start": datetime.datetime.utcnow().isoformat()}}
    }
    
    fields_to_test = [
        ("Model Name", {"Model Name": {"rich_text": [{"text": {"content": "Gemini-Test"}}]}}),
        ("Session ID", {"Session ID": {"rich_text": [{"text": {"content": "sess-123"}}]}}),
        ("Run ID", {"Run ID": {"rich_text": [{"text": {"content": TEST_RUN_ID}}]}}),
        ("User ID", {"User ID": {"rich_text": [{"text": {"content": "user-debug"}}]}}),
        ("Environment", {"Environment": {"select": {"name": "Test"}}}),
        ("Latency", {"Latency": {"number": 123.45}}),
        ("Cost", {"Cost": {"number": 0.005}}),
        ("Token Count", {"Token Count": {"number": 1000}}),
        ("Input Tokens", {"Input Tokens": {"number": 800}}),
        ("Output Tokens", {"Output Tokens": {"number": 200}}),
        ("Duration", {"Duration": {"number": 1.5}}),
        ("Response Code", {"Response Code": {"number": 200}}),
        ("Success", {"Success": {"checkbox": True}}),
        ("Request ID", {"Request ID": {"rich_text": [{"text": {"content": "req-xyz"}}]}}),
        ("Endpoint", {"Endpoint": {"rich_text": [{"text": {"content": "generate"}}]}}),
        ("Error Message", {"Error Message": {"rich_text": [{"text": {"content": "None"}}]}}),
        ("Feedback", {"Feedback": {"rich_text": [{"text": {"content": "Great"}}]}}),
        ("Rating", {"Rating": {"number": 5}}),
    ]
    
    for name, prop_payload in fields_to_test:
        print(f"Testing '{name}'... ", end="")
        full_payload = base_props.copy()
        try:
            full_payload.update(prop_payload)
            client.pages.create(
                parent={"database_id": DB_ID},
                properties=full_payload
            )
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")

if __name__ == "__main__":
    debug_all_fields()
