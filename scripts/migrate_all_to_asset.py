
import os
import sys
import argparse
import time
from rich.console import Console
from rich.prompt import Confirm
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def migrate_all(target_symbol):
    load_dotenv()
    console = Console()
    target_symbol = target_symbol.upper().split('-')[0] + "-USD" # Ensure ARB-USD format
    
    console.print(f"[bold red]🚨 MIGRATION ALERT: SELLING ALL ASSETS TO BUY {target_symbol}[/]")
    
    try:
        api = RobinhoodCryptoAPI()
        try: api.get_account() 
        except: pass

        # 1. Fetch Current Holdings
        console.print("[dim]Fetching holdings...[/]")
        holdings = api.get_holdings()
        
        to_sell = []
        for h in holdings:
            sym = f"{h.asset_code}-USD"
            qty = float(h.total_quantity)
            if qty > 0 and sym != target_symbol:
                to_sell.append((sym, qty))
        
        if not to_sell:
            console.print("[yellow]No other assets to liquidate.[/]")
        else:
            console.print(f"Found {len(to_sell)} assets to liquidate: {[s[0] for s in to_sell]}")
            
            # CONFIRMATION
            if not args.yes:
                if not Confirm.ask(f"[bold red]Are you sure you want to LIQUIDATE EVERYTHING and go 100% into {target_symbol}?[/]"):
                    console.print("[green]Migration Cancelled.[/]")
                    return

            # 2. Liquidate
            console.print("[bold yellow]Selling Assets...[/]")
            for sym, qty in to_sell:
                try:
                    console.print(f"Selling {qty} {sym}...", end=" ")
                    # Sell 99.9% to avoid dust errors if needed, but 100% usually fine on market
                    api.place_market_order(sym, "sell", asset_quantity=qty)
                    console.print("[green]OK[/]")
                    time.sleep(1.0) # Rate limit
                except Exception as e:
                    console.print(f"[red]Failed: {e}[/]")

            console.print("[dim]Waiting 5s for funds to settle...[/]")
            time.sleep(5)

        # 3. Buy Target
        acc = api.get_account()
        cash = float(acc.get('buying_power', 0.0))
        
        console.print(f"[bold green]Available Cash: ${cash:.2f}[/]")
        
        if cash < 1.00:
            console.print("[red]Insufficient funds to buy target.[/]")
            return
            
        if cash < 1.00:
            console.print("[red]Insufficient funds to buy target.[/]")
            return
            
        # Buy buffer (98% to be safe from slippage)
        buy_amt = cash * 0.98
        
        # FIX: API requires asset_quantity for market buys? 
        # Calculate qty from current price
        prices = api.get_best_bid_ask(target_symbol)
        if target_symbol in prices:
            ask = prices[target_symbol]['ask_price']
            qty_est = buy_amt / ask
            # precision: 6 decimals safe for most
            qty_str = f"{qty_est:.6f}"
            
            console.print(f"[bold cyan]Buying {qty_str} {target_symbol} (~${buy_amt:.2f})...[/]")
            try:
                 order = api.place_market_order(target_symbol, "buy", asset_quantity=float(qty_str))
                 if order:
                     console.print(f"[bold green]✅ SUCCESS! Order ID: {order.order_id}[/]")
                     console.print(f"Price: ${order.average_price} | Qty: {order.filled_quantity}")
                 else:
                     console.print("[red]Buy Order Returned None.[/]")
            except Exception as e:
                console.print(f"[red]Buy Failed: {e}[/]")
        else:
            console.print("[red]Could not fetch price to calculate quantity.[/]")

    except Exception as e:
        console.print_exception()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Target Asset (e.g. ARB)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation")
    args = parser.parse_args()
    migrate_all(args.symbol)
