"""
Penny Shaver Bot (Snowball + Brain Edition)
===========================================
A high-frequency trading bot that skims micro-profits into a long-term holdings bucket.
Featuring a Rich-powered dashboard, real-time AI strategy insights via Vertex AI,
and a stable, flicker-free terminal interface.

Gold Standard Compliance:
- Pylint score target: 9.0+
- Enterprise Throttling (30 CPM)
- Zero-jitter UI layout
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, List, Optional, Tuple

import msvcrt
from dotenv import load_dotenv
from google.genai import types
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load Env Vars
load_dotenv()

# pylint: disable=import-error, wrong-import-position
from services.llm.reasoning_agent import ReasoningAgent
from services.llm.trading_tools import TRADING_TOOLS
from services.llm.unk_agent import UnkAiAgent
from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI
from trading.core.shared import enterprise_throttle
from trading.integrations.memory import TradingMemory
from trading.analysis.analyzer import TechnicalAnalyzer
from trading.analysis.news_sentiment import get_market_sentiment

# Helper for Decimal
D = Decimal

@dataclass
# pylint: disable=too-many-instance-attributes
class Config:
    """
    Configuration parameters for the Penny Shaver bot.
    Controls asset selection, sizing, triggers, and execution logic.
    """
    # Asset Selection
    symbols: List[str] = field(default_factory=lambda: [
        "BTC-USD", "ETH-USD", "SOL-USD", "PEPE-USD", "DOGE-USD",
        "CRV-USD", "XCN-USD", "LINK-USD", "LTC-USD"
    ])

    # Scalp sizing
    notional_usd: Decimal = D("10.00")     # dollars per scalp entry
    skim_usd: Decimal = D("0.07")          # TARGET PROFIT: $0.07 per trade
    stop_loss_usd: Decimal = D("0.03")     # MAX LOSS: $0.03 per trade

    # Filters
    max_spread_pct: Decimal = D("0.0250")  # 2.5%
    min_mid_price: Decimal = D("0.0001")   # ignore dust

    # Execution buffers
    buy_aggression: Decimal = D("0.00")
    extra_edge_pct: Decimal = D("0.0010")

    # Risk rails
    max_open_positions: int = 2
    order_ttl_sec: int = 25
    cooldown_sec: int = 2

    # Holdings sweep behavior
    holdings_asset: str = "BTC-USD"
    holdings_min_buy_usd: Decimal = D("5.00")

    # Opportunity Miner
    enable_miner: bool = True
    miner_path: str = "opportunities.csv"

    # Mode
    # Senior Tip: Default to FALSE for real-money accountability
    paper_trade: bool = os.getenv("PAPER_TRADE", "false").lower() == "true"


@dataclass
class Position:
    """
    Represents an active trading position.
    Tracks entry price, quantity, and associated order IDs.
    """
    symbol: str
    qty: Decimal
    buy_order_id: str
    buy_price: Decimal
    sell_order_id: Optional[str] = None
    opened_ts: float = field(default_factory=time.time)

# pylint: disable=too-many-instance-attributes, too-many-public-methods
class PennyShaverBot:
    """
    The orchestrator for the Penny Shaver high-frequency strategy.
    Manages the UI dashboard, API interactions, and AI strategy worker.
    """
    def __init__(self, api: RobinhoodCryptoAPI, cfg: Config):
        """
        Initialize the bot with API client and configuration.
        Sets up state, logging, and AI integrations.
        """
        self.api = api
        self.cfg = cfg
        self.log = logging.getLogger("penny_shaver")
        self.running = True
        self.state_lock = threading.RLock()

        self.positions: Dict[str, Position] = {}
        self.holdings_bucket_usd: Decimal = D("0.00")

        self.console = Console()
        # Persistent Layout (Rich Best Practice - create once, update regions)
        self.layout = self._create_layout()
        self.stats = {
            "trades": 0, "wins": 0, "losses": 0,
            "total_pnl": D("0.00"), "last_action": "Initializing...",
            "loop_count": 0, "start_time": time.time(),
            "logs": deque(maxlen=100),
            "chat_metrics": {"received": 0, "processed": 0, "errors": 0}
        }
        self.price_history: Dict[str, List[float]] = {}
        self.market_data_cache: Dict[str, dict] = {}
        self.holdings_cache: List[Any] = []
        self.asset_metadata: Dict[str, Any] = {}

        # Chat & Brain State
        self.chat_log: deque[Tuple[str, str]] = deque(maxlen=500) # Support long-running sessions
        self.chat_draft = ""
        # Trigger initial thinking
        self.thought = "Initializing strategy... Scanning market conditions."
        
        self.chat_queue = deque()  # Queue for chat processing
        self.persona = "Unk Mode"
        self._chat_busy = False
        self.tech_analyzer = TechnicalAnalyzer()  # Technical analysis module
        print("[BOOT] State initialized.", flush=True)
 
        # AI & Memory Integration
        try:
            print("[BOOT] Initializing TradingMemory...", flush=True)
            self.tm = TradingMemory()
            print("[BOOT] Initializing ReasoningAgent...", flush=True)
            self.agent = ReasoningAgent()
            print("[BOOT] Initializing UnkAiAgent...", flush=True)
            self.fallback = UnkAiAgent(mode="unk")
            self.log_entry("AI Systems Online.")
        except RuntimeError as err:
            self.log_entry(f"AI Init Failed (Runtime): {err}")
            self.agent = None
            self.fallback = None
        except ImportError as err:
            self.log_entry(f"AI Init Failed (Missing Deps): {err}")
            self.agent = None
            self.fallback = None
        except Exception as err:  # pylint: disable=broad-exception-caught
            self.log_entry(f"AI Init Partial: {err}")
            self.agent = None
            self.fallback = None

    def log_entry(self, msg: str, *args):
        """
        Add a timestamped entry to the local stats log.
        Used for the 'System Logs' panel in the dashboard.
        Supports lazy formatting like logging.
        """
        if args:
            msg = msg % args
        with self.state_lock:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.stats["logs"].append(f"[{ts}] {msg}")
            self.stats["last_action"] = msg
            if getattr(self, "headless", False):
                print(f"[{ts}] {msg}", flush=True)

    # ================= LAYOUT & UI =================
    def _create_layout(self) -> Layout:
        """Create persistent Layout structure ONCE (Rich Best Practice)."""
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="middle", ratio=1),
            Layout(name="bottom", size=18),
            Layout(name="input_bar", size=3)  # LOCKED input at very bottom
        )
        layout["middle"].split_row(
            Layout(name="left", ratio=30),
            Layout(name="right", ratio=70)
        )
        layout["bottom"].split_row(
            Layout(name="logs", ratio=30),
            Layout(name="chat", ratio=40),
            Layout(name="brain", ratio=30)
        )
        return layout

    def make_layout(self) -> Layout:
        """Compatibility alias for _create_layout."""
        return self._create_layout()

    def get_header(self) -> Panel:
        """Bloomberg Style Header (Gold Pattern)."""
        clock = datetime.datetime.now().strftime("%H:%M:%S").replace(":", "[blink]:[/]")
        mode = "[bold green]LIVE[/]" if not self.cfg.paper_trade else "[bold yellow]PAPER[/]"

        grid = Table.grid(expand=True)
        grid.add_column(ratio=1, justify="left")
        grid.add_column(ratio=1, justify="center")
        grid.add_column(ratio=1, justify="right")
        
        branding = Text("🚀 WHO VISIONS SNOWBALL v3.1", style="bold cyan")
        center_text = Text.from_markup(f"{clock} | Mode: {mode}")

        # Realized PNL from closed trades
        realized = float(self.stats['total_pnl'])

        # Unrealized PNL from open positions
        unrealized = 0.0
        for sym, pos in self.positions.items():
            curr = float(self.market_data_cache.get(sym, {}).get("ask_price", 0))
            if curr > 0:
                unrealized += (curr - float(pos.buy_price)) * float(pos.qty)

        total_pnl = realized + unrealized
        pnl_text = Text.from_markup(f"NET PNL: [{'bold green' if total_pnl>=0 else 'bold red'}]${total_pnl:.2f}[/]")

        grid.add_row(branding, center_text, pnl_text)
        return Panel(grid, style="white on black", border_style="cyan")

    def get_market_grid(self) -> Panel:
        """
        Generate the Market Scanner panel showing symbol bid/ask/spread.
        Forces a fixed size (15 slots) to prevent layout jumping on refresh.
        """
        grid = Table(expand=True, box=box.SIMPLE, show_header=False)
        for _ in range(5):
            grid.add_column(ratio=1, justify="center")

        markets = []
        for sym, data in self.market_data_cache.items():
            bid = float(data.get("bid_price", 0))
            ask = float(data.get("ask_price", 0))
            if bid > 0 and ask > 0:
                mid = (bid + ask) / 2
                spread = (ask - bid) / bid * 100
                markets.append((sym, mid, spread))

        markets.sort(key=lambda x: x[2])
        
        # Force 15 slots (3 rows of 5) to prevent jumping
        slots = []
        for i in range(15):
            if i < len(markets):
                sym, mid, spread = markets[i]
                color = "cyan" if sym in self.positions else "white"
                sprd_color = "green" if spread < 0.5 else "yellow"
                p_text = f"${mid:.8f}" if mid < 0.01 else f"${mid:.4f}" if mid < 1 else f"${mid:.2f}"
                slots.append(f"[{color}][bold]{sym.replace('-USD','')}[/]\n{p_text}\n[{sprd_color}]{spread:.2f}%[/]")
            else:
                slots.append("[dim]---\n---\n---[/]")
        
        for i in range(0, 15, 5):
            grid.add_row(*slots[i:i+5])
            
        return Panel(grid, title="[bold]MARKET SCANNER[/]", border_style="blue")

    def get_positions_tree(self) -> Panel:
        """Hierarchy with fixed vertical footprint (Gold Pattern)."""
        root = Tree("[bold cyan]Portfolio[/]")

        # Senior Tip: Dynamic precision based on price scale
        def fmt_p(val):
            v = float(val)
            if v < 0.0001:
                return f"${v:.8f}"
            if v < 1:
                return f"${v:.4f}"
            return f"${v:.2f}"

        # 1. CORE ROBINHOOD HOLDINGS
        if self.holdings_cache:
            real_node = root.add("[bold green]LIVE ACCOUNT ASSETS[/]")
            any_real = False
            for h in self.holdings_cache:
                if h.total_quantity > 0:
                    any_real = True
                    sym = f"{h.asset_code}-USD"
                    curr = float(self.market_data_cache.get(sym, {}).get("ask_price", 0))
                    entry = h.average_buy_price if h.average_buy_price else 0.0
                    
                    # Calculate P&L if we have both entry and current price
                    pnl_pct = 0.0
                    if entry > 0 and curr > 0:
                        pnl_pct = ((curr - entry) / entry) * 100
                    
                    pnl_color = "green" if pnl_pct >= 0 else "red"
                    h_node = real_node.add(f"[bold]{h.asset_code}[/] [{pnl_color}]{pnl_pct:+.2f}%[/]")
                    
                    table = Table(box=None, show_header=False, pad_edge=False, collapse_padding=True)
                    table.add_row("Qty:", f"{h.total_quantity:.6f}")
                    if entry > 0:
                        table.add_row("Entry:", fmt_p(entry))
                    if curr > 0:
                        table.add_row("Price:", fmt_p(curr))
                        val = h.total_quantity * curr
                        table.add_row("Value:", f"${val:.2f}")
                    h_node.add(table)
            if not any_real:
                real_node.add("[dim]No positions in account.[/]")

        # 2. BOT OVERLAY (Orders/Tactics)
        if self.positions:
            tactical_node = root.add(f"[bold yellow]BOT { 'SIMULATED' if self.cfg.paper_trade else 'TACTICAL' } ACTIONS[/]")
            for sym, pos in self.positions.items():
                curr = float(self.market_data_cache.get(sym, {}).get("ask_price", 0))
                pnl = ((curr - float(pos.buy_price)) / float(pos.buy_price) * 100) if curr > 0 else 0
                node = tactical_node.add(f"[bold]{sym.replace('-USD','')}[/] : [{ 'green' if pnl>=0 else 'red' }]{pnl:+.2f}%[/]")

                table = Table(box=None, show_header=False, pad_edge=False, collapse_padding=True)
                table.add_row("Entry:", fmt_p(pos.buy_price))
                table.add_row("Curr:", fmt_p(curr))
                node.add(table)

        if not self.positions and not self.holdings_cache:
            root.add("[dim]Syncing with Robinhood API...[/]")

        return Panel(root, title="[bold]ACCOUNT PERFORMANCE[/]", border_style="green", height=15)

    def get_chat_panel(self) -> Panel:
        """Displays Chat History ONLY (no input - that's in get_input_panel)."""
        # Calculate available lines (15 total - 2 border = ~13 lines for history)
        available_lines = 13
        
        # 1. Flatten history into individual lines
        lines = []
        history = list(self.chat_log)
        for who, msg in history:
            color = "green" if who == "User" else "blue" if who == "Unk" else "magenta"
            safe_msg = escape(msg)
            # Break message into lines
            msg_lines = safe_msg.split("\n")
            for i, line in enumerate(msg_lines):
                prefix = f"[bold {color}]{who}[/]: " if i == 0 else " " * (len(who) + 3)
                lines.append(f"{prefix}{line}")

        # 2. Take only the last 'available_lines'
        lines = lines[-available_lines:]
        
        # 3. Padding to keep height stable
        padding = [""] * (available_lines - len(lines))
        chat_text = "\n".join(padding + lines)
        
        return Panel(Text.from_markup(chat_text), title="[bold]LIVE CHAT[/]", border_style="yellow", height=15)

    def get_input_panel(self) -> Panel:
        """LOCKED input panel at the bottom of the screen.
        
        This is in a dedicated Layout region to prevent flickering.
        Uses Panel.fit for minimal visual disruption.
        """
        cursor = "█" if int(time.time()*2)%2==0 else " "
        safe_draft = escape(self.chat_draft)
        input_text = f"[bold cyan]You >[/] {safe_draft}{cursor}"
        return Panel(Text.from_markup(input_text), border_style="bold gold1", title="[bold]INPUT[/]")

    def get_brain_panel(self) -> Panel:
        """Markdown reflection with technical analysis (Enhanced Gold Pattern)."""
        # Get technical analysis for primary position
        rsi_display = "N/A"
        fibo_display = "N/A"
        sentiment_display = "NEUTRAL"
        signal_display = "HOLD"
        
        try:
            # Find primary symbol from holdings
            primary_sym = "SOL-USD"  # Default fallback
            if self.holdings_cache:
                for h in self.holdings_cache:
                    if h.total_quantity > 0:
                        primary_sym = f"{h.asset_code}-USD"
                        break
            
            # Feed current price to analyzer
            if primary_sym in self.market_data_cache:
                price = float(self.market_data_cache[primary_sym].get("ask_price", 0))
                if price > 0:
                    self.tech_analyzer.add_price(primary_sym, price)
            
            # Get analysis if we have enough history
            history = self.tech_analyzer.price_history.get(primary_sym, [])
            if len(history) >= 14:
                analysis = self.tech_analyzer.analyze(primary_sym, history)
                rsi_display = f"{analysis.rsi:.1f}"
                if analysis.nearest_support > 0:
                    fibo_display = f"S:${analysis.nearest_support:.2f}"
                sentiment_display = analysis.sentiment
                signal_display = analysis.overall_signal
        except Exception:
            pass  # Fail silently, show defaults
        
        # Get news sentiment
        try:
            news = get_market_sentiment()
            sentiment_display = news.get("sentiment", "NEUTRAL")
        except Exception:
            pass
        
        # Color-code sentiment
        sent_color = "green" if "BULLISH" in sentiment_display else "red" if "BEARISH" in sentiment_display else "yellow"
        signal_color = "green" if "BUY" in signal_display else "red" if "SELL" in signal_display else "yellow"
        
        md_content = f"""
# {self.persona}
---
### Technical Analysis
- **RSI (14)**: {rsi_display}
- **Fibonacci**: {fibo_display}
- **Sentiment**: [{sent_color}]{sentiment_display}[/]
- **Signal**: [{signal_color}]{signal_display}[/]
---
### Strategy Reflection
*{self.thought}*

- **Bucket**: ${self.holdings_bucket_usd:.2f}
- **Win/Loss**: {self.stats['wins']}/{self.stats['losses']}
"""
        return Panel(Markdown(md_content), border_style="magenta", title="[bold]THE BRAIN[/]", height=18)

    def get_log_panel(self) -> Panel:
        """Displays rolling logs (Gold Pattern)."""
        # Show exactly last 15 lines for height stability
        logs = list(self.stats["logs"])[-15:]

        # Pad with empty lines if needed
        padding_needed = 15 - len(logs)
        logs = ([""] * padding_needed) + logs

        log_text = "\n".join(logs)
        return Panel(Text.from_markup(log_text), border_style="dim white",
                     title="[bold]SYSTEM LOGS[/]", height=18)

    def update_dashboard(self) -> None:
        """Update individual regions of persistent layout (Rich Best Practice).
        
        This is the correct pattern from Rich docs - update regions instead of
        regenerating the entire layout. Prevents input flickering.
        """
        self.layout["header"].update(self.get_header())
        self.layout["left"].update(self.get_positions_tree())
        self.layout["right"].update(self.get_market_grid())
        self.layout["logs"].update(self.get_log_panel())
        self.layout["chat"].update(self.get_chat_panel())
        self.layout["brain"].update(self.get_brain_panel())
        self.layout["input_bar"].update(self.get_input_panel())  # LOCKED input region

    def generate_dashboard(self) -> Layout:
        """Compatibility method - updates and returns the persistent layout."""
        self.update_dashboard()
        return self.layout

    # ================= WORKERS =================
    def strategy_worker(self):
        """
        Background worker that periodically updates the AI's internal strategy thought.
        Refreshes every 60 seconds.
        """
        while self.running:
            if not self.agent:
                break
            try:
                if self.agent.is_thinking:
                    time.sleep(1)
                    continue

                # Get TA for primary asset
                ta_context = {}
                try:
                    # Find most active asset or default to SOL
                    active_sym = "SOL-USD"
                    if self.holdings_cache:
                        msg_asset = max(self.holdings_cache, key=lambda h: float(h.total_quantity) * float(self.market_data_cache.get(f"{h.asset_code}-USD", {}).get("ask_price", 0)))
                        active_sym = f"{msg_asset.asset_code}-USD"
                    
                    history = self.tech_analyzer.price_history.get(active_sym, [])
                    if len(history) >= 14:
                        an = self.tech_analyzer.analyze(active_sym, history)
                        ta_context = {
                            "symbol": active_sym,
                            "rsi": round(an.rsi, 1),
                            "signal": an.overall_signal,
                            "sentiment": an.sentiment
                        }
                except Exception:
                    pass

                ctx = {
                    "bucket_usd": float(self.holdings_bucket_usd),
                    "wins": self.stats["wins"],
                    "losses": self.stats["losses"],
                    "pnl": float(self.stats["total_pnl"]),
                    "technical_analysis": ta_context
                }
                res = self.agent.query(f"Quick status check: {json.dumps(ctx)}. One sentence advice?")
                with self.state_lock:
                    self.thought = res
            except Exception as err:  # pylint: disable=broad-exception-caught
                self.log.error("Strategy Worker Error: %s", err)
            time.sleep(60)

    def chat_worker(self):
        """
        Dedicated background worker for AI chat interactions.
        Uses a queue to ensure sequential processing and thread safety.
        """
        while self.running:
            msg = None
            with self.state_lock:
                if self.chat_queue:
                    msg = self.chat_queue.popleft()
            
            if not msg:
                time.sleep(0.1)
                continue

            self._chat_busy = True
            # Senior Tech: Use a unique marker for the thinking status to avoid pops from the wrong turn
            turn_id = f"think_{uuid.uuid4().hex[:4]}"
            with self.state_lock:
                self.chat_log.append(("System", f"Thinking... ({turn_id})"))

            try:
                self.stats["chat_metrics"]["received"] += 1
                self.log.debug("Processing chat message: %s", msg[:30])
                
                # 1. Get Context
                trading_context = self.tm.get_context_for_ai()

                # 2. History (Enterprise Tip: Support 200+ turns if context allows)
                contents = []
                with self.state_lock:
                    # Filter out system logs to keep memory clean
                    clean_history = [
                        (who, text) for who, text in self.chat_log
                        if who in ("User", "Unk")
                    ]
                    # Dynamically scale history (last 100 turns for deep context)
                    for who, text in clean_history[-100:]:
                        role = "user" if who == "User" else "model"
                        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

                # 3. Instruction Set (Master Time Synchronization)
                now_ny = datetime.datetime.now()
                now_utc = datetime.datetime.utcnow()
                
                # Dynamic Technical Injection
                tech_reality = ""
                try:
                    # Find active asset
                    active_sym = "SOL-USD"
                    if self.holdings_cache:
                        msg_asset = max(self.holdings_cache, key=lambda h: float(h.total_quantity) * float(self.market_data_cache.get(f"{h.asset_code}-USD", {}).get("ask_price", 0)))
                        active_sym = f"{msg_asset.asset_code}-USD"
                    
                    history = self.tech_analyzer.price_history.get(active_sym, [])
                    if len(history) >= 14:
                        an = self.tech_analyzer.analyze(active_sym, history)
                        tech_reality = f"""
**TECHNICAL REALITY ({active_sym}):**
- **Price**: ${history[-1]:.4f}
- **RSI**: {an.rsi:.1f} ({an.rsi_status})
- **Trend**: {an.trend_status}
- **Signal**: {an.overall_signal}
- **Sentiment**: {an.sentiment}
"""
                except Exception:
                    pass

                instr = "You are Unk, a 35-65 year old Urban Uncle crypto expert. WAR MODE (Real Money)."
                system_instruction = f"""{instr}
**ABSOLUTE TIME SYNC (MANDATORY):**
- **DAVE'S NY TIME:** {now_ny.strftime('%Y-%m-%d %I:%M:%S %p')}
- **SYSTEM UTC TIME:** {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **URGENT:** All 'RECENT TRADES' in context use UTC. 
- You MUST anchor your response to {now_ny.strftime('%I:%M %p')}. If Dave asks for the time, report the NY time.

{tech_reality}

**STYLE:**
- Be the "Old Head". Concise, direct, alpha-first.
- Roasts are fine but protect the principal.
- Use markdown. Bullet points for metrics.

**TRADING STATUS:** {'PAPER' if self.cfg.paper_trade else 'LIVE (REAL MONEY)'}
- Assets: {[h.asset_code for h in self.holdings_cache if h.total_quantity > 0]}
"""
                system_instruction += f"\n\n**CONTEXT:**\n- Dave is in NY.\n- Trading context: {trading_context}"

                # 4. Agentic Execution
                # Senior Tip: Use a reasonable timeout to prevent hangs
                resp = self.fallback.run(
                    contents,
                    config={
                        "system_instruction": system_instruction,
                        "thinking_config": {"thinking_level": "low"}
                    },
                    tools=TRADING_TOOLS
                )

                with self.state_lock:
                    # Atomic Pop: Find and remove ONLY our specific thinking marker
                    for i in range(len(self.chat_log) - 1, -1, -1):
                        if self.chat_log[i][0] == "System" and turn_id in self.chat_log[i][1]:
                            del self.chat_log[i]
                            break
                    self.chat_log.append(("Unk", resp))
                    self.log_entry("AI: Responded to Dave.")
                    self.stats["chat_metrics"]["processed"] += 1

            except Exception as err:  # pylint: disable=broad-exception-caught
                with self.state_lock:
                    # Atomic Pop cleanup on failure
                    for i in range(len(self.chat_log) - 1, -1, -1):
                        if self.chat_log[i][0] == "System" and turn_id in self.chat_log[i][1]:
                            del self.chat_log[i]
                            break
                    err_msg = str(err).replace("\n", " ")
                    self.chat_log.append(("System", f"Worker Error: {err_msg[:60]}"))
                    self.log_entry("Chat Worker Fail: %s", err)
                    self.stats["chat_metrics"]["errors"] += 1
            finally:
                self._chat_busy = False
                time.sleep(0.1) # Small rest before next queue item

    def handle_chat_response(self, msg: str):
        """Enqueue a message for the chat worker."""
        with self.state_lock:
            self.chat_queue.append(msg)

    def process_live_input(self):
        """
        Poll for keyboard input via msvcrt.
        Handles backspace, enter (send to AI), and printable characters.
        """
        while msvcrt.kbhit():
            try:
                char = msvcrt.getch()
                if char == b'\x03':  # Ctrl-C
                    self.running = False
                elif char == b'\x08':  # Backspace
                    with self.state_lock:
                        self.chat_draft = self.chat_draft[:-1]
                elif char in (b'\r', b'\n'):  # Handle all Enter variants
                    with self.state_lock:
                        msg = self.chat_draft.strip()
                        if msg:
                            # Senior Tip: Log input exactly as Dave sees it
                            self.log_entry("Input Received: %s", msg)
                            self.chat_log.append(("User", msg))
                            self.chat_draft = ""
                            self.handle_chat_response(msg)
                else:
                    try:
                        # Senior Tip: Log hex for non-printable keys to catch Windows control chars
                        if char.decode('utf-8').isprintable():
                            with self.state_lock:
                                self.chat_draft += char.decode('utf-8')
                        else:
                            self.log.debug("Control Key: %s", char.hex())
                    except UnicodeDecodeError:
                        self.log.debug("Raw Key: %s", char.hex())
            except EOFError:
                break
            except Exception as err:  # pylint: disable=broad-exception-caught
                self.log_entry("Input Error: %s", err)
                # Don't break cycle, just skip problematic read
                continue

    # ================= STRESS TEST =================
    def run_stress_test(self, count: int = 5):
        """Simulate a rapid-fire multi-turn conversation."""
        self.log_entry(f"!!! STRESS TEST STARTING: {count} messages !!!")
        questions = [
            "Hi Unk, you awake?",
            "What's the current time in NY?",
            "How many assets are we scanning right now?",
            "Give me a quick status check on AERO.",
            "Thanks Unk, keep it 100."
        ]
        
        for i in range(min(count, len(questions))):
            q = questions[i]
            self.log_entry(f"STRESS INJECT ({i+1}/{count}): {q}")
            with self.state_lock:
                self.chat_log.append(("User", q))
                self.handle_chat_response(q)
            # Wait for response before next one
            timeout = time.time() + 30
            while self._chat_busy and time.time() < timeout:
                time.sleep(0.1)
            time.sleep(2) # Breath between messages
        
        self.log_entry("!!! STRESS TEST COMPLETE !!!")

    # ================= CORE LOGIC =================
    def run_forever(self):
        """
        Main operation loop for the bot.
        """
        print("[BOOT] run_forever entered.", flush=True)
        self.log_entry("Bot Engine Initializing...")
        try:
            self.log_entry("Fetching real Robinhood holdings...")
            self.holdings_cache = self.api.get_holdings()

            self.log_entry("Fetching constraints for assets...")
            # Fetch all pairs and filter by status
            pairs = self.api.get_trading_pairs()
            self.asset_metadata = {
                p["symbol"]: p for p in pairs
                if p["symbol"] in self.cfg.symbols
            }
            # Update symbols to only include those that are actually tradable right now
            tradable_symbols = {
                p["symbol"] for p in pairs
                if p.get("status") == "tradable"
            }
            # Filter watchlist to only what is tradable
            self.cfg.symbols = [
                s for s in self.cfg.symbols if s in tradable_symbols
            ]
            
            self.log_entry("Cleaning up open orders...")
            for order in self.api.get_orders():
                if order.state == "open":
                    self.api.cancel_order(order.order_id)
            self.log_entry("Fetching holdings...")
            self.holdings_cache = self.api.get_holdings()
        except (RuntimeError, ValueError, KeyError) as err:
            self.log_entry("Startup Warning: %s", err)

        self.log_entry("Starting background workers...")
        threading.Thread(target=self.strategy_worker, daemon=True).start()
        threading.Thread(target=self.chat_worker, daemon=True).start()

        if getattr(self, "headless", False):
            self.log_entry("Running in HEADLESS mode (UI Disabled)")
            while self.running:
                try:
                    # Logic tick
                    if self.stats["loop_count"] % 20 == 0:
                        self.step()
                    self.stats["loop_count"] += 1
                    time.sleep(0.05)
                except KeyboardInterrupt:
                    break
            return

        with Live(
            self.layout,  # Use persistent layout directly
            console=self.console,
            screen=True,
            auto_refresh=True,
            refresh_per_second=4,
            redirect_stdout=True,  # Capture stdout to prevent bleeding
            redirect_stderr=True,  # Capture stderr to prevent bleeding
        ) as live:
            while self.running:
                try:
                    # 1. Non-blocking Input (highest priority - check every loop)
                    self.process_live_input()

                    # 2. Update layout regions
                    self.update_dashboard()

                    # 3. Step logic (Logic tick)
                    if self.stats["loop_count"] % 20 == 0:
                        self.step()

                    self.stats["loop_count"] += 1
                    time.sleep(0.05)  # Fast input polling
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    # Prevent one UI error from crashing the whole bot
                    # Log to file for debugging since TUI truncates
                    with open("ui_debug.log", "a") as f:
                        f.write(f"TS: {time.time()} - Error in update_dashboard: {e}\n")
                        traceback.print_exc(file=f)
                    self.log_entry(f"UI Error: {str(e)[:20]}")
                    time.sleep(1)

    def step(self):
        """
        Execute one tactical trading step.
        Includes updating holdings cache, managing positions, and scanning for new opportunities.
        """
        if self.stats["loop_count"] % 20 == 0:
            try:
                self.holdings_cache = self.api.get_holdings()
            except Exception as err:  # pylint: disable=broad-exception-caught
                self.log.debug("Holdings update skipped: %s", err)

        self._manage_positions()

        if len(self.positions) < self.cfg.max_open_positions:
            try:
                enterprise_throttle.acquire()  # Gold Throttling
                self.market_data_cache = self.api.get_best_bid_ask(*self.cfg.symbols)
                best = self._select_best()
                if best:
                    self._maybe_open(best)
            except Exception as err:  # pylint: disable=broad-exception-caught
                self.log_entry("Scan failed: %s", err)

        # Periodic update log
        if self.stats["loop_count"] % 60 == 0:
            self.log_entry("Active. Scanned %d assets.", len(self.market_data_cache))

        self._maybe_buy_holdings()

    def _select_best(self) -> Optional[str]:
        """
        Scan market data cache to find the asset with the lowest spread.
        Filters based on max_spread_pct.
        """
        best_sym, best_sprd = None, D("999")
        for sym in self.cfg.symbols:
            bid, ask = self._get_bid_ask(sym)
            if bid <= 0 or ask <= 0:
                continue
            spread = (ask - bid) / bid * 100
            if spread < self.cfg.max_spread_pct * 100 and spread < best_sprd:
                best_sym, best_sprd = sym, spread
        return best_sym

    def _get_bid_ask(self, symbol: str) -> Tuple[Decimal, Decimal]:
        """
        Extract bid and ask prices from the market data cache for a symbol.
        Returns a tuple of (bid, ask) as Decimals.
        """
        data = self.market_data_cache.get(symbol, {})
        return D(str(data.get("bid_price", 0))), D(str(data.get("ask_price", 0)))

    def _maybe_open(self, symbol: str):
        """
        Evaluate and potentially open a new position for a given symbol.
        Calculates quantity based on notional setting and executes buy.
        """
        bid, ask = self._get_bid_ask(symbol)
        qty = (self.cfg.notional_usd / ask).quantize(D("0.000001"), ROUND_DOWN)
        if self.cfg.paper_trade:
            self.positions[symbol] = Position(
                symbol,
                qty,
                f"P_{uuid.uuid4().hex[:4]}",
                bid
            )
            self.log_entry(f"PAPER: OPEN {symbol} @ {bid}")
            return
        oid = self.api.place_limit_buy(symbol, str(qty), str(bid), str(uuid.uuid4()))
        if oid:
            self.positions[symbol] = Position(symbol, qty, oid, bid)
            self.log_entry(f"OPEN {symbol} @ {bid}")

    def _manage_positions(self):
        """
        Monitor and manage existing open positions.
        Handles taking profit (skipping to bucket) and stop loss logic.
        """
        for sym, pos in list(self.positions.items()):
            if self.cfg.paper_trade:
                bid, _ = self._get_bid_ask(sym)
                target = pos.buy_price + (self.cfg.skim_usd / pos.qty)
                if bid >= target:
                    self.holdings_bucket_usd += self.cfg.skim_usd
                    self.stats["wins"] += 1
                    self.stats["total_pnl"] += (target - pos.buy_price) * pos.qty
                    del self.positions[sym]
                elif (bid - pos.buy_price) * pos.qty <= -self.cfg.stop_loss_usd:
                    self.stats["losses"] += 1
                    del self.positions[sym]
                continue

            order_dict = self.api.get_order_as_dict(pos.sell_order_id or pos.buy_order_id)
            status = order_dict.get("status", "").lower()
            if pos.sell_order_id is None:
                if status in {"filled", "executed"}:
                    take_profit_price = (
                        pos.buy_price + (self.cfg.skim_usd / pos.qty)
                    ).quantize(D("0.00000001"))
                    pos.sell_order_id = self.api.place_limit_sell(
                        sym,
                        str(pos.qty),
                        str(take_profit_price),
                        str(uuid.uuid4())
                    )
                    self.log_entry(f"BUY FILL {sym}. SELL @ {take_profit_price}")
                elif time.time() - pos.opened_ts > self.cfg.order_ttl_sec:
                    self.api.cancel_order(pos.buy_order_id)
                    del self.positions[sym]
            else:
                if status in {"filled", "executed"}:
                    self.holdings_bucket_usd += self.cfg.skim_usd
                    self.stats["wins"] += 1
                    del self.positions[sym]
                else:
                    bid, _ = self._get_bid_ask(sym)
                    if (bid - pos.buy_price) * pos.qty <= -self.cfg.stop_loss_usd:
                        self.api.cancel_order(pos.sell_order_id)
                        self.api.place_market_order(
                            sym,
                            "sell",
                            asset_quantity=float(pos.qty)
                        )
                        self.stats["losses"] += 1
                        del self.positions[sym]

    def _maybe_buy_holdings(self):
        """
        Check if the accumulated holdings bucket exceeds the minimum buy amount.
        If so, executes a buy for the designated holdings asset (BTC-USD).
        """
        if self.holdings_bucket_usd < self.cfg.holdings_min_buy_usd:
            return
        amt = self.holdings_bucket_usd
        self.holdings_bucket_usd = D("0")
        _, ask = self._get_bid_ask(self.cfg.holdings_asset)
        if ask > 0 and not self.cfg.paper_trade:
            qty = (amt / ask).quantize(D("0.000001"), ROUND_DOWN)
            self.api.place_limit_buy(
                self.cfg.holdings_asset,
                str(qty),
                str(ask),
                str(uuid.uuid4())
            )

def main():
    """
    Application entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Penny Shaver Bot")
    parser.add_argument("--stress-test", action="store_true", help="Run automated chat stress test")
    parser.add_argument("--headless", action="store_true", help="Run without UI for testing")
    args = parser.parse_args()

    api_key = os.getenv('ROBINHOOD_API_KEY', '')
    priv_key = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
    api = RobinhoodCryptoAPI(api_key=api_key, private_key_base64=priv_key)

    cfg = Config()
    try:
        # Senior Tip: Only fetch pairs once at boot to save calls
        pairs = api.get_trading_pairs()
        valid = [
            p["symbol"] for p in pairs
            if p["symbol"].endswith("-USD") and p.get("status") == "tradable"
        ]
        valid = [v for v in valid if v not in {"USDC-USD", "USDT-USD", "BUSD-USD"}]
        if valid:
            cfg.symbols = valid[:15]  # Match grid size
    except Exception as err:  # pylint: disable=broad-exception-caught
        logging.error("Main init warning: %s", err)

    bot = PennyShaverBot(api, cfg)
    bot.headless = args.headless
    
    if args.stress_test:
        # Run stress test in background thread while bot is running
        threading.Thread(target=bot.run_stress_test, daemon=True).start()
        
    bot.run_forever()


if __name__ == "__main__":
    main()
