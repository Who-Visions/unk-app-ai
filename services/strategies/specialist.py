from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.betting_types import BettingDecision, BettingRequest

from .base import Strategy

# Add the NBA repo to path to allow imports
NBA_REPO_PATH = Path("downloads/NBA-Machine-Learning-Sports-Betting").resolve()
sys.path.append(str(NBA_REPO_PATH))

try:
    import joblib
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    from src.Utils import Expected_Value
    from src.Utils import Kelly_Criterion as kc
    from src.Utils.tools import (create_todays_games, get_json_data,
                                 get_todays_games_json, to_data_frame)
except ImportError:
    # Handle missing deps gracefully during scaffold
    np = None
    pd = None
    xgb = None


class SpecialistStrategy(Strategy):
    name = "Specialist"

    def __init__(self):
        self.model_dir = NBA_REPO_PATH / "Models" / "XGBoost_Models"
        self.model = None
        self.calibrator = None

    def decide(self, req: BettingRequest, *, config: Dict[str, Any]) -> BettingDecision:
        """
        Orchestrate the 5-step BetOS pipeline for NBA betting.
        """
        # 1. Preprocess
        game_data = self.preprocess(req)

        # 2. Predict
        probs = self.predict(game_data)

        # 3. Price (Calculate EV)
        prices = self.price(probs)

        # 4. Select Bets
        selection = self.select_bets(prices, game_data.get("odds"), config)

        # 4b. Size Stakes
        stake = 0.0
        if selection["action"] == "bet":
            stake = self.size_stakes(req.bankroll, selection)

        # 5. Explain (Unk Persona)
        decision = BettingDecision(
            strategy=self.name,
            action=selection["action"],
            selection=selection["target"],
            stake=stake,
            confidence=selection["confidence"],
            metadata=selection["metadata"]
        )

        explanation = self.explain(decision)
        # Attach explanation to metadata for upstream use if needed,
        # though ReasoningEngine might handle the final voice.
        decision.metadata["unk_explanation"] = explanation

        return decision

    def preprocess(self, req: BettingRequest) -> Dict[str, Any]:
        """
        Load NBA data and prepare features.
        """
        if not pd:
            raise RuntimeError("Pandas/Numpy not installed.")

        # TODO: Implement full data loading from main.py logic
        # For now, we stub the data structure expected by the model
        return {
            "game_id": "LAL_vs_BOS",
            "home": "BOS",
            "away": "LAL",
            "odds": {"BOS": 1.5, "LAL": 2.7},  # Decimal odds
            "features": np.random.rand(1, 20)  # Mock features
        }

    def predict(self, market_state: Dict[str, Any]) -> Dict[str, float]:
        """
        Run XGBoost model.
        """
        if not self.model:
            self._load_model()

        # Mock prediction if no model loaded (or stub)
        # Real logic: self.model.predict(xgb.DMatrix(market_state["features"]))
        return {"home_win": 0.65, "away_win": 0.35}

    def price(self, probabilities: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate EV.
        """
        # EV = (Prob * Odds) - 1
        return probabilities

    def select_bets(self, prices: Dict[str, float], odds: Dict[str, float], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify value.
        """
        home_prob = prices["home_win"]
        home_odds = odds["BOS"]

        ev_home = (home_prob * home_odds) - 1

        if ev_home > 0.05:  # 5% edge threshold
            return {
                "action": "bet",
                "target": "BOS",
                "confidence": home_prob,
                "ev": ev_home,
                "metadata": {"ev": ev_home}
            }

        return {
            "action": "pass",
            "target": None,
            "confidence": 0.0,
            "metadata": {}
        }

    def size_stakes(self, bankroll: float, selection: Dict[str, Any]) -> float:
        """
        Kelly Criterion.
        """
        # Kelly = (bp - q) / b
        # b = odds - 1
        # p = probability
        # q = 1 - p

        if selection.get("action") != "bet":
            return 0.0

        # Simplified half-kelly for safety
        return bankroll * 0.02

    def explain(self, output: BettingDecision) -> str:
        """
        Unk says...
        """
        if output.action == "pass":
            return "Unk says NO. Lines are too tight, nephew. Keep your money in your pocket today."

        return (f"Unk says HANDLE YO BIZNASS. We getting {output.confidence*100:.1f}% on {output.selection}. "
                f"The math says it's +EV. Put a lil' change on it, but don't go crazy.")

    def _load_model(self):
        """Helper to load XGBoost model."""
        # Logic to find latest .json model similar to XGBoost_Runner
        pass
