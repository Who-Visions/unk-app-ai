from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class BettingRequest:
    strategy: str
    sport: str
    market: str
    bankroll: float
    inputs: Dict[str, Any]


@dataclass
class BettingDecision:
    strategy: str
    action: str  # "bet", "pass", "hedge", "arb"
    selection: Optional[str]
    stake: float
    confidence: float
    metadata: Dict[str, Any]
