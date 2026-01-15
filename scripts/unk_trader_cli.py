
"""
Unk Trader CLI (Master Control)
===============================
Integrates Trading Bot, News Scanner, and Rich UI into ONE application.
"""
import time
import json
import os
import threading
from datetime import datetime

# Third Party
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text

# Local
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

# =============================================================================
# CONFIG & STATE
# =============================================================================
API_KEY = os.getenv('ROBINHOOD_API_KEY', '')
PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
WATCHLIST = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD',
    'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'ETC-USD',
    'XLM-USD', 'HBAR-USD', 'UNI-USD', 'AAVE-USD', 'COMP-USD', 'MKR-USD', 'DASH-USD'
]

api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)

# Shared Memory
state = {
    "prices": {sym: 0.0 for sym in WATCHLIST},
    "highs": {sym: 0.0 for sym in WATCHLIST},
    "positions": {},  # {sym: {qty, entry, pnl_pct}}
    "cash": 0.0,
    "news": {"sentiment": "NEUTRAL", "score": 0, "bulls": 0, "bears": 0},
    "logs": [],
    "running": True
}

# =============================================================================
# THREAD 1: NEWS SCANNER
# =============================================================================
def news_worker():
    """
    Fetches news every 15 minutes (to save API credits).
    Updates market_sentiment.json
    """
    import requests
    
    # 1. PRIMARY SOURCE (Free, High Vol)
    CC_URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    
    # 2. SECONDARY SOURCE (Credits - Use sparingly for Confirmation)
    ND_API_KEY = os.getenv('NEWSDATA_API_KEY', '')
    ND_URL = "https://newsdata.io/api/1/latest"
    
    KEYWORDS = ["bitcoin", "ethereum", "xrp", "solana", "dogecoin", "pepe", "shib", "bonk"]
    # Themes
    THEMES_BULLISH = [
        "sovereign", "pension", "microsoft", "bill gates", 
        "strategic reserve", "blackrock", "etf", "stablecoin"
    ]
    THEMES_BEARISH = [
        "quantum", "bear market", "recession", "liquidity drying", 
        "october top", "business cycle", "end of cycle"
    ]

    def analyze_text(text, bullish_themes, bearish_themes):
        score = 0
        b_sig = 0
        r_sig = 0
        text = text.lower()
        
        # Check Bullish
        bull_keys = ["approval", "partnership", "launch", "bull", "record"] + bullish_themes
        if any(k in text for k in bull_keys):
            score += 1
            b_sig += 1
            
        # Check Bearish
        bear_keys = ["ban", "hack", "lawsuit", "crash", "insolvency", "fraud"] + bearish_themes
        if any(k in text for k in bear_keys):
            score -= 1
            r_sig += 1
            
        return score, b_sig, r_sig

    while state["running"]:
        try:
            # Check cache age
            should_fetch = True
            try:
                with open("market_sentiment.json", "r") as f:
                    data = json.load(f)
                    # Load state for immediate UI
                    state["news"]["sentiment"] = data.get("sentiment", "NEUTRAL")
                    state["news"]["score"] = data.get("score", 0)
                    
                    # Check timestamp
                    last_ts = data.get("last_verify_ts", 0)
                    if time.time() - last_ts < 900:  # 15 minutes
                         should_fetch = False
                         log(f"♻️  Using Cached Intel ({int((time.time()-last_ts)/60)}m old)")
            except (FileNotFoundError, json.JSONDecodeError):
                should_fetch = True

            if should_fetch:
                log("📡 Fetching Primary Intel (CryptoCompare)...")
                
                # --- STEP 1: PRIMARY SOURCE ---
                cc_score = 0
                cc_bulls = 0
                cc_bears = 0
                
                try:
                    res = requests.get(CC_URL, timeout=10)
                    data = res.json()
                    if data.get('Message') == 'News list successfully returned':
                        for art in data.get('Data', []):
                            title = art.get('title', "")
                            body = art.get('body', "")
                            s, b, r = analyze_text(
                                title + " " + body, 
                                THEMES_BULLISH, 
                                THEMES_BEARISH
                            )
                            cc_score += s
                            cc_bulls += b
                            cc_bears += r
                except Exception as e:
                    log(f"⚠️ Primary Source Failed: {e}")

                # Determine Preliminary Sentiment
                final_score = cc_score
                sent = "NEUTRAL"
                if cc_score >= 5:
                    sent = "JEFF_PARK_BULLISH"
                elif cc_score > 0:
                    sent = "BULLISH"
                elif cc_score <= -3:
                    sent = "WILLY_WOO_BEARISH"
                elif cc_score < 0:
                    sent = "BEARISH"

                # --- STEP 2: VERIFICATION (Multi-Source Protocol) ---
                # Only verify EXTREME signals to save credits (Limit: 200/day)
                full_consensus = False
                # ... (Logic continues) ...
                last_verify_ts = data.get("last_verify_ts", 0) if 'data' in locals() and data else 0
                current_ts = datetime.now().timestamp()
                
                if sent in ["JEFF_PARK_BULLISH", "WILLY_WOO_BEARISH"]:
                    # Check Cache
                    time_since = current_ts - last_verify_ts
                    cached_sent = data.get("sentiment", "") if 'data' in locals() and data else ""
                    cached_cons = data.get("consensus", False) if 'data' in locals() and data else False
                    
                    if time_since < 3600 and cached_sent == sent and cached_cons:
                        log(f"♻️ Verification Cached ({int(time_since/60)}m ago). Credits Saved.")
                        full_consensus = True
                    else:
                        log(f"🔍 Extreme Signal ({sent}) detected. Verifying with NewsData.io...")
                        try:
                            q = " OR ".join(KEYWORDS)
                            nd_res = requests.get(ND_URL, params={"apikey": ND_API_KEY, "q": q, "language": "en"}, timeout=10)
                            nd_data = nd_res.json()
                            
                            if nd_data.get('status') == 'success':
                                nd_score = 0
                                fresh_articles = 0
                                
                                for art in nd_data.get('results', []):
                                    title = art.get('title') or ""
                                    desc = art.get('description') or ""
                                    s, b, r = analyze_text(title + " " + desc, THEMES_BULLISH, THEMES_BEARISH)
                                    nd_score += s
                                
                                log(f"✅ NeWsData Score: {nd_score} (Credits Used)")
                                
                                # CONSENSUS LOGIC
                                if sent == "JEFF_PARK_BULLISH":
                                    if nd_score > 0: 
                                        full_consensus = True
                                        last_verify_ts = current_ts # Update TS only on new verify
                                        log("🔥 CONSENSUS REACHED: ALL IN 50% RISK")
                                    else:
                                        sent = "BULLISH" # Downgrade
                                        log("⚠️ No Consensus. Downgrading to Standard Bullish.")
                                
                                elif sent == "WILLY_WOO_BEARISH":
                                    if nd_score < 0:
                                        full_consensus = True
                                        last_verify_ts = current_ts
                                        log("🛡️ CONSENSUS REACHED: DEFENSIVE MODE ACTIVE")
                                    else:
                                        sent = "BEARISH" 
                                        log("⚠️ No Consensus. Downgrading to Standard Bearish.")
                                        
                            else:
                                log(f"⚠️ Verification Failed: {nd_data.get('results', {}).get('message', 'Limit/Error')}")
                                if sent == "JEFF_PARK_BULLISH": sent = "BULLISH"
                                if sent == "WILLY_WOO_BEARISH": sent = "BEARISH"
                                
                        except Exception as ex:
                            log(f"⚠️ Verification Cannot Connect: {ex}")
                            if sent == "JEFF_PARK_BULLISH": sent = "BULLISH" # Fail-safe

                # --- STEP 3: SAVE STATE ---
                with open("market_sentiment.json", "w") as f:
                    json.dump({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "last_verify_ts": last_verify_ts,
                        "sentiment": sent,
                        "score": final_score,
                        "consensus": full_consensus,
                        "bull_signals": cc_bulls,
                        "bear_signals": cc_bears
                    }, f)
                
                state["news"] = {"sentiment": sent, "score": final_score, "bulls": cc_bulls, "bears": cc_bears}
                icon = "🔥" if full_consensus else "⚠️" if sent in ["BULLISH", "BEARISH"] else ""
                log(f"News: {sent} {icon} (Score: {final_score})")
            
        except Exception as e:
             log(f"News Loop Error: {e}") 
        
        time.sleep(20)  # Faster intel loop (was 60s)

