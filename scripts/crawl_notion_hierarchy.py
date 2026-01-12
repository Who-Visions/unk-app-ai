
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def get_title(obj):
    if "properties" in obj:
        # Page: usually strict "title" property
        for key, val in obj["properties"].items():
            if val["id"] == "title":
                t_list = val.get("title", [])
                if t_list: return t_list[0]["plain_text"]
    elif "title" in obj:
        # Database or Child Page block often has direct title
        t_list = obj.get("title", [])
        if isinstance(t_list, list) and t_list:
             return t_list[0].get("plain_text", "")
        # Block title?
        if isinstance(obj.get("child_page"), dict):
            return obj["child_page"].get("title", "")
        if isinstance(obj.get("child_database"), dict):
            return obj["child_database"].get("title", "")
            
    return "Untitled"

def crawl_children(client, block_id, depth=0):
    if depth > 2: return # Limit recursion
    
    try:
        children = client.blocks.children.list(block_id=block_id)
        for block in children.get("results", []):
            if block["type"] == "child_database":
                title = block["child_database"].get("title", "Untitled DB")
                print(f"{'  ' * (depth+1)}📂 DB: [bold]{title}[/bold] ({block['id']})")
            elif block["type"] == "child_page":
                title = block["child_page"].get("title", "Untitled Page")
                print(f"{'  ' * (depth+1)}📄 Page: {title} ({block['id']})")
                # Recurse into pages
                crawl_children(client, block["id"], depth + 1)
    except Exception as e:
        pass
        # print(f"{'  ' * (depth+1)}Error scanning children: {e}")

def main():
    token = os.environ.get("NOTION_WHO_VISIONS_SECRET")
    if not token:
        print("❌ No token.")
        return

    client = Client(auth=token)
    print("🕷️ Crawling Notion Workspace...")
    
    # Start with Search to get Roots
    results = client.search(filter={"property": "object", "value": "page"}).get("results", [])
    
    print(f"Found {len(results)} Root-accessible objects.")
    
    with open("notion_hierarchy.txt", "w", encoding="utf-8") as f:
        for obj in results:
            title = get_title(obj)
            obj_type = obj["object"]
            line = f"ROOT {obj_type.upper()}: {title} ({obj['id']})\n"
            print(line.strip())
            f.write(line)
            
            # Scan children
            crawl_children_to_file(client, obj["id"], f)

def crawl_children_to_file(client, block_id, f, depth=0):
    if depth > 2: return
    try:
        children = client.blocks.children.list(block_id=block_id)
        for block in children.get("results", []):
            if block["type"] == "child_database":
                title = block["child_database"].get("title", "Untitled DB")
                line = f"{'  ' * (depth+1)}📂 DB: {title} ({block['id']})\n"
                print(line.strip())
                f.write(line)
            elif block["type"] == "child_page":
                title = block["child_page"].get("title", "Untitled Page")
                line = f"{'  ' * (depth+1)}📄 Page: {title} ({block['id']})\n"
                print(line.strip())
                f.write(line)
                crawl_children_to_file(client, block["id"], f, depth + 1)
    except Exception:
        pass

if __name__ == "__main__":
    main()
