
import os
import sys
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

import skills.notion_skill as ns
from skills.notion_skill import NotionSkill

console = Console()

def main():
    console.print("[bold blue]🔍 Scanning Notion Database Schemas...[/bold blue]\n")
    
    notion = NotionSkill()
    if not notion.client:
        console.print("[red]❌ No Notion Client[/red]")
        return

    # 1. Identify Target Databases/Pages from Code
    # Inspect the module for constants starting with DB_ or PAGE_
    resource_map = {name: val for name, val in vars(ns).items() if name.startswith(("DB_", "PAGE_"))}
    
    console.print(f"Found {len(resource_map)} Constants (DBs/Pages) in Code.")
    
    # 2. Iterate and Introspect
    for name, res_id in resource_map.items():
        console.print(f"\n[bold]{name}[/bold] ({res_id})")
        
        try:
            # Try as Database first
            try:
                db = notion.client.databases.retrieve(res_id)
                object_type = "database"
            except Exception:
                # Fallback to Page
                db = notion.client.pages.retrieve(res_id)
                object_type = "page"

            # Title extraction differs by type
            real_title = "Untitled"
            if object_type == "database":
                title_obj = db.get("title", [])
                if title_obj: real_title = title_obj[0]["plain_text"]
            else:
                # Page title extraction
                props = db.get("properties", {})
                for key, val in props.items():
                    if val["id"] == "title":
                        t_list = val.get("title", [])
                        if t_list: real_title = t_list[0]["plain_text"]
            
            console.print(f"✅ [green]Connected ({object_type})[/green]: '{real_title}'")
            
            if object_type == "database":
                # Print Properties Table for DBs
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Property Name")
                table.add_column("Type")
                table.add_column("Configuration")
                
                props = db.get("properties", {})
                for prop_name, prop_data in props.items():
                    p_type = prop_data["type"]
                    # Extract extra config if any (e.g. select options)
                    config = ""
                    if p_type == "select":
                        options = [o["name"] for o in prop_data["select"]["options"]]
                        config = f"Options: {', '.join(options)}"
                    elif p_type == "status":
                         options = [o["name"] for o in prop_data["status"]["options"]]
                         config = f"Options: {', '.join(options)}"
                    elif p_type == "relation":
                        config = f"Relation DB: {prop_data['relation'].get('database_id', 'Unknown')}"
                    elif p_type == "formula":
                        config = f"Expr: {prop_data['formula'].get('expression', 'Unknown')}"
                        
                    table.add_row(prop_name, p_type, config)
                    
                console.print(table)
            else:
                # Page: List Child Databases
                console.print(f"[dim]ℹ️ Page: {db.get('url')}[/dim]")
                console.print("[dim]Scanning for Child Databases...[/dim]")
                
                # We need to list blocks (children) and check their type
                try:
                    children = notion.client.blocks.children.list(block_id=res_id)
                    child_dbs = []
                    
                    for block in children.get("results", []):
                        if block["type"] == "child_database":
                            bdb = block["child_database"]
                            child_dbs.append(f"{bdb['title']} ({block['id']})")
                    
                    if child_dbs:
                        console.print(f"   📂 Found {len(child_dbs)} Child Databases:")
                        for c in child_dbs:
                            console.print(f"      - [bold cyan]{c}[/bold cyan]")
                    else:
                        console.print("   (No direct child databases found)")
                        
                except Exception as e:
                    console.print(f"   [red]Failed to list children: {e}[/red]")
            
        except Exception as e:
            err_str = str(e)
            if "Could not find" in err_str or "404" in err_str:
                console.print("[red]❌ Not Found / No Access[/red]")
                console.print("[dim]   (Check if Integration is added to this page)[/dim]")
            else:
                 console.print(f"[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    main()
