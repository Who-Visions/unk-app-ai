
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from skills.notion_skill import NotionSkill

def example_query_db():
    notion = NotionSkill()

    # Target: Project Tracker (or our Test DB)
    db_id = "17b824015391800c8f12c9869150047d"

    print(f"Querying DB {db_id}...")

    # Filter for 'Not Started'
    query_filter = {
        "property": "Status",
        "select": {
            "equals": "Not Started"
        }
    }

    # Sort by Name
    sorts = [
        {
            "property": "Name",
            "direction": "ascending"
        }
    ]

    results = notion.query_database(db_id, filter=query_filter, sort=sorts)

    print(f"Found {len(results)} pages:")
    for page in results:
        title = notion._extract_title(page)
        print(f" - {title} ({page['id']})")

if __name__ == "__main__":
    example_query_db()
