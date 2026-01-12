
import os
import sys
import json
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_ID = "d17006d5c557416688cfd3a7df1f8d8c"

def dump_json():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"DTO: {DB_ID}")
    try:
        obj = client.databases.retrieve(DB_ID)
        with open("schema_dump.json", "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
        print("✅ Dumped to schema_dump.json")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    dump_json()
