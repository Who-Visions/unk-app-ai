
import os
import sys

from dotenv import load_dotenv

from skills.notion_skill import NotionSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()


def mock_web_form_submission():
    """Simulates receiving a JSON payload from a web form."""
    return {
        "name": "Jane User",
        "email": "jane@example.com",
        "inquiry_type": "Sales",
        "message": "Interested in enterprise plan."
    }


def example_web_form_handler():
    notion = NotionSkill()
    # Target: Lead Gen DB (Using constant if defined, or fallback to generic ID)
    # Using a generic ID here for the example, would be env var in production.
    db_id = "17b82401539180769b55c27591605380"  # Web Projects (using as Lead Gen proxy)

    data = mock_web_form_submission()
    print(f"Received Form Data: {data}")

    print("creating lead in Notion...")

    # Map Form Data to Notion Properties
    properties = {
        "Name": {"title": [{"text": {"content": f"Lead: {data['name']}"}}]},
        "Status": {"select": {"name": "New"}},
        # In a real DB, you'd have Email and Type properties
        # "Email": {"email": data['email']},
        # "Type": {"select": {"name": data['inquiry_type']}}
    }

    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Inquiry Details"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": data['message']}}]}
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": f"Contact: {data['email']}"}}],
                "icon": {"emoji": "📧"}
            }
        }
    ]

    result = notion.create_page(
        parent_id=db_id,
        title=f"Lead: {data['name']}",
        properties=properties,
        children=children
    )

    if "id" in result:
        print(f"✅ Lead Created: {result.get('url')}")
    else:
        print(f"❌ Failed: {result}")


if __name__ == "__main__":
    example_web_form_handler()
