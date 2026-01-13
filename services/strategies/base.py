from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from services.betting_types import BettingDecision, BettingRequest


class Strategy(ABC):
    name: str

    @abstractmethod
    def decide(self, req: BettingRequest, *, config: Dict[str, Any]) -> BettingDecision:
        """
        Main entry point for the strategy.
        Should orchestrate the 5-step BetOS pipeline:
        1. preprocess()
        2. predict()
        3. price()
        4. size_stakes() (incorporating risk)
        5. explain() (Unk persona)
        """
        raise NotImplementedError

    def preprocess(self, event_batch: Any) -> Any:
        """Step 1: Data normalization."""
        return event_batch

    def predict(self, market_state: Any) -> Any:
        """Step 2: Probability generation."""
        raise NotImplementedError

    def price(self, probabilities: Any) -> Any:
        """Step 3: Fair price calculation."""
        raise NotImplementedError

    def select_bets(self, prices: Any, odds: Any, constraints: Any) -> Any:
        """Step 4: Opportunity identification."""
        raise NotImplementedError

    def size_stakes(self, bankroll: float, risk_policy: Any) -> float:
        """Step 4b: EV/Kelly sizing."""
        raise NotImplementedError

    def explain(self, output: Any) -> str:
        """
        Step 5: Unk Persona integration.
        Must return advice in the voice of 'Unk':
        - Direct, tough love.
        - "Unk says NO" or "HANDLE YO BIZNASS".
        - Explains WHY not just WHAT.
        """
        return f"Unk says: I ain't got no explanation for {self.name} yet. Stay tuned, nephew."