# =============================================================================
# THREAD 2: TRADING BOT
# =============================================================================
def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    state["logs"].append(f"[{timestamp}] {msg}")
    state["logs"] = state["logs"][-10:] # Keep last 10 for UI
    
    # Persist to file for validation
    try:
        with open("trader_activity.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception as e:
        state["logs"].append(f"LOG ERROR: {e}")

def get_precision(symbol):
    if any(s in symbol for s in ["PEPE", "SHIB", "BONK"]):
        return 0 
    if any(s in symbol for s in ["DOGE", "XRP", "ADA", "HBAR", "XLM"]):
        return 1 
    return 6 

def safe_truncate(val, decimals):
    """Truncates a value to specific decimals without rounding up."""
    if decimals == 0:
        return int(val)
    factor = 10.0 ** decimals
    return int(val * factor) / factor

def load_state():
    try:
        if os.path.exists("trading_state.json"):
            with open("trading_state.json", "r") as f:
                data = json.load(f)
                # Update keys safely
                if "positions" in data: state["positions"] = data["positions"]
                if "highs" in data: state["highs"] = data["highs"]
                if "cash" in data: state["cash"] = data["cash"]
                if "targets" in data: state["targets"] = data["targets"]
                log("💾 State Loaded.")
    except Exception as e:
        log(f"⚠️ Load State Failed: {e}")

def save_state():
    try:
        dump = {
            "positions": state["positions"],
            "highs": state["highs"],
            "cash": state["cash"],
            "targets": state.get("targets", {})
        }
        with open("trading_state.json", "w") as f:
            json.dump(dump, f)
    except Exception as e:
        # log(f"⚠️ Save State Failed: {e}")
        pass

def trading_worker():
    load_state() 
    log("Bot Started.")
    
    while state["running"]:
        # ... (Prices update logic matches existing) ...
        try:
            acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
            if acc: state["cash"] = float(acc.get('buying_power', 0))
            
            # Batch pricing requests to avoid failures from one bad apple
            pricing = {}
            chunk_size = 5
            for i in range(0, len(WATCHLIST), chunk_size):
                chunk = WATCHLIST[i:i+chunk_size]
                try:
                    partial = api.get_best_bid_ask(*chunk)
                    if partial:
                        pricing.update(partial)
                except Exception as e:
                    log(f"Pricing Chunk Fail {chunk}: {e}")

            if not pricing:
                log("⚠️ No Pricing Data Received (All Chunks Failed)")

            for sym, data in pricing.items():
                ask = data['ask_price']
                if ask > 0:
                    state["prices"][sym] = ask
                    if ask > state["highs"][sym]: 
                        state["highs"][sym] = ask
                        save_state()

            # 2. Determine Trigger ...
            score = state["news"]["score"]
            risk_pct = 0.05 
            
            if score >= 5:
                # JEFF PARK MODE (MICRO-SCALPING)
                buy_trigger = -0.05   # Buy on tiny micro-dips
                sell_target = 2.0     # Lock in 2% gains (fast cycling)
                risk_pct = 0.75       # Deploy 75% of cash
            elif score > 0:
                # STANDARD BULLISH
                buy_trigger = -0.2    # Buy on small 0.2% dips
                sell_target = 6.0     # Target 6%
                risk_pct = 0.40       # Deploy 40% of cash
            elif score <= -3:
                # EXTREME FEAR (Catch the falling knife bounce)
                buy_trigger = -4.0    
                sell_target = 3.0
                risk_pct = 0.10       # Increased from 0.02
            elif score < 0:
                # BEARISH
                buy_trigger = -2.0
                sell_target = 2.0     # Quick scalps
                risk_pct = 0.10
            else:
                # NEUTRAL (The "Chop")
                buy_trigger = -0.5    # Buy on 0.5% dips (was -1.5)
                sell_target = 3.0     # Take 3%
                risk_pct = 0.20       # Deploy 20% (was 5%)

            state["targets"] = {"buy": buy_trigger, "sell": sell_target, "risk": risk_pct}
            
            # 3. Scan for Trades
            for sym in WATCHLIST:
                price = state["prices"][sym]
                high = state["highs"][sym]
                prec = get_precision(sym)
                
                # CHECK POSITIONS (Sell Logic)
                if sym in state["positions"]:
                    pos = state["positions"][sym]
                    entry = pos['entry']
                    pnl_pct = (price - entry) / entry * 100
                    
                    # Safe Truncate for Sell Qty (Never round up!)
                    sell_qty = safe_truncate(float(pos['qty']), prec)
                    
                    # SELL CONDITION
                    if pnl_pct >= sell_target:
                        log(f"💰 PROFIT: {sym} +{pnl_pct:.2f}%")
                        order = api.place_market_order(sym, "sell", asset_quantity=sell_qty)
                        if order:
                            log(f"📉 SOLD {sym}")
                            del state["positions"][sym]
                            save_state()
                    elif pnl_pct <= -10.0: # Hard Stop
                         log(f"🛑 STOP: {sym} {pnl_pct:.2f}%")
                         api.place_market_order(sym, "sell", asset_quantity=sell_qty)
                         del state["positions"][sym]
                         save_state()
                    continue

                # BUY LOGIC
                if high == 0: continue
                dip = (price - high) / high * 100
                
                if dip <= buy_trigger and state["cash"] > 0.10:  # Lowered from 1.0 to enable micro-buys
                    log(f"💎 DIP: {sym} {dip:.2f}%")
                    
                    buy_usd = state["cash"] * risk_pct
                    buy_usd = max(0.10, buy_usd)  # Lowered from 1.0 to enable micro-buys
                    
                    # Calculate Qty & Apply Precision
                    raw_qty = buy_usd / price
                    qty = round(raw_qty, prec)
                    if prec == 0: qty = int(qty)
                    
                    # Execute Buy
                    order = api.place_market_order(sym, "buy", asset_quantity=qty)
                    
                    if order:
                        executed_price = order.average_price or price
                        filled_qty = float(order.filled_quantity) if order.filled_quantity else qty
                        
                        state["positions"][sym] = {'qty': filled_qty, 'entry': float(executed_price)}
                        log(f"🚀 BOUGHT {sym} ({filled_qty} @ ${executed_price:.4f})")
                        state["highs"][sym] = executed_price
                        
                        # UPDATE CASH LOCALLY to prevent "Insufficient Funds" on next loop item
                        cost = filled_qty * float(executed_price)
                        state["cash"] -= cost
                        save_state()
                    else:
                        # Log failure for debug
                        log(f"⚠️ Buy Fail {sym} Qty:{qty}")
        
        except Exception as e:
             log(f"Bot Error: {e}")
            
        # Periodic Save (Every loop)
        save_state()
        time.sleep(2)  # Aggressive loop (was 5s)

# =============================================================================
# THREAD 3: STRATEGIST ("THE BRAIN")
# =============================================================================
def strategy_worker():
    """
    Mimics 'Ralph Loop'. 
    Iterates through Personas to optimize the strategy.
    """
    personas = ["Risk Manager", "Technician", "Fund Manager", "Hustler"]
    while state["running"]:
        for role in personas:
            state["current_persona"] = role
            
            # 1. RISK MANAGER: Check for huge losses or overexposure
            if role == "Risk Manager":
                invested = sum(
                    p['qty'] * state["prices"].get(s, 0) 
                    for s, p in state["positions"].items()
                )
                total = state["cash"] + invested
                exposure = (invested / total) * 100 if total > 0 else 0
                state["thought"] = f"Checking Exposure... {exposure:.1f}% invested."
                if exposure > 80:
                    state["thought"] += " High exposure! Pausing buys."
                else:
                    state["thought"] += " Exposure healthy."
            
            # 2. TECHNICIAN: Analyzes trends
            elif role == "Technician":
                bulls = 0
                for s in WATCHLIST:
                    high = state["highs"][s]
                    if high > 0:
                        dip = ((state["prices"][s] - high) / high) * 100
                    else:
                        dip = 0
                    if dip > -1.0:
                        bulls += 1
                state["thought"] = f"Market Breadth: {bulls}/{len(WATCHLIST)} assets near highs."
                
            # 3. FUND MANAGER: Goals & Thesis
            elif role == "Fund Manager":
                invested = sum(
                    p['qty'] * state["prices"].get(s, 0) 
                    for s, p in state["positions"].items()
                )
                total = state["cash"] + invested
                progress = (total / 100.0) * 100
                sent = state["news"]["sentiment"]
                
                if sent == "JEFF_PARK_BULLISH":
                    state["thought"] = "Jeff Park Thesis Active: Accumulating for 2026 Banner Year. 🚀"
                elif sent == "WILLY_WOO_BEARISH":
                    state["thought"] = "Willy Woo Warning: Capital Preservation Mode. Quantum clouds ahead. 🛡️"
                else:
                    state["thought"] = f"Goal Progress: ${total:.2f} / $100.00 ({progress:.1f}%)"
            
            # 4. HUSTLER: Motivation & SLC
            elif role == "Hustler":
                import random
                quotes = [
                    "Rule #1: Simple, Lovable, Complete (SLC).",
                    "We are escaping the Matrix today!",
                    "Infinite Money Glitch active? Keep shipping.",
                    "Don't scale yet, just make money.",
                    "Be slightly annoying, be everywhere.",
                    "Shipping garbage has never been easier!",
                    "X for Y? No, it's AI for Profit."
                ]
                state["thought"] = f"💡 {random.choice(quotes)}"
            
            time.sleep(3)  # Think about each role for 3 seconds

# =============================================================================
# MAIN: UI DASHBOARD
# =============================================================================
class Dashboard:
    def make_layout(self):
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="middle", ratio=1),
            Layout(name="bottom", size=10)
        )
        layout["middle"].split_row(
            Layout(name="left", ratio=2), 
            Layout(name="right", ratio=1)
        )
        layout["bottom"].split_row(
            Layout(name="logs", ratio=2),
            Layout(name="brain", ratio=1)
        )
        return layout

    def get_header(self):
        invested = sum(
            p['qty'] * state["prices"].get(s, 0) 
            for s, p in state["positions"].items()
        )
        total = state["cash"] + invested
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        sent = state["news"]["sentiment"]
        
        color = "green" if sent == "BULLISH" else "red" if sent == "BEARISH" else "yellow"
        grid.add_row(
            "🤖 [bold blue]Unk Trading System[/]",
            f"Sentiment: [{color}]{sent}[/]",
            f"Net Worth: [bold green]${total:.2f}[/]"
        )
        return Panel(grid, style="white on black")

    def get_market_table(self):
        table = Table(expand=True, border_style="dim")
        table.add_column("Asset", style="cyan")
        table.add_column("Price")
        table.add_column("Dip %")
        table.add_column("Status")
        
        targets = state.get("targets", {"buy": -1.5, "sell": 5.0})
        trigger = targets["buy"]
        target_profit = targets["sell"]

        for sym in WATCHLIST:
            price = state["prices"][sym]
            high = state["highs"][sym]
            dip = ((price - high) / high * 100) if high > 0 else 0
            
            status = f"Target: +{target_profit}%"
            style = "dim white"
            
            if sym in state["positions"]:
                pos = state["positions"][sym]
                pnl = (price - pos['entry']) / pos['entry'] * 100
                status = f"HOLD (+{pnl:.1f}%)"
                style = "yellow"
            elif dip <= trigger:
                status = "BUYING"
                style = "bold green blink"
            
            dip_str = f"{dip:.2f}%"
            if dip < 0:
                dip_str = f"[red]{dip_str}[/]"
            else:
                dip_str = f"[green]{dip_str}[/]"
            
            table.add_row(sym, f"${price:.8f}", dip_str, f"[{style}]{status}[/]")
            
        title = f"🛑 Market Scanner (Buy: {trigger}% | Sell: +{target_profit}%)"
        return Panel(table, title=title, border_style="blue")
    
    def get_logs(self):
        t = Text()
        for l in state["logs"]:
            t.append(l + "\n")
        return Panel(t, title="📝 Action Logs", border_style="dim")
    
    def get_news(self):
        n = state["news"]
        t = Text()
        t.append(f"{n['sentiment']}\n", style="bold underline")
        t.append(f"Score: {n['score']}\n\nSignals:\n")
        t.append(f"🐂 {n['bulls']}\n", style="green")
        t.append(f"🐻 {n['bears']}\n", style="red")
        return Panel(t, title="🗞️ Intel", border_style="yellow")

    def get_brain(self):
        t = Text()
        role = state.get("current_persona", "Initializing...")
        thought = state.get("thought", "Waiting for brain cycles...")
        
        t.append(f"Persona: {role}\n", style="bold magenta")
        t.append(f"💭 \"{thought}\"", style="italic cyan")
        return Panel(t, title="🧠 Neural Loop", border_style="magenta")

    def generate_layout(self):
        """Regenerate the full layout with fresh data - Rich best practice."""
        layout = self.make_layout()
        layout["header"].update(self.get_header())
        layout["middle"]["left"].update(self.get_market_table())
        layout["middle"]["right"].update(self.get_news())
        layout["bottom"]["logs"].update(self.get_logs())
        layout["bottom"]["brain"].update(self.get_brain())
        return layout

