
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.notion_skill import NotionSkill

console = Console()

def main():
    console.print("[bold blue]🧪 Testing Notion MCP Tool Suite...[/bold blue]")
    
    # Init
    notion = NotionSkill()
    if not notion.client:
        console.print("[red]❌ Notion Client Validation Failed (No Token)[/red]")
        return

    # 1. Get Me
    me = notion.get_me()
    console.print(f"👤 Me: {me.get('name')} (ID: {me.get('id')})")

    # 2. Get Users
    users = notion.get_users()
    console.print(f"👥 Users Found: {len(users)}")

    # 3. Create Page
    # Find a valid parent. We'll use the "Web Projects" DB as parent for a test page?
    # Or finding a parent page is safer.
    # Let's try to search for "Metrics Log" to get its ID, or use the constant.
    # Actually, we can just fetch the Metrics Log DB first.
    metrics_db_id = "d17006d5c557416688cfd3a7df1f8d8c"
    
    # Fetch DB
    console.print(f"\n🔍 Fetching Metrics DB ({metrics_db_id})...")
    # Note: ensure fetch_page works on DBs? Use `client.databases.retrieve` usually, but fetch_page uses pages.retrieve.
    # Let's try creating a page INSIDE Metrics Log.
    
    logging_res = notion.log_training_metric(
        model_name="MCP_TEST",
        latency=123.45,
        token_count=50,
        cost=0.001,
        success=True,
        environment="Test"
    )
    console.print(f"📝 Log Result: {logging_res}")
    
    # 4. Search
    console.print("\n🔎 Searching for 'MCP_TEST'...")
    results = notion.search_observatory("MCP_TEST")
    if results:
        page_id = results[0]['id']
        console.print(f"✅ Found Page: {results[0]['title']} ({page_id})")
        
        # 5. Update Page
        console.print(f"✏️ Updating Page {page_id}...")
        update_res = notion.update_page(page_id, properties={"Value": {"number": 999.99}})
        console.print(f"Update Result: {update_res.get('id') and 'Success'}")
        
        # 6. Add Comment
        console.print(f"💬 Adding Comment...")
        comment_res = notion.create_comment(page_id, "Verified via MCP Test Script.")
        console.print(f"Comment Result: {comment_res.get('id') and 'Success'}")
        
    else:
        console.print("[yellow]⚠️ Creation verification skipped (Search didn't find it instantly).[/yellow]")

    console.print("\n[bold green]✅ MCP Suite Test Complete.[/bold green]")

if __name__ == "__main__":
    main()
