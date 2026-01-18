"""
Unk Trader CLI (Master Control)
===============================
Integrates Trading Bot, News Scanner, and Rich UI into ONE application.
"""
# pylint: disable=too-many-lines,too-many-statements,too-many-branches,too-many-locals,too-many-nested-blocks,broad-exception-caught,protected-access,unused-argument,unused-variable,invalid-name,missing-function-docstring,multiple-statements,no-else-return,unspecified-encoding,bare-except,chained-comparison,too-few-public-methods,consider-using-from-import,wrong-import-position,trailing-whitespace,line-too-long
import json
import os
import threading
import sys
import asyncio
import statistics
import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from collections import deque
import random
import msvcrt # Windows Key Detection
import urllib.request
import urllib.parse
from dotenv import load_dotenv
from rich import box
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.tree import Tree
from rich.markdown import Markdown
from rich.traceback import install

# Install Rich Traceback
install(show_locals=True)

# Add project root to path (two levels up from trading/core)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load Env Vars Immediately
load_dotenv()

# Enterprise Trading Architecture
from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI
import trading.integrations.cloud_sync as cloud_sync
from trading.core.governor import SafeGovernor
from trading.integrations.memory import TradingMemory

# Shared Services (Remain in services/ for other modules)
from services.loredb import loredb
from google.genai import types
from services.llm.unk_agent import UnkAiAgent
from services.llm.trading_tools import TRADING_TOOLS

# PAPER TRADING MODE
PAPER_TRADE = os.getenv('PAPER_TRADE', 'false').lower() == 'true'
WARRIOR_MODE = True # Enable Warrior Scanner
if PAPER_TRADE:
    print("=" * 60)
    print("🎮 PAPER TRADING MODE ACTIVE - NO REAL ORDERS WILL EXECUTE")
    print("=" * 60)



# =============================================================================
# INFRASTRUCTURE PATCHES (Thread Safety & Throttling)
# =============================================================================
state_lock = threading.RLock()

def log(msg):
    """Thread-safe logging to UI and file."""
    with state_lock:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        state["logs"].append(entry)
        if len(state["logs"]) > 200:
            state["logs"].pop(0)

    # File Logging
    try:
        # Move logs to a dedicated logs folder eventually, but for now root is fine
        with open("trader_activity.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def safe_run_async(coro):
    """Defensive helper to run async coroutines in sync contexts."""
    try:
        return asyncio.run(coro)
    except Exception as e:
        log(f"Async Error: {e}")
        return None

def safe_truncate(val, decimals):
    """
    Truncates using Decimal for financial precision.
    Never loses fractional cents.
    """
    if decimals == 0:
        return int(val)
    
    try:
        d = Decimal(str(val))
        quantizer = Decimal('0.1') ** decimals
        result = d.quantize(quantizer, rounding=ROUND_DOWN)
        return float(result)
    except Exception as e:
        # Fallback to old method if Decimal fails
        # log(f"Decimal truncate failed for {val}: {e}")
        factor = 10.0 ** decimals
        return int(val * factor) / factor

def get_state_snapshot(*keys):
    """Thread-safe snapshot of state values"""
    with state_lock:
        if not keys:
            return {
                "positions": dict(state["positions"]),
                "prices": dict(state["prices"]),
                "highs": dict(state["highs"]),
                "cash": state["cash"],
                "news": dict(state["news"]),
                "targets": state.get("targets", {}).copy()
            }
        return {k: state[k].copy() if isinstance(state[k], dict) else state[k] for k in keys}

class APIThrottle:
    """Rate limitation helper."""
    def __init__(self, calls_per_minute=30):
        self.calls = deque()
        self.limit = calls_per_minute
        self.lock = threading.Lock()
    
    def acquire(self, endpoint="default"):
        with self.lock:
            now = time.time()
            while self.calls and self.calls[0] < now - 60:
                self.calls.popleft()
            
            if len(self.calls) >= self.limit:
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # Retry
                    return self.acquire(endpoint) 
            
            self.calls.append(now)
            return True

class CloudSyncManager:
    """Throttles cloud sync operations."""
    def __init__(self, min_interval=5.0):
        self.last_sync = 0.0
        self.pending = False
        self.min_interval = float(min_interval)
        self.lock = threading.Lock()
    
    def should_sync(self):
        with self.lock:
            now = time.time()
            if now - self.last_sync >= self.min_interval:
                self.last_sync = now
                self.pending = False
                return True
            self.pending = True
            return False

api_throttle = APIThrottle(calls_per_minute=30)
cloud_sync_mgr = CloudSyncManager(min_interval=5.0)

# =============================================================================
# CONFIG & STATE
# =============================================================================
API_KEY = os.getenv('ROBINHOOD_API_KEY', '')
PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
WATCHLIST = [
    # Full Robinhood Tradable List (33 coins)
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD',
    'XRP-USD', 'ADA-USD', 'AVAX-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'ETC-USD',
    'XLM-USD', 'HBAR-USD', 'UNI-USD', 'AAVE-USD', 'COMP-USD', 'XTZ-USD',
    'DOT-USD', 'SUI-USD', 'OP-USD', 'ARB-USD', 'SEI-USD', 'CRV-USD', 
    'LDO-USD', 'ENA-USD', 'WIF-USD', 'VIRTUAL-USD', 'AERO-USD', 'SYRUP-USD', 'XCN-USD'
]
SMALL_COINS = [
    'SHIB-USD', 'DOGE-USD', 'BONK-USD', 'PEPE-USD', 
    'ADA-USD', 'XLM-USD', 'AVAX-USD', 'LINK-USD', 'ETC-USD'
]
BIG_COINS = ['BTC-USD', 'ETH-USD']

# SCALP TIER: Fast rotation at 0.3% profit (User requested)
SCALP_COINS = [
    'ETH-USD', 'ADA-USD', 'ETC-USD'
]

try:
    api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)
    # Force fetch account number on startup (Required for V2 endpoints)
    acc_info = api.get_account()
    if acc_info:
        # log(f"API Initialized. Account: {api.account_number}")
        pass
except Exception as e:
    log(f"API Init Failed: {e}")
    # Continue anyway, let individual calls fail if must
    pass
governor = SafeGovernor()

# Shared Memory
state = {
    "prices": {sym: 0.0 for sym in WATCHLIST},
    "highs": {sym: 0.0 for sym in WATCHLIST},
    "positions": {},  # {sym: {qty, entry, pnl_pct}}
    "cash": 0.0,
    "news": {"sentiment": "NEUTRAL", "score": 0, "bulls": 0, "bears": 0},
    "targets": {"buy": -1.5, "sell": 1.5, "risk": 0.95}, # Default targets
    "last_buy": time.time(),  # Watchdog
    "logs": [],               # Rolling logs
    "current_persona": "Init",
    "thought": "Initializing...",
    "funnel_pool": 0.0,
    "trends": {},             # {sym: pct_change_24h}
    "warrior_signals": {},    # {sym: {pattern, timestamp}}
    "chat_log": [],           # List of (Who, Msg) tuples
    "chat_draft": "",         # Current unsent input
    # STRATEGY GATING (New Keys)
    "buy_paused": False,
    "pause_reason": "",
    "exposure_pct": 0.0,
    "exposure_limit": 0.0,
    "last_pause_log_ts": 0.0,
    "running": True,
    # Performance Metrics
    "daily_start_balance": 0.0,
    "winning_trades": 0,
    "losing_trades": 0,
    "best_trade_sym": "",
    "best_trade_pct": 0.0,
    "worst_trade_sym": "",
    "worst_trade_pct": 0.0,
    "total_trades": 0,
    "shave_opportunities": 0
}

