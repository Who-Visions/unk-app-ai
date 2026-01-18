"""
Penny Shaver Bot (Robinhood Crypto)
Skims a fixed USD amount per completed scalp cycle and sweeps it into a "holdings" bucket.

Default mode is PAPER trading. Set PAPER_TRADE=false only after you confirm fills and math.

This script assumes you already have:
  from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

You must implement or map these methods on RobinhoodCryptoAPI:
  get_best_bid_ask(symbol) -> tuple[float, float]
  place_limit_buy(symbol, quantity, limit_price, client_order_id) -> str(order_id)
  place_limit_sell(symbol, quantity, limit_price, client_order_id) -> str(order_id)
  get_order(order_id) -> dict(status=..., filled_qty=..., avg_price=...)
  cancel_order(order_id) -> None
"""

from __future__ import annotations

import os
import sys
import time
import uuid
import math
import logging
import random
import csv
import datetime
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Optional, Tuple, List
from dotenv import load_dotenv

# Add project root to path (two levels up from trading/bots)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load Env Vars
load_dotenv()

# Your existing wrapper
from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI

# -------------------- config --------------------

def D(x: str | float | int) -> Decimal:
    return Decimal(str(x))

@dataclass
class Config:
    # Trading universe (Full Robinhood Assets - Validated)
    symbols: List[str] = field(default_factory=lambda: [
        # Majors & L1s
        "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD", 
        "BCH-USD", "DOT-USD", "LTC-USD", "XLM-USD", "XTZ-USD", 
        "ETC-USD", "SUI-USD", "HBAR-USD",

        # DeFi & L2s
        "UNI-USD", "AAVE-USD", "CRV-USD", "COMP-USD", 
        "AERO-USD", "ARB-USD", "OP-USD", "LINK-USD",
        
        # Meme & High Vol
        "DOGE-USD", "SHIB-USD", "PEPE-USD", "WIF-USD", "BONK-USD", 
        "XRP-USD"
    ])

    # Scalp sizing
    notional_usd: Decimal = D("10.00")     # dollars per scalp entry
    skim_usd: Decimal = D("0.01")          # how much profit to siphon into holdings per completed cycle

    # Filters
    max_spread_pct: Decimal = D("0.0250") # 2.5%
    min_mid_price: Decimal = D("0.0001")   # ignore dust priced pairs

    # Execution buffers
    buy_aggression: Decimal = D("0.00")    # 0.00 means try bid, raise slightly if you want faster fills
    extra_edge_pct: Decimal = D("0.0010")  # add 0.10% extra take profit to cover spread and noise

    # Risk rails
    max_open_positions: int = 2
    max_live_orders: int = 6
    order_ttl_sec: int = 25               # cancel and retry if not filled
    cooldown_sec: int = 5

    # Holdings sweep behavior
    holdings_asset: str = "BTC-USD"
    holdings_min_buy_usd: Decimal = D("5.00")  # buy holdings asset once bucket reaches this amount

    # API Limits
    min_loop_sleep_sec: float = 1.0    # 60 RPM max safely under 100 limit

    # Mode
    paper_trade: bool = os.getenv("PAPER_TRADE", "true").lower() == "true"


# -------------------- helpers --------------------

class RateLimiter:
    """Very simple per loop pacing. Extend to token bucket if needed."""
    def __init__(self, min_interval_sec: float):
        self.min_interval_sec = min_interval_sec
        self._last = 0.0

    def sleep_if_needed(self):
        now = time.time()
        dt = now - self._last
        if dt < self.min_interval_sec:
            time.sleep(self.min_interval_sec - dt)
        self._last = time.time()

def quantize_qty(qty: Decimal, step: Decimal = D("0.00000001")) -> Decimal:
    # adjust step to your venue’s min increment if needed
    return (qty / step).to_integral_value(rounding=ROUND_DOWN) * step

def pct(a: Decimal, b: Decimal) -> Decimal:
    # a / b safe
    if b == 0:
        return D("0")
    return a / b

# -------------------- core bot --------------------

@dataclass
class Position:
    symbol: str
    qty: Decimal
    buy_order_id: str
    buy_price: Decimal
    sell_order_id: Optional[str] = None
    opened_ts: float = field(default_factory=time.time)

