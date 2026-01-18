import re
from collections import defaultdict
from rich.console import Console
from rich.table import Table

console = Console()

LOG_FILE = "trader_activity.log"

def parse_logs():
    stats = {
        "buys": 0,
        "sells": 0,
        "profits_detected": 0,
        "sell_errors": 0,
        "dust_removals": 0,
        "total_profit_pct_sum": 0.0,
        "recent_trades": []
    }
    
    # Track open positions from logs to estimate hold time? (Complex, skip for now)
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        console.print("[red]Log file not found.[/red]")
        return

    # Regex patterns
    buy_pat = re.compile(r"BOUGHT\s+([A-Z]+-USD)")
    sell_pat = re.compile(r"SOLD\s+([A-Z]+-USD)")
    profit_pat = re.compile(r"PROFIT:\s+([A-Z]+-USD)\s+([\d\.]+)%")
    fail_pat = re.compile(r"Sell Fail")
    dust_pat = re.compile(r"DUST DETECTED")
    
    for line in lines:
        if buy_pat.search(line):
            stats["buys"] += 1
        
        if sell_pat.search(line):
            stats["sells"] += 1
            # Try to associate with recent profit msg
            stats["recent_trades"].append({"type": "SELL", "line": line.strip()})
            
        profit_match = profit_pat.search(line)
        if profit_match:
            stats["profits_detected"] += 1
            stats["total_profit_pct_sum"] += float(profit_match.group(2))
            
        if fail_pat.search(line):
            stats["sell_errors"] += 1
            
        if dust_pat.search(line):
            stats["dust_removals"] += 1

    return stats

def display_report(stats):
    table = Table(title="🤖 Unk Trader Performance Audit")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Buys", str(stats["buys"]))
    table.add_row("Total Sells (Executed)", str(stats["sells"]))
    table.add_row("Profits Detected (Signals)", str(stats["profits_detected"]))
    table.add_row("Sell Failures (Missed)", str(stats["sell_errors"]))
    table.add_row("Dust Corrections", str(stats["dust_removals"]))
    
    if stats["profits_detected"] > 0:
        avg_profit = stats["total_profit_pct_sum"] / stats["profits_detected"]
        table.add_row("Avg Profit % (When Detected)", f"{avg_profit:.2f}%")
        
    console.print(table)
    
    console.print("\n[bold]Recent Sales:[/bold]")
    for trade in stats["recent_trades"][-10:]:
        console.print(f" - {trade['line']}")

if __name__ == "__main__":
    stats = parse_logs()
    if stats:
        display_report(stats)
