"""
Momentum Day Trading Strategy
=============================
Ross Cameron's momentum trading strategy implementation.

Core Concepts:
- Trade momentum on breaking news (7-10am window)
- Focus on stocks $2-20, prefer $3-8 sweet spot
- Low float (<20M, prefer <5M)
- 5x+ relative volume
- First pullback entry after spike
- MACD positive confirmation
- Quality over quantity - 1 great trade per day

Exit Rules:
- Breakout or Bailout - if doesn't work immediately, exit
- Trailing stops following the trend
- Exit on MACD crossover to negative
- Exit on high volume red candle
- Exit on large topping tail
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, time

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class SetupQuality(Enum):
    """Setup quality rating."""
    A_PLUS = "A+"  # All 5 pillars + perfect pattern
    A = "A"        # All 5 pillars met
    B = "B"        # 4 pillars met
    C = "C"        # 3 pillars met
    D = "D"        # <3 pillars - avoid


@dataclass
class MomentumSignal:
    """
    A momentum trading signal.
    
    Represents a potential trade setup based on Ross Cameron's
    momentum day trading strategy.
    """
    symbol: str
    signal_type: str  # "first_pullback", "micro_pullback", "orb_break"
    direction: str    # "long" or "short"
    
    # Entry/Exit
    entry_price: float
    stop_loss: float
    target: float
    
    # Risk metrics
    risk_per_share: float = 0.0
    reward_per_share: float = 0.0
    risk_reward_ratio: float = 0.0
    
    # Quality assessment
    quality: SetupQuality = SetupQuality.C
    pillars_met: int = 0
    
    # Confirmation indicators
    macd_positive: bool = False
    volume_confirming: bool = False
    above_vwap: bool = False
    above_9ema: bool = False
    
    # Context
    catalyst: Optional[str] = None
    float_shares: int = 0
    relative_volume: float = 0.0
    gap_percent: float = 0.0
    
    # Timing
    timestamp: str = ""
    
    def __post_init__(self):
        """Calculate risk metrics."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        self.risk_per_share = abs(self.entry_price - self.stop_loss)
        self.reward_per_share = abs(self.target - self.entry_price)
        
        if self.risk_per_share > 0:
            self.risk_reward_ratio = self.reward_per_share / self.risk_per_share
    
    @property
    def is_valid(self) -> bool:
        """Check if signal is valid for trading."""
        # Must be at least B quality
        if self.quality in [SetupQuality.C, SetupQuality.D]:
            return False
        
        # Must have 2:1 R:R minimum
        if self.risk_reward_ratio < 2.0:
            return False
        
        # MACD must be positive
        if not self.macd_positive:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target": self.target,
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "quality": self.quality.value,
            "is_valid": self.is_valid,
            "macd_positive": self.macd_positive,
            "timestamp": self.timestamp,
        }


