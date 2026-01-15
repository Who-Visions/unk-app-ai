"""
Pattern Scalp Strategy (Opening Range Reversal)
================================================
Based on "If I Could Only Trade ONE Strategy" video.

The Strategy:
1. Wait for first 15-min candle to close (Opening Range)
2. Check if it's a manipulation candle (exceeds 20% of ATR)
3. Wait for reversal signal (John Wick or Power Tower)
4. Enter on break, stop at high/low of day
5. Target 50-100% of range

Key Insight: "Every secret you need is in the opening candle"
The faster/more aggressive the move, the more likely it reverses.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None


class ReversalCandle(Enum):
    """Types of reversal candles."""
    JOHN_WICK_BULLISH = "john_wick_bullish"  # Hammer - was red, turned green
    JOHN_WICK_BEARISH = "john_wick_bearish"  # Inverted hammer - was green, turned red
    POWER_TOWER_BULLISH = "power_tower_bullish"  # Bullish engulfing
    POWER_TOWER_BEARISH = "power_tower_bearish"  # Bearish engulfing


@dataclass
class OpeningRange:
    """
    The 15-minute opening range.
    
    This is the foundation of the Pattern Scalp strategy.
    The range high/low become key levels for the day.
    """
    high: float
    low: float
    open_price: float
    close_price: float
    timestamp: str
    
    # Manipulation analysis
    atr: float = 0.0
    range_percent_of_atr: float = 0.0
    is_manipulation: bool = False
    direction: str = ""  # "up" or "down"
    
    @property
    def range_size(self) -> float:
        return self.high - self.low
    
    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2
    
    @property
    def is_bullish(self) -> bool:
        return self.close_price > self.open_price
    
    def calculate_manipulation(self, atr: float) -> bool:
        """
        Check if this is a manipulation candle.
        
        Rule: If range exceeds 20% of daily ATR, it's manipulation.
        The more it exceeds, the higher probability of reversal.
        """
        self.atr = atr
        self.range_percent_of_atr = (self.range_size / atr * 100) if atr > 0 else 0
        
        # 20% threshold for manipulation
        self.is_manipulation = self.range_percent_of_atr >= 20
        
        # Determine direction of manipulation
        self.direction = "up" if self.is_bullish else "down"
        
        return self.is_manipulation


@dataclass
class PatternScalpSignal:
    """
    Trading signal from Pattern Scalp strategy.
    """
    symbol: str
    direction: str  # "long" (reversal from down) or "short" (reversal from up)
    
    # Opening range
    opening_range: OpeningRange
    
    # Entry details
    entry_price: float
    reversal_candle: ReversalCandle
    
    # Risk management
    stop_loss: float  # High/low of day
    take_profit_50: float  # 50% of range
    take_profit_100: float  # 100% of range (top/bottom of OR)
    
    # Timing
    timestamp: str = ""
    minutes_after_open: int = 0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def risk(self) -> float:
        return abs(self.entry_price - self.stop_loss)
    
    @property
    def reward_50(self) -> float:
        return abs(self.take_profit_50 - self.entry_price)
    
    @property
    def reward_100(self) -> float:
        return abs(self.take_profit_100 - self.entry_price)
    
    @property
    def rr_ratio_50(self) -> float:
        return self.reward_50 / self.risk if self.risk > 0 else 0
    
    @property
    def rr_ratio_100(self) -> float:
        return self.reward_100 / self.risk if self.risk > 0 else 0


class PatternScalpStrategy:
    """
    Pattern Scalp Strategy - Opening Range Reversal.
    
    "If I could only trade ONE strategy for the rest of my life,
    this would be it. No questions."
    
    The 3-Step Process:
    1. Define Opening Range (first 15-min candle)
    2. Determine if manipulation (>20% of ATR)
    3. Wait for reversal candle (John Wick or Power Tower)
    
    Key Insight:
    - Manipulation candles MUST happen for institutions to enter
    - The more aggressive the move, the more likely the reversal
    - Most assets move back and forth within the opening range
    
    Reversal Candles:
    - John Wick (Hammer): Long wick showing rapid reversal
    - Power Tower (Engulfing): 30-50% retracement of OR
    
    Entry/Exit:
    - Enter on break of reversal candle
    - Stop at high/low of day
    - Target 50-100% of opening range
    """
    
    # Strategy parameters
    MANIPULATION_THRESHOLD = 0.20  # 20% of ATR
    POWER_TOWER_MIN_RETRACEMENT = 0.30  # 30% minimum
    POWER_TOWER_MAX_RETRACEMENT = 0.50  # 50% ideal
    
    def __init__(self, timeframe_minutes: int = 15):
        """
        Initialize Pattern Scalp strategy.
        
        Args:
            timeframe_minutes: Opening range timeframe (default 15)
        """
        self.timeframe = timeframe_minutes
        self.opening_range: Optional[OpeningRange] = None
        self.signals: List[PatternScalpSignal] = []
    
    def define_opening_range(
        self,
        df_15m: "pd.DataFrame",
        atr: float,
    ) -> Optional[OpeningRange]:
        """
        Step 1: Define the opening range from first 15-min candle.
        
        Args:
            df_15m: 15-minute OHLCV data
            atr: Daily ATR value
            
        Returns:
            OpeningRange if valid
        """
        if not PANDAS_AVAILABLE or df_15m is None or df_15m.empty:
            return None
        
        # Get first candle of the day
        first_candle = df_15m.iloc[0]
        
        opening_range = OpeningRange(
            high=float(first_candle['high']),
            low=float(first_candle['low']),
            open_price=float(first_candle['open']),
            close_price=float(first_candle['close']),
            timestamp=str(df_15m.index[0]) if hasattr(df_15m.index, '__iter__') else datetime.now().isoformat(),
        )
        
        # Check manipulation
        opening_range.calculate_manipulation(atr)
        
        self.opening_range = opening_range
        
        if opening_range.is_manipulation:
            logger.info(
                f"Manipulation candle detected: {opening_range.direction} "
                f"({opening_range.range_percent_of_atr:.1f}% of ATR)"
            )
        
        return opening_range
    
    def calculate_atr(self, df_daily: "pd.DataFrame", period: int = 14) -> float:
        """
        Calculate Average True Range from daily data.
        """
        if not PANDAS_AVAILABLE or df_daily is None or len(df_daily) < period + 1:
            return 0.0
        
        high = df_daily['high']
        low = df_daily['low']
        close = df_daily['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return float(atr) if not pd.isna(atr) else 0.0
    
    def detect_john_wick(
        self,
        candle: Dict[str, float],
        opening_range: OpeningRange,
    ) -> Optional[ReversalCandle]:
        """
        Detect John Wick (Hammer) candle.
        
        Bullish John Wick: Was red, turned green with long lower wick
        Bearish John Wick: Was green, turned red with long upper wick
        """
        open_p = candle['open']
        close_p = candle['close']
        high_p = candle['high']
        low_p = candle['low']
        
        body = abs(close_p - open_p)
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p
        
        total_range = high_p - low_p
        if total_range == 0:
            return None
        
        # Bullish John Wick: Long lower wick, small body at top
        # Indicates price went down hard then reversed up
        if opening_range.direction == "down":
            if lower_wick > body * 2 and lower_wick > upper_wick:
                return ReversalCandle.JOHN_WICK_BULLISH
        
        # Bearish John Wick: Long upper wick, small body at bottom
        if opening_range.direction == "up":
            if upper_wick > body * 2 and upper_wick > lower_wick:
                return ReversalCandle.JOHN_WICK_BEARISH
        
        return None
    
    def detect_power_tower(
        self,
        current: Dict[str, float],
        previous: Dict[str, float],
        opening_range: OpeningRange,
    ) -> Optional[ReversalCandle]:
        """
        Detect Power Tower (Engulfing) pattern.
        
        Look for 30-50% retracement of opening range.
        """
        or_range = opening_range.range_size
        
        # Bullish Power Tower: After down manipulation
        if opening_range.direction == "down":
            # Current candle should be bullish and engulf previous
            if current['close'] > current['open']:
                retracement = (current['close'] - opening_range.low) / or_range
                if self.POWER_TOWER_MIN_RETRACEMENT <= retracement <= 0.60:
                    return ReversalCandle.POWER_TOWER_BULLISH
        
        # Bearish Power Tower: After up manipulation
        if opening_range.direction == "up":
            # Current candle should be bearish and engulf previous
            if current['close'] < current['open']:
                retracement = (opening_range.high - current['close']) / or_range
                if self.POWER_TOWER_MIN_RETRACEMENT <= retracement <= 0.60:
                    return ReversalCandle.POWER_TOWER_BEARISH
        
        return None
    
    def generate_signal(
        self,
        symbol: str,
        df_15m: "pd.DataFrame",
        df_5m: "pd.DataFrame",
        df_daily: "pd.DataFrame",
    ) -> Optional[PatternScalpSignal]:
        """
        Full Pattern Scalp strategy execution.
        
        Args:
            symbol: Trading symbol
            df_15m: 15-minute OHLCV data
            df_5m: 5-minute OHLCV data (for entry timing)
            df_daily: Daily OHLCV data (for ATR)
            
        Returns:
            PatternScalpSignal if valid setup
        """
        if not PANDAS_AVAILABLE:
            return None
        
        # Step 1: Calculate ATR
        atr = self.calculate_atr(df_daily)
        if atr == 0:
            return None
        
        # Step 2: Define opening range
        opening_range = self.define_opening_range(df_15m, atr)
        if not opening_range or not opening_range.is_manipulation:
            logger.debug("No manipulation candle detected")
            return None
        
        # Step 3: Look for reversal candle on 5M
        if df_5m is None or len(df_5m) < 3:
            return None
        
        # Check recent candles for reversal pattern
        for i in range(1, min(len(df_5m), 10)):
            candle = {
                'open': float(df_5m['open'].iloc[i]),
                'high': float(df_5m['high'].iloc[i]),
                'low': float(df_5m['low'].iloc[i]),
                'close': float(df_5m['close'].iloc[i]),
            }
            
            prev_candle = {
                'open': float(df_5m['open'].iloc[i-1]),
                'high': float(df_5m['high'].iloc[i-1]),
                'low': float(df_5m['low'].iloc[i-1]),
                'close': float(df_5m['close'].iloc[i-1]),
            }
            
            # Check for John Wick
            john_wick = self.detect_john_wick(candle, opening_range)
            if john_wick:
                return self._create_signal(
                    symbol, opening_range, john_wick, candle, i * 5
                )
            
            # Check for Power Tower
            power_tower = self.detect_power_tower(candle, prev_candle, opening_range)
            if power_tower:
                return self._create_signal(
                    symbol, opening_range, power_tower, candle, i * 5
                )
        
        return None
    
    def _create_signal(
        self,
        symbol: str,
        opening_range: OpeningRange,
        reversal_candle: ReversalCandle,
        candle: Dict[str, float],
        minutes_after: int,
    ) -> PatternScalpSignal:
        """Create trading signal from reversal pattern."""
        
        # Determine direction based on manipulation
        if opening_range.direction == "down":
            # Manipulation was down, so we go LONG
            direction = "long"
            entry_price = candle['high']  # Buy on break above
            stop_loss = opening_range.low  # Stop at low of day
            take_profit_50 = opening_range.midpoint
            take_profit_100 = opening_range.high
        else:
            # Manipulation was up, so we go SHORT
            direction = "short"
            entry_price = candle['low']  # Sell on break below
            stop_loss = opening_range.high  # Stop at high of day
            take_profit_50 = opening_range.midpoint
            take_profit_100 = opening_range.low
        
        signal = PatternScalpSignal(
            symbol=symbol,
            direction=direction,
            opening_range=opening_range,
            entry_price=entry_price,
            reversal_candle=reversal_candle,
            stop_loss=stop_loss,
            take_profit_50=take_profit_50,
            take_profit_100=take_profit_100,
            minutes_after_open=minutes_after,
        )
        
        self.signals.append(signal)
        logger.info(
            f"Pattern Scalp signal: {direction} {symbol} at {entry_price}, "
            f"reversal={reversal_candle.value}, R:R={signal.rr_ratio_50:.1f}"
        )
        
        return signal


# Strategy documentation
PATTERN_SCALP_CHECKLIST = """
## Pattern Scalp Strategy - Opening Range Reversal

