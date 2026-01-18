
import os
import sys
import time
import statistics
from datetime import datetime
from rich.console import Console
from rich.table import Table
import requests
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

console = Console()
api = RobinhoodCryptoAPI()

# Ross Cameron's "Warrior" Criteria
MIN_CHANGE_PCT = 5.0  # (Lowered from 10% for crypto frequency)
MIN_REL_VOL = 3.0     # 3x Volume
MAX_PRICE = 200.0     # Crypto can be pricier, but focusing on small caps helps
PULLBACK_WINDOW = 3   # How many candles to look back for the pullback

def fetch_top_movers(limit=10):
    url = f"https://min-api.cryptocompare.com/data/top/totalvolfull?limit={limit}&tsym=USD"
    try:
        data = requests.get(url).json()['Data']
        movers = []
        for d in data:
            coin = d['CoinInfo']['Name']
            if coin in ['USDT', 'USDC', 'FDUSD']: continue
            
            # Check 24h Change
            change_24h = d['RAW']['USD']['CHANGEPCT24HOUR']
            if change_24h >= MIN_CHANGE_PCT:
                movers.append({
                    'symbol': f"{coin}-USD",
                    'change': change_24h,
                    'price': d['RAW']['USD']['PRICE'],
                    'vol_24h': d['RAW']['USD']['VOLUME24HOUR'],
                    'vol_day_to': d['RAW']['USD']['VOLUMEDAYTO']
                })
        return movers
    except Exception as e:
        console.print(f"[red]Fetch Error: {e}[/red]")
        return []

def check_first_pullback(symbol):
    """
    Detects 'First Pullback' Pattern:
    1. Strong Trend Up.
    2. Recent Candle was RED (Close < Open).
    3. Current Candle is GREEN (breaking back up) OR Inside Bar.
    """
    try:
        # Get 1-minute candles (last 10 mins)
        # Using a public API for candle data to avoid RH rate limits on discovery
        url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={symbol.split('-')[0]}&tsym=USD&limit=10"
        res = requests.get(url).json()
        candles = res['Data']['Data']
        
        if len(candles) < 5: return False, "No Data"
        
        last_c = candles[-2] # Completed candle
        curr_c = candles[-1] # Forming candle
        prev_c = candles[-3]
        
        # Check Trend (Are we comfortably above EMA/SMA? Simplified: Higher Highs)
        is_uptrend = last_c['close'] > candles[-5]['close']
        
        if not is_uptrend: return False, "No Uptrend"
        
        # Pullback Logic: Last candle was RED
        is_red = last_c['close'] < last_c['open']
        
        # Volume Spike? (Relative Vol)
        av_vol = statistics.mean([c['volumeto'] for c in candles[:-2]])
        rel_vol = last_c['volumeto'] / av_vol if av_vol > 0 else 0
        
        if is_red and rel_vol > 1.5:
             # This is a high volume pullback (absorption?)
             return True, f"Pullback Detected (RelVol {rel_vol:.1f}x)"
             
        return False, "Wait"

    except Exception as e:
        return False, f"Error: {e}"

def scan_loop():
    console.print("[bold green]🏹 Warrior Scalp Scanner Initialized...[/bold green]")
    console.print(f"Criteria: >{MIN_CHANGE_PCT}% Move, First Pullback Pattern.")
    
    while True:
        try:
            movers = fetch_top_movers()
            
            table = Table(title=f"Scanner Results ({datetime.now().strftime('%H:%M:%S')})")
            table.add_column("Asset", style="cyan")
            table.add_column("Change %", style="green")
            table.add_column("Pattern", style="bold magenta")
            table.add_column("Action", style="white")
            
            for m in movers:
                found, reason = check_first_pullback(m['symbol'])
                
                action = "-"
                style = "dim"
                if found: 
                    action = "🚨 SIGNAL 🚨"
                    style = "bold red blink"
                
                table.add_row(
                    m['symbol'], 
                    f"+{m['change']:.2f}%",
                    reason,
                    f"[{style}]{action}[/{style}]"
                )
            
            console.clear()
            console.print(table)
            
            time.sleep(15) 
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Scan Loop Error: {e}[/red]")
            time.sleep(5)

if __name__ == "__main__":
    scan_loop()
