"""
Active Scalp Manager (Sniper)
=============================
Dedicated process to monitor a single asset for specific Stop Loss and Take Profit levels.
Executes Market Orders immediately when levels are breached.

Usage:
    python scripts/active_scalp.py ETC --stop 12.62 --tp1 13.16 --tp2 13.34
"""
import sys
import os
import time
import argparse
import signal
from decimal import Decimal, ROUND_DOWN
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local Imports
try:
    from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
except ImportError:
    # Fallback for direct script run
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

load_dotenv()

# Setup Console
console = Console()

class ScalpSniper:
    def __init__(self, symbol, stop_loss, tp1, tp2, dry_run=False):
        self.symbol = f"{symbol.upper()}-USD" if "-USD" not in symbol.upper() else symbol.upper()
        self.stop_loss = float(stop_loss)
        self.tp1 = float(tp1)
        self.tp2 = float(tp2)
        self.dry_run = dry_run
        
        self.tp1_hit = False
        self.running = True
        
        # API Init
        api_key = os.getenv('ROBINHOOD_API_KEY')
        private_key = os.getenv('ROBINHOOD_PRIVATE_KEY')
        
        if not api_key or not private_key:
            raise ValueError("Missing Credentials in .env")
            
        self.api = RobinhoodCryptoAPI(api_key=api_key, private_key_base64=private_key)
        self.account = self.api.get_account()
        
        # State
        self.current_price = 0.0
        self.position_qty = 0.0
        self.start_qty = 0.0
        self.msg_log = []

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.msg_log.append(f"[{ts}] {msg}")
        if len(self.msg_log) > 10:
            self.msg_log.pop(0)

    def fetch_data(self):
        """Fetches Price and Holdings."""
        try:
            # 1. Price
            quotes = self.api.get_best_bid_ask(self.symbol)
            if quotes and self.symbol in quotes:
                # Use BID price for selling checks (pessimistic)
                self.current_price = float(quotes[self.symbol].get('bid_price', 0))
            
            # 2. Holdings (only if we don't have a local track or periodic check)
            # Fetch every loop? Maybe too heavy. Let's trust local state after init.
            if self.start_qty == 0:
                holdings = self.api.get_holdings()
                for h in holdings:
                    if f"{h.asset_code}-USD" == self.symbol:
                         self.start_qty = float(h.total_quantity)
                         self.position_qty = self.start_qty
                         self.log(f"Position Located: {self.start_qty} {self.symbol}")
                         break
                         
        except Exception as e:
            self.log(f"Data Fetch Error: {e}")

    def execute_sell(self, pct_to_sell, reason):
        """Executes Market Sell."""
        if self.position_qty <= 0:
            self.log("No position to sell!")
            return

        qty_to_sell = self.position_qty * pct_to_sell
        
        # Format Qty (Precision handling)
        # ETC has precision issues? Let's use 6 decimals safe
        qty_str = f"{qty_to_sell:.6f}"
        qty_float = float(qty_str)

        msg = f"EXECUTING {reason}: Sell {qty_to_sell:.4f} ({pct_to_sell*100}%) @ ${self.current_price:.2f}"
        self.log(f"[bold red]{msg}[/]")
        
        if self.dry_run:
            self.log("[yellow]DRY RUN: Order simulated.[/]")
            self.position_qty -= qty_float
            return

        try:
            order = self.api.place_market_order(self.symbol, "sell", asset_quantity=qty_float)
            if order:
                self.log(f"[green]ORDER FILLED: {order.get('id', 'Unknown')}[/]")
                self.position_qty -= qty_float
            else:
                self.log(f"[red]Order Failed: API Return None[/]")
                
        except Exception as e:
            self.log(f"[red]Order Exception: {e}[/]")

    def check_triggers(self):
        """Core Logic Check."""
        if self.current_price <= 0:
            return

        p = self.current_price
        
        # 1. STOP LOSS
        if p <= self.stop_loss:
            self.execute_sell(1.0, f"STOP LOSS FAILSAFE (${self.stop_loss})")
            self.running = False # Exit after stop out
            
        # 2. TP1 (50%)
        elif p >= self.tp1 and not self.tp1_hit:
            self.execute_sell(0.5, f"TAKE PROFIT 1 (${self.tp1})")
            self.tp1_hit = True
            
        # 3. TP2 (100% Remainder)
        elif p >= self.tp2:
            self.execute_sell(1.0, f"TAKE PROFIT 2 (${self.tp2})")
            self.running = False # Mission Complete

    def render_ui(self):
        """Renders simple dashboard."""
        
        # Color Logic
        p_color = "white"
        if self.current_price <= self.stop_loss * 1.01: p_color = "red"
        elif self.current_price >= self.tp1 * 0.99: p_color = "green"
        
        # Status Table
        table = Table(show_header=False, box=None)
        table.add_row("Symbol", f"[bold cyan]{self.symbol}[/]")
        table.add_row("Current Price", f"[{p_color}]${self.current_price:.4f}[/]")
        table.add_row("Position", f"{self.position_qty:.4f}")
        table.add_row("", "")
        
        # Distances
        # Distances
        if self.current_price > 0:
            sl_diff = ((self.current_price - self.stop_loss) / self.current_price) * 100
            tp1_diff = ((self.tp1 - self.current_price) / self.current_price) * 100
            
            table.add_row("Distance to STOP", f"[red]{sl_diff:+.2f}%[/] (${self.stop_loss})")
            table.add_row("Distance to TP1",  f"[green]{tp1_diff:+.2f}%[/] (${self.tp1})")
        else:
             table.add_row("Distance to STOP", f"[dim]Waiting for data...[/]")
             table.add_row("Distance to TP1",  f"[dim]Waiting for data...[/]")

        table.add_row("Distance to TP2",  f"[bold green]${self.tp2}[/]")

        # Logs
        log_txt = "\n".join(self.msg_log)
        
        panel = Panel(
            table,
            title=f"🎯 SCALP SNIPER ({'DRY RUN' if self.dry_run else 'LIVE'})",
            border_style="red" if self.dry_run else "green"
        )
        
        layout = Layout()
        layout.split_column(
            Layout(panel, ratio=6),
            Layout(Panel(Text.from_markup(log_txt), title="Logs"), ratio=4)
        )
        return layout

    def run(self):
        try:
            self.log(f"Sniper Armed: {self.symbol}")
            self.log(f"SL: {self.stop_loss} | TP1: {self.tp1} | TP2: {self.tp2}")
            
            with Live(self.render_ui(), refresh_per_second=4) as live:
                while self.running:
                    self.fetch_data()
                    self.check_triggers()
                    
                    live.update(self.render_ui())
                    time.sleep(1) # 1Hz Scan
                    
                self.log("Sniper Mission Ended.")
                live.update(self.render_ui())
                # Keep open for a few seconds to see result
                time.sleep(5)
                
        except KeyboardInterrupt:
            console.print("[yellow]Sniper Disarmed by User.[/]")
        except Exception as e:
            console.print_exception()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Active Scalp Manager')
    parser.add_argument('symbol', help='Asset Symbol (e.g. ETC)')
    parser.add_argument('--stop', required=True, type=float, help='Stop Loss Price')
    parser.add_argument('--tp1', required=True, type=float, help='Take Profit 1 Price')
    parser.add_argument('--tp2', required=True, type=float, help='Take Profit 2 Price')
    parser.add_argument('--dry-run', action='store_true', help='Simulate orders')
    
    args = parser.parse_args()
    
    bot = ScalpSniper(args.symbol, args.stop, args.tp1, args.tp2, args.dry_run)
    bot.run()