# =============================================================================
# THREAD 1: NEWS SCANNER
# =============================================================================
def news_worker():
    """
    Fetches news every 15 minutes (to save API credits).
    Updates market_sentiment.json
    """
    
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
        try: # pylint: disable=broad-exception-caught
            # Check cache age
            should_fetch = True
            try:
                with open("market_sentiment.json", "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    # Load state for immediate UI
                    state["news"]["sentiment"] = cached_data.get("sentiment", "NEUTRAL")
                    state["news"]["score"] = cached_data.get("score", 0)
                    
                    # Check timestamp
                    last_ts = cached_data.get("last_verify_ts", 0)
                    if time.time() - last_ts < 180:  # 3 minutes
                        should_fetch = False
                        # log(f"Using Cached Intel ({int((time.time()-last_ts)/60)}m old)")
                        
                        # --- SYNC CACHED DATA TO SITE ---
                        try:
                            site_path = r"C:\Users\super\Watchtower\HQ_Blade\AiwithDav3_site\public\data\news_feed.json"
                            os.makedirs(os.path.dirname(site_path), exist_ok=True)
                            with open(site_path, "w") as f2:
                                json.dump({
                                    "updated": datetime.fromtimestamp(last_ts).strftime("%H:%M"),
                                    "sentiment": cached_data.get("sentiment", "NEUTRAL"),
                                    "score": cached_data.get("score", 0),
                                    "articles": cached_data.get("articles", [])
                                }, f2)
                        except Exception as e:
                            log(f"Cache Sync Error: {e}")

            except (FileNotFoundError, json.JSONDecodeError):
                cached_data = {}
                should_fetch = True

            if should_fetch:
                log("Fetching Primary Intel (CryptoCompare)...")
                
                # --- STEP 1: PRIMARY SOURCE ---
                cc_score = 0
                cc_bulls = 0
                cc_bears = 0
                articles_list = []
                
                try:
                    with urllib.request.urlopen(CC_URL, timeout=10) as res:
                        data = json.loads(res.read().decode())
                    if data.get('Message') == 'News list successfully returned':
                        # Capture top 15 articles
                        for art in data.get('Data', [])[:15]:
                            title = art.get('title', "")
                            body = art.get('body', "")
                            url = art.get('url', "")
                            source = art.get('source', "CryptoCompare")
                            pub_time = art.get('published_on', 0)
                            
                            s, b, r = analyze_text(
                                title + " " + body, 
                                THEMES_BULLISH, 
                                THEMES_BEARISH
                            )
                            cc_score += s
                            cc_bulls += b
                            cc_bears += r
                            
                            articles_list.append({
                                "title": title,
                                "url": url,
                                "source": source,
                                "sentiment_score": s,
                                "published_on": pub_time
                            })
                except Exception as e:
                    log(f"Primary Source Failed: {e}")

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
                last_verify_ts = cached_data.get("last_verify_ts", 0) if 'cached_data' in locals() and cached_data else 0
                current_ts = datetime.now().timestamp()
                
                if sent in ["JEFF_PARK_BULLISH", "WILLY_WOO_BEARISH"]:
                    # Check Cache - CACHE ALL ATTEMPTS for 30 minutes to save credits
                    time_since = current_ts - last_verify_ts
                    cached_sent = cached_data.get("sentiment", "") if cached_data else ""
                    cached_cons = cached_data.get("consensus", False) if cached_data else False
                    
                    # If verified in last 30 MINUTES (1800s), skip API call entirely
                    if time_since < 1800 and cached_sent in ["JEFF_PARK_BULLISH", "WILLY_WOO_BEARISH", "BULLISH", "BEARISH"]:
                        log(f"Verification Cached ({int(time_since/60)}m ago). Credits Saved.")
                        full_consensus = cached_cons
                        # Use cached sentiment result (may have been downgraded)
                        sent = cached_sent
                    else:
                        # STRICT LIMIT: NewsData.io (200 credits/day -> ~1 call/8min).
                        # Let's use 15 min safe buffer to save for real volatility.
                        last_nd = state.get("last_nd_call", 0)
                        if current_ts - last_nd < 1800: # 30 minutes
                            log(f"Skipping Verification (Rate Limit Active). Last call {int((current_ts-last_nd)/60)}m ago.")
                            # Trust primary for now? Or hold neutral?
                            # Trusting primary to keep flow moving.
                            # full_consensus = False # No consensus yet
                        else:
                            log(f"Extreme Signal ({sent}) detected. Verifying with NewsData.io...")
                            try:
                                q = " OR ".join(KEYWORDS)
                                params = urllib.parse.urlencode({"apikey": ND_API_KEY, "q": q, "language": "en"})
                                nd_url_full = f"{ND_URL}?{params}"
                                
                                with urllib.request.urlopen(nd_url_full, timeout=10) as nd_res:
                                    nd_data = json.loads(nd_res.read().decode())
                                
                                with state_lock:
                                    state["last_nd_call"] = current_ts
                                
                                # try:
                                #     nd_data = nd_res.json()
                                # except:
                                #     nd_data = {}
                            
                                if nd_data.get('status') == 'success':
                                    nd_score = 0
                                    fresh_articles = 0
                                    
                                    for art in nd_data.get('results', []):
                                        title = art.get('title') or ""
                                        desc = art.get('description') or ""
                                        link = art.get('link') or ""
                                        pub = art.get('pubDate') or ""
                                        
                                        s, b, r = analyze_text(title + " " + desc, THEMES_BULLISH, THEMES_BEARISH)
                                        nd_score += s
                                        
                                        # Append verification articles to top of feed
                                        articles_list.insert(0, {
                                            "title": f"[VERIFY] {title}",
                                            "url": link,
                                            "source": "NewsData.io",
                                            "sentiment_score": s,
                                            "published_on": current_ts
                                        })
                                
                                    log(f"NeWsData Score: {nd_score} (Credits Used)")
                                    
                                    # CONSENSUS LOGIC
                                    if sent == "JEFF_PARK_BULLISH":
                                        if nd_score > 0: 
                                            full_consensus = True
                                            last_verify_ts = current_ts # Update TS only on new verify
                                            log("CONSENSUS REACHED: ALL IN 50% RISK")
                                        else:
                                            sent = "BULLISH" # Downgrade
                                            log("No Consensus. Downgrading to Standard Bullish.")
                                    
                                    elif sent == "WILLY_WOO_BEARISH":
                                        if nd_score < 0:
                                            full_consensus = True
                                            last_verify_ts = current_ts
                                            log("CONSENSUS REACHED: DEFENSIVE MODE ACTIVE")
                                        else:
                                            sent = "BEARISH" 
                                            log("No Consensus. Downgrading to Standard Bearish.")
                                        
                                else:
                                    msg = nd_data.get('results', {}).get('message', 'Limit/Error')
                                    log(f"Verification Skipped: {msg}")
                                    # FALLBACK: If credits out, trust the primary source (Don't downgrade)
                                    full_consensus = True 
                                    last_verify_ts = current_ts # Prevent spamming API
                                    log("Credits Exhausted -> Trusting Primary Signal (JEFF PARK ACTIVE)")
                                
                            except Exception as ex:
                                log(f"Verification Cannot Connect: {ex}")
                                # Keep original sentiment, assume primary is right
                                full_consensus = True
                                last_verify_ts = current_ts

                # --- STEP 3: SAVE STATE ---
                # Local Persistent
                with open("market_sentiment.json", "w") as f:
                    json.dump({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "last_verify_ts": last_verify_ts,
                        "sentiment": sent,
                        "score": final_score,
                        "consensus": full_consensus,
                        "bull_signals": cc_bulls,
                        "bear_signals": cc_bears,
                        "articles": articles_list
                    }, f)
                
                # Cache Intel in LoreDB (Long-Term Memory)
                try:
                    summary = f"Market News Intel: {sent} (Score: {final_score}). "
                    if full_consensus:
                        summary += "CONSENSUS VERIFIED."
                    asyncio.run(loredb.add_memory(
                        summary, 
                        source="system", 
                        metadata={"type": "news_intel", "sentiment": sent, "score": final_score}
                    ))
                except Exception as e:
                    log(f"LoreDB Cache Error: {e}")
                
                # --- SITE INTEGRATION (ZERO COST FEED) ---
                try:
                    site_path = r"C:\Users\super\Watchtower\HQ_Blade\AiwithDav3_site\public\data\news_feed.json"
                    # Ensure dir exists (safe check)
                    os.makedirs(os.path.dirname(site_path), exist_ok=True)
                    
                    with open(site_path, "w") as f:
                        json.dump({
                            "updated": datetime.now().strftime("%H:%M"),
                            "sentiment": sent,
                            "score": final_score,
                            "articles": articles_list
                        }, f)
                    # log(f"Site Feed Updated: {site_path}")
                except Exception as e:
                    log(f"Site Sync Error: {e}")

                with state_lock:
                    state["news"] = {
                        "sentiment": sent, 
                        "score": final_score, 
                        "bulls": cc_bulls, 
                        "bears": cc_bears,
                        "articles": articles_list
                    }
                
                icon = "!" if full_consensus else "?" if sent in ["BULLISH", "BEARISH"] else ""
                log(f"News: {sent} {icon} (Score: {final_score})")
            
        except Exception as e:
            log(f"News Loop Error: {e}") 
        
        time.sleep(20)  # Faster intel loop (was 60s)

# =============================================================================
# THREAD 2: TRADING BOT
# =============================================================================


# =============================================================================
# THREAD 2: TRADING BOT
# =============================================================================

def fetch_momentum_data():
    """
    FETches 24h % Change from CryptoCompare for ALL Watchlist items.
    Updates state["trends"].
    """
    try:
        # Build CSV of symbols (BTC,ETH,etc)
        syms = ",".join([s.split('-')[0] for s in WATCHLIST])
        url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={syms}&tsyms=USD"
        
        with urllib.request.urlopen(url, timeout=5) as res:
            data = json.loads(res.read().decode())
        
        if "RAW" in data:
            with state_lock:
                for sym in WATCHLIST:
                    coin = sym.split('-')[0]
                    if coin in data["RAW"]:
                        try:
                            # Extract 24h Change %
                            pct = data["RAW"][coin]["USD"]["CHANGEPCT24HOUR"]
                            state["trends"][sym] = float(pct)
                            # Explicit log for BTC since user is watching it
                            if coin == "BTC":
                                log(f"BTC Trend: {float(pct):+.2f}%")
                        except:
                            pass
            # log("Momentum Data Updated")
            
    except Exception as e:
        log(f"Momentum Fetch Error: {e}")

def get_precision(symbol):
    if any(s in symbol for s in ["PEPE", "SHIB", "BONK"]):
        return 0 
    if any(s in symbol for s in ["DOGE", "XRP", "ADA", "HBAR", "XLM"]):
        return 1
    # High Value Coins (LTC, AVAX, SOL, ETH, BTC, etc) get max precision
    return 6 

def load_state():
    try:
        if os.path.exists("trading_state.json"):
            with open("trading_state.json", "r") as f:
                data = json.load(f)
                with state_lock:
                    # Update keys safely
                    if "positions" in data: state["positions"] = data["positions"]
                    if "highs" in data: state["highs"] = data["highs"]
                    if "cash" in data: state["cash"] = data["cash"]
                    if "targets" in data: state["targets"] = data["targets"]
                log("State Loaded.")
    except Exception as e:
        log(f"Load State Failed: {e}")
    
    # Reload Healing Config
    try:
        heal_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "healing.json")
        if os.path.exists(heal_path):
            with open(heal_path, "r") as f:
                state["healing_config"] = json.load(f).get("strategies", {}).get("healing", {})
            log("Healing Config Refreshed.")
    except Exception as e:
        log(f"Healing Load Error: {e}")
    
    # Initial Sync
    sync_with_api()

