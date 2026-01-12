
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# The ID found in 'data_sources' of the previous DB dump
SOURCE_DB_ID = "834a6235-8c85-4207-b022-dbff6c85ff2d"

def inspect_source_db():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🔍 Inspecting Source DB: {SOURCE_DB_ID}")
    try:
        db = client.databases.retrieve(SOURCE_DB_ID)
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
    inspect_source_db()
