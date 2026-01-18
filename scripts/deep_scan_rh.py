
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

console = Console()

def deep_scan():
    console.print("[bold cyan]🔍 Robinhood Deep Scan Initiated...[/bold cyan]")
    
    try:
        api = RobinhoodCryptoAPI()
        
        # 1. Account Info
        account = api.get_account()
        cash = float(account.get("buying_power", 0))
        console.print(f"💰 [bold green]Buying Power (Cash): ${cash:.2f}[/bold green]")
        
        # 2. Holdings
        holdings = api.get_holdings()
        console.print(f"📂 Found {len(holdings)} Holdings entries.")
        
        active_holdings = []
        tickers = []
        
        for h in holdings:
            qty = float(h.total_quantity)
            if qty > 0:
                active_holdings.append(h)
                tickers.append(f"{h.asset_code}-USD")
        
        # 3. Get Real-Time Prices
        prices = {}
        if tickers:
            try:
                # Fetch in chunks if needed (assuming small list for now)
                quote_data = api.get_best_bid_ask(*tickers)
                for sym, data in quote_data.items():
                    prices[sym] = float(data.get("bid_price", 0))
            except Exception as e:
                console.print(f"[red]Price Fetch Error: {e}[/red]")

        # 4. Build Report
        table = Table(title="💼 Portfolio Scan")
        table.add_column("Asset", style="cyan")
        table.add_column("Quantity", style="magenta")
        table.add_column("Price (Bid)", style="green")
        table.add_column("Value ($)", style="bold gold1")
        table.add_column("Status", style="white")

        total_crypto_val = 0.0
        dust_count = 0
        
        for h in active_holdings:
            sym = f"{h.asset_code}-USD"
            qty = float(h.total_quantity)
            price = prices.get(sym, 0.0)
            value = qty * price
            
            total_crypto_val += value
            
            status = "ACTIVE"
            if value < 1.00: 
                status = "[red]DUST (<$1)[/red]"
                dust_count += 1
            elif value < 5.00:
                status = "[yellow]SMALL (<$5)[/yellow]"
            
            table.add_row(
                h.asset_code, 
                f"{qty:.8f}",
                f"${price:.4f}",
                f"${value:.2f}",
                status
            )
            
        
        # WRITE TO FILE
        net_worth = cash + total_crypto_val
        
        with open("scan_report.md", "w", encoding="utf-8") as f:
            f.write(f"# 🔍 Robinhood Deep Scan ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
            f.write(f"## Financials\n")
            f.write(f"- **Buying Power**: `${cash:.2f}`\n")
            f.write(f"- **Crypto Value**: `${total_crypto_val:.2f}`\n")
            f.write(f"- **Net Worth**:    `${net_worth:.2f}`\n\n")
            
            f.write("## Holdings\n")
            f.write("| Asset | Qty | Price | Value | Status |\n")
            f.write("|-------|-----|-------|-------|--------|\n")
            
            for h in active_holdings:
                sym = f"{h.asset_code}-USD"
                qty = float(h.total_quantity)
                price = prices.get(sym, 0.0)
                value = qty * price
                
                status = "ACTIVE"
                if value < 1.00: status = "**DUST (<$1)**"
                elif value < 5.00: status = "SMALL (<$5)"
                
                f.write(f"| {h.asset_code} | {qty:.8f} | ${price:.4f} | ${value:.2f} | {status} |\n")
            
            f.write(f"\n**Dust Count**: {dust_count} assets unable to sell.\n")
            
        console.print("[green]Scan Complete. Saved to scan_report.md[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Scan Failed: {e}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deep_scan()