def rebuild_cost_basis(api_client):
    """
    Reconstructs average buy price (cost basis) from Order History.
    Required because Robinhood Crypto API does not return cost basis in holdings.
    """
    try:
        # log("Rebuilding Cost Basis from Orders...")
        orders = api_client.get_orders(state="filled")
        orders.sort(key=lambda x: x.created_at)
        
        portfolio = {} # {symbol: {'qty': 0.0, 'avg_price': 0.0}}
        
        for o in orders:
            sym = o.symbol
            side = o.side
            qty = o.filled_quantity
            price = o.average_price or 0.0
            
            if sym not in portfolio:
                portfolio[sym] = {'qty': 0.0, 'avg_price': 0.0}
            
            p = portfolio[sym]
            
            if side == 'buy':
                new_qty = p['qty'] + qty
                if new_qty > 0:
                    current_val = p['qty'] * p['avg_price']
                    new_val = qty * price
                    p['avg_price'] = (current_val + new_val) / new_qty
                p['qty'] = new_qty
            elif side == 'sell':
                p['qty'] = max(0, p['qty'] - qty)
                if p['qty'] == 0:
                    p['avg_price'] = 0.0
                    
        # Convert to simple map
        cost_map = {k: v['avg_price'] for k, v in portfolio.items() if v['qty'] > 0}
        # log(f"Cost Basis Rebuild Complete ({len(cost_map)} items)")
        return cost_map
        
    except Exception as e:
        log(f"Cost Basis Rebuild Error: {e}")
        return {}

def sync_with_api():
    """
    Forcefully syncs local state with Robinhood API ground truth.
    Handles external trades (phone app) by:
    1. Updating quantities
    2. Adding new positions
    3. Pruning phantoms
    4. Updating buying power
    """
    try:
        # log("Syncing with API...")
        # 0. Rebuild Cost Basis (The Hard Way)
        cost_map = rebuild_cost_basis(api) 
        
        # log("Fetching Holdings...")
        holdings = api.get_holdings()
        real_holdings = {}
        for h in holdings:
            qty = float(h.total_quantity) if h.total_quantity else 0
            if qty > 0:
                sym = f"{h.asset_code}-USD"
                # Use calculated cost basis if available, else 0
                entry = cost_map.get(sym, 0.0)
                real_holdings[sym] = {'qty': qty, 'entry': entry}
        
        with state_lock:
            # 2. Prune Phantoms
            phantom = [sym for sym in state["positions"] if sym not in real_holdings]
            for sym in phantom:
                log(f"Removing phantom position: {sym} (not in Robinhood)")
                del state["positions"][sym]
            
            # 3. Update/Add Real Holdings
            for sym, data in real_holdings.items():
                qty = data['qty']
                entry = data['entry']
                
                # Update entry if we found a valid one
                if entry > 0:
                     state["positions"].setdefault(sym, {})['entry'] = entry
                
                if sym in state["positions"]:
                    # Update quantity if changed
                    old_qty = float(state["positions"][sym].get('qty', 0))
                    if abs(old_qty - qty) > 0.00000001:
                        # log(f"Synced {sym}: Qty {old_qty} -> {qty}")
                        state["positions"][sym]['qty'] = qty
                else:
                    # New position found
                    log(f"Found new position: {sym} ({qty}) @ ${entry:.2f}")
                    current_price = state["prices"].get(sym, 0)
                    final_entry = entry if entry > 0 else current_price
                    state["positions"][sym] = {'qty': qty, 'entry': final_entry}
            
            # 4. Update Cash
            acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
            if acc:
                state["cash"] = float(acc.get('buying_power', 0))
        
        save_state()
        log("Synced with Robinhood")
        
    except Exception as e:
        log(f"Robinhood Sync Failed: {e}")

