"""
Continuation Trading Strategy
=============================
Based on Trey's "7-Step Framework" insights.

Core Approach:
- LIFO: Last In, First Out
- Buy into strength (don't chase bottoms)
- Let winners run with trailing stops
- No upside profit targets - just trail

Key Indicators:
- 200 SMA for macro strength
- Price above 200 SMA = strong stock
- Custom column: % distance from 200 SMA on 5min chart

Exit Strategy:
- Trailing stop (no fixed profit target)
- Exit on first sign of measured weakness
- Protect downside, let upside run
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None


@dataclass
class ContinuationSignal:
    """
    Continuation trading signal.
    
    For trading strength that's already showing.
    Don't try to time bottoms - buy the move.
    """
    symbol: str
    direction: str  # "long" or "short"
    
    # Entry
    entry_price: float
    
    # Trailing stop
    initial_stop: float
    current_stop: float = 0.0
    
    # No fixed target - let it run
    trailing_percent: float = 0.03  # 3% trail
    
    # Strength metrics
    distance_from_200sma: float = 0.0  # % above 200 SMA
    momentum_score: float = 0.0
    
    # Risk
    risk_per_share: float = 0.0
    
    # Status
    timestamp: str = ""
    is_active: bool = True
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if not self.current_stop:
            self.current_stop = self.initial_stop
        
        self.risk_per_share = abs(self.entry_price - self.initial_stop)
    
    def update_trailing_stop(self, current_price: float) -> float:
        """
        Update trailing stop based on current price.
        
        Args:
            current_price: Current stock price
            
        Returns:
            New stop price
        """
        if self.direction == "long":
            new_stop = current_price * (1 - self.trailing_percent)
            if new_stop > self.current_stop:
                self.current_stop = round(new_stop, 2)
        else:
            new_stop = current_price * (1 + self.trailing_percent)
            if new_stop < self.current_stop:
                self.current_stop = round(new_stop, 2)
        
        return self.current_stop
    
    def check_stop_hit(self, current_price: float) -> bool:
        """Check if stop was hit."""
        if self.direction == "long":
            return current_price <= self.current_stop
        else:
            return current_price >= self.current_stop
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "initial_stop": self.initial_stop,
            "current_stop": self.current_stop,
            "distance_from_200sma": round(self.distance_from_200sma, 2),
            "momentum_score": round(self.momentum_score, 2),
            "is_active": self.is_active,
            "timestamp": self.timestamp,
        }


class ContinuationStrategy:
    """
    Continuation Trading Strategy.
    
    Philosophy: "Last In, First Out" (LIFO)
    - Buy strength, don't try to time bottoms
    - Let winners run with trailing stops
    - Win rate will be lower but R:R much higher
    - Typical stats: 38% win rate, avg win 3x avg loss
    
    Entry Rules:
    - Stock must be above 200 SMA (macro strong)
    - Look for stocks highest % above 200 SMA
    - Buy on continued strength (not pullbacks)
    
    Exit Rules:
    - Trailing stop only (no profit target)
    - Exit on first measured weakness
    - Never scale out of winners
    
    Usage:
        strategy = ContinuationStrategy()
        
        # Scan for strongest stocks
        strongest = strategy.rank_by_strength(symbols_list, timeframe="5m")
        
        # Generate signal
        signal = strategy.generate_signal(df, symbol)
        
        # Manage position
        while signal.is_active:
            signal.update_trailing_stop(current_price)
            if signal.check_stop_hit(current_price):
                break
    """
    
    # Config
    SMA_LENGTH = 200
    TRAILING_PERCENT = 0.03  # 3%
    INITIAL_STOP_PERCENT = 0.05  # 5%
    
    # Strength thresholds
    MIN_DISTANCE_FROM_SMA = 10.0  # 10% above 200 SMA minimum
    
    def __init__(
        self,
        sma_length: int = 200,
        trailing_percent: float = 0.03,
        initial_stop_percent: float = 0.05,
    ):
        self.SMA_LENGTH = sma_length
        self.TRAILING_PERCENT = trailing_percent
        self.INITIAL_STOP_PERCENT = initial_stop_percent
    
    def calculate_200sma(self, df: "pd.DataFrame") -> float:
        """Calculate 200 period SMA."""
        if not PANDAS_AVAILABLE or df is None or len(df) < self.SMA_LENGTH:
            return 0.0
        
        close = df["close"] if "close" in df.columns else df["Close"]
        sma = close.rolling(window=self.SMA_LENGTH).mean()
        return float(sma.iloc[-1])
    
    def distance_from_200sma(self, df: "pd.DataFrame") -> float:
        """
        Calculate % distance from 200 SMA.
        
        This is the key scan column for continuation trading.
        Sort descending to find strongest stocks.
        
        Returns:
            Percentage above/below 200 SMA
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < self.SMA_LENGTH:
            return 0.0
        
        close = df["close"] if "close" in df.columns else df["Close"]
        current_price = float(close.iloc[-1])
        sma = self.calculate_200sma(df)
        
        if sma <= 0:
            return 0.0
        
        return ((current_price - sma) / sma) * 100
    
    def is_macro_strong(self, df: "pd.DataFrame") -> bool:
        """
        Check if stock is macro strong (above 200 SMA).
        
        This is the foundation - only trade strong stocks.
        """
        distance = self.distance_from_200sma(df)
        return distance > 0
    
    def calculate_momentum_score(self, df: "pd.DataFrame") -> float:
        """
        Calculate momentum score based on recent price action.
        
        Factors:
        - Recent returns (5, 10, 20 bars)
        - Volume confirmation
        - Distance from 200 SMA
        
        Returns:
            Momentum score 0-100
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < self.SMA_LENGTH:
            return 0.0
        
        close = df["close"] if "close" in df.columns else df["Close"]
        volume = df["volume"] if "volume" in df.columns else df["Volume"]
        
        score = 0.0
        
        # Return factors (40 points)
        ret_5 = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) >= 6 else 0
        ret_10 = (close.iloc[-1] / close.iloc[-11] - 1) * 100 if len(close) >= 11 else 0
        ret_20 = (close.iloc[-1] / close.iloc[-21] - 1) * 100 if len(close) >= 21 else 0
        
        score += min(ret_5 * 2, 15)  # Max 15 pts
        score += min(ret_10, 15)     # Max 15 pts
        score += min(ret_20 * 0.5, 10)  # Max 10 pts
        
        # Volume confirmation (20 points)
        recent_vol = float(volume.iloc[-5:].mean())
        avg_vol = float(volume.mean())
        vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 0
        score += min(vol_ratio * 5, 20)
        
        # Distance from SMA (40 points)
        distance = self.distance_from_200sma(df)
        score += min(distance, 40)
        
        return max(0, min(100, score))
    
    def generate_signal(
        self,
        df: "pd.DataFrame",
        symbol: str,
    ) -> Optional[ContinuationSignal]:
        """
        Generate continuation trading signal.
        
        Only generates signal if:
        - Stock is above 200 SMA
        - Showing continued strength
        
        Args:
            df: OHLCV DataFrame
            symbol: Stock ticker
            
        Returns:
            ContinuationSignal if conditions met
        """
        if not self.is_macro_strong(df):
            logger.debug(f"{symbol}: Not above 200 SMA - skip")
            return None
        
        distance = self.distance_from_200sma(df)
        
        if distance < self.MIN_DISTANCE_FROM_SMA:
            logger.debug(f"{symbol}: Only {distance:.1f}% above SMA - weak")
            return None
        
        close = df["close"] if "close" in df.columns else df["Close"]
        current_price = float(close.iloc[-1])
        
        # Initial stop
        initial_stop = current_price * (1 - self.INITIAL_STOP_PERCENT)
        
        momentum = self.calculate_momentum_score(df)
        
        return ContinuationSignal(
            symbol=symbol,
            direction="long",
            entry_price=round(current_price, 2),
            initial_stop=round(initial_stop, 2),
            trailing_percent=self.TRAILING_PERCENT,
            distance_from_200sma=distance,
            momentum_score=momentum,
        )
    
    def rank_stocks_by_strength(
        self,
        dfs: Dict[str, "pd.DataFrame"],
    ) -> List[tuple[str, float]]:
        """
        Rank stocks by distance from 200 SMA.
        
        This replicates the scan column from the video:
        "% difference from current price away from 200 SMA on 5min chart"
        
        Args:
            dfs: Dict of symbol -> DataFrame
            
        Returns:
            List of (symbol, distance) sorted descending
        """
        results = []
        
        for symbol, df in dfs.items():
            if df is None or len(df) < self.SMA_LENGTH:
                continue
            
            distance = self.distance_from_200sma(df)
            if distance > 0:  # Only include stocks above SMA
                results.append((symbol, distance))
        
        # Sort by distance descending (strongest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def should_exit(
        self,
        signal: ContinuationSignal,
        current_price: float,
        df: "pd.DataFrame" = None,
    ) -> tuple[bool, str]:
        """
        Check if should exit position.
        
        Exit conditions:
        - Trailing stop hit
        - Stock breaks below 200 SMA
        
        Args:
            signal: Active signal
            current_price: Current price
            df: Recent price data (optional)
            
        Returns:
            (should_exit, reason)
        """
        # Update trailing stop first
        signal.update_trailing_stop(current_price)
        
        # Check stop
        if signal.check_stop_hit(current_price):
            signal.is_active = False
            return True, f"Trailing stop hit at {signal.current_stop}"
        
        # Check if still above 200 SMA
        if df is not None and not self.is_macro_strong(df):
            signal.is_active = False
            return True, "Broke below 200 SMA"
        
        return False, ""


def create_continuation_strategy(
    trailing_percent: float = 0.03,
) -> ContinuationStrategy:
    """Create a continuation strategy instance."""
    return ContinuationStrategy(trailing_percent=trailing_percent)
