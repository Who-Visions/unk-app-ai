"""
DayTrader Strategy - Enhanced
=============================
Day trading strategy using technical indicators from stockstats.
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
        get_stock_info_yfinance,
        get_technical_indicators,
        calculate_stock_score,
        calculate_technical_score,
        YFINANCE_AVAILABLE,
        STOCKSTATS_AVAILABLE
    )
except ImportError:
    YFINANCE_AVAILABLE = False
    STOCKSTATS_AVAILABLE = False
    get_stock_info_yfinance = None
    get_technical_indicators = None
    calculate_stock_score = None
    calculate_technical_score = None


class DayTraderStrategy(Strategy):
    """
    Day trading strategy with Unk's tough-love guidance.
    
    Enhanced with technical indicators:
    - RSI for overbought/oversold
    - MACD for momentum
    - Bollinger Bands for volatility
    - ATR for stop placement
    """
    name = "DayTrader"
    
    def __init__(self):
        self.risk_per_trade = 0.02  # 2% risk
        self.reward_ratio = 2.0     # 2:1 reward/risk
    
    def decide(
        self,
        req: TradingRequest,
        *,
        config: Dict[str, Any] = None
    ) -> TradingDecision:
        """Execute the trading pipeline."""
        config = config or {}
        
        # Get market data
        market_data = self._get_market_data(req.symbol)
        
        # Get technical analysis
        tech_data = self._get_technicals(req.symbol)
        
        # Calculate scores
        fund_score = calculate_stock_score(market_data) if calculate_stock_score and "error" not in market_data else {}
        tech_score = calculate_technical_score(tech_data) if calculate_technical_score and "error" not in tech_data else {}
        
        # Combine scores for decision
        combined = fund_score.get("fundamental_score", 0) + tech_score.get("technical_score", 0)
        
        # Determine action
        if combined >= 3:
            action = "buy"
            confidence = min(0.85, 0.55 + (combined * 0.05))
        elif combined <= -3:
            action = "sell"
            confidence = min(0.8, 0.5 + (abs(combined) * 0.05))
        else:
            action = "watch"
            confidence = 0.5
        
        # Calculate levels
        price = market_data.get("price", 100.0)
        atr = tech_data.get("atr_14", price * 0.02)
        
        if action == "buy":
            entry = price
            stop_loss = price - (atr * 1.5)
            take_profit = price + (atr * 1.5 * self.reward_ratio)
        elif action == "sell":
            entry = price
            stop_loss = price + (atr * 1.5)
            take_profit = price - (atr * 1.5 * self.reward_ratio)
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
        
        # Collect signals
        signals = []
        signals.extend(fund_score.get("factors", [])[:3])
        signals.extend(tech_score.get("signals", [])[:3])
        
        decision = TradingDecision(
            strategy=self.name,
            action=action,
            symbol=req.symbol.upper(),
            position_size=round(position_size, 2),
            confidence=confidence,
            entry_price=round(entry, 2) if entry else None,
            stop_loss=round(stop_loss, 2) if stop_loss else None,
            take_profit=round(take_profit, 2) if take_profit else None,
            metadata={
                "combined_score": combined,
                "fundamental_score": fund_score.get("fundamental_score", 0),
                "technical_score": tech_score.get("technical_score", 0),
                "signals": signals,
                "shares": shares,
                "rsi": tech_data.get("rsi_14"),
                "macd_cross": tech_data.get("macd_cross"),
                "atr": round(atr, 2) if atr else None
            }
        )
        
        decision.metadata["unk_explanation"] = self.explain(decision)
        return decision
    
    def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data via yfinance."""
        if YFINANCE_AVAILABLE and get_stock_info_yfinance:
            try:
                return get_stock_info_yfinance(symbol)
            except Exception as e:
                logger.warning(f"Market data fetch failed for {symbol}: {e}")
        return {"price": 100.0}
    
    def _get_technicals(self, symbol: str) -> Dict[str, Any]:
        """Get technical indicators."""
        if YFINANCE_AVAILABLE and STOCKSTATS_AVAILABLE and get_technical_indicators:
            try:
                return get_technical_indicators(symbol, period="3mo")
            except Exception as e:
                logger.warning(f"Technicals fetch failed for {symbol}: {e}")
        return {}
    
    def explain(self, output: TradingDecision) -> str:
        """Unk's trading advice."""
        symbol = output.symbol
        signals = output.metadata.get("signals", [])
        combined = output.metadata.get("combined_score", 0)
        rsi = output.metadata.get("rsi")
        shares = output.metadata.get("shares", 0)
        
        signals_str = ". ".join(signals[:3]) if signals else "the numbers"
        rsi_note = f" RSI at {rsi:.0f}." if rsi else ""
        
        if output.action == "watch":
            if combined < 0:
                return (
                    f"Unk says NAH on {symbol}, nephew. Score: {combined}. "
                    f"{signals_str}. Keep yo money until something real comes along."
                )
            return (
                f"Unk says WAIT on {symbol}. Score: {combined}.{rsi_note} "
                f"Put it on the watchlist. Good trades come to those who WAIT."
            )
        
        if output.action == "buy":
            return (
                f"Unk says {symbol} looking RIGHT! Score: {combined}.{rsi_note} "
                f"{signals_str}. "
                f"Entry ${output.entry_price:.2f}, stop ${output.stop_loss:.2f}, "
                f"target ${output.take_profit:.2f}. "
                f"{shares} shares (${output.position_size:.2f}). "
                f"HANDLE YO BIZNASS, nephew!"
            )
        
        if output.action == "sell":
            return (
                f"Unk says GET OUT of {symbol}! Score: {combined}. {signals_str}. "
                f"Lock in your gains. The market taketh away!"
            )
        
        return f"Unk watching {symbol}. Stay patient."
