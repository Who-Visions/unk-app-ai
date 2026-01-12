
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def inspect_metrics():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print("🔍 Searching for 'Metrics log'...")
    try:
        results = client.search(query="Metrics Log").get("results", [])
        print(f"Found {len(results)} matches.")
        
        for r in results:
            obj_type = r["object"]
            title_text = "Untitled"
            
            if obj_type == "database":
                t_list = r.get("title", [])
                if t_list: title_text = t_list[0]["plain_text"]
                print(f"\n[DATABASE] {title_text} ({r['id']})")
                print(f"   Properties: {list(r['properties'].keys())}")
                
            elif obj_type == "page":
                # Find title prop
                props = r.get("properties", {})
                for key, val in props.items():
                    if val["id"] == "title":
                        t_list = val.get("title", [])
                        if t_list: title_text = t_list[0]["plain_text"]
                print(f"\n[PAGE] {title_text} ({r['id']})")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_metrics()
