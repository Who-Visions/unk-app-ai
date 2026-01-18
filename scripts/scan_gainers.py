
import os
import sys
import json
import requests
import time
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def scan_gainers():
    load_dotenv()
    console = Console()
    
    console.print("[bold blue]🚀 Scanning Robinhood Crypto Universe...[/]")
    
    try:
        # 1. Get All Assets
        api = RobinhoodCryptoAPI()
        # Init account to be safe
        try:
             api.get_account() 
        except: 
             pass
             
        pairs = api.get_trading_pairs()
        if not pairs:
            # Fallback List if API fails
            symbols = [
                'BTC', 'ETH', 'DOGE', 'LTC', 'SHIB', 'AAVE', 'AERO', 'ARB', 'ASTER', 'AVAX',
                'AVNT', 'BCH', 'BNB', 'BONK', 'ADA', 'MEW', 'LINK', 'COMP', 'CRV', 'WIF',
                'ENA', 'ETC', 'FLOKI', 'HBAR', 'HYPE', 'LDO', 'SYRUP', 'MOODENG', 'TRUMP',
                'ONDO', 'XCN', 'OP', 'PNUT', 'PEPE', 'XPL', 'DOT', 'POPCAT', 'PENGU', 'SEI',
                'SOL', 'SUI', 'XLM', 'XTZ', 'TON', 'UNI', 'USDC', 'VIRTUAL', 'WLFI', 'XRP', 'ZORA'
            ]
            console.print("[yellow]⚠️  Could not fetch pairs from API. Using fallback list.[/]")
        else:
            symbols = [p['symbol'].split('-')[0] for p in pairs]
            console.print(f"✅ Found {len(symbols)} assets on Robinhood.")

        # 2. Fetch Market Data (CryptoCompare)
        # Batching 30 at a time to be safe / not hit URL limits
        console.print("[dim]Fetching 24h Momentum data...[/]")
        
        results = []
        batch_size = 50
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            syms_str = ",".join(batch)
            url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={syms_str}&tsyms=USD"
            
            try:
                res = requests.get(url, timeout=10)
                data = res.json()
                
                if "RAW" in data:
                    for sym in batch:
                        if sym in data["RAW"]:
                            try:
                                usd = data["RAW"][sym]["USD"]
                                chg_pct = usd["CHANGEPCT24HOUR"]
                                price = usd["PRICE"]
                                vol = usd["VOLUME24HOURTO"]
                                results.append({
                                    "symbol": sym,
                                    "change": float(chg_pct),
                                    "price": float(price),
                                    "vol": float(vol),
                                    "rsi": 50.0, # Default
                                    "status": "WAIT"
                                })
                            except:
                                pass
            except Exception as e:
                console.print(f"[red]Batch Error:[/ {e}")
            
            time.sleep(0.5) 

        # 3. Sort by Gain & Analyze Top 20 Candidates
        results.sort(key=lambda x: x['change'], reverse=True)
        top_candidates = results[:20]
        
        console.print(f"[dim]Analyzing technicals for top {len(top_candidates)} movers...[/]")
        
        smart_picks = []
        
        for r in top_candidates:
            # RSI Check (fetch hourly candles)
            try:
                hist_url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={r['symbol']}&tsym=USD&limit=24"
                h_res = requests.get(hist_url, timeout=5).json()
                if h_res['Response'] == 'Success':
                     closes = [c['close'] for c in h_res['Data']['Data']]
                     
                     # Calculate RSI-14
                     period = 14
                     if len(closes) > period:
                         deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                         gains = [x for x in deltas if x > 0]
                         losses = [abs(x) for x in deltas if x < 0]
                         
                         avg_gain = sum(gains[-period:]) / period if gains else 0
                         avg_loss = sum(losses[-period:]) / period if losses else 0
                         
                         if avg_loss == 0:
                             rsi = 100.0
                         else:
                             rs = avg_gain / avg_loss
                             rsi = 100 - (100 / (1 + rs))
                             
                         r['rsi'] = rsi
                         
                         # Determine Status
                         if rsi > 70:
                             r['status'] = "OVERBOUGHT"
                             r['style'] = "red"
                         elif rsi < 30:
                             r['status'] = "OVERSOLD"
                             r['style'] = "green"
                         elif 45 <= rsi <= 65 and r['change'] > 2.0:
                             r['status'] = "SMART BUY"
                             r['style'] = "bold green"
                             smart_picks.append(r)
                         else:
                             r['status'] = "NEUTRAL"
                             r['style'] = "yellow"
            except:
                pass
            time.sleep(0.2) # Rate limit

        # Display Table
        table = Table(title="🧠 SMART SCANNER (ROI + RSI)", show_header=True)
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Asset", style="bold")
        table.add_column("Change", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("RSI (1h)", justify="right")
        table.add_column("Verdict", justify="center")
        
        for idx, r in enumerate(top_candidates):
            color = "green" if r['change'] > 0 else "red"
            rsi_val = r['rsi']
            rsi_color = "red" if rsi_val > 70 else ("green" if rsi_val < 30 else "yellow")
            
            table.add_row(
                str(idx+1),
                r['symbol'],
                f"[{color}]{r['change']:+.2f}%[/]",
                f"${r['price']:,.4f}",
                f"[{rsi_color}]{rsi_val:.1f}[/]",
                f"[{r.get('style', 'dim')}]{r.get('status', 'WAIT')}[/]"
            )
            
        console.print(table)
        
        if smart_picks:
            best = smart_picks[0]
            console.print(f"\n[bold green]🌟 TOP SMART PICK: {best['symbol']} (Change: {best['change']:+.2f}%, RSI: {best['rsi']:.1f})[/]")
            console.print("[dim]This entry shows strong momentum without being overextended.[/]")
        else:
            console.print("\n[yellow]No 'Smart Buys' found in top gainers. Market might be overheated. Patience is key.[/]")
        
    except Exception as e:
        console.print_exception()

if __name__ == "__main__":
    scan_gainers()
