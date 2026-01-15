"""
Trading Types
=============
Data structures for stock trading operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TradingRequest:
    """Request for trading analysis/decision."""
    strategy: str          # "DayTrader", "SwingTrader", "Scalper"
    symbol: str            # "AAPL", "TSLA", etc.
    market: str            # "stocks", "crypto", "forex"
    portfolio_value: float # Total portfolio to manage risk
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingDecision:
    """Trading decision output from strategy."""
    strategy: str
    action: str            # "buy", "sell", "hold", "watch"
    symbol: str
    position_size: float   # Dollar amount to allocate
    confidence: float      # 0.0 - 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