def save_state():
    """Thread-safe save with cloud sync throttling"""
    try:
        # Get snapshot with lock
        with state_lock:
            dump = {
                "positions": dict(state["positions"]),
                "highs": dict(state["highs"]),
                "prices": dict(state["prices"]),
                "cash": state["cash"],
                "targets": state.get("targets", {}).copy(),
                "funnel_pool": state.get("funnel_pool", 0.0)
            }
        
        # Local save (always)
        abs_path = r"c:\Users\super\Watchtower\unk-app-ai\trading_state.json"
        with open(abs_path, "w") as f:
            json.dump(dump, f, indent=2)
        
        # Cloud sync (throttled)
        if cloud_sync_mgr.should_sync():
            cloud_sync.push_state(dump)
        
    except Exception as e:
        pass # log(f"Save State Error: {e}")

def execute_buy_order(sym, price, qty, prec):
    """
    Thread-safe buy execution with locking + Paper Trade support.
    """
    
    if PAPER_TRADE:
        time.sleep(0.1)  # Simulate network
        log(f"📝 PAPER: Would buy {qty} {sym} @ ${price:.4f}")
        with state_lock:
            state["positions"][sym] = {'qty': qty, 'entry': price}
            cost = qty * price
            state["cash"] = max(0, state["cash"] - cost)
            state["last_buy"] = time.time()
        return True, qty, price

    with state_lock:
        # Re-check cash under lock
        cost = qty * price
        if state["cash"] < cost:
            log(f"Buy Rejected: Insufficient Cash (Need ${cost:.2f}, Have ${state['cash']:.2f})")
            return False, 0, 0
        
        # Reserve cash (Lock it)
        state["cash"] -= cost 
    
    try:
        # Execute API Call (Unlocked to prevent holding state_lock during net IO)
        api_throttle.acquire("order")
        order = api.place_market_order(sym, "buy", asset_quantity=qty)
        
        if order:
            # Handle both Dict and Object (CryptoOrder) response types
            try:
                if isinstance(order, dict):
                    filled_qty = float(order.get('quantity', qty))
                    avg_price = float(order.get('average_price', price))
                else:
                    # Assume Object with attributes
                    filled_qty = float(getattr(order, 'quantity', qty))
                    if getattr(order, 'average_price', None):
                         avg_price = float(order.average_price)
                    else:
                         avg_price = price
            except:
                # Fallback if parsing fails but order exists
                filled_qty = qty
                avg_price = price
                
            log(f"ORDER FILLED: {sym} x {filled_qty} @ ${avg_price:.2f}")
            
            with state_lock:
                 # Finalize state update with actuals
                 state["positions"][sym] = {
                     'qty': filled_qty,
                     'entry': avg_price,
                     'pnl_pct': 0.0
                 }
                 state["last_buy"] = time.time()
                 # Note: Cash was already deducted pessimistically. 
                 
            # GOVERNOR: Record Order Time
            governor.record_order(sym)
            
            return True, filled_qty, avg_price
        else:
            # Rollback Lock on API failure
            with state_lock:
                state["cash"] += cost
            log(f"Order Failed: {getattr(api, 'last_error', 'Unknown')}")
            return False, 0, 0

    except Exception as e:
        # Rollback Lock on Exception
        with state_lock:
            state["cash"] += cost
        log(f"Buy Exception {sym}: {e}")
        return False, 0, 0

def can_buy(symbol=None, spread_bps=0):
    """
    Risk Manager check - returns True if buying is allowed.
    Blocks buys if overexposed or in defensive mode.
    Now integrates SafeGovernor.
    """
    # 1. Governor Check (Safety First)
    if symbol:
        safe, reason = governor.can_trade(symbol, spread_bps)
        if not safe:
            # Only log if reason changes to avoid spam
            return False
            
    with state_lock:
        # Check exposure
        invested = sum(
            float(p.get("qty", 0)) * state["prices"].get(s, 0)
            for s, p in state["positions"].items()
        )
        total = invested + state["cash"]
        
        if total <= 0:
            return False
        
        exposure = (invested / total) * 100.0
        # Check explicit pause
        if state.get("buy_paused", False):
            return False
            
        return True

def compute_exposure(positions: dict, prices: dict, cash: float):
    invested = 0.0
    for sym, pos in positions.items():
        price = prices.get(sym, 0.0)
        qty = float(pos.get('qty', 0.0))
        invested += qty * price
    
    total = invested + cash
    exposure = (invested / total) * 100.0 if total > 0 else 0.0
    return invested, total, exposure

def apply_buy_gate():
    """
    Runs under Risk Manager.
    Writes the single source of truth:
      state["buy_paused"], state["pause_reason"], exposure fields.
    """
    snap = get_state_snapshot("positions", "prices", "cash", "news")
    invested, total, exposure = compute_exposure(snap["positions"], snap["prices"], snap["cash"])

    sent = snap["news"].get("sentiment", "NEUTRAL")

    if sent == "JEFF_PARK_BULLISH":
        limit = 75.0
    elif sent == "WILLY_WOO_BEARISH":
        limit = 30.0
    else:
        limit = 60.0

    paused = total <= 0 or exposure > limit
    reason = "Total is zero" if total <= 0 else f"Exposure {exposure:.1f}% exceeds {limit:.0f}% cap"

    with state_lock:
        state["exposure_pct"] = exposure
        state["exposure_limit"] = limit
        state["buy_paused"] = bool(paused)
        state["pause_reason"] = reason if paused else ""

def record_trade(sym, pnl_pct):
    """Track trade statistics"""
    with state_lock:
        state["total_trades"] = state.get("total_trades", 0) + 1
        
        if pnl_pct > 0:
            state["winning_trades"] = state.get("winning_trades", 0) + 1
            if pnl_pct > state.get("best_trade_pct", 0):
                state["best_trade_pct"] = pnl_pct
                state["best_trade_sym"] = sym
        else:
            state["losing_trades"] = state.get("losing_trades", 0) + 1
            if pnl_pct < state.get("worst_trade_pct", 0):
                state["worst_trade_pct"] = pnl_pct
                state["worst_trade_sym"] = sym
                
        # GOVERNOR: Track Results (Auto-Lockout on streaks)
        governor.record_result(pnl_pct)

