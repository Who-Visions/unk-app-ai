
import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# Load env vars
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.config import NOTION_WHO_VISIONS_SECRET, NOTION_OBSERVATORY_SECRET

def check_id(target_id):
    # Try both tokens
    for name, token in [("Who Visions", NOTION_WHO_VISIONS_SECRET), ("Observatory", NOTION_OBSERVATORY_SECRET)]:
        print(f"Checking with {name}...")
        client = Client(auth=token)
        try:
            # Try as database
            db = client.databases.retrieve(target_id)
            print(f"✅ FOUND as DATABASE via {name}!")
            print(f"   Title: {db['title'][0]['plain_text'] if db['title'] else 'Untitled'}")
            print(f"   URL: {db['url']}")
            return
        except Exception as e:
            if "object_not_found" not in str(e):
                 print(f"   Error checking DB: {e}")
        
        try:
            # Try as page
            pg = client.pages.retrieve(target_id)
            print(f"✅ FOUND as PAGE via {name}!")
            print(f"   URL: {pg['url']}")
            return
        except Exception:
            pass
            
    print("❌ ID not found or not accessible with either token.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_notion_id.py <ID>")
    else:
        check_id(sys.argv[1])
