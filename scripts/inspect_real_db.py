
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# The ID found in the search results that is actually a DATABASE
REAL_DB_ID = "61502f6ea44da77b715f7344be92a342"

def inspect_real_db():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🔍 Inspecting Real DB: {REAL_DB_ID}")
    try:
        db = client.databases.retrieve(REAL_DB_ID)
        title = db['title'][0]['plain_text']
        print(f"✅ Connected to: {title}")
        print("📋 Properties Found:")
        
        props = db.get("properties", {})
        sorted_keys = sorted(props.keys())
        for k in sorted_keys:
            print(f"   - {k} ({props[k]['type']})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_real_db()
