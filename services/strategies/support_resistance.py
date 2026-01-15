"""
Support/Resistance Zone Strategy
=================================
Based on the "ONLY Trading Strategy I'll Use in 2026 (Step-By-Step)" video.

7-Step Checklist:
1. Mark highs/lows on 4H timeframe
2. Set alerts at zones
3. Wait for alert (no noise trading)
4. Drop to 1M when zone is tapped
5. Wait for consolidation break OR recent high/low break
6. Enter with stop below/above recent swing low/high
7. Target 2:1 R:R minimum

Stats: 55% win rate, 2.4 avg R:R over 7 years
Assets: NQ, ES, YM futures (7am-12pm CST window)
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any, Tuple
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


class ZoneType(Enum):
    """Type of price zone."""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    BREAK_RETEST_SUPPORT = "break_retest_support"  # Former resistance now support
    BREAK_RETEST_RESISTANCE = "break_retest_resistance"  # Former support now resistance


class EntryTrigger(Enum):
    """Type of entry trigger."""
    CONSOLIDATION_BREAK = "consolidation_break"
    SWING_HIGH_BREAK = "swing_high_break"
    SWING_LOW_BREAK = "swing_low_break"


@dataclass
class PriceZone:
    """
    A support or resistance zone.
    
    Zones are drawn from wick to body on 4H timeframe.
    - Resistance: highest wick to highest body
    - Support: lowest wick to lowest body
    """
    zone_type: ZoneType
    high: float  # Top of zone
    low: float   # Bottom of zone
    created_at: str
    
    # Tracking
    times_tested: int = 0
    times_respected: int = 0
    is_broken: bool = False
    
    # Metadata
    timeframe: str = "4H"
    days_old: int = 0
    
    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2
    
    @property
    def width(self) -> float:
        return self.high - self.low
    
    @property
    def respect_rate(self) -> float:
        if self.times_tested == 0:
            return 0.0
        return self.times_respected / self.times_tested * 100
    
    def contains_price(self, price: float) -> bool:
        """Check if price is within zone."""
        return self.low <= price <= self.high
    
    def is_valid_for_trade(self) -> bool:
        """Check if zone is fresh enough for trading (1-3 days old)."""
        return 0 <= self.days_old <= 3


@dataclass
class ZoneSignal:
    """
    Trading signal from Support/Resistance strategy.
    """
    symbol: str
    direction: str  # "long" or "short"
    zone: PriceZone
    
    # Entry details
    entry_price: float
    trigger: EntryTrigger
    
    # Risk management
    stop_loss: float
    take_profit: float
    
    # Calculated
    risk_reward_ratio: float = 0.0
    
    # Timing
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        # Calculate R:R
        if self.direction == "long":
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        
        if risk > 0:
            self.risk_reward_ratio = round(reward / risk, 2)
    
    @property
    def is_valid(self) -> bool:
        """Check if signal meets minimum 2:1 R:R requirement."""
        return self.risk_reward_ratio >= 2.0


class SupportResistanceStrategy:
    """
    Support/Resistance Zone Trading Strategy.
    
    The 7-Step Checklist:
    1. Mark highs/lows on 4H using Heikin-Ashi
    2. Set alerts at zones
    3. Wait - don't trade the noise
    4. When zone tapped, drop to 1M
    5. Wait for consolidation break or swing high/low break
    6. Enter with stop at recent swing
    7. Target minimum 2:1 R:R
    
    Trading Window: 7am-12pm CST (8:30 market open is key)
    Preferred Assets: NQ, ES, YM futures
    
    Historical Stats:
    - Win Rate: 55%
    - Average R:R: 2.4
    - 7 years of data
    """
    
    # Trading window (CST converted to hours)
    TRADING_START_HOUR = 7
    TRADING_END_HOUR = 12
    MARKET_OPEN_HOUR = 8
    MARKET_OPEN_MINUTE = 30
    
    # Strategy parameters
    MIN_RR_RATIO = 2.0
    MAX_ZONE_AGE_DAYS = 3
    PREFERRED_ZONE_AGE_DAYS = 1
    
    def __init__(
        self,
        min_rr_ratio: float = 2.0,
        max_zone_age: int = 3,
    ):
        """
        Initialize strategy.
        
        Args:
            min_rr_ratio: Minimum risk-reward ratio (default 2.0)
            max_zone_age: Maximum age of zone in days
        """
        self.min_rr_ratio = min_rr_ratio
        self.max_zone_age = max_zone_age
        self.zones: List[PriceZone] = []
        self.alerts: Dict[str, float] = {}
    
    def mark_zones_4h(self, df: "pd.DataFrame") -> List[PriceZone]:
        """
        Step 1: Mark highs and lows on 4H timeframe.
        
        Uses pivot points to identify zones.
        Zone = wick to body of pivot candle.
        """
        if not PANDAS_AVAILABLE or df is None or df.empty:
            return []
        
        zones = []
        
        # Find pivot highs (resistance)
        for i in range(2, len(df) - 2):
            # Check if this is a pivot high
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                
                # Create resistance zone (highest wick to highest body)
                candle = df.iloc[i]
                body_high = max(candle['open'], candle['close'])
                wick_high = candle['high']
                
                zones.append(PriceZone(
                    zone_type=ZoneType.RESISTANCE,
                    high=wick_high,
                    low=body_high,
                    created_at=str(df.index[i]) if hasattr(df.index, '__iter__') else datetime.now().isoformat(),
                    timeframe="4H",
                ))
            
            # Check if this is a pivot low
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                
                # Create support zone (lowest wick to lowest body)
                candle = df.iloc[i]
                body_low = min(candle['open'], candle['close'])
                wick_low = candle['low']
                
                zones.append(PriceZone(
                    zone_type=ZoneType.SUPPORT,
                    high=body_low,
                    low=wick_low,
                    created_at=str(df.index[i]) if hasattr(df.index, '__iter__') else datetime.now().isoformat(),
                    timeframe="4H",
                ))
        
        self.zones = zones
        return zones
    
    def set_alerts(self, zones: List[PriceZone]) -> Dict[str, float]:
        """
        Step 2: Set alerts at zones.
        
        Returns dict of zone_id -> alert_price.
        """
        alerts = {}
        for i, zone in enumerate(zones):
            zone_id = f"zone_{i}_{zone.zone_type.value}"
            # Alert at midpoint of zone
            alerts[zone_id] = zone.midpoint
        
        self.alerts = alerts
        logger.info(f"Set {len(alerts)} alerts at zones")
        return alerts
    
    def is_in_trading_window(self, current_time: time = None) -> bool:
        """
        Step 3: Check if we're in trading window.
        
        Only trade 7am-12pm CST.
        """
        if current_time is None:
            current_time = datetime.now().time()
        
        return (time(self.TRADING_START_HOUR, 0) <= current_time <= 
                time(self.TRADING_END_HOUR, 0))
    
    def is_after_market_open(self, current_time: time = None) -> bool:
        """Check if after 8:30 market open."""
        if current_time is None:
            current_time = datetime.now().time()
        
        return current_time >= time(self.MARKET_OPEN_HOUR, self.MARKET_OPEN_MINUTE)
    
    def check_zone_tap(
        self,
        current_price: float,
        zones: List[PriceZone] = None,
    ) -> Optional[PriceZone]:
        """
        Check if price has tapped into any zone.
        
        Returns the zone if tapped, None otherwise.
        """
        if zones is None:
            zones = self.zones
        
        for zone in zones:
            if zone.contains_price(current_price) and zone.is_valid_for_trade():
                zone.times_tested += 1
                return zone
        
        return None
    
    def detect_consolidation_break(
        self,
        df_1m: "pd.DataFrame",
        zone: PriceZone,
    ) -> Optional[Tuple[EntryTrigger, float, float]]:
        """
        Step 4-5: Detect consolidation break on 1M timeframe.
        
        Returns (trigger_type, entry_price, swing_point) or None.
        """
        if not PANDAS_AVAILABLE or df_1m is None or len(df_1m) < 10:
            return None
        
        recent = df_1m.tail(20)
        
        # Find recent swing highs and lows
        swing_high = recent['high'].max()
        swing_high_idx = recent['high'].idxmax()
        swing_low = recent['low'].min()
        swing_low_idx = recent['low'].idxmin()
        
        current_price = df_1m['close'].iloc[-1]
        
        # For support zone, look for break above consolidation/swing high
        if zone.zone_type in [ZoneType.SUPPORT, ZoneType.BREAK_RETEST_SUPPORT]:
            if current_price > swing_high:
                return (EntryTrigger.SWING_HIGH_BREAK, current_price, swing_low)
        
        # For resistance zone, look for break below consolidation/swing low
        if zone.zone_type in [ZoneType.RESISTANCE, ZoneType.BREAK_RETEST_RESISTANCE]:
            if current_price < swing_low:
                return (EntryTrigger.SWING_LOW_BREAK, current_price, swing_high)
        
        return None
    
    def calculate_targets(
        self,
        entry: float,
        stop: float,
        direction: str,
        recent_swings: List[float] = None,
    ) -> Optional[float]:
        """
        Step 6-7: Calculate take profit for minimum 2:1 R:R.
        
        Targets recent swing highs/lows.
        """
        risk = abs(entry - stop)
        min_target_distance = risk * self.min_rr_ratio
        
        if direction == "long":
            min_target = entry + min_target_distance
            if recent_swings:
                # Find nearest swing high that gives 2:1
                valid_targets = [s for s in recent_swings if s >= min_target]
                if valid_targets:
                    return min(valid_targets)
            return min_target
        else:
            min_target = entry - min_target_distance
            if recent_swings:
                # Find nearest swing low that gives 2:1
                valid_targets = [s for s in recent_swings if s <= min_target]
                if valid_targets:
                    return max(valid_targets)
            return min_target
    
    def generate_signal(
        self,
        symbol: str,
        df_4h: "pd.DataFrame",
        df_1m: "pd.DataFrame",
        current_price: float,
    ) -> Optional[ZoneSignal]:
        """
        Full strategy execution - generate trading signal.
        
        Args:
            symbol: Trading symbol (NQ, ES, YM)
            df_4h: 4-hour OHLCV data
            df_1m: 1-minute OHLCV data  
            current_price: Current price
            
        Returns:
            ZoneSignal if valid setup found
        """
        # Step 1: Mark zones if not done
        if not self.zones:
            self.mark_zones_4h(df_4h)
        
        # Step 3: Check trading window
        if not self.is_in_trading_window():
            logger.debug("Outside trading window")
            return None
        
        # Step 4: Check zone tap
        zone = self.check_zone_tap(current_price)
        if not zone:
            return None
        
        logger.info(f"Price tapped into {zone.zone_type.value} zone")
        
        # Step 5: Check for entry trigger on 1M
        trigger_result = self.detect_consolidation_break(df_1m, zone)
        if not trigger_result:
            return None
        
        trigger, entry_price, swing_point = trigger_result
        
        # Step 6: Set stop loss at recent swing
        if zone.zone_type in [ZoneType.SUPPORT, ZoneType.BREAK_RETEST_SUPPORT]:
            direction = "long"
            stop_loss = swing_point - (entry_price - swing_point) * 0.1  # Small buffer
        else:
            direction = "short"
            stop_loss = swing_point + (swing_point - entry_price) * 0.1
        
        # Step 7: Calculate target for 2:1 R:R
        take_profit = self.calculate_targets(entry_price, stop_loss, direction)
        
        signal = ZoneSignal(
            symbol=symbol,
            direction=direction,
            zone=zone,
            entry_price=entry_price,
            trigger=trigger,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        # Only return if meets minimum R:R
        if signal.is_valid:
            zone.times_respected += 1
            logger.info(f"Valid signal: {direction} at {entry_price}, R:R {signal.risk_reward_ratio}")
            return signal
        
        logger.debug(f"Signal rejected: R:R {signal.risk_reward_ratio} < {self.min_rr_ratio}")
        return None


# The 7-Step Checklist (for reference/display)
SUPPORT_RESISTANCE_CHECKLIST = """
## Support/Resistance Zone Strategy - 7-Step Checklist

