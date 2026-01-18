
import os
import sys
import time
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

console = Console()

# Dynamic Watch List
def get_watchlist_table(api, prices):
    table = Table(title=f"🚑 Recovery Ward ({datetime.now().strftime('%H:%M:%S')})")
    table.add_column("Patient", style="cyan")
    table.add_column("Qty", style="magenta")
    table.add_column("Current Price", style="green")
    table.add_column("Value ($)", style="bold gold1")
    table.add_column("Status", style="white")
    
    total_val = 0.0
    
    # 1. Get All Holdings
    holdings = api.get_holdings()
    active_holdings = [h for h in holdings if float(h.total_quantity) > 0]
    
    # 2. Sort by Value (High to Low)
    active_holdings.sort(key=lambda h: float(h.total_quantity) * prices.get(f"{h.asset_code}-USD", 0), reverse=True)
    
    # Load Trading State for Entry Prices
    try:
        with open("trading_state.json", "r") as f:
            state = json.load(f)
            positions = state.get("positions", {})
    except:
        positions = {}

    for h in active_holdings:
        sym = f"{h.asset_code}-USD"
        qty = float(h.total_quantity)
        price = prices.get(sym, 0.0)
        val = qty * price
        total_val += val
        
        # P&L Calc
        pnl_str = "-"
        pnl_style = "white"
        
        if sym in positions:
            entry = float(positions[sym]['entry'])
            if entry > 0:
                pnl_usd = (price - entry) * qty
                pnl_pct = (price - entry) / entry * 100
                
                if pnl_pct > 0: 
                    pnl_str = f"+{pnl_pct:.2f}% (${pnl_usd:.2f})"
                    pnl_style = "bold green"
                else: 
                    pnl_str = f"{pnl_pct:.2f}% (${pnl_usd:.2f})"
                    pnl_style = "red"
        
        status = "Hold"
        if val < 1.0: status = "[dim]Dust[/dim]"
        elif val > 5.0: status = "[green]Active[/green]"
        
        table.add_row(sym, f"{qty:.4f}", f"${price:.4f}", f"${val:.2f}", f"[{pnl_style}]{pnl_str}[/{pnl_style}]", status)
        
    return table, total_val

def watch_loop():
    api = RobinhoodCryptoAPI()
    console.print("[bold yellow]👀 Starting Dynamic Recovery Watch... (Ctrl+C to stop)[/bold yellow]")
    
    with Live(refresh_per_second=1) as live:
        while True:
            try:
                # Need to refresh holdings periodically? No, assuming fixed for now or refresh loop
                # Better to move get_holdings inside loop or simplistic approach:
                # Just fetch all prices for known tickers? 
                # Let's just fetch holdings inside the table gen (slow but accurate)
                
                # Fetch Holdings First to know what to get prices for
                holdings = api.get_holdings()
                tickers = [f"{h.asset_code}-USD" for h in holdings if float(h.total_quantity) > 0]
                
                if not tickers: 
                     time.sleep(5)
                     continue

                data = api.get_best_bid_ask(*tickers)
                prices = {s: float(d.get("bid_price", 0)) for s, d in data.items()}
                
                # Re-use the table logic (tweaked to match new sig)
                table = Table(title=f"🚑 Active Positions Monitor ({datetime.now().strftime('%H:%M:%S')})")
                table.add_column("Asset", style="cyan")
                table.add_column("Qty", style="magenta")
                table.add_column("Price", style="green")
                table.add_column("Value ($)", style="bold gold1")
                table.add_column("P&L", style="bold")
                table.add_column("State", style="white")
                
                total_val = 0.0
                
                for h in holdings:
                    qt = float(h.total_quantity)
                    if qt <= 0: continue
                    
                    s = f"{h.asset_code}-USD"
                    p = prices.get(s, 0.0)
                    v = qt * p
                    total_val += v
                    
                    st = "Hold"
                    if v < 1.0: st = "[dim]Dust[/dim]"
                    elif v > 5.0: st = "[green]Active[/green]"
                    
                    table.add_row(s, f"{qt:.4f}", f"${p:.4f}", f"${v:.2f}", st)

                # Fetch Cash
                acct = api.get_account()
                cash = float(acct.get("buying_power", 0))
                
                # Summary Panel
                summary = f"""
                [bold]Total Assets[/bold]:    [gold1]${total_val:.2f}[/gold1]
                [bold]Cash on Hand[/bold]:    [green]${cash:.2f}[/green]
                ---------------------------
                [bold]Net Worth[/bold]:       ${total_val + cash:.2f}
                """
                
                layout = Layout()
                layout.split_column(
                    Layout(Panel(summary, title="📊 Live Portfolio")),
                    Layout(table)
                )
                
                live.update(layout)
                time.sleep(10) # 10s refresh
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                time.sleep(5)

if __name__ == "__main__":
    watch_loop()
