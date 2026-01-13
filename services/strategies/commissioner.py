from __future__ import annotations

from typing import Any, Dict

from services.betting import BettingDecision, BettingRequest

from .base import Strategy


class CommissionerStrategy(Strategy):
    name = "Commissioner"

    def decide(self, req: BettingRequest, *, config: Dict[str, Any]) -> BettingDecision:
        # TODO: implement using patterns learned from: Crypto-Fantasy-League
        # Expected outputs:
        # action: "bet" | "pass" | "hedge" | "arb"
        # stake: float (respect bankroll and risk constraints)
        # confidence: 0..1
        return BettingDecision(
            strategy=self.name,
            action="pass",
            selection=None,
            stake=0.0,
            confidence=0.0,
            metadata={"source_repo": "Crypto-Fantasy-League", "todo": True},
        )