### Pre-Trade Setup
1. **Mark Zones on 4H** - Draw rectangles from wick to body at pivot points
2. **Set Alerts** - Alert at zone midpoints so you don't watch charts all day
3. **Sit on Hands** - Everything between zones is NOISE. Don't trade it.

### When Alert Triggers
4. **Drop to 1M Timeframe** - Look for entry confirmation
5. **Wait for Entry Trigger**:
   - Consolidation break (price goes sideways then breaks out)
   - OR break of most recent swing high/low

### Entry & Exit
6. **Enter with Stop at Recent Swing**:
   - Long: Stop below recent swing low
   - Short: Stop above recent swing high
7. **Target Minimum 2:1 R:R** - Use recent swing high/low as target

### Key Rules
- Trading Window: 7am-12pm CST
- Wait for 8:30 market open candlestick
- Zone Age: 1-3 days (fresher = stronger)
- No chasing - if you miss entry, wait for next setup

### Historical Stats (7 Years)
- Win Rate: 55%
- Average R:R: 2.4
- Assets: NQ, ES, YM futures
"""


def create_sr_strategy(
    min_rr_ratio: float = 2.0,
    max_zone_age: int = 3,
) -> SupportResistanceStrategy:
    """Create Support/Resistance strategy instance."""
    return SupportResistanceStrategy(
        min_rr_ratio=min_rr_ratio,
        max_zone_age=max_zone_age,
    )
