
import os
import sys
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from routers.config import NOTION_WHO_VISIONS_SECRET
from skills.notion_skill import DB_AI_TRAINING

client = Client(auth=NOTION_WHO_VISIONS_SECRET)

DB_METRICS = "d17006d5c557416688cfd3a7df1f8d8c"
print(f"Inspecting DB: {DB_METRICS}")
try:
    db = client.databases.retrieve(DB_METRICS)
    import json
    with open("schema_full.json", "w") as f:
        # Dump full object but use indent
        f.write(json.dumps(db, indent=2))
except Exception as e:
    print(f"Error: {e}")
