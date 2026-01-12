
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def debug_token():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    print(f"🔑 Debugging Token: {token[:4]}...{token[-4:] if token else 'None'}")
    
    if not token:
        print("❌ No token found in environment.")
        return

    client = Client(auth=token)
    
    print("\n1. Testing users.list()...")
    try:
        users = client.users.list()
        print(f"✅ Success! Found {len(users.get('results', []))} users.")
        for u in users.get("results", [])[:3]: # Show first 3
            print(f"   - {u.get('name')} ({u.get('type')})")
    except Exception as e:
        print(f"❌ Failed: {e}")
        
    print("\n2. Testing search()...")
    try:
        results = client.search(page_size=5)
        print(f"✅ Success! Found {len(results.get('results', []))} objects.")
        for r in results.get("results", []):
            title = "Untitled"
            if r["object"] == "page":
                props = r.get("properties", {})
                # Try getting title from properties
                for key, val in props.items():
                    if val["id"] == "title":
                        t_list = val.get("title", [])
                        if t_list: title = t_list[0]["plain_text"]
            elif r["object"] == "database":
                t_list = r.get("title", [])
                if t_list: title = t_list[0]["plain_text"]
                
            print(f"   - [{r['object']}] {title} ({r['id']})")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    debug_token()
