"""
Trading Service
===============
Main service for coordinating stock trading strategies.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from services.trading_types import TradingDecision, TradingRequest

# Trading strategy registry
TRADING_STRATEGY_REGISTRY: Dict[str, Any] = {}


def _load_trading_strategies():
    """Lazy load trading strategies to avoid circular imports."""
    global TRADING_STRATEGY_REGISTRY
    if not TRADING_STRATEGY_REGISTRY:
        from services.strategies.daytrader import DayTraderStrategy
        from services.strategies.swingtrader import SwingTraderStrategy
        from services.strategies.stockscalper import ScalperStrategy
        from services.strategies.warrior_momentum import WarriorMomentum
        
        TRADING_STRATEGY_REGISTRY = {
            "DayTrader": DayTraderStrategy,
            "SwingTrader": SwingTraderStrategy,
            "Scalper": ScalperStrategy,
            "WarriorMomentum": WarriorMomentum,
        }


class TradingService:
    """
    Service for stock trading analysis and decisions.
    
    Available strategies:
    - DayTrader: Standard day trading (2% risk, 2:1 R/R)
    - SwingTrader: Multi-day holds (3% risk, 3:1 R/R)
    - Scalper: Quick momentum trades (1% risk, 1.5:1 R/R)
    """
    
    def __init__(self, *, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        _load_trading_strategies()
    
    def analyze(self, req: TradingRequest) -> TradingDecision:
        """
        Analyze a stock and get trading recommendation.
        
        Args:
            req: TradingRequest with symbol, strategy, and portfolio info
            
        Returns:
            TradingDecision with action, sizing, and Unk's explanation
        """
        _load_trading_strategies()
        
        if req.strategy not in TRADING_STRATEGY_REGISTRY:
            available = list(TRADING_STRATEGY_REGISTRY.keys())
            raise ValueError(
                f"Unknown strategy: {req.strategy}. Available: {available}"
            )
        
        strat = TRADING_STRATEGY_REGISTRY[req.strategy]()
        return strat.decide(req, config=self.config)
    
    def get_available_strategies(self) -> list:
        """Return list of available trading strategies."""
        _load_trading_strategies()
        return list(TRADING_STRATEGY_REGISTRY.keys())
    
    def get_strategy_info(self) -> Dict[str, Dict[str, Any]]:
        """Return info about each strategy."""
        _load_trading_strategies()
        return {
            "DayTrader": {
                "description": "Standard day trading",
                "risk_per_trade": "2%",
                "reward_ratio": "2:1",
                "hold_period": "1 day",
                "best_for": "Active traders, liquid stocks"
            },
            "SwingTrader": {
                "description": "Multi-day swing trades",
                "risk_per_trade": "3%",
                "reward_ratio": "3:1",
                "hold_period": "3-10 days",
                "best_for": "Part-time traders, trending stocks"
            },
            "Scalper": {
                "description": "Quick momentum trades",
                "risk_per_trade": "1%",
                "reward_ratio": "1.5:1",
                "hold_period": "Minutes to hours",
                "best_for": "High frequency, volatile stocks"
            },
            "WarriorMomentum": {
                "description": "Momentum strategy based on Warrior Trading insights",
                "risk_per_trade": "Dynamic (Goal based)",
                "reward_ratio": "2:1",
                "hold_period": "Minutes",
                "best_for": "Blue Sky Breakouts, Hot Themes"
            }
        }
