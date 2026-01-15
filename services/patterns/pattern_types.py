"""
Pattern Type Definitions
========================
Dataclasses for technical pattern detection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class PatternType(Enum):
    """Types of patterns we detect."""
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    BREAK_RETEST = "break_retest"
    FIRST_CANDLE_RULE = "first_candle_rule"  # ORB
    MICRO_PULLBACK = "micro_pullback"  # 1 candle
    FAILED_AUCTION = "failed_auction"
    ABSORPTION = "absorption"


class PatternDirection(Enum):
    """Direction of the pattern signal."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


@dataclass
class BullFlag:
    """
    Bull Flag Pattern (Ross Cameron).
    
    Structure:
    1. Initial spike (pole) - big green candle(s)
    2. Consolidation (flag) - 2-7 candles pulling back
    3. Breakout - first candle to make new high
    
    Entry: First candle to make new high after pullback
    Stop: Low of the pullback
    Target: Retest of high of day (2:1 min R:R)
    """
    entry_price: float
    stop_loss: float
    target: float
    
    # Pattern details
    pole_high: float  # Top of initial spike
    flag_low: float   # Bottom of pullback
    flag_bars: int    # Number of consolidation candles
    
    # Risk metrics
    risk_per_share: float = 0.0
    reward_per_share: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # Validation
    is_valid: bool = True
    invalidation_reason: Optional[str] = None
    
    def __post_init__(self):
        """Calculate risk metrics."""
        self.risk_per_share = abs(self.entry_price - self.stop_loss)
        self.reward_per_share = abs(self.target - self.entry_price)
        if self.risk_per_share > 0:
            self.risk_reward_ratio = self.reward_per_share / self.risk_per_share
        
        # Validate 2:1 minimum
        if self.risk_reward_ratio < 2.0:
            self.is_valid = False
            self.invalidation_reason = f"R:R {self.risk_reward_ratio:.1f} < 2.0"


@dataclass
class BreakRetest:
    """
    Break and Retest Pattern (Tony & JDub ICT).
    
    Structure:
    1. Price breaks key level (PDH, PDL, PMH, PML)
    2. Price retests level (now support/resistance)
    3. First candle to make new high/low after retest
    
    Entry: First candle to make new high after retest
    Stop: Below retest low
    Target: 2:1 minimum
    """
    level_type: str  # "PDH", "PDL", "PMH", "PML", "ORH", "ORL"
    level_price: float
    
    # Trade setup
    direction: PatternDirection
    entry_price: float
    stop_loss: float
    target: float
    
    # Retest details
    retest_price: float  # Where price touched level
    retest_bar_index: int  # When retest occurred
    
    # Risk metrics
    risk_reward_ratio: float = 0.0
    
    def __post_init__(self):
        """Calculate R:R."""
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.target - self.entry_price)
        if risk > 0:
            self.risk_reward_ratio = reward / risk


@dataclass  
class FirstCandleSetup:
    """
    First Candle Rule / Opening Range Breakout (ORB).
    
    Structure:
    1. Wait for first 5-minute candle to close
    2. Entry on break of high (long) or low (short)
    3. Stop at opposite side of opening range
    4. Target: 2x the opening range
    """
    timeframe_minutes: int  # Usually 5
    
    # Opening range
    or_high: float
    or_low: float
    or_range: float
    
    # Trade setup
    direction: PatternDirection
    entry_price: float
    stop_loss: float
    target: float
    
    # Timing
    open_time: str  # When market opened
    setup_time: str  # When setup became valid
    
    def __post_init__(self):
        """Calculate opening range."""
        self.or_range = self.or_high - self.or_low


@dataclass
class MicroPullback:
    """
    Micro Pullback (1 candle consolidation).
    
    Very aggressive entry - only 1 red candle after spike.
    Higher risk but faster entry on strong momentum.
    """
    entry_price: float
    stop_loss: float
    target: float
    pullback_bar_index: int
    
    # MACD confirmation
    macd_positive: bool = True


@dataclass
class PatternSignal:
    """
    Generic pattern signal for strategy integration.
    """
    pattern_type: PatternType
    direction: PatternDirection
    
    # Trade parameters
    entry_price: float
    stop_loss: float
    target: float
    
    # Confidence and quality
    confidence: float = 0.7
    quality: str = "B"  # A, B, C, D
    
    # Timing
    bar_index: int = -1
    timestamp: Optional[str] = None
    
    # Raw pattern data
    pattern_data: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "pattern_type": self.pattern_type.value,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target": self.target,
            "confidence": self.confidence,
            "quality": self.quality,
            "risk_reward": round(
                abs(self.target - self.entry_price) / 
                abs(self.entry_price - self.stop_loss), 2
            ) if self.entry_price != self.stop_loss else 0,
        }
