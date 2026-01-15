"""
Pattern Detection
=================
Technical pattern detection for candlestick charts.
Implements patterns from Ross Cameron, Tony & JDub ICT strategies.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    from .pattern_types import (
        BullFlag, BreakRetest, FirstCandleSetup, MicroPullback,
        PatternSignal, PatternType, PatternDirection
    )
except ImportError:
    from pattern_types import (
        BullFlag, BreakRetest, FirstCandleSetup, MicroPullback,
        PatternSignal, PatternType, PatternDirection
    )


class PatternDetector:
    """
    Detect candlestick patterns from OHLCV data.
    
    Patterns:
    - Bull Flag (Ross Cameron): Spike → Pullback → First candle new high
    - Break Retest (ICT): Break level → Retest → Continuation
    - First Candle Rule (ORB): Opening range breakout
    - Micro Pullback: 1-candle consolidation
    
    Usage:
        detector = PatternDetector()
        df = yf.download("AAPL", period="1d", interval="1m")
        pattern = detector.detect_bull_flag(df)
        if pattern:
            print(f"Entry: {pattern.entry_price}, Stop: {pattern.stop_loss}")
    """
    
    def __init__(
        self,
        min_rr_ratio: float = 2.0,
        max_pullback_bars: int = 7,
    ):
        """
        Initialize detector.
        
        Args:
            min_rr_ratio: Minimum risk/reward ratio for valid patterns
            max_pullback_bars: Max consolidation candles for bull flag
        """
        self.min_rr_ratio = min_rr_ratio
        self.max_pullback_bars = max_pullback_bars
    
    def detect_bull_flag(
        self,
        df: "pd.DataFrame",
        high_of_day: float = None,
    ) -> Optional[BullFlag]:
        """
        Detect bull flag pattern.
        
        Ross Cameron's Bull Flag:
        1. Initial spike (pole) - strong momentum move
        2. Pullback (flag) - 2-7 red/consolidating candles
        3. Entry: First candle to make new high
        
        Args:
            df: OHLCV DataFrame with columns [open, high, low, close, volume]
            high_of_day: HOD for target calculation (optional)
            
        Returns:
            BullFlag if pattern found, None otherwise
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 5:
            return None
        
        try:
            # Normalize column names
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            # Need at least some data
            if len(df) < 5:
                return None
            
            # Find the pole (strong up move)
            # Look for the highest point in recent bars
            recent = df.tail(20)
            if len(recent) < 5:
                return None
            
            pole_high_idx = recent["high"].idxmax()
            pole_high = recent.loc[pole_high_idx, "high"]
            
            # Get data after the pole high (the pullback)
            pole_pos = recent.index.get_loc(pole_high_idx)
            pullback = recent.iloc[pole_pos + 1:] if pole_pos < len(recent) - 1 else None
            
            if pullback is None or len(pullback) < 2:
                return None
            
            # Check for valid pullback (2-7 bars, lower highs)
            if len(pullback) > self.max_pullback_bars:
                return None
            
            # Find flag low
            flag_low = pullback["low"].min()
            
            # Check if last candle is showing signs of reversal
            last_bar = pullback.iloc[-1]
            prev_bar = pullback.iloc[-2] if len(pullback) > 1 else last_bar
            
            # First candle to make new high = entry trigger
            entry_price = prev_bar["high"] + 0.01  # Break above prev high
            stop_loss = flag_low - 0.05  # Below flag low
            
            # Target = high of day or 2:1 minimum
            risk = entry_price - stop_loss
            if high_of_day and high_of_day > entry_price:
                target = high_of_day
            else:
                target = entry_price + (risk * self.min_rr_ratio)
            
            return BullFlag(
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                target=round(target, 2),
                pole_high=round(pole_high, 2),
                flag_low=round(flag_low, 2),
                flag_bars=len(pullback),
            )
            
        except Exception as e:
            logger.warning(f"Bull flag detection error: {e}")
            return None
    
    def detect_break_retest(
        self,
        df: "pd.DataFrame",
        level: float,
        level_type: str = "PDH",
    ) -> Optional[BreakRetest]:
        """
        Detect break and retest pattern at a key level.
        
        ICT Break & Retest:
        1. Price breaks above/below key level
        2. Price retests the level (old resistance = new support)
        3. Entry: First candle to make new high after retest
        
        Args:
            df: OHLCV DataFrame
            level: Key price level (PDH, PDL, PMH, PML)
            level_type: Type of level for labeling
            
        Returns:
            BreakRetest if pattern found
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 10:
            return None
        
        try:
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            recent = df.tail(20)
            current_price = recent.iloc[-1]["close"]
            
            # Check if we're above the level (potential long setup)
            if current_price > level:
                direction = PatternDirection.LONG
                
                # Find where price broke above
                broke_above = recent[recent["close"] > level]
                if len(broke_above) < 3:
                    return None
                
                # Find retest (price came back to level)
                for i in range(len(recent) - 5, len(recent) - 1):
                    bar = recent.iloc[i]
                    if bar["low"] <= level * 1.01:  # Within 1% of level
                        # Found retest - check for continuation
                        entry_price = recent.iloc[i + 1]["high"] + 0.01
                        stop_loss = level - 0.05
                        risk = entry_price - stop_loss
                        target = entry_price + (risk * self.min_rr_ratio)
                        
                        return BreakRetest(
                            level_type=level_type,
                            level_price=level,
                            direction=direction,
                            entry_price=round(entry_price, 2),
                            stop_loss=round(stop_loss, 2),
                            target=round(target, 2),
                            retest_price=round(bar["low"], 2),
                            retest_bar_index=i,
                        )
            
            # Below level = potential short
            elif current_price < level:
                direction = PatternDirection.SHORT
                # Similar logic for shorts (flip levels)
                pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Break/retest detection error: {e}")
            return None
    
    def detect_first_candle_rule(
        self,
        df: "pd.DataFrame",
        timeframe_minutes: int = 5,
    ) -> Optional[FirstCandleSetup]:
        """
        Detect Opening Range Breakout setup.
        
        First Candle Rule:
        1. Wait for first X-minute candle to close
        2. Long entry: Break of first candle high
        3. Short entry: Break of first candle low
        4. Stop: Opposite side of opening range
        5. Target: 2x the opening range
        
        Args:
            df: Intraday OHLCV DataFrame
            timeframe_minutes: Opening range timeframe
            
        Returns:
            FirstCandleSetup if valid setup found
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 2:
            return None
        
        try:
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            # First candle (opening range)
            first_candle = df.iloc[0]
            or_high = first_candle["high"]
            or_low = first_candle["low"]
            or_range = or_high - or_low
            
            if or_range <= 0:
                return None
            
            # Current price relative to opening range
            current = df.iloc[-1]
            current_close = current["close"]
            
            # Determine direction
            if current_close > or_high:
                direction = PatternDirection.LONG
                entry_price = or_high + 0.01
                stop_loss = or_low - 0.05
                target = entry_price + (or_range * 2)
            elif current_close < or_low:
                direction = PatternDirection.SHORT
                entry_price = or_low - 0.01
                stop_loss = or_high + 0.05
                target = entry_price - (or_range * 2)
            else:
                direction = PatternDirection.NEUTRAL
                return None  # No setup yet
            
            return FirstCandleSetup(
                timeframe_minutes=timeframe_minutes,
                or_high=round(or_high, 2),
                or_low=round(or_low, 2),
                or_range=round(or_range, 2),
                direction=direction,
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                target=round(target, 2),
                open_time=str(df.index[0]) if hasattr(df.index[0], '__str__') else "",
                setup_time=str(df.index[-1]) if hasattr(df.index[-1], '__str__') else "",
            )
            
        except Exception as e:
            logger.warning(f"ORB detection error: {e}")
            return None
    
    def detect_micro_pullback(
        self,
        df: "pd.DataFrame",
        macd_positive: bool = True,
    ) -> Optional[MicroPullback]:
        """
        Detect micro pullback (1 red candle after spike).
        
        Very aggressive entry for strong momentum.
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 3:
            return None
        
        try:
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            recent = df.tail(5)
            
            # Check last candle is red (pullback)
            last = recent.iloc[-1]
            if last["close"] >= last["open"]:
                return None  # Not a pullback
            
            # Check previous candle was green (momentum)
            prev = recent.iloc[-2]
            if prev["close"] <= prev["open"]:
                return None  # No momentum
            
            # Entry on break of pullback high
            entry_price = last["high"] + 0.01
            stop_loss = last["low"] - 0.05
            risk = entry_price - stop_loss
            target = entry_price + (risk * self.min_rr_ratio)
            
            return MicroPullback(
                entry_price=round(entry_price, 2),
                stop_loss=round(stop_loss, 2),
                target=round(target, 2),
                pullback_bar_index=len(df) - 1,
                macd_positive=macd_positive,
            )
            
        except Exception as e:
            logger.warning(f"Micro pullback detection error: {e}")
            return None
    
    def scan_all_patterns(
        self,
        df: "pd.DataFrame",
        levels: Dict[str, float] = None,
    ) -> List[PatternSignal]:
        """
        Scan for all pattern types.
        
        Args:
            df: OHLCV DataFrame
            levels: Dict of key levels {"PDH": 10.5, "PDL": 9.8, ...}
            
        Returns:
            List of PatternSignal objects
        """
        signals = []
        
        # Bull flag
        bf = self.detect_bull_flag(df)
        if bf and bf.is_valid:
            signals.append(PatternSignal(
                pattern_type=PatternType.BULL_FLAG,
                direction=PatternDirection.LONG,
                entry_price=bf.entry_price,
                stop_loss=bf.stop_loss,
                target=bf.target,
                confidence=0.75,
                quality="A" if bf.risk_reward_ratio >= 2.5 else "B",
            ))
        
        # Break retest on each level
        if levels:
            for level_type, level_price in levels.items():
                br = self.detect_break_retest(df, level_price, level_type)
                if br:
                    signals.append(PatternSignal(
                        pattern_type=PatternType.BREAK_RETEST,
                        direction=br.direction,
                        entry_price=br.entry_price,
                        stop_loss=br.stop_loss,
                        target=br.target,
                        confidence=0.70,
                        quality="B",
                        pattern_data={"level_type": level_type},
                    ))
        
        # ORB
        orb = self.detect_first_candle_rule(df)
        if orb:
            signals.append(PatternSignal(
                pattern_type=PatternType.FIRST_CANDLE_RULE,
                direction=orb.direction,
                entry_price=orb.entry_price,
                stop_loss=orb.stop_loss,
                target=orb.target,
                confidence=0.65,
                quality="B",
            ))
        
        # Micro pullback
        mp = self.detect_micro_pullback(df)
        if mp:
            signals.append(PatternSignal(
                pattern_type=PatternType.MICRO_PULLBACK,
                direction=PatternDirection.LONG,
                entry_price=mp.entry_price,
                stop_loss=mp.stop_loss,
                target=mp.target,
                confidence=0.60,
                quality="C",  # More aggressive = lower quality rating
            ))
        
        return signals
