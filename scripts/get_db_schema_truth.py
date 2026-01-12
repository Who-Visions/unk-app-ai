
import os
import sys
import json
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_ID = "d17006d5c557416688cfd3a7df1f8d8c"

def get_truth():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    client = Client(auth=token)
    
    print(f"🔍 Introspecting DB: {DB_ID}")
    
    try:
        # 1. Check Object Type
        obj = client.databases.retrieve(DB_ID)
        print(f"ObjectType: {obj['object']}")
        print(f"Title: {obj['title'][0]['plain_text']}")
        
        # 2. Dump Properties
        print("\n📋 SCHEMA TRUTH:")
        props = obj.get('properties', {})
        for name, details in props.items():
            ptype = details['type']
            print(f"   '{name}': {ptype}")
            if ptype == 'select':
                opts = [o['name'] for o in details['select']['options']]
                print(f"      Options: {opts}")
            if ptype == 'multi_select':
                opts = [o['name'] for o in details['multi_select']['options']]
                print(f"      Options: {opts}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_truth()
