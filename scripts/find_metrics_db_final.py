
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def find_metrics_db():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print("🔍 Searching for Database named 'Metrics Log'...")
    try:
        # Search specifically for databases
        results = client.search(
            query="Metrics Log",
            filter={"property": "object", "value": "database"}
        ).get("results", [])
        
        print(f"Found {len(results)} matches.")
        
        for r in results:
            title = "Untitled"
            if r.get("title"):
                title = r["title"][0]["plain_text"]
            
            print(f"\n✅ DATABASE: '{title}' ({r['id']})")
            print(f"   Properties: {list(r['properties'].keys())}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_metrics_db()
