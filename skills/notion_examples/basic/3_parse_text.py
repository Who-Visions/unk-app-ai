
import os
import sys

from dotenv import load_dotenv

from skills.notion_skill import NotionSkill

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()


def extract_text_recursive(block):
    """
    Recursively extracts plain text from a block.
    Supports Paragraph, Heading, Bullet item, etc.
    """
    btype = block.get("type")
    content = ""

    # Common text holding blocks
    if btype in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle", "quote", "callout"]:
        text_obj = block.get(btype, {}).get("rich_text", [])
        for t in text_obj:
            content += t.get("plain_text", "")

    # Add newline for block separation
    if content:
        content += "\n"

    return content


def example_parse_text():
    notion = NotionSkill()

    # Target search or specific page
    print("Searching for an example page to parse...")
    results = notion.search_observatory("MCP")
    if not results:
        print("No pages found to parse.")
        return

    target_page = results[0]
    page_id = target_page["id"]
    print(f"Parsing: {target_page.get('title')} ({page_id})")

    # Fetch Content using MCP tool
    data = notion.fetch_page(page_id)
    if "error" in data:
        print(f"Error fetching: {data['error']}")
        return

    blocks = data.get("content", [])
    full_text = ""

    for block in blocks:
        full_text += extract_text_recursive(block)

    print("\n--- EXTRACTED TEXT ---")
    print(full_text)
    print("----------------------")


if __name__ == "__main__":
    example_parse_text()