def trading_worker(): # pylint: disable=too-many-statements,broad-exception-caught,too-many-branches,too-many-nested-blocks
    """
    FINAL HARDENED VERSION (v2.2)
    Integrates ALL patches:
    - Thread safety
    - API throttling  
    - Strategy gating
    - Circuit breakers
    - Performance tracking
    - Decimal precision
    """
    load_state()
    log("🚀 Bot Started (v2.2 - Final Hardened)")
    
    if PAPER_TRADE:
        log("📝 PAPER TRADING MODE - Simulated orders only")
    
    # failed_stops = {} # Removed unused variable
    
    # === 200ms GOVERNOR LOOP ===
    # State for loop
    loop_tick = 0
    BATCH_SIZE = len(WATCHLIST) # Full watchlist scan for HFT
    WATCHLIST_LEN = len(WATCHLIST)
    
    log(f"⚡ HFT Shaver: Starting 200ms Scan Loop ({len(WATCHLIST)} assets)")
    
    while state["running"]:
        tick_start = time.time()
        
        try:
            # 1. SCAN PHASE (Very Fast)
            # Round-robin batching
            start_idx = (loop_tick * BATCH_SIZE) % WATCHLIST_LEN
            end_idx = start_idx + BATCH_SIZE
            batch = WATCHLIST[start_idx:end_idx]
            
            try:
                # Unlocked API call
                api_throttle.acquire("pricing")
                partial = api.get_best_bid_ask(*batch)
                
                if partial:
                    with state_lock:
                        for sym, data in partial.items():
                            ask = float(data.get('ask_price', 0))
                            if ask > 0:
                                # PENNY SHAVER: Detect Micro-Dip
                                prev_p = state["prices"].get(sym, 0)
                                if prev_p > 0:
                                    diff = (ask - prev_p) / prev_p
                                    # If price drops 0.05% in 200ms -> Shave Opp
                                    if diff < -0.0005: 
                                        state["shave_opportunities"] += 1
                                        # (Optional) Log highly concentrated opps
                                        # if state["shave_opportunities"] % 100 == 0:
                                        #     log(f"🔥 Found {state['shave_opportunities']} Shave Opps")
                                
                                state["prices"][sym] = ask
                                if ask > state["highs"].get(sym, 0):
                                    state["highs"][sym] = ask
            except Exception as e:
                log(f"Price Fetch Error: {e}")
                pass # Fail fast, catch next tick
            
            # 2. DECISION PHASE (Gated)
            # Only run heavy logic if Governor allows (State not LOCKOUT)
            now = time.time()
            snapshot = get_state_snapshot()
            
            # A) Micro-Shave / Sell Logic (Fast Check)
            for sym, pos in snapshot["positions"].items():
                price = snapshot["prices"].get(sym, 0)
                if price <= 0: continue
                
                entry = float(pos['entry'])
                qty = float(pos['qty'])
                
                # === HEALING STRATEGY (Specific Assets) ===
                # Logic: Sell 40% @ +7% of Anchor | Re-buy @ -3% of Anchor
                if sym in ["BONK-USD", "AERO-USD", "SHIB-USD"]:
                    try:
                        # Optimization: Cache config for 60 seconds
                        now_ts = time.time()
                        if now_ts - state.get("last_healing_load", 0) > 60:
                            if os.path.exists("healing_config.json"):
                                with open("healing_config.json", "r", encoding="utf-8") as f:
                                    state["healing_config"] = json.load(f)
                            state["last_healing_load"] = now_ts

                        h_conf = state.get("healing_config", {}).get("strategies", {}).get("healing", {}).get(sym)
                        
                        if h_conf and h_conf["active"]:
                            anchor = h_conf["anchor_price"]
                            
                            # 1. SELL CHECK (+7% from Anchor)
                            pct_diff = (price - anchor) / anchor
                            
                            if pct_diff >= h_conf.get("sell_target_pct", 0.07):
                                safe, reason = governor.can_trade(sym, "sell", current_price=price, entry_price=anchor)
                                if not safe:
                                    log(f"🛡️ Gov Block (Healing Sell): {reason}")
                                if safe:
                                    log(f"🩹 HEALING SELL: {sym} hit +{pct_diff*100:.1f}% (Target +{h_conf.get('sell_target_pct', 0.07)*100:.0f}%). Selling 40%.")
                                    sell_qty = qty * h_conf.get("sell_amount_pct", 0.40)
                                    
                                    prec = get_precision(sym)
                                    if sym in ['SHIB-USD', 'BONK-USD']:
                                        prec = 0
                                    
                                    safe_sell_qty = safe_truncate(sell_qty, prec)
                                    
                                    api_throttle.acquire("order")
                                    if not PAPER_TRADE:
                                        api.place_market_order(sym, "sell", asset_quantity=safe_sell_qty)
                                    else:
                                        execute_buy_order(sym, price, -safe_sell_qty, prec) # Paper sell simulation logic needed or update manual

                                    governor.record_order(sym)
                                    governor.record_result(pct_diff*100)
                                    continue
                            
                            # 2. RE-BUY CHECK (-3% from Anchor)
                            elif pct_diff <= h_conf.get("buy_reset_pct", -0.03):
                                if state["cash"] > 2.00:
                                    safe, reason = governor.can_trade(sym, "buy", current_price=price, entry_price=anchor)
                                    if not safe:
                                         log(f"🛡️ Gov Block (Healing Buy): {reason}")
                                    if safe:
                                        log(f"🩹 HEALING BUY: {sym} hit {pct_diff*100:.1f}% (Target {h_conf.get('buy_reset_pct', -0.03)*100:.0f}%). Re-entering.")
                                        buy_amt = 6.00 # Fixed chunk
                                        if state["cash"] < 6.00:
                                            buy_amt = state["cash"] * 0.98
                                        
                                        prec = get_precision(sym)
                                        if sym in ['SHIB-USD', 'BONK-USD']:
                                            prec = 0
                                        
                                        buy_qty = safe_truncate(buy_amt / price, prec)
                                        
                                        api_throttle.acquire("order")
                                        if not PAPER_TRADE:
                                            api.place_market_order(sym, "buy", asset_quantity=buy_qty)
                                        else:
                                             execute_buy_order(sym, price, buy_qty, prec)
                                            
                                        governor.record_order(sym)
                                        continue

                    except Exception as e:
                        log(f"Healing Error {sym}: {e}")
                
                # === END HEALING LOGIC ===

                if entry > 0 and qty > 0:
                    pnl_pct = (price - entry) / entry * 100
                    
                    # GOVERNOR: Update PnL Stream
                    # (In a real 200ms bot, we'd only do this on change, but here is fine)
                    
                    # Micro-Shave Trigger (> $1.00 profit)
                    cost_basis = qty * entry
                    current_value = qty * price
                    profit_value = current_value - cost_basis
                    
                    if profit_value >= 1.00:
                        prec = get_precision(sym)
                        shave_qty = safe_truncate(profit_value / price, prec)
                        
                        if 0 < shave_qty < qty:
                            # GOVERNOR GATE: Rate Limit + Hard Floor
                            safe, reason = governor.can_trade(sym, "sell", current_price=price, entry_price=entry)
                            if not safe:
                                # Log only if it's not just a rate limit (too spammy)
                                if "Rate" not in reason:
                                     log(f"🛡️ Gov Block (Shave): {reason}")
                            if safe:
                                log(f"✂️ SHAVE: {sym} +{pnl_pct:.2f}% (${profit_value:.2f})")
                                api_throttle.acquire("order")
                                
                                if not PAPER_TRADE:
                                    api.place_market_order(sym, "sell", asset_quantity=shave_qty)
                                
                                governor.record_order(sym)
                                governor.record_result(pnl_pct)

            # 3. BACKGROUND TASKS (Low Frequency)
            # Sync Account (Every 15s)
            if loop_tick % 75 == 0: # 75 * 0.2 = 15s
                 try:
                    # pylint: disable=protected-access
                    api_throttle.acquire("account")
                    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
                    if acc:
                        with state_lock:
                             state["cash"] = float(acc.get('buying_power', 0))
                 except Exception: # pylint: disable=broad-exception-caught
                     pass

            # Sync State (Every 5 min)
            if now - state.get("last_sync_check", 0) > 300:
                log("🔄 Periodic Sync")
                sync_with_api()
                with state_lock:
                    state["last_sync_check"] = now
            
            # Momentum (Every 60s)
            if now - state.get("last_mom_check", 0) > 60:
                fetch_momentum_data()
                with state_lock:
                    state["last_mom_check"] = now

            # Risk Gate Update (Every 1s)
            if loop_tick % 5 == 0:
                apply_buy_gate()

        except Exception as e: # pylint: disable=broad-exception-caught
            log(f"Loop Error: {e}")

        # 4. SLEEP PHASE (Maintain 200ms Cadence)
        loop_tick += 1
        elapsed = time.time() - tick_start
        sleep_time = max(0.005, 0.2 - elapsed) # Faster tick floor
        time.sleep(sleep_time)
        
        # Periodic Save (Throttled)
        if loop_tick % 50 == 0: # Every 10 seconds
            save_state()

