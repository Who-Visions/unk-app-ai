
import os
import sys
import time
from dotenv import load_dotenv
from rich.console import Console

# Load Env
load_dotenv()

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.notion_skill import NotionSkill

console = Console()

def main():
    console.print("[bold purple]🧪 Testing Deep Dive Notion Tools...[/bold purple]")
    notion = NotionSkill()
    if not notion.client:
        console.print("[red]❌ No Notion Client[/red]")
        return

    # 1. Get Me & Test Get User
    me = notion.get_me()
    my_id = me.get("id")
    console.print(f"👤 Me: {me.get('name')} ({my_id})")
    
    if my_id:
        console.print(f"🔍 Testing get_user({my_id})...")
        user_info = notion.get_user(my_id)
        console.print(f"✅ User Info Retrieved: {user_info.get('name') == me.get('name')}")

    # 2. Get Teams (Expect empty or error, but valid call)
    console.print(f"👥 Testing get_teams()...")
    teams = notion.get_teams()
    console.print(f"✅ Teams: {len(teams)} (Expected empty/restricted)")

    # 3. Duplicate Page Test
    # We need a page to duplicate. Let's create a temp one first to avoid messing up real data.
    console.print("\n📄 Creating Temp Source Page...")
    # Parent: Use Web Projects DB or a known page. 
    # Let's use the DB_WEB_PROJECTS constant if possible, or just create in Metrics Log implementation?
    # No, let's use the first page from a search as source if safe, or easier: create one.
    # To create, we need a parent.
    # CONSTANT:
    DB_PROJECT_TRACKER = "17b824015391800c8f12c9869150047d"
    
    create_res = notion.create_page(
        parent_id=DB_PROJECT_TRACKER,
        title="MCP_DUPE_TEST_SOURCE",
        properties={} # Simplified: Title only to avoid schema errors
    )
    
    if "id" in create_res:
        source_id = create_res["id"]
        console.print(f"✅ Created Source: {source_id}")
        
        # DUPLICATE
        console.print("🔄 Duplicating Page...")
        dupe_res = notion.duplicate_page(source_id)
        if "new_page_id" in dupe_res:
            dupe_id = dupe_res["new_page_id"]
            console.print(f"✅ Duplication Success! New ID: {dupe_id}")
            console.print(f"🔗 URL: {dupe_res.get('url')}")
            
            # MOVE (Advanced)
            # Try to move duplicates to "Done" status (update) or move parent?
            # Let's try move_page_advanced to SAME parent (noop) or different if we knew one.
            # We'll just try to move it to the same DB to check API response.
            console.print("🚚 Testing Move (to same parent)...")
            move_res = notion.move_page_advanced(dupe_id, DB_PROJECT_TRACKER)
            console.print(f"Move Result: {move_res.get('id') and 'Success (or No-op)'}")
            
            # CLEANUP
            console.print("\n🧹 Cleaning up (Archiving)...")
            notion.update_page(source_id, archived=True)
            notion.update_page(dupe_id, archived=True)
            console.print("✅ Cleanup Complete.")
            
        else:
             console.print(f"[red]❌ Duplication Failed: {dupe_res}[/red]")
             # Cleanup source
             notion.update_page(source_id, archived=True)
    else:
        console.print(f"[red]❌ Setup Failed (Could not create source): {create_res}[/red]")

    console.print("\n[bold green]✅ Deep Dive Test Complete.[/bold green]")

if __name__ == "__main__":
    main()