class PennyShaverBot:
    def __init__(self, api: RobinhoodCryptoAPI, cfg: Config):
        self.api = api
        self.cfg = cfg
        self.log = logging.getLogger("penny_shaver")

        # DEBUG: Inspect Metadata for Execution Reality Checks
        try:
            pairs = self.api.get_trading_pairs("BTC-USD")
            if pairs:
                self.log.info(f"METADATA INSPECTION (BTC-USD): {pairs[0]}")
        except Exception as e:
            self.log.error(f"Failed to inspect metadata: {e}")

        self.positions: Dict[str, Position] = {}
        self.holdings_bucket_usd: Decimal = D("0.00")

        self.limiter = RateLimiter(cfg.min_loop_sleep_sec)

    def run_forever(self):
        # 1. Fetch Constraints / Metadata
        self.asset_metadata = {}
        try:
            self.log.info("Fetching asset metadata from API...")
            raw_pairs = self.api.get_trading_pairs(*self.cfg.symbols)
            for item in raw_pairs:
                sym = item.get("symbol")
                if sym:
                    self.asset_metadata[sym] = item
            self.log.info(f"Loaded constraints for {len(self.asset_metadata)} assets.")
        except Exception as e:
            self.log.error(f"Failed to load asset constraints: {e}")

        self.log.info("Starting PennyShaver | paper_trade=%s | symbols=%s",
                      self.cfg.paper_trade, self.cfg.symbols)

        while True:
            try:
                self.step()
            except KeyboardInterrupt:
                self.log.warning("Interrupted. Exiting.")
                return
            except Exception as e:
                self.log.exception("Loop error: %s", e)
                time.sleep(2.0)

    def step(self):
        self.limiter.sleep_if_needed()

        # manage existing positions first
        self._manage_positions()

        # risk rails
        if len(self.positions) >= self.cfg.max_open_positions:
            return

        # Batch Fetch Quotes (Optimization)
        try:
            # Fetch all symbols in one go
            # Note: 50 symbols is usually fine for one GET request URL length
            self.market_data_cache = self.api.get_best_bid_ask(*self.cfg.symbols)
            # self.log.info(f"Batched fetch complete. Count: {len(self.market_data_cache)}")
        except Exception as e:
            self.log.error(f"Batch fetch failed: {e}")
            self.market_data_cache = {}

        # Select the single best opportunity (Sniper Mode)
        best_sym = self.select_best_opportunity()
        if best_sym:
            # self.log.info(f"Sniper selected: {best_sym}")
            self._maybe_open(best_sym)
            time.sleep(self.cfg.cooldown_sec)
        else:
            # self.log.info("No valid opportunities found.")
            time.sleep(self.cfg.min_loop_sleep_sec)

        # attempt holdings sweep occasionally
        self._maybe_buy_holdings()

    def select_best_opportunity(self) -> Optional[str]:
        """Find the single best asset with the tightest spread."""
        candidates = []
        
        for sym in self.cfg.symbols:
            # cached lookup (fast)
            bid, ask = self._get_bid_ask(sym)
            
            if not self._is_valid_quote(bid, ask):
                continue
                
            mid = (bid + ask) / D("2")
            if mid < self.cfg.min_mid_price:
                continue
                
            spread = ask - bid
            spread_pct = pct(spread, mid)
            
            # 1. Filter by Max Spread
            if spread_pct > self.cfg.max_spread_pct:
                # Opportunity Miner Log
                if self.cfg.enable_miner and time.time() % 10 < 1: # sample 10% for miner to save space
                     if spread_pct < (self.cfg.max_spread_pct * D("2")): # only log "close" misses
                        self._log_candidate(sym, bid, ask, spread_pct, "TOO_WIDE")
                continue

            # 2. Add to candidates list
            candidates.append((sym, spread_pct))
            
            # Opportunity Miner: Log valid ones
            if self.cfg.enable_miner:
                 self._log_candidate(sym, bid, ask, spread_pct, "VALID_SPREAD")

        if not candidates:
            return None
            
        # 3. Sort by spread_pct Ascending (Tightest first)
        candidates.sort(key=lambda x: x[1])
        
        return candidates[0][0]

    def _log_candidate(self, symbol: str, bid: Decimal, ask: Decimal, spread_pct: Decimal, status: str):
        """Log valid trade opportunity to CSV for volume analysis."""
        try:
            file_exists = os.path.isfile(self.cfg.miner_path)
            with open(self.cfg.miner_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["timestamp", "symbol", "bid", "ask", "spread_pct", "status"])
                
                # We log it as 'FOUND' - execution depends on other checks
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    symbol,
                    f"{bid:.8f}",
                    f"{ask:.8f}",
                    f"{spread_pct:.5f}",
                    status
                ])
        except Exception as e:
            self.log.error(f"Miner log failed: {e}")

    def _get_bid_ask(self, symbol: str) -> Tuple[Decimal, Decimal]:
        # Fast Path: Check Batch Cache
        if hasattr(self, 'market_data_cache') and symbol in self.market_data_cache:
            data = self.market_data_cache[symbol]
            return D(data["bid_price"]), D(data["ask_price"])

        # Slow Path: Direct API Call (Fallback)
        try:
            res = self.api.get_best_bid_ask(symbol)
            if symbol in res:
                bid_f = res[symbol].get("bid_price", 0)
                ask_f = res[symbol].get("ask_price", 0)
                return D(bid_f), D(ask_f)
            return D(0), D(0)
        except Exception:
            return D(0), D(0)

    def _is_valid_quote(self, bid: Decimal, ask: Decimal) -> bool:
        return (bid > 0) and (ask > 0) and (ask > bid)

    def _maybe_open(self, symbol: str) -> bool:
        bid, ask = self._get_bid_ask(symbol)

        # Hard guard: prevents division by zero and bogus orders
        if not self._is_valid_quote(bid, ask):
            return False

        mid = (bid + ask) / D("2")
        if mid < self.cfg.min_mid_price:
            return False

        spread = ask - bid
        spread_pct = pct(spread, mid)
        if spread_pct > self.cfg.max_spread_pct:
            if time.time() % 30 < 1:
                self.log.info(
                    "Skipping %s | spread_pct %0.4f > max %0.4f",
                    symbol, float(spread_pct), float(self.cfg.max_spread_pct)
                )
            return False

        qty = quantize_qty(self.cfg.notional_usd / ask)
        if qty <= 0:
            return False

        buy_price = bid + (mid * self.cfg.buy_aggression)

        # Clamp buy price to a sane range
        if buy_price <= 0:
            return False
        if buy_price > ask:
            buy_price = ask

        # --- Execution Reality Check (Metadata Enforcement) ---
        # Default constraints if metadata missing
        min_tick = D("0.00000001")
        min_qty_req = D("0.00000001")
        
        if hasattr(self, 'asset_metadata') and symbol in self.asset_metadata:
            meta = self.asset_metadata[symbol]
            # Try to find price increment
            # Robinhood API often uses 'min_order_price_increment' in 'trading_pairs' endpoint
            if "min_order_price_increment" in meta:
                 min_tick = D(str(meta["min_order_price_increment"]))
            elif "price_increment" in meta:
                 min_tick = D(str(meta["price_increment"]))
            elif "quote_increment" in meta:
                 min_tick = D(str(meta["quote_increment"]))
            
            # Try to find min order quantity
            if "min_order_quantity" in meta:
                 min_qty_req = D(str(meta["min_order_quantity"]))
            elif "min_order_size" in meta:
                 min_qty_req = D(str(meta["min_order_size"]))
            elif "min_trade_amount" in meta:
                 min_qty_req = D(str(meta["min_trade_amount"]))

        # Enforce Price Increment (Fixes "round to nearest 0.00001" error)
        buy_price = quantize_qty(buy_price, min_tick)
        
        if qty < min_qty_req:
            # self.log.info(f"Skipping {symbol}: qty {qty} < min {min_qty_req}")
            return False
        
        # Also enforce quantity STEP (some assets require integer quantities like 1.0)
        # We assume min_qty_req is also the step size, which is true for most crypto
        qty = quantize_qty(qty, min_qty_req)
        
        if qty < min_qty_req:
             return False

        client_id = str(uuid.uuid4())

        if self.cfg.paper_trade:
            buy_order_id = f"PAPER_{client_id}"
            self.positions[symbol] = Position(
                symbol=symbol,
                qty=qty,
                buy_order_id=buy_order_id,
                buy_price=buy_price
            )
            self.log.info(
                "[PAPER] OPEN %s | qty=%s | buy=%s | spread_pct=%0.4f",
                symbol, qty, buy_price, float(spread_pct)
            )
            return True

        buy_order_id = self.api.place_limit_buy(
            symbol=symbol,
            quantity=str(qty),
            limit_price=str(buy_price),
            client_order_id=client_id
        )

        # Only create position if order was actually placed
        if not buy_order_id:
            self.log.warning("Order placement failed for %s, skipping position", symbol)
            return False

        self.positions[symbol] = Position(
            symbol=symbol,
            qty=qty,
            buy_order_id=buy_order_id,
            buy_price=buy_price
        )

        self.log.info(
            "OPEN %s | qty=%s | buy_order=%s | buy=%s | spread_pct=%0.4f",
            symbol, qty, buy_order_id, buy_price, float(spread_pct)
        )
        return True

    def _manage_positions(self):
        for sym in list(self.positions.keys()):
            pos = self.positions[sym]

            if self.cfg.paper_trade:
                # simulate immediate fill then immediate TP fill using current bid/ask
                bid, ask = self._get_bid_ask(sym)
                
                # create take profit target
                target_profit = self.cfg.skim_usd
                required_delta = (target_profit / pos.qty)  # USD per unit
                tp_price = (pos.buy_price + required_delta) * (D("1") + self.cfg.extra_edge_pct)
                tp_price = tp_price.quantize(D("0.00000001"))

                # simulate: if bid >= tp_price, close and siphon
                if bid > 0 and bid >= tp_price:
                    realized = (tp_price - pos.buy_price) * pos.qty
                    siphon = min(realized, self.cfg.skim_usd)
                    self.holdings_bucket_usd += siphon

                    self.log.info("[PAPER] CLOSE %s | buy=%s | sell=%s | qty=%s | pnl=%s | siphon=%s | bucket=%s",
                                  sym, pos.buy_price, tp_price, pos.qty, realized, siphon, self.holdings_bucket_usd)
                    del self.positions[sym]
                continue

            # live mode: check buy, then place sell, then check sell
            if pos.sell_order_id is None:
                od = self.api.get_order_as_dict(pos.buy_order_id)
                status = (od.get("status") or "").lower()
                age = time.time() - pos.opened_ts

                if status in {"filled", "executed"}:
                    filled_qty = D(od.get("filled_qty", od.get("quantity", "0")))
                    avg_price = D(od.get("avg_price", od.get("price", str(pos.buy_price))))
                    pos.qty = filled_qty if filled_qty > 0 else pos.qty
                    pos.buy_price = avg_price

                    # compute take profit
                    required_delta = (self.cfg.skim_usd / pos.qty)
                    tp_price = (pos.buy_price + required_delta) * (D("1") + self.cfg.extra_edge_pct)
                    tp_price = tp_price.quantize(D("0.00000001"))

                    client_id = str(uuid.uuid4())
                    sell_order_id = self.api.place_limit_sell(
                        symbol=sym,
                        quantity=str(pos.qty),
                        limit_price=str(tp_price),
                        client_order_id=client_id
                    )
                    pos.sell_order_id = sell_order_id
                    self.log.info("ARM TP %s | sell_order=%s | tp=%s | qty=%s", sym, sell_order_id, tp_price, pos.qty)

                elif status in {"canceled", "rejected"}:
                    self.log.warning("BUY FAILED %s | status=%s", sym, status)
                    del self.positions[sym]

                elif age > self.cfg.order_ttl_sec:
                    self.api.cancel_order(pos.buy_order_id)
                    self.log.warning("BUY TTL CANCEL %s | order=%s", sym, pos.buy_order_id)
                    del self.positions[sym]

                continue

            # manage sell
            od = self.api.get_order_as_dict(pos.sell_order_id)
            status = (od.get("status") or "").lower()

            if status in {"filled", "executed"}:
                sell_price = D(od.get("avg_price", od.get("price", "0")))
                realized = (sell_price - pos.buy_price) * pos.qty
                siphon = min(realized, self.cfg.skim_usd)
                if siphon > 0:
                    self.holdings_bucket_usd += siphon

                self.log.info("CLOSE %s | buy=%s | sell=%s | qty=%s | pnl=%s | siphon=%s | bucket=%s",
                              sym, pos.buy_price, sell_price, pos.qty, realized, siphon, self.holdings_bucket_usd)
                del self.positions[sym]

            elif status in {"canceled", "rejected"}:
                self.log.warning("SELL FAILED %s | status=%s", sym, status)
                del self.positions[sym]

    def _maybe_buy_holdings(self):
        if self.holdings_bucket_usd < self.cfg.holdings_min_buy_usd:
            return

        # buy holdings asset using bucket amount
        amount = self.holdings_bucket_usd
        self.holdings_bucket_usd = D("0.00")

        bid, ask = self._get_bid_ask(self.cfg.holdings_asset)
        if ask == 0:
            self.holdings_bucket_usd += amount
            return
            
        qty = quantize_qty(amount / ask)

        if qty <= 0:
            self.log.warning("Holdings sweep skipped, qty computed as 0")
            self.holdings_bucket_usd += amount
            return

        if self.cfg.paper_trade:
            self.log.info("[PAPER] HOLDINGS BUY %s | spend=%s | est_price=%s | qty=%s",
                          self.cfg.holdings_asset, amount, ask, qty)
            return

        client_id = str(uuid.uuid4())
        order_id = self.api.place_limit_buy(
            symbol=self.cfg.holdings_asset,
            quantity=str(qty),
            limit_price=str(ask),
            client_order_id=client_id
        )
        self.log.info("HOLDINGS BUY %s | order=%s | spend=%s | price=%s | qty=%s",
                      self.cfg.holdings_asset, order_id, amount, ask, qty)