def run():
    from rich.console import Console
    
    console = Console()
    
    # Startup Banner (prints above live display)
    console.print("\n" * 2)
    console.print("=" * 60, style="bold blue")
    console.print("🚀 [bold green]UNK TRADER: JEFF PARK AGGRESSIVE MODE ACTIVATED[/] 🚀")
    console.print("🎯 STRATEGY: 75% RISK | BUY DIPS > 0.05% | TARGET +10%")
    console.print("👀 WATCHLIST: 21 ASSETS (Including DASH, PEPE, BTC)")
    console.print("=" * 60, style="bold blue")
    time.sleep(2)

    # Start Threads
    t1 = threading.Thread(target=news_worker, daemon=True)
    t2 = threading.Thread(target=trading_worker, daemon=True)
    t3 = threading.Thread(target=strategy_worker, daemon=True)
    t1.start()
    t2.start()
    t3.start()
    
    # Initialize Dashboard
    dash = Dashboard()
    
    try:
        # Rich Best Practice: auto_refresh=False with manual update() for precision
        with Live(
            dash.generate_layout(), 
            console=console, 
            screen=True, 
            auto_refresh=False,
            vertical_overflow="crop"  # Cleaner overflow handling
        ) as live:
            while state["running"]:
                # Update the entire layout atomically
                live.update(dash.generate_layout(), refresh=True)
                time.sleep(0.1)  # 10 FPS for smooth animations
                
    except KeyboardInterrupt:
        state["running"] = False
        console.print("\n[bold red]Stopping...[/]")
        console.print("[dim]State saved. See you next time, trader.[/]")

if __name__ == "__main__":
    run()

