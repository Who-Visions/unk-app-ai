
import os
import sys
import uuid
import datetime
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_ID = "d17006d5c557416688cfd3a7df1f8d8c"

def debug_write():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🧪 Debugging Writes to {DB_ID}")
    
    base_props = {
        "Name": {"title": [{"text": {"content": "Debug Entry"}}]},
        "Date": {"date": {"start": datetime.datetime.utcnow().isoformat()}}
    }
    
    # Test Optional Fields One by One
    test_fields = [
        ("Rating (Number)", {"Rating": {"number": 5}}),
        ("Feedback (Text)", {"Feedback": {"rich_text": [{"text": {"content": "Test"}}]}}),
        ("Error Message (Text)", {"Error Message": {"rich_text": [{"text": {"content": "Err"}}]}}),
        ("Input Tokens (Number)", {"Input Tokens": {"number": 100}}),
        ("Cost (Number)", {"Cost": {"number": 0.01}})
    ]
    
    for name, prop_dict in test_fields:
        print(f"   Trying {name}...", end="")
        payload = base_props.copy()
        payload.update(prop_dict)
        
        try:
            client.pages.create(
                parent={"database_id": DB_ID},
                properties=payload
            )
            print(" ✅ OK")
        except Exception as e:
            print(f" ❌ FAIL: {e}")

if __name__ == "__main__":
    debug_write()
