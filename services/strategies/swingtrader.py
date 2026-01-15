"""
SwingTrader Strategy
====================
Medium-term swing trading strategy using technical analysis.
Looks for multi-day setups with higher reward potential.
"""
from __future__ import annotations

from typing import Any, Dict

from services.trading_types import TradingDecision, TradingRequest

try:
    from .base import Strategy
except ImportError:
    from base import Strategy

import logging
logger = logging.getLogger(__name__)

try:
    from skills.stock_skill import (
        get_combined_analysis,
        YFINANCE_AVAILABLE,
        STOCKSTATS_AVAILABLE
    )
except ImportError:
    YFINANCE_AVAILABLE = False
    STOCKSTATS_AVAILABLE = False
    get_combined_analysis = None


class SwingTraderStrategy(Strategy):
    """
    Swing trading strategy for multi-day holds.
    
    Uses technical indicators for entry/exit:
    - RSI for oversold/overbought conditions
    - MACD for trend confirmation
    - Bollinger Bands for volatility
    - Support/resistance from recent highs/lows
    """
    name = "SwingTrader"
    
    def __init__(self):
        self.risk_per_trade = 0.03  # 3% risk for swings
        self.reward_ratio = 3.0     # 3:1 for longer holds
    
    def decide(
        self,
        req: TradingRequest,
        *,
        config: Dict[str, Any] = None
    ) -> TradingDecision:
        """Execute swing trade analysis."""
        config = config or {}
        
        # Get combined analysis
        analysis = self._get_analysis(req.symbol)
        
        # Generate decision from analysis
        signal = analysis.get("combined_signal", "HOLD")
        tech = analysis.get("technical_analysis", {})
        fund = analysis.get("fundamental_analysis", {})
        technicals = analysis.get("technicals", {})
        
        # Map signal to action
        action_map = {
            "STRONG BUY": "buy",
            "BUY": "buy",
            "HOLD": "watch",
            "SELL": "sell",
            "STRONG SELL": "sell"
        }
        action = action_map.get(signal, "watch")
        
        # Get price levels
        price = analysis.get("fundamentals", {}).get("price", 100.0)
        atr = technicals.get("atr_14", price * 0.02)
        
        # Calculate levels
        if action == "buy":
            entry = price
            stop_loss = price - (atr * 2)
            take_profit = price + (atr * 2 * self.reward_ratio)
        elif action == "sell":
            entry = price
            stop_loss = price + (atr * 2)
            take_profit = price - (atr * 2 * self.reward_ratio)
        else:
            entry = price
            stop_loss = None
            take_profit = None
        
        # Position sizing
        risk_amount = req.portfolio_value * self.risk_per_trade
        if stop_loss:
            risk_per_share = abs(entry - stop_loss)
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            position_size = shares * entry
        else:
            shares = 0
            position_size = 0
        
        # Build all signals
        all_signals = []
        all_signals.extend(tech.get("signals", []))
        all_signals.extend(fund.get("factors", []))
        
        decision = TradingDecision(
            strategy=self.name,
            action=action,
            symbol=req.symbol.upper(),
            position_size=round(position_size, 2),
            confidence=analysis.get("combined_confidence", 0.5),
            entry_price=round(entry, 2) if entry else None,
            stop_loss=round(stop_loss, 2) if stop_loss else None,
            take_profit=round(take_profit, 2) if take_profit else None,
            metadata={
                "combined_score": analysis.get("combined_score", 0),
                "fundamental_score": fund.get("fundamental_score", 0),
                "technical_score": tech.get("technical_score", 0),
                "signals": all_signals[:6],
                "shares": shares,
                "rsi": technicals.get("rsi_14"),
                "macd_cross": technicals.get("macd_cross"),
                "hold_period": "3-10 days"
            }
        )
        
        decision.metadata["unk_explanation"] = self.explain(decision)
        return decision
    
    def _get_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get combined fundamental + technical analysis."""
        if YFINANCE_AVAILABLE and STOCKSTATS_AVAILABLE and get_combined_analysis:
            try:
                return get_combined_analysis(symbol)
            except Exception as e:
                logger.warning(f"Combined analysis failed for {symbol}: {e}")
        
        return {
            "combined_signal": "HOLD",
            "combined_score": 0,
            "combined_confidence": 0.5
        }
    
    def explain(self, output: TradingDecision) -> str:
        """Unk's swing trading advice."""
        symbol = output.symbol
        signals = output.metadata.get("signals", [])
        combined_score = output.metadata.get("combined_score", 0)
        rsi = output.metadata.get("rsi")
        shares = output.metadata.get("shares", 0)
        
        signals_str = ". ".join(signals[:3]) if signals else "the technicals"
        
        if output.action == "watch":
            return (
                f"Unk says PATIENCE on {symbol}, nephew. "
                f"Score is {combined_score} - ain't nothing jumping out at me. "
                f"Wait for that RSI to hit oversold or a clear MACD cross. "
                f"Swing trades need CONVICTION, not FOMO."
            )
        
        if output.action == "buy":
            rsi_note = f" RSI at {rsi:.0f}." if rsi else ""
            return (
                f"Unk says {symbol} SWING SETUP! Combined score: {combined_score}.{rsi_note} "
                f"{signals_str}. "
                f"Entry ${output.entry_price:.2f}, stop ${output.stop_loss:.2f}, "
                f"target ${output.take_profit:.2f}. "
                f"Get {shares} shares and HOLD for 3-10 days. "
                f"This one got room to run, nephew. Let it breathe!"
            )
        
        if output.action == "sell":
            return (
                f"Unk says EXIT {symbol}! Score {combined_score}. {signals_str}. "
                f"Take your gains and bounce. Don't marry the position!"
            )
        
        return f"Unk watching {symbol}. Wait for the setup."
