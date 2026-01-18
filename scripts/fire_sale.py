
import os
import sys
import time
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

console = Console()

def fire_sale():
    console.print("[bold red]🔥 FIRE SALE INITIATED...[/bold red]")
    console.print("Targeting 'Small Bags' ($1.00 - $10.00) to unlock liquidity.")
    
    try:
        api = RobinhoodCryptoAPI()
        holdings = api.get_holdings()
        
        # Get Prices
        tickers = [f"{h.asset_code}-USD" for h in holdings if float(h.total_quantity) > 0]
        if not tickers:
            console.print("No holdings found.")
            return

        prices_map = api.get_best_bid_ask(*tickers)
        
        unlocked_cash = 0.0
        
        for h in holdings:
            qty = float(h.total_quantity)
            if qty <= 0: continue
            
            sym = f"{h.asset_code}-USD"
            price = float(prices_map.get(sym, {}).get("bid_price", 0))
            value = qty * price
            
            # CRITERIA: > $1.00 (To avoid Dust Error) AND < $10.00 (Small Bags)
            if 1.00 < value < 10.00:
                console.print(f"Selling {sym} (Val: ${value:.2f})...")
                
                # EXECUTE SELL
                order = api.place_market_order(sym, "sell", asset_quantity=qty)
                
                if order:
                    console.print(f"✅ SOLD {sym} for approx ${value:.2f}")
                    unlocked_cash += value
                    time.sleep(1) # Rate limit safety
                else:
                    console.print(f"❌ FAILED to sell {sym}: {api.last_error}")
            else:
                if value <= 1.00:
                    console.print(f"Skipping {sym} (Dust <$1: ${value:.2f})")
                else:
                    console.print(f"Skipping {sym} (Keeper >$10: ${value:.2f})")
                    
        console.print(f"\n[bold green]💰 Total Cash Unlocked: ~${unlocked_cash:.2f}[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Fire Sale Error: {e}[/bold red]")

if __name__ == "__main__":
    confirm = input("⚠️ Type 'BURN' to confirm FIRE SALE of all assets between $1-$10: ")
    if confirm == "BURN":
        fire_sale()
    else:
        console.print("Aborted.")
