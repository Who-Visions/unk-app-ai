
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

console = Console()

def audit_recent_activity():
    console.print("[bold cyan]🕵️ Auditing Recent Robinhood Orders...[/bold cyan]")
    
    try:
        api = RobinhoodCryptoAPI()
        orders = api.get_orders() # Gets recent orders
        
        # Sort by updated_at (newest first)
        orders.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        
        table = Table(title=f"📜 Transaction Log (Last 20)")
        table.add_column("Time", style="dim")
        table.add_column("Action", style="bold")
        table.add_column("Asset", style="cyan")
        table.add_column("Qty", style="magenta")
        table.add_column("Price", style="green")
        table.add_column("Value", style="gold1")
        table.add_column("State", style="white")

        count = 0
        total_liq = 0.0
        
        for o in orders[:20]:
            # Parse Time
            ts_str = o.updated_at or o.created_at
            # RH dates look like: 2024-01-16T15:55:00.123456Z
            try:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                local_ts = dt.astimezone().strftime('%H:%M:%S')
            except:
                local_ts = ts_str

            # Value Calc
            val = 0.0
            if o.average_price and o.filled_quantity:
                val = o.average_price * o.filled_quantity
                if o.side == "sell" and o.state == "filled":
                    total_liq += val

            # Colorize Side
            side_str = o.side.upper()
            if side_str == "BUY": side_str = "[green]BUY[/green]"
            elif side_str == "SELL": side_str = "[red]SELL[/red]"
            
            table.add_row(
                local_ts,
                side_str,
                o.symbol,
                f"{o.filled_quantity:.6f}",
                f"${o.average_price:.4f}" if o.average_price else "-",
                f"${val:.2f}",
                o.state
            )
            count += 1

        console.print(table)
        console.print(f"\n[bold green]💵 Total Liquidity Unlocked (Sells): ${total_liq:.2f}[/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error fetching orders: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    audit_recent_activity()