# =============================================================================
# THREAD 3: STRATEGIST ("THE BRAIN")
# =============================================================================
# =============================================================================
# THREAD 3: STRATEGIST ("THE BRAIN" - POWERED BY VERTEX AI)
# =============================================================================
def strategy_worker():  # pylint: disable=too-many-branches,too-many-locals
    """
    Real AI Loop.
    Uses ReasoningAgent (Vertex AI) to analyze market state.
    """
    # Lazy import to avoid circular dep issues at top level if any
    try:
        from services.llm.reasoning_agent import ReasoningAgent
        from services.llm.unk_agent import UnkAiAgent
        
        # Primary: Vertex AI Reasoning Engine
        agent = ReasoningAgent()
        has_primary = agent.connected
        
        # Fallback: Gemini 3 Flash (Global)
        fallback = UnkAiAgent(mode="unk")
        has_fallback = True # Assuming API key is present
        
    except Exception as e:
        log(f"AI Init Failed: {e}")
        has_primary = False
        has_fallback = False
        
    log(f"🧠 Brain Online: Primary={'ON' if has_primary else 'OFF'} | Fallback={'ON' if has_fallback else 'OFF'}")
    
    while state["running"]:
        try:
            # 1. Gather Context
            snapshot = get_state_snapshot("positions", "prices", "cash", "news", "highs", "targets")
            
            # 2. AI Analysis (Every 60s)
            context = {
                "cash": snapshot["cash"],
                "equity": sum(p['qty'] * snapshot['prices'].get(s, 0) for s, p in snapshot['positions'].items()),
                "sentiment": snapshot["news"]["sentiment"],
                "positions": {s: f"{p['qty']:.4f} (@${p['entry']:.2f})" for s, p in snapshot['positions'].items()},
                "market_prices": {s: f"${p:.2f}" for s, p in snapshot['prices'].items() if p > 0}
            }
            
            prompt = (
                f"Analyze this market state for a crypto trader: {json.dumps(context)}. "
                "Provide a short, punchy thought (max 1 sentence) on what we should do next. "
                "Adopt the persona of a 'Street-Smart Hedge Fund Manager'."
            )
            
            if has_primary:
                try:
                    thought = agent.query(prompt)
                    with state_lock:
                        state["thought"] = f"Vertex: {thought}"
                        state["current_persona"] = "Vertex AI"
                except Exception as e:
                    log(f"Primary AI Failed: {e}. Switching to Fallback.")
                    has_primary = False # Demote temporarily? Or just retry next loop?
                    # Fallthrough to fallback
            
            if not has_primary and has_fallback:
                try:
                    # Unk Agent speak
                    thought = fallback.run(prompt, config={"system_instruction": "You are a crypto strategist."})
                    with state_lock:
                        state["thought"] = f"Gemini 3: {thought}"
                        state["current_persona"] = "Unk (Flash)"
                except Exception as e:
                     state["thought"] = "AI Offline. Monitoring..."
                     state["current_persona"] = "Blind"

            if not has_primary and not has_fallback:
                 state["thought"] = "AI Deep Offline."
                 state["current_persona"] = "Manual"

            time.sleep(60) # Reflect for 1 minute

        except Exception as e:
            log(f"Strategy Error: {e}")
            time.sleep(10)

# =============================================================================
# THREAD 4: WARRIOR SCANNER (Background Intelligence)
# =============================================================================
def check_first_pullback(symbol):
    """
    Detects 'First Pullback' Pattern (Warrior Trading):
    1. Strong Trend Up.
    2. Recent Candle was RED.
    3. High Relative Volume.
    """
    try:
        # Get 15-minute candles (last 10 periods = 150 mins)
        coin = symbol.split('-')[0]
        # aggregate=15 gives 15-minute candles
        url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={coin}&tsym=USD&limit=10&aggregate=15"
        with urllib.request.urlopen(url, timeout=5) as resp:
            res = json.loads(resp.read().decode())
        candles = res['Data']['Data']
        
        if len(candles) < 5:
            return False, "No Data"
        
        last_c = candles[-2] # Completed candle
        # prev_c = candles[-3]
        
        # Trend Check (Higher Highs)
        is_uptrend = last_c['close'] > candles[-5]['close']
        if not is_uptrend:
            return False, "No Uptrend"
        
        # Pullback Logic: Last candle RED
        is_red = last_c['close'] < last_c['open']
        
        # Volume Spike (Relative Vol)
        vols = [c['volumeto'] for c in candles[:-2]]
        if not vols:
            return False, "No Vol Data"
        
        av_vol = statistics.mean(vols)
        rel_vol = last_c['volumeto'] / av_vol if av_vol > 0 else 0
        
        if is_red and rel_vol > 1.5:
             return True, f"Pullback (RelVol {rel_vol:.1f}x)"
             
        return False, "Wait"

    except Exception: # pylint: disable=broad-exception-caught
        return False, "Error"

def warrior_worker():
    """
    Scans watchlist for Warrior Trading setups.
    Runs independently to not block the trading loop.
    """
    if not WARRIOR_MODE:
        return
    
    log("⚔️ Warrior Scanner Active")
    
    while state["running"]:
        try:
            # Audit all watchlist items
            # Rate limit friendly: 1 asset every 2 seconds? 
            # Or batch? CryptoCompare handles ~20 req/sec freely usually, but let's be safe.
            
            suspects = []
            for sym in WATCHLIST:
                # 1. Simple Momentum Filter (Only scan if up > 3% today)
                trend = state["trends"].get(sym, 0)
                if trend > 3.0:
                    found, reason = check_first_pullback(sym)
                    if found:
                        suspects.append((sym, reason))
                        
                        # Add to State
                        with state_lock:
                            state["warrior_signals"][sym] = {
                                "pattern": reason,
                                "timestamp": time.time()
                            }
                            # Notify Strategist indirectly via signals
                
                time.sleep(1.0) # Slow scan to avoid API ban
            
            # Prune old signals (> 5 mins)
            with state_lock:
                now = time.time()
                to_del = [s for s, v in state["warrior_signals"].items() if now - v["timestamp"] > 300]
                for s in to_del:
                    del state["warrior_signals"][s]
            
        except Exception as e: # pylint: disable=broad-exception-caught
            log(f"Warrior Scan Error: {e}")
            time.sleep(10)

