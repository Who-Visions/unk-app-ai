
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

PAGE_ID = "d17006d5c557416688cfd3a7df1f8d8c"

def find_child_db():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🔍 Scanning children of Page {PAGE_ID}...")
    try:
        children = client.blocks.children.list(block_id=PAGE_ID)
        found = False
        for block in children.get("results", []):
            if block["type"] == "child_database":
                db_id = block["id"]
                title = block["child_database"].get("title", "Untitled")
                print(f"✅ FOUND DATABASE: '{title}'")
                print(f"   ID: {db_id}")
                
                # Now get schema
                db = client.databases.retrieve(db_id)
                print(f"   Properties: {list(db['properties'].keys())}")
                found = True
                
        if not found:
            print("❌ No child database found in this page.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_child_db()
