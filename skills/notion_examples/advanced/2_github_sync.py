
"""
Advanced Example: GitHub Sync (Logic Stub)
Simulates syncing GitHub issues to Notion.
Requires PyGithub (not installed), so we mock the GitHub part.
"""
import os
import sys

from dotenv import load_dotenv

from skills.notion_skill import NotionSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()


# Mock Issue Data
MOCK_ISSUES = [
    {"id": 101, "title": "Fix Login Bug", "state": "open",
        "url": "https://github.com/org/repo/issues/101"},
    {"id": 102, "title": "Add Dark Mode", "state": "closed",
        "url": "https://github.com/org/repo/issues/102"},
]


def example_github_sync():
    notion = NotionSkill()
    db_id = "17b824015391800c8f12c9869150047d"  # Project Tracker

    print("🔄 Starting Mock GitHub Sync...")

    for issue in MOCK_ISSUES:
        print(f"Processing Issue #{issue['id']}: {issue['title']}")

        # 1. Check if exists (Search logic or Query specific property)
        # Ideally we have a "GitHub ID" property. We'll simulate checking by Title here.
        # This is inefficient but demonstrates the logic.
        existing = notion.query_database(db_id, filter={
            "property": "Name",
            "title": {"equals": f"GH-{issue['id']}: {issue['title']}"}
        })

        if existing:
            page_id = existing[0]["id"]
            print(f"  -> Found existing {page_id}. Updating...")
            # Update Status based on State
            status = "Done" if issue["state"] == "closed" else "Not Started"
            notion.update_page(page_id, properties={"Status": {"select": {"name": status}}})
        else:
            print(f"  -> Creating new entry...")
            notion.create_page(
                parent_id=db_id,
                title=f"GH-{issue['id']}: {issue['title']}",
                properties={
                    "Status": {"select": {"name": "Not Started"}},
                    "Type": {"select": {"name": "Task"}}
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": [{"type": "text", "text": {"content": f"Imported from {issue['url']}"}}]}
                    }
                ]
            )

    print("✅ Sync logic complete.")


if __name__ == "__main__":
    example_github_sync()