# =============================================================================
# MAIN: ENTERPRISE DASHBOARD
# =============================================================================
class Dashboard:
    """
    Main terminal user interface class using Rich.
    Manages the layout and rendering of all panels.
    """
    def make_layout(self):
        """Define the grid layout for the terminal UI."""
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="middle", ratio=1),
            Layout(name="bottom", size=22)
        )
        layout["middle"].split_row(
            Layout(name="left", ratio=3),   # Positions (30%)
            Layout(name="right", ratio=7)   # Market (70%)
        )
        layout["bottom"].split_row(
            Layout(name="logs", ratio=3),   # Logs (30%)
            Layout(name="chat", ratio=4),   # Chat (40%)
            Layout(name="brain", ratio=3)   # Brain (30%)
        )
        return layout

    def get_header(self):
        """Top banner with branding, clock, and net worth."""
        snapshot = get_state_snapshot("positions", "prices", "cash", "news")
        
        invested = sum(
            p['qty'] * snapshot["prices"].get(s, 0) 
            for s, p in snapshot["positions"].items()
        )
        total = snapshot["cash"] + invested
        
        # Grid for perfect alignment
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1, justify="left")
        grid.add_column(ratio=1, justify="center")
        grid.add_column(ratio=1, justify="right")
        
        sent = snapshot["news"]["sentiment"]
        # Center: Clock (Bloomberg Style)
        # Uses the blinking colon trick from the user's reference
        if sent == "BULLISH":
            sent_color = "green"
        elif sent == "BEARISH":
            sent_color = "red"
        elif sent == "JEFF_PARK_BULLISH":
            sent_color = "bold green"
        else:
            sent_color = "yellow"
        
        # Left: Branding
        branding = Text("🚀 Unk Enterprise Terminal v2.1", style="bold cyan")
        
        # Center: Clock (Bloomberg Style)
        # Dave is in New York (Eastern Time). Using system local time.
        clock = datetime.now().strftime("%H:%M:%S").replace(":", "[blink]:[/]")
        center_text = Text.from_markup(f"SYSTEM TIME: {clock} (ET) | SENTIMENT: [{sent_color}]{sent}[/]")
        
        # Right: Net Worth
        nw_style = "bold green" if total >= 100 else "bold white"
        net_worth = Text.from_markup(f"NET WORTH: [{nw_style}]${total:.2f}[/]")
        
        grid.add_row(branding, center_text, net_worth)
        
        return Panel(
            grid, 
            style="white on black", 
            border_style="cyan",
            title="[bold]WHO VISIONS LLC[/]",
            title_align="center"
        )

    def get_positions_tree(self): # pylint: disable=too-many-locals
        """
        Thread-safe positions tree view.
        Uses Rich Tree to show hierarchical pnl/data.
        """
        snapshot = get_state_snapshot("positions", "prices")
        
        root = Tree("[bold cyan]Portfolio[/]")
        
        if not snapshot["positions"]:
            root.add("[dim]No Active Positions[/]")
        else:
            # Sort by PnL (Winners first)
            sorted_pos = []
            for sym, pos in snapshot["positions"].items():
                qty = float(pos['qty'])
                entry = float(pos['entry'])
                curr = snapshot["prices"].get(sym, 0)
                if entry > 0:
                    pnl = (curr - entry) / entry * 100
                else:
                    pnl = 0
                sorted_pos.append((sym, qty, entry, curr, pnl))
            
            # Sort descending by pnl
            sorted_pos.sort(key=lambda x: x[4], reverse=True)

            for sym, qty, entry, curr, pnl in sorted_pos:
                pnl_color = "green" if pnl >= 0 else "red"
                symbol_text = f"[bold]{sym.replace('-USD', '')}[/]"
                
                # Leaf Node
                node_text = f"{symbol_text} : [{pnl_color}]{pnl:+.2f}%[/]"
                asset_node = root.add(node_text)
                
                # Details
                prec = get_precision(sym)
                q_fmt = f"{qty:.{prec}f}" if qty <= 1000 else f"{qty:,.0f}"
                
                table = Table(box=None, show_header=False, pad_edge=False, collapse_padding=True)
                table.add_row("Qty:", q_fmt)
                table.add_row("Entry:", f"${entry:.6f}" if entry < 1 else f"${entry:.2f}")
                table.add_row("Curr:", f"${curr:.6f}" if curr < 1 else f"${curr:.2f}")
                
                asset_node.add(table)
        
        return Panel(root, title="[bold]ACTIVE POSITIONS[/]", border_style="green")

    def get_market_grid(self):
        """Main market overview grid using panel color coding."""
        snapshot = get_state_snapshot("prices", "highs", "targets", "positions")
        
        # 6-Column Grid for 16:9 Widescreen
        grid = Table(expand=True, box=box.SIMPLE, show_header=False, padding=(0, 2))
        
        # 6 Columns
        for _ in range(6):
            grid.add_column(ratio=1, justify="center")
        
        current_row = []
        
        targets = snapshot["targets"]
        
        for sym in WATCHLIST:
            price = snapshot["prices"].get(sym, 0)
            high = snapshot["highs"].get(sym, 0)
            dip = ((price - high) / high * 100) if high > 0 else 0
            
            # Color logic
            color = "dim white"
            if dip <= targets.get("buy", -1.5):
                color = "bold green" # Buy Zone
            if sym in snapshot["positions"]:
                color = "bold cyan"     # Owned
            
            # Formatted Cell: "ASSET \n $Price \n -Dip%"
            p_text = f"${price:.2f}" if price > 1 else f"${price:.6f}"
            cell = f"[{color}][bold]{sym.replace('-USD','')}[/]\n{p_text}\n{dip:+.1f}%[/]"
            
            current_row.append(cell)
            if len(current_row) == 6:
                grid.add_row(*current_row)
                grid.add_row("") # Spacer
                current_row = []
        
        if current_row: # Add leftovers
            while len(current_row) < 6:
                current_row.append("")
            grid.add_row(*current_row)

        return Panel(
            grid, 
            title="[bold]MARKET SCANNER (50 Assets)[/]", 
            border_style="blue"
        )
        
    def get_log_panel(self):
        """Displays rolling logs."""
        # Show last 18 logs
        logs = state["logs"][-18:]
        log_text = "\n".join(logs)
        return Panel(
            Text.from_markup(log_text), 
            title="[bold]SYSTEM LOGS[/]", 
            border_style="dim white"
        )

    def get_chat_panel(self):
        """Displays Chat History."""
        # Show last 15 messages (scrolling)
        # Format: [User]: Msg \n [AI]: Msg
        history = state.get("chat_log", [])[-15:]
        
        
        chat_text = ""
        # 1. History
        for who, msg in history:
            if who == "User":
                chat_text += f"[bold green]User[/]: {msg}\n"
            elif who == "Vertex":
                chat_text += f"[bold blue]Vertex[/]: {msg}\n"
            elif "Gemini" in who:
                chat_text += f"[bold magenta]{who}[/]: {msg}\n"
            else:
                chat_text += f"[dim]{who}: {msg}[/]\n"
        
        # 2. Live Draft Input
        draft = state.get("chat_draft", "")
        cursor = "█" if int(time.time() * 2) % 2 == 0 else " " # Blinking
        chat_text += f"\n[bold cyan]You >[/] {draft}{cursor}"

        return Panel(
            Text.from_markup(chat_text),
            title="[bold]LIVE CHAT (Type anytime)[/]",
            border_style="green"
        )
        
    def get_brain_panel(self): # pylint: disable=too-many-locals
        """
        Renders the 'Brain' panel using Markdown for structured thinking display.
        """
        snapshot = get_state_snapshot("targets", "news", "cash", "positions", "prices")
        with state_lock:
            paused = bool(state.get("buy_paused", False))
            reason = state.get("pause_reason", "")
            exposure = float(state.get("exposure_pct", 0.0))
            limit = float(state.get("exposure_limit", 0.0))
            thought = state.get("thought", "Thinking...")
            persona = state.get("current_persona", "Init")
            w_signals = state.get("warrior_signals", {})


        t = snapshot.get("targets", {})
        score = snapshot["news"].get("score", 0)

        buy_status = "**PAUSED**" if paused else "**ACTIVE**"
        
        # Sentiment Color
        score_color = "green" if score > 0 else "red" if score < 0 else "yellow"

        # Construct Markdown Content
        md_content = f"""
# Mode: {persona}

- **Buy Gate**: {buy_status} ({reason if paused else "OK"})
- **Exposure**: {exposure:.1f}% (Cap {limit:.0f}%)
- **Targets**: Buy {t.get('buy'):.2f}% | Sell {t.get('sell'):.2f}% | Risk {t.get('risk')*100:.0f}%
- **Sentiment**: <span style="color:{score_color}">{score:+d}</span>

---
### Thought Process
*{thought}*
"""
        # Append Warrior Alerts
        if w_signals:
            md_content += "\n### ⚔️ Warrior Signals\n"
            for s, v in w_signals.items():
                md_content += f"- **{s.split('-')[0]}**: {v['pattern']}\n"

        return Panel(
            Markdown(md_content), 
            title="[bold]THE BRAIN[/]", 
            border_style="magenta"
        )

    def generate_layout(self):
        """Generates the full dashboard layout."""
        layout = self.make_layout()
        layout["header"].update(self.get_header())
        layout["left"].update(self.get_positions_tree())  # Changed to Tree
        layout["right"].update(self.get_market_grid())
        layout["logs"].update(self.get_log_panel())
        layout["chat"].update(self.get_chat_panel())
        layout["brain"].update(self.get_brain_panel())
        return layout