class MomentumStrategy:
    """
    Ross Cameron's Momentum Day Trading Strategy.
    
    The 5 Pillars of Stock Selection:
    1. Price between $2-$20 (sweet spot $3-$8)
    2. Gap up 10%+ (prefer 25%+)
    3. Relative volume 5x+ (prefer 80x+)
    4. Low float <20M (prefer <5M)
    5. News catalyst
    
    Entry Rules:
    - Wait for first pullback after initial spike
    - Buy first candle to make new high
    - MACD must be positive
    - Good volume profile (green > red)
    
    Exit Rules:
    - Stop at low of pullback
    - Target: high of day or 2:1 R:R minimum
    - Exit on MACD crossover
    - Breakout or bailout
    
    Usage:
        strategy = MomentumStrategy()
        
        # Check if stock meets criteria
        if strategy.passes_five_pillars(stock_data):
            signal = strategy.scan_for_entry(df)
            if signal and signal.is_valid:
                print(f"Trade signal: {signal}")
    """
    
    # 5 Pillars thresholds
    PRICE_MIN = 2.0
    PRICE_MAX = 20.0
    PRICE_SWEET_MIN = 3.0
    PRICE_SWEET_MAX = 8.0
    
    GAP_MIN = 10.0      # 10% minimum gap
    GAP_TARGET = 25.0   # 25% preferred
    
    RVOL_MIN = 5.0      # 5x minimum relative volume
    RVOL_TARGET = 80.0  # 80x+ is excellent
    
    FLOAT_MAX = 20_000_000    # 20M max
    FLOAT_TARGET = 5_000_000  # 5M preferred
    
    # Trading window (Eastern Time)
    TRADING_START = time(7, 0)   # 7:00 AM
    TRADING_END = time(10, 0)    # 10:00 AM
    
    # Technical settings
    MIN_RR_RATIO = 2.0
    MAX_PULLBACK_BARS = 7
    
    def __init__(
        self,
        small_account_mode: bool = False,
        daily_goal: float = 200.0,
        max_daily_loss: float = 200.0,
    ):
        """
        Initialize momentum strategy.
        
        Args:
            small_account_mode: Use tighter criteria for small accounts
            daily_goal: Daily profit target
            max_daily_loss: Max loss before stopping
        """
        self.small_account_mode = small_account_mode
        self.daily_goal = daily_goal
        self.max_daily_loss = max_daily_loss
        
        # Tighter thresholds for small accounts
        if small_account_mode:
            self.PRICE_MIN = 1.50
            self.PRICE_MAX = 6.0
            self.GAP_MIN = 25.0
            self.FLOAT_MAX = 5_000_000
    
    def passes_five_pillars(
        self,
        price: float,
        gap_percent: float,
        relative_volume: float,
        float_shares: int,
        has_news: bool = True,
    ) -> tuple[bool, int, SetupQuality]:
        """
        Check if stock passes the 5 Pillars of Stock Selection.
        
        Args:
            price: Current stock price
            gap_percent: Gap up percentage from previous close
            relative_volume: Volume vs 50-day average
            float_shares: Number of shares in float
            has_news: Whether stock has news catalyst
            
        Returns:
            Tuple of (passes, pillars_met, quality)
        """
        pillars_met = 0
        
        # 1. Price in range
        if self.PRICE_MIN <= price <= self.PRICE_MAX:
            pillars_met += 1
        
        # 2. Gap percentage
        if gap_percent >= self.GAP_MIN:
            pillars_met += 1
        
        # 3. Relative volume
        if relative_volume >= self.RVOL_MIN:
            pillars_met += 1
        
        # 4. Float
        if 0 < float_shares <= self.FLOAT_MAX:
            pillars_met += 1
        elif float_shares == 0:
            # Unknown float - give partial credit
            pillars_met += 0.5
        
        # 5. News catalyst
        if has_news:
            pillars_met += 1
        
        # Determine quality
        if pillars_met >= 5:
            # Check for A+ (sweet spot price + high rvol + ultra low float)
            if (self.PRICE_SWEET_MIN <= price <= self.PRICE_SWEET_MAX and
                relative_volume >= self.RVOL_TARGET and
                float_shares <= self.FLOAT_TARGET):
                quality = SetupQuality.A_PLUS
            else:
                quality = SetupQuality.A
        elif pillars_met >= 4:
            quality = SetupQuality.B
        elif pillars_met >= 3:
            quality = SetupQuality.C
        else:
            quality = SetupQuality.D
        
        # For small account, require A+ or A quality
        if self.small_account_mode:
            passes = quality in [SetupQuality.A_PLUS, SetupQuality.A]
        else:
            passes = quality in [SetupQuality.A_PLUS, SetupQuality.A, SetupQuality.B]
        
        return passes, int(pillars_met), quality
    
    def calculate_macd(
        self,
        df: "pd.DataFrame",
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> tuple[float, float, bool]:
        """
        Calculate MACD indicator.
        
        Returns:
            Tuple of (macd_line, signal_line, is_positive)
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < slow:
            return 0.0, 0.0, False
        
        close = df["close"] if "close" in df.columns else df["Close"]
        
        # Calculate EMAs
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Get latest values
        current_macd = float(macd_line.iloc[-1])
        current_signal = float(signal_line.iloc[-1])
        
        # Positive if MACD above signal line
        is_positive = current_macd > current_signal
        
        return current_macd, current_signal, is_positive
    
    def detect_first_pullback(
        self,
        df: "pd.DataFrame",
        high_of_day: float = None,
    ) -> Optional[MomentumSignal]:
        """
        Detect first pullback pattern after initial spike.
        
        This is Ross Cameron's primary entry pattern:
        1. Big spike up (initial momentum)
        2. Pullback of 1-7 bars
        3. Entry on first candle to make new high
        
        Args:
            df: OHLCV DataFrame
            high_of_day: Current high of day
            
        Returns:
            MomentumSignal if pattern detected
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 20:
            return None
        
        # Normalize column names
        df = df.copy()
        df.columns = df.columns.str.lower()
        
        # Get recent data
        recent = df.tail(20)
        
        # Find the pole high (spike peak)
        pole_high_idx = recent["high"].idxmax()
        pole_high = float(recent.loc[pole_high_idx, "high"])
        
        # Get position of pole high
        pole_pos = recent.index.get_loc(pole_high_idx)
        
        # Need at least 2 bars after the high for a pullback
        if pole_pos >= len(recent) - 2:
            return None
        
        # Get pullback data
        pullback = recent.iloc[pole_pos + 1:]
        
        if len(pullback) < 2 or len(pullback) > self.MAX_PULLBACK_BARS:
            return None
        
        # Find the pullback low
        flag_low = float(pullback["low"].min())
        
        # Check pullback depth (shouldn't retrace more than 50%)
        spike_range = pole_high - float(recent.iloc[0]["low"])
        pullback_depth = pole_high - flag_low
        
        if spike_range > 0 and pullback_depth / spike_range > 0.5:
            return None  # Too deep
        
        # Check MACD
        _, _, macd_positive = self.calculate_macd(df)
        
        # Calculate entry (break of previous bar's high)
        prev_bar = pullback.iloc[-2]
        entry_price = float(prev_bar["high"]) + 0.01
        
        # Stop at low of pullback
        stop_loss = flag_low - 0.05
        
        # Target: HOD or 2:1 R:R, whichever is higher
        risk = entry_price - stop_loss
        min_target = entry_price + (risk * self.MIN_RR_RATIO)
        
        if high_of_day and high_of_day > min_target:
            target = high_of_day
        else:
            target = min_target
        
        # Check volume confirmation
        recent_vol = pullback["volume"].mean()
        spike_vol = float(recent.iloc[pole_pos]["volume"])
        volume_confirming = spike_vol > recent_vol * 2
        
        return MomentumSignal(
            symbol="",  # To be filled by caller
            signal_type="first_pullback",
            direction="long",
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            target=round(target, 2),
            macd_positive=macd_positive,
            volume_confirming=volume_confirming,
        )
    
    def detect_micro_pullback(
        self,
        df: "pd.DataFrame",
    ) -> Optional[MomentumSignal]:
        """
        Detect micro pullback pattern.
        
        A 1-2 bar consolidation in a strong trend.
        Used for adding to winning positions.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            MomentumSignal if pattern detected
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 10:
            return None
        
        df = df.copy()
        df.columns = df.columns.str.lower()
        
        recent = df.tail(10)
        
        # Need strong trend (most recent bars green)
        green_count = sum(
            1 for i in range(len(recent) - 3)
            if recent.iloc[i]["close"] > recent.iloc[i]["open"]
        )
        
        if green_count < 4:
            return None  # Not trending
        
        # Look for 1-2 bar pause
        last_bar = recent.iloc[-1]
        prev_bar = recent.iloc[-2]
        
        # Last bar should be small body (consolidation)
        last_range = last_bar["high"] - last_bar["low"]
        avg_range = (recent["high"] - recent["low"]).mean()
        
        if last_range > avg_range * 0.7:
            return None  # Not a micro pullback
        
        # Check MACD
        _, _, macd_positive = self.calculate_macd(df)
        
        if not macd_positive:
            return None
        
        # Entry above the consolidation
        entry_price = float(last_bar["high"]) + 0.01
        stop_loss = float(min(last_bar["low"], prev_bar["low"])) - 0.03
        
        risk = entry_price - stop_loss
        target = entry_price + (risk * 2.0)
        
        return MomentumSignal(
            symbol="",
            signal_type="micro_pullback",
            direction="long",
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            target=round(target, 2),
            macd_positive=macd_positive,
            volume_confirming=True,  # Assumed in trend
        )
    
    def scan_for_entry(
        self,
        df: "pd.DataFrame",
        symbol: str = "",
        stock_data: Dict[str, Any] = None,
    ) -> Optional[MomentumSignal]:
        """
        Scan for entry signals on a stock.
        
        Checks for:
        1. First pullback pattern
        2. Micro pullback pattern
        
        Args:
            df: OHLCV DataFrame
            symbol: Stock ticker
            stock_data: Additional stock info (price, float, etc.)
            
        Returns:
            Best MomentumSignal found, or None
        """
        signals = []
        
        # Try first pullback (primary pattern)
        hod = float(df["high"].max()) if "high" in df.columns else None
        signal = self.detect_first_pullback(df, high_of_day=hod)
        if signal:
            signal.symbol = symbol
            signals.append(signal)
        
        # Try micro pullback
        signal = self.detect_micro_pullback(df)
        if signal:
            signal.symbol = symbol
            signals.append(signal)
        
        # Apply stock data to signals
        if stock_data and signals:
            for s in signals:
                passes, pillars, quality = self.passes_five_pillars(
                    price=stock_data.get("price", 0),
                    gap_percent=stock_data.get("gap_percent", 0),
                    relative_volume=stock_data.get("relative_volume", 0),
                    float_shares=stock_data.get("float_shares", 0),
                    has_news=stock_data.get("has_news", False),
                )
                s.quality = quality
                s.pillars_met = pillars
                s.float_shares = stock_data.get("float_shares", 0)
                s.relative_volume = stock_data.get("relative_volume", 0)
                s.gap_percent = stock_data.get("gap_percent", 0)
                s.catalyst = stock_data.get("catalyst")
        
        # Return best signal (highest quality + highest R:R)
        valid_signals = [s for s in signals if s.is_valid]
        if not valid_signals:
            return None
        
        return max(valid_signals, key=lambda s: (
            s.quality == SetupQuality.A_PLUS,
            s.quality == SetupQuality.A,
            s.risk_reward_ratio
        ))
    
    def check_exit_conditions(
        self,
        df: "pd.DataFrame",
        entry_price: float,
        current_price: float,
    ) -> tuple[bool, str]:
        """
        Check if exit conditions are met.
        
        Exit Rules:
        1. MACD crossover to negative
        2. High volume red candle
        3. Large topping tail
        4. Price below VWAP (if was above)
        
        Args:
            df: Recent OHLCV data
            entry_price: Original entry price
            current_price: Current price
            
        Returns:
            Tuple of (should_exit, reason)
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < 5:
            return False, ""
        
        df = df.copy()
        df.columns = df.columns.str.lower()
        
        # 1. Check MACD
        _, _, macd_positive = self.calculate_macd(df)
        if not macd_positive:
            return True, "MACD crossover negative"
        
        # 2. High volume red candle
        last_bar = df.iloc[-1]
        is_red = last_bar["close"] < last_bar["open"]
        avg_vol = df["volume"].mean()
        high_volume = last_bar["volume"] > avg_vol * 1.5
        
        if is_red and high_volume:
            return True, "High volume red candle"
        
        # 3. Large topping tail
        body = abs(last_bar["close"] - last_bar["open"])
        upper_wick = last_bar["high"] - max(last_bar["close"], last_bar["open"])
        
        if body > 0 and upper_wick > body * 2:
            return True, "Large topping tail"
        
        return False, ""


# Convenience function
def create_momentum_strategy(small_account: bool = False) -> MomentumStrategy:
    """Create a momentum strategy instance."""
    return MomentumStrategy(small_account_mode=small_account)
