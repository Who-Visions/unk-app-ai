
import os
import sys

from dotenv import load_dotenv

from skills.notion_skill import NotionSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()


def example_create_blocks():
    notion = NotionSkill()
    if not notion.client:
        print("❌ Notion client invalid.")
        return

    # User must provide a PAGE ID for this example to target.
    # In a real tool we'd ask, here we'll search for the MCP test page or creating a new one.
    db_id = "17b824015391800c8f12c9869150047d"  # Project Tracker

    # Create a scratch page to hold blocks
    print("Creating scratch page for Block Examples...")
    page_res = notion.create_page(db_id, "Block Example Scratchpad")
    if "error" in page_res:
        print(f"❌ Failed to create page: {page_res['error']}")
        return

    page_id = page_res["page_id"]
    print(f"✅ Created Scratchpad: {page_id}")

    # 1. Add Basic Blocks (Paragraph, Heading)
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Hello from API"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "This is a basic text block created via "}},
                    {"type": "text", "text": {"content": "Notion API",
                                              "link": {"url": "https://developers.notion.com"}}}
                ]
            }
        },
        {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": "Review this example"}}],
                "checked": False
            }
        }
    ]

    print("Appending blocks...")
    notion.client.blocks.children.append(page_id, children=blocks)
    print("✅ Blocks appended.")


if __name__ == "__main__":
    example_create_blocks()
