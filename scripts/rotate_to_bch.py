"""
MANUAL TRADE SCRIPT: Rotate DOGE + SHIB -> BCH
Approved by User: 2026-01-16 11:59 AM
"""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
from rich.console import Console

console = Console()

def rotate():
    api = RobinhoodCryptoAPI()
    
    console.print("[bold yellow]🔄 ROTATION: DOGE + SHIB -> BCH[/bold yellow]")
    
    # 1. Get Current Holdings
    holdings = api.get_holdings("DOGE", "SHIB")
    
    doge_qty = 0
    shib_qty = 0
    
    for h in holdings:
        if h.asset_code == "DOGE":
            doge_qty = float(h.total_quantity)
        elif h.asset_code == "SHIB":
            shib_qty = float(h.total_quantity)
    
    console.print(f"DOGE Qty: {doge_qty}")
    console.print(f"SHIB Qty: {shib_qty}")
    
    total_cash = 0.0
    
    # 2. SELL DOGE
    if doge_qty > 0:
        console.print(f"[red]SELLING DOGE: {doge_qty}[/red]")
        order = api.place_market_order("DOGE-USD", "sell", asset_quantity=doge_qty)
        if order:
            console.print(f"✅ SOLD DOGE")
            # Estimate cash
            prices = api.get_best_bid_ask("DOGE-USD")
            doge_price = float(prices["DOGE-USD"]["bid_price"])
            total_cash += doge_qty * doge_price
        else:
            console.print(f"[red]❌ DOGE SELL FAILED[/red]")
        time.sleep(1)
    
    # 3. SELL SHIB
    if shib_qty > 0:
        console.print(f"[red]SELLING SHIB: {shib_qty}[/red]")
        order = api.place_market_order("SHIB-USD", "sell", asset_quantity=shib_qty)
        if order:
            console.print(f"✅ SOLD SHIB")
            prices = api.get_best_bid_ask("SHIB-USD")
            shib_price = float(prices["SHIB-USD"]["bid_price"])
            total_cash += shib_qty * shib_price
        else:
            console.print(f"[red]❌ SHIB SELL FAILED[/red]")
        time.sleep(1)
    
    console.print(f"\n[bold green]💵 Estimated Cash from Sales: ${total_cash:.2f}[/bold green]")
    
    # 4. Wait for settlement
    console.print("[dim]Waiting 2s for settlement...[/dim]")
    time.sleep(2)
    
    # 5. BUY BCH with proceeds
    if total_cash > 0.50:
        console.print(f"[green]BUYING BCH with ${total_cash:.2f}[/green]")
        order = api.place_market_order("BCH-USD", "buy", quote_amount=total_cash * 0.98) # 2% buffer for fees
        if order:
            console.print(f"✅ BOUGHT BCH")
        else:
            console.print(f"[red]❌ BCH BUY FAILED[/red]")
    else:
        console.print("[yellow]⚠️ Not enough cash to buy BCH[/yellow]")
    
    console.print("\n[bold cyan]🔄 ROTATION COMPLETE[/bold cyan]")

if __name__ == "__main__":
    rotate()
