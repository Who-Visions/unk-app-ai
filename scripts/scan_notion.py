
import os
import sys
from notion_client import Client

def scan():
    token = os.environ.get("NOTION_OBSERVATORY_SECRET")
    # token = "PLACEHOLDER"
    if not token:
        print("ERROR: No Notion Token found.")
        return

    notion = Client(auth=token)
    
    print(f"--- Scanning Notion for integration token: {token[:10]}... ---")
    
    try:
        # 1. Search for everything
        results = notion.search().get("results", [])
        databases = [r for r in results if r["object"] == "database"]
        print(f"Found {len(databases)} databases accessible to this integration.")
        
        for db in databases:
            title_parts = db.get("title", [])
            title = title_parts[0].get("plain_text", "Untitled") if title_parts else "Untitled"
            db_id = db['id'].replace("-", "")
            print(f"\n--- Database: {title} ---")
            print(f"  ID: {db_id}")
            print("  Properties:")
            for prop_name, prop_data in db.get("properties", {}).items():
                print(f"    - {prop_name} ({prop_data['type']})")

        # 2. Check the specific page if it's not a database result
        hub_id = "2ebca671311e81dbafadd01e29d2856f"
        print(f"\n--- Checking Specific Hub Page: {hub_id} ---")
        try:
            page = notion.pages.retrieve(page_id=hub_id)
            title_prop = page.get("properties", {}).get("title", {}).get("title", [])
            title = title_prop[0].get("plain_text", "Unknown") if title_prop else "Unknown"
            print(f"Page Found: {title}")
            
            # List children to find inline databases
            children = notion.blocks.children.list(block_id=hub_id).get("results", [])
            for child in children:
                if child["type"] == "child_database":
                    db_id = child["id"]
                    db_title = child["child_database"]["title"]
                    print(f"  - Found Inline Database: {db_title} ({db_id})")
                    
                    # Get DB details
                    try:
                        db_details = notion.databases.retrieve(database_id=db_id)
                        print(f"    - DB: {db_title}")
                        print(f"    - Object Keys: {list(db_details.keys())}")
                        if "properties" in db_details:
                            props = db_details["properties"]
                            print(f"    - Number of Properties: {len(props)}")
                            print(f"    - Property Names: {list(props.keys())[:10]}... (Total {len(props)})")
                        else:
                            print("    - PROPERTIES KEY ABSENT FROM RESPONSE")
                            # Print a snippet of the object to see what it IS
                            snippet = {k: db_details[k] for k in list(db_details.keys())[:5]}
                            print(f"    - Object Snippet: {snippet}")
                    except Exception as ex:
                        print(f"      [Retrieve Error: {ex}]")
        except Exception as e:
            print(f"Could not retrieve specific page: {e}")

    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    scan()