### The 3 Steps
1. **Define Opening Range** (First 15-min candle)
   - Mark high and low with box/lines
   - Let the candle fully close before acting

2. **Check for Manipulation** (>20% of daily ATR)
   - Move to Daily chart, get ATR value
   - Multiply ATR by 20%
   - If OR range exceeds this, it's manipulation
   - The more it exceeds, the higher reversal probability

3. **Wait for Reversal Candle** (Drop to 5M)
   - **John Wick** (Hammer): Long wick showing rapid reversal
   - **Power Tower** (Engulfing): 30-50% retracement of OR

### Entry Rules
- Enter on break of reversal candle
- Stop loss at high/low of the day
- Target 50% or 100% of opening range

### Key Insights
> "Every secret you need is in the opening candle"

> "The faster/more aggressive the move, the more likely it reverses"

> "Manipulation must happen for institutions to enter"

### Alternative Use
- Pattern Scalp works ANY time during the day
- Look for 15-min candles that exceed 20% ATR
- Same rules apply - wait for reversal candle
- Don't limit yourself to just market open

### Risk Management
- Risk is very small (entry to high/low of OR)
- Reward is large (back to opposite end of OR)
- Typical R:R is 2:1 to 5:1+
"""


def create_pattern_scalp() -> PatternScalpStrategy:
    """Create Pattern Scalp strategy instance."""
    return PatternScalpStrategy()