# =============================================================================
# RUN LOOP
# =============================================================================

# =============================================================================
# CHAT LOGIC
# =============================================================================
def HandleChatResponse(user_msg):
    """Background AI Worker - FAST MODE using Gemini Flash direct."""
    try:
        with state_lock:
             state["chat_log"].append(("System", "Thinking..."))

        # Log user message to LoreDB (Async)
        safe_run_async(loredb.add_memory(user_msg, source="user", metadata={"type": "chat_input"}))

        # Get trading and news context (cached, fast)
        tm = TradingMemory()
        trading_context = tm.get_context_for_ai()
        
        with state_lock:
            news = state.get("news", {})
            news_sent = news.get("sentiment", "NEUTRAL")
            news_score = news.get("score", 0)
            articles = news.get("articles", [])[:3] # Top 3 headlines
            
        news_text = f"Sentiment: {news_sent} (Score: {news_score})\n"
        if articles:
            news_text += "Top Headlines:\n"
            for a in articles:
                news_text += f"- {a.get('title')} ({a.get('source')})\n"
        
        # 1. Build Multi-Turn History (up to 100 turns)
        contents = []
        
        # Get last 100 messages from state
        with state_lock:
            history = state.get("chat_log", [])[:-1] # Exclude "Thinking..."
            # Keep only last 100 turns
            history = history[-100:]
        
        for who, text in history:
            role = "user" if who == "User" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

        # Use Gemini 3 Flash with LOW thinking for speed
        agent = UnkAiAgent(mode="unk")
        
        # Gemini-style system instruction
        system_instruction = """You are Unk, Dave's crypto trading assistant. Communicate like this:

**STYLE:**
- Be concise and direct. Use bullet points for lists.
- Use markdown formatting: **bold** for emphasis, `code` for values.
- Lead with the answer, then context if needed.
- No fluff, no filler phrases like "I'd be happy to help".

**TRADING TOOLS:**
- You have access to tools: `buy_crypto`, `sell_crypto`, `get_holdings`, `get_price`.
- If Dave asks to buy or sell, use the appropriate tool.
- If he asks what he owns, use `get_holdings`.
- Always confirm the action to Dave after the tool returns.

**CONTEXT:**
- Dave is in New York (Eastern Time).
- Trading context: {ctx}
- Market News: {news}""".format(ctx=trading_context, news=news_text)
        
        # Run with full context
        resp = agent.run(
            contents, # Pass full history
            config={
                "system_instruction": system_instruction,
                "thinking_config": {"thinking_level": "low"}
            },
            tools=TRADING_TOOLS
        )
        
        # Log AI response to LoreDB
        safe_run_async(loredb.add_memory(resp, source="model", metadata={"type": "chat_output"}))

        with state_lock:
            state["chat_log"].pop()  # Remove "Thinking..."
            state["chat_log"].append(("Unk", resp))
            
            # Prune local state to 100 turns
            if len(state["chat_log"]) > 100:
                state["chat_log"] = state["chat_log"][-100:]
                
    except Exception as e:
         with state_lock:
             if state["chat_log"] and state["chat_log"][-1][1] == "Thinking...":
                 state["chat_log"].pop()
             state["chat_log"].append(("System", f"AI Failed: {e}"))

def run():
    """
    Main entry point.
    Starts background threads (News, Trading, Strategy, Warrior)
    and launches the Rich Live Dashboard.
    """
    # Defensive Global Check
    global asyncio, loredb
    
    # Initialize DB (Safe)
    if 'loredb' in globals():
        safe_run_async(loredb.init_db())
    else:
        print("ERROR: loredb not found in global scope!")
        time.sleep(5)
        return
    
    # Start Threads
    t1 = threading.Thread(target=news_worker, daemon=True)
    t2 = threading.Thread(target=trading_worker, daemon=True)
    t3 = threading.Thread(target=strategy_worker, daemon=True)
    t4 = threading.Thread(target=warrior_worker, daemon=True)
    t1.start()
    t2.start()
    t3.start()
    t4.start()

    log("Enterprise System Initialized.")
    state["running"] = True # Force ON in case it was saved as False
    
    # Startup AI Health Check (Test Mode)
    if "--test-mode" in sys.argv:
        log("🧪 TEST MODE: Triggering AI Startup Pulse...")
        test_msg = "Hello Unk, verify your systems are online. What do I own?"
        with state_lock:
            state["chat_log"].append(("User", test_msg))
        threading.Thread(target=HandleChatResponse, args=(test_msg,), daemon=True).start()

    # Start UI
    dash = Dashboard()
    console = Console()
    
    # Input Manager Logic (Improved for Responsiveness)
    def process_live_input():
        # Process ALL keys in the buffer to prevent lag
        while msvcrt.kbhit():
            try:
                char = msvcrt.getch()
                
                # Ctrl+C
                if char == b'\x03':
                    raise KeyboardInterrupt
                
                # Backspace
                if char == b'\x08':
                    with state_lock:
                        state["chat_draft"] = state["chat_draft"][:-1]
                    continue

                # Enter
                if char == b'\r':
                    msg = state.get("chat_draft", "").strip()
                    if msg:
                        with state_lock:
                            state["chat_log"].append(("User", msg))
                            state["chat_draft"] = "" # Clear
                        # Spawn background AI
                        threading.Thread(target=HandleChatResponse, args=(msg,), daemon=True).start()
                    continue

                # Regular Char (Decode safely)
                try:
                    decoded = char.decode('utf-8')
                    if decoded.isprintable():
                        with state_lock:
                            state["chat_draft"] += decoded
                except:
                    pass
            except Exception:
                break

    try:
        print("DEBUG: Starting Live Dashboard context...")
        # Rich Best Practice: 4 FPS (0.25s) is perfectly smooth for text
        while state["running"]:
            # 1. LIVE LOOP
            with Live(
                dash.generate_layout(),
                console=console,
                screen=True,            # Full screen
                auto_refresh=False,     # Manual control
                refresh_per_second=10,  # Higher FPS for smooth typing
                transient=False 
            ) as live:
                while state["running"]:
                    live.update(dash.generate_layout(), refresh=True)
                    
                    # NON-BLOCKING INPUT
                    process_live_input()
                    
                    time.sleep(0.05) # 20 FPS for responsive typing
                    
    except KeyboardInterrupt:
        print("DEBUG: CAUGHT KeyboardInterrupt")
        state["running"] = False
        console.print("\n[bold red]System Halt.[/]")
    except Exception as e: # pylint: disable=broad-exception-caught
        print(f"DEBUG: CAUGHT Exception: {e}")
        state["running"] = False
        console.print_exception()

if __name__ == "__main__":
    run()
