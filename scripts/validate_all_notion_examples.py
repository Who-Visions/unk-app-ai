
import os
import sys
import asyncio
from rich.console import Console
from rich.table import Table

# Add root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Example Functions
# Note: We import them safely. If an import fails, the test fails.
try:
    from skills.notion_examples.basic import (
        _1_create_blocks as basic_1,
        _2_linked_blocks as basic_2,
        _3_parse_text as basic_3
    )
    from skills.notion_examples.intermediate import (
        _1_query_db as inter_1,
        _2_web_form_handler as inter_2
    )
    from skills.notion_examples.advanced import (
        _1_spotify_sync as adv_1,
        _2_github_sync as adv_2
    )
except ImportError as e:
    # Handle the fact that file names start with numbers (1_create...), so standard import might fail 
    # if we didn't rename them or use importlib. 
    # Python modules shouldn't start with numbers ideally.
    # I will use importlib to handle the numeric prefixes.
    pass

import importlib

console = Console()

def run_module_example(module_path, func_name):
    """Runs a specific example function dynamically."""
    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, func_name)
        
        # Capture stdout to avoid clutter? Or just print section headers.
        console.print(f"[bold yellow]▶ Running {module_path}...[/bold yellow]")
        try:
            func() # All examples currently take no args
            return True, "Completed without Exception"
        except Exception as e:
            return False, f"Runtime Error: {e}"
            
    except ImportError as e:
        return False, f"Import Error: {e}"
    except AttributeError:
        return False, f"Function {func_name} not found in {module_path}"

def main():
    console.print("[bold blue]🧪 Deep Validation: Notion Logic & Examples[/bold blue]\n")
    
    results = []
    
    # List of (Module Path, Function Name)
    tests = [
        ("skills.notion_examples.basic.1_create_blocks", "example_create_blocks"),
        ("skills.notion_examples.basic.2_linked_blocks", "example_linked_blocks"),
        ("skills.notion_examples.basic.3_parse_text", "example_parse_text"),
        ("skills.notion_examples.intermediate.1_query_db", "example_query_db"),
        ("skills.notion_examples.intermediate.2_web_form_handler", "example_web_form_handler"),
        ("skills.notion_examples.advanced.1_spotify_sync", "example_spotify_sync"),
        ("skills.notion_examples.advanced.2_github_sync", "example_github_sync"),
    ]
    
    for mod, func in tests:
        success, msg = run_module_example(mod, func)
        results.append({
            "Example": mod.split('.')[-1],
            "Status": "✅ PASS" if success else "❌ FAIL",
            "Details": msg
        })
        console.print(f"Result: {results[-1]['Status']}\n")

    # Summary Table
    table = Table(title="Validation Results")
    table.add_column("Example", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")
    
    for r in results:
        style = "green" if "PASS" in r["Status"] else "red"
        table.add_row(r["Example"], f"[{style}]{r['Status']}[/{style}]", r["Details"])
        
    console.print(table)

if __name__ == "__main__":
    main()
