from __future__ import annotations

from typing import Any, Dict, Optional

from services.betting_types import BettingDecision, BettingRequest
from services.strategies.registry import STRATEGY_REGISTRY


class BettingService:
    def __init__(self, *, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def decide(self, req: BettingRequest) -> BettingDecision:
        if req.strategy not in STRATEGY_REGISTRY:
            raise ValueError(
                f"Unknown strategy: {req.strategy}. Available: {list(STRATEGY_REGISTRY)}")

        strat = STRATEGY_REGISTRY[req.strategy]()
        return strat.decide(req, config=self.config)
