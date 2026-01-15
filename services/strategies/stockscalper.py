"""
Scalper Strategy
================
Quick in-and-out scalping strategy for small, frequent gains.
Uses momentum and volatility indicators.
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
        get_technical_indicators,
        calculate_technical_score,
        YFINANCE_AVAILABLE,
        STOCKSTATS_AVAILABLE
    )
except ImportError:
    YFINANCE_AVAILABLE = False
    STOCKSTATS_AVAILABLE = False
    get_technical_indicators = None
    calculate_technical_score = None


class ScalperStrategy(Strategy):
    """
    Scalping strategy for quick trades (minutes to hours).
    
    Focus on:
    - High volume momentum
    - RSI extremes
    - MACD crossovers
    - Tight stops, quick profits
    """
    name = "Scalper"
    
    def __init__(self):
        self.risk_per_trade = 0.01  # 1% risk for quick trades
        self.reward_ratio = 1.5     # 1.5:1 for fast exits
        self.min_volume_ratio = 1.5  # Need high volume
    
    def decide(
        self,
        req: TradingRequest,
        *,
        config: Dict[str, Any] = None
    ) -> TradingDecision:
        """Execute scalp trade analysis."""
        config = config or {}
        
        # Get technical indicators
        technicals = self._get_technicals(req.symbol)
        tech_score = {}
        
        if technicals and "error" not in technicals:
            tech_score = calculate_technical_score(technicals) if calculate_technical_score else {}
        
        # Scalping logic - need strong momentum
        rsi = technicals.get("rsi_14", 50)
        volume_ratio = technicals.get("volume_ratio", 1.0)
        macd_cross = technicals.get("macd_cross", "neutral")
        price = technicals.get("close", 100.0)
        atr = technicals.get("atr_14", price * 0.01)
        
        # Determine action
        score = 0
        signals = []
        
        # RSI extremes
        if rsi and rsi < 25:
            score += 2
            signals.append("RSI extremely oversold")
        elif rsi and rsi < 35:
            score += 1
            signals.append("RSI oversold")
        elif rsi and rsi > 75:
            score -= 2
            signals.append("RSI extremely overbought")
        elif rsi and rsi > 65:
            score -= 1
            signals.append("RSI overbought")
        
        # Volume check - need high volume for scalps
        if volume_ratio and volume_ratio > 2.0:
            score += 1
            signals.append("Very high volume")
        elif volume_ratio and volume_ratio < 0.8:
            score = 0  # Don't scalp low volume
            signals.append("Low volume - avoid")
        
        # MACD
        if macd_cross == "bullish":
            score += 1
            signals.append("MACD bullish")
        elif macd_cross == "bearish":
            score -= 1
            signals.append("MACD bearish")
        
        # Determine action
        if score >= 2 and volume_ratio > 1.5:
            action = "buy"
            confidence = min(0.75, 0.5 + (score * 0.08))
        elif score <= -2 and volume_ratio > 1.5:
            action = "sell"
            confidence = min(0.75, 0.5 + (abs(score) * 0.08))
        else:
            action = "watch"
            confidence = 0.4
        
        # Tight levels for scalping
        if action == "buy":
            entry = price
            stop_loss = price - atr  # 1 ATR stop
            take_profit = price + (atr * self.reward_ratio)
        elif action == "sell":
            entry = price
            stop_loss = price + atr
            take_profit = price - (atr * self.reward_ratio)
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
                "scalp_score": score,
                "signals": signals,
                "shares": shares,
                "rsi": rsi,
                "volume_ratio": round(volume_ratio, 2) if volume_ratio else None,
                "hold_period": "minutes to hours"
            }
        )
        
        decision.metadata["unk_explanation"] = self.explain(decision)
        return decision
    
    def _get_technicals(self, symbol: str) -> Dict[str, Any]:
        """Get technical indicators."""
        if YFINANCE_AVAILABLE and STOCKSTATS_AVAILABLE and get_technical_indicators:
            try:
                return get_technical_indicators(symbol, period="1mo")
            except Exception as e:
                logger.warning(f"Scalper technicals failed for {symbol}: {e}")
        return {}
    
    def explain(self, output: TradingDecision) -> str:
        """Unk's scalping advice."""
        symbol = output.symbol
        signals = output.metadata.get("signals", [])
        rsi = output.metadata.get("rsi", 50)
        vol = output.metadata.get("volume_ratio", 1.0)
        shares = output.metadata.get("shares", 0)
        
        if output.action == "watch":
            if vol and vol < 1.0:
                return (
                    f"Unk says NAH on scalping {symbol}. Volume too low. "
                    f"Scalps need VOLUME. Find something moving!"
                )
            return (
                f"Unk says {symbol} ain't ready for a scalp. "
                f"RSI at {rsi:.0f}, waiting for extreme reading. "
                f"Quick money needs quick setups. This ain't it."
            )
        
        if output.action == "buy":
            return (
                f"Unk says SCALP {symbol} NOW! RSI {rsi:.0f}, "
                f"volume {vol:.1f}x average. {'. '.join(signals[:2])}. "
                f"Entry ${output.entry_price:.2f}, "
                f"stop ${output.stop_loss:.2f}, "
                f"quick target ${output.take_profit:.2f}. "
                f"{shares} shares. Get IN, get OUT, get PAID. "
                f"This is a HIT AND RUN, nephew!"
            )
        
        if output.action == "sell":
            return (
                f"Unk says SHORT SCALP {symbol}. "
                f"RSI {rsi:.0f} overbought, {'. '.join(signals[:2])}. "
                f"Quick money on the downside. Execute!"
            )
        
        return f"Unk watching {symbol} for scalp opportunity."
