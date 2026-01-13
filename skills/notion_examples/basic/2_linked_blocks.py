
import os
import sys

from dotenv import load_dotenv

from skills.notion_skill import NotionSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()


def example_linked_blocks():
    notion = NotionSkill()
    db_id = "17b824015391800c8f12c9869150047d"

    # Create Scratchpad
    print("Creating Linked Block Scratchpad...")
    page_res = notion.create_page(db_id, "Linked Block Example")
    if "error" in page_res:
        print(f"Error: {page_res}")
        return
    page_id = page_res["page_id"]

    # 2. Add Linked/Mention Blocks
    blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Mentioning a user: "}
                    },
                    {
                        "type": "mention",
                        "mention": {
                            "type": "user",
                            "user": {"id": notion.get_me().get("id", "5cee30c3-0fe0-4d9a-a22b-0cc2d6e228e1")}
                        }
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Link to Database: "}
                    },
                    {
                        "type": "mention",
                        "mention": {
                            "type": "database",
                            "database": {"id": db_id}
                        }
                    }
                ]
            }
        }
    ]

    print("Appending linked blocks...")
    notion.client.blocks.children.append(page_id, children=blocks)
    print("✅ Linked Blocks appended.")


if __name__ == "__main__":
    example_linked_blocks()
