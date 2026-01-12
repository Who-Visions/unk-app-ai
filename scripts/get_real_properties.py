
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_ID = "d17006d5c557416688cfd3a7df1f8d8c"

def get_props():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    try:
        db = client.databases.retrieve(DB_ID)
        print(f"✅ DB Connected: {db['title'][0]['plain_text']}")
        print(f"\nREAL PROPERTIES in DB ({len(db['properties'])}):")
        for key in db['properties'].keys():
            print(f"   - {key}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_props()
