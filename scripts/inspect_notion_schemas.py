
import os
import sys
import json
from notion_client import Client
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.config import NOTION_OBSERVATORY_SECRET, NOTION_WHO_VISIONS_SECRET

SECRETS = {
    "The Observatory": NOTION_OBSERVATORY_SECRET,
    "Who Visions LLC": NOTION_WHO_VISIONS_SECRET
}

def inspect_schemas_for_token(name, token):
    if not token or "ntn" not in token:
        print(f"⚠️ Skipping {name}: Invalid token.")
        return

    print(f"\n🔐 Connecting to '{name}' (...{token[-4:]})...")
    notion = Client(auth=token)
    
    print("   (Fetching all objects...)")
    try:
        # Try both unfiltered and filtered searches
        search_res = notion.search(page_size=100).get("results", [])
        print(f"   [DEBUG] Raw search count: {len(search_res)}")
        
        if len(search_res) > 0:
            print(f"   [DEBUG] Found {len(search_res)} objects total.")
            for obj in search_res:
                obj_type = obj["object"]
                try:
                    # Title extraction depends on type
                    title = "Untitled"
                    if obj_type == "database":
                        t = obj.get("title", [])
                        title = t[0]["plain_text"] if t else "Untitled"
                    elif obj_type == "page":
                        # Page title is in properties usually, but messy in search results if not minimal
                        # Fallback to checking 'properties' -> 'title'
                        props = obj.get("properties", {})
                        for key, val in props.items():
                            if val["type"] == "title" and val["title"]:
                                title = val["title"][0]["plain_text"]
                                break
                    
                    print(f"   - [{obj_type}] {title} (ID: {obj['id']})")
                except Exception:
                    print(f"   - [{obj_type}] (Error Parsing Title) ID: {obj['id']}")

        # Filter for databases only
        results = [obj for obj in search_res if obj["object"] == "database"]
        
        if not results:
            print(f"⚠️ No database schemas accessible for '{name}'.")
            # Don't return, let loop finish or just continue
        else:
            print(f"✅ Found {len(results)} databases for '{name}'.\n")

        for db in results:
            title_obj = db.get("title", [])
            title = title_obj[0]["plain_text"] if title_obj else "Untitled"
            db_id = db["id"]
            
            print(f"📂 DATABASE: {title}")
            print(f"   ID: {db_id}")
            print(f"   URL: {db.get('url')}")
            print("   SCHEMA:")
            
            properties = db.get("properties", {})
            # Sort by name for readability
            for prop_name, prop_data in sorted(properties.items()):
                prop_type = prop_data["type"]
                options = ""
                
                # Extract options for select/multi_select
                if prop_type in ["select", "multi_select"]:
                    opts = [opt["name"] for opt in prop_data[prop_type]["options"]]
                    options = f" ({', '.join(opts)})"
                elif prop_type == "formula":
                    options = f" (Formula: {prop_data['formula'].get('expression', 'N/A')})"
                elif prop_type == "relation":
                    options = f" (Related to: {prop_data['relation'].get('database_id', 'Unknown')})"
                
                print(f"    - {prop_name:<20} : {prop_type}{options}")
            print("-" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error inspecting schemas for {name}: {e}")

if __name__ == "__main__":
    print("🧠 Notion Schema Inspector")
    print("========================")
    for name, secret in SECRETS.items():
        inspect_schemas_for_token(name, secret)