# -------------------- entry --------------------

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s"
    )

    cfg = Config()

    # Optional: override symbols from env
    env_syms = os.getenv("PENNY_SHAVER_SYMBOLS", "").strip()
    if env_syms:
        cfg.symbols = [s.strip() for s in env_syms.split(",") if s.strip()]

    # Match CLI initialization exactly (lines 174-198 in unk_trader_cli.py)
    API_KEY = os.getenv('ROBINHOOD_API_KEY', '')
    PRIVATE_KEY = os.getenv('ROBINHOOD_PRIVATE_KEY', '')
    api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)
    # Force fetch account number on startup
    acc_info = api.get_account()
    if acc_info:
        logging.info(f"API Initialized. Account: {api.account_number}")

    # Dynamic Asset Discovery (Avoids 400 Errors)
    try:
        logging.info("Fetching official tradable assets from Robinhood API...")
        pairs = api.get_trading_pairs()
        valid_symbols = []
        for p in pairs:
            # Filter for USD pairs that are API tradable
            sym = p.get("symbol")
            # Note: User docs say "Only USD symbols that have is_api_tradable=true"
            if sym and sym.endswith("-USD"):
                # Strict Tradability Check
                is_tradable = p.get("is_api_tradable") is True or p.get("tradability") == "tradable"
                
                if not is_tradable:
                    continue

                # Blacklist Stablecoins (Low Volatility + Market Order Only restrictions)
                if sym in {"USDC-USD", "USDT-USD", "BUSD-USD"}:
                    continue
                valid_symbols.append(sym)
        
        if valid_symbols:
            cfg.symbols = valid_symbols
            logging.info(f"Discovered {len(valid_symbols)} tradable assets: {valid_symbols}")
        else:
            logging.warning("Discovery returned 0 assets, falling back to config.")
            
    except Exception as e:
        logging.error(f"Asset discovery failed: {e}")

    bot = PennyShaverBot(api=api, cfg=cfg)
    bot.run_forever()

if __name__ == "__main__":
    main()
