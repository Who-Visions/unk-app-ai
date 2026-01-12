
import os
import sys
import logging
from notion_client import Client
from dotenv import load_dotenv

# Silence HTTP logs
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.config import NOTION_WHO_VISIONS_SECRET

ids_to_check = [
    "eb09880f9fe0450ea9c0fb23a201a235"
]

client = Client(auth=NOTION_WHO_VISIONS_SECRET)

import json

results = {}
print("Mapping IDs...")
for db_id in ids_to_check:
    try:
        db = client.databases.retrieve(db_id)
        title = db['title'][0]['plain_text'] if db['title'] else 'Untitled'
        results[db_id] = title
        print(f"{db_id} : {title}")
    except Exception as e:
        print(f"{db_id} : ERROR {e}")

with open("id_map.json", "w") as f:
    json.dump(results, f, indent=2)
