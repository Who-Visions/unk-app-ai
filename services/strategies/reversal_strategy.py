"""
Reversal Trading Strategy
=========================
Based on Trey's "7-Step Framework" insights.

Core Approach:
- Buy dips on macro strong stocks
- Higher win rate, smaller wins
- Typical stats: 72-86% win rate, avg loss > avg win
- Scale INTO positions (not out)

Key Indicators:
- Stock above 200 SMA (macro strong)
- RSI below 40 (oversold/dip)
- Quick exit on first bounce

Combined with Continuation:
- Trade both strategies simultaneously
- Continuation: lower win%, higher R:R
- Reversal: higher win%, lower R:R
- Together: smoother P&L curve
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


class ScaleLevel(Enum):
    """Position scaling levels."""
    FIRST = 1   # 25% position
    SECOND = 2  # 50% position
    THIRD = 3   # 75% position
    FULL = 4    # 100% position


@dataclass
class ReversalSignal:
    """
    Reversal trading signal.
    
    For buying dips on macro strong stocks.
    Scale into position, exit quickly on bounce.
    """
    symbol: str
    direction: str  # "long" or "short"
    
    # Entry zones (for scaling in)
    entry_price_1: float  # First scale (25%)
    entry_price_2: float  # Second scale (50%)
    entry_price_3: float  # Third scale (75%)
    
    # Risk
    stop_loss: float
    profit_target: float  # Fixed target (first bounce)
    
    # Current state
    current_scale: ScaleLevel = ScaleLevel.FIRST
    avg_entry_price: float = 0.0
    
    # Indicators
    rsi_value: float = 0.0
    distance_from_200sma: float = 0.0
    
    # Status
    timestamp: str = ""
    is_active: bool = True
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        
        if not self.avg_entry_price:
            self.avg_entry_price = self.entry_price_1
    
    def add_scale(self, price: float, scale_level: ScaleLevel) -> None:
        """
        Add to position at scale level.
        
        Updates average entry price.
        """
        old_size = self.current_scale.value
        new_size = scale_level.value
        
        # Calculate new average
        total = (self.avg_entry_price * old_size) + (price * (new_size - old_size))
        self.avg_entry_price = total / new_size
        self.current_scale = scale_level
    
    @property
    def risk_per_share(self) -> float:
        return abs(self.avg_entry_price - self.stop_loss)
    
    @property
    def reward_per_share(self) -> float:
        return abs(self.profit_target - self.avg_entry_price)
    
    @property
    def risk_reward_ratio(self) -> float:
        if self.risk_per_share > 0:
            return self.reward_per_share / self.risk_per_share
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "avg_entry_price": round(self.avg_entry_price, 2),
            "stop_loss": self.stop_loss,
            "profit_target": self.profit_target,
            "current_scale": self.current_scale.name,
            "risk_reward_ratio": round(self.risk_reward_ratio, 2),
            "rsi_value": round(self.rsi_value, 1),
            "is_active": self.is_active,
            "timestamp": self.timestamp,
        }


class ReversalStrategy:
    """
    Reversal Trading Strategy (Dip Buying).
    
    Philosophy:
    - Buy dips on MACRO STRONG stocks
    - Scale into positions
    - Quick exits on first bounce
    - High win rate, smaller wins
    
    Entry Rules:
    - Stock must be ABOVE 200 SMA (macro strong)
    - RSI must be BELOW 40 (oversold/dip)
    - Scale in as price drops further
    
    Exit Rules:
    - Fixed profit target (first bounce)
    - Stop loss if breaks key support
    - Exit quickly - don't hold for big moves
    
    Typical Stats:
    - Win Rate: 72-86%
    - Avg Win: $97
    - Avg Loss: $124
    - Profitable due to high win rate
    
    Combined with Continuation Strategy:
    - Continuation: 38% win, 3:1 R:R
    - Reversal: 72% win, 0.8:1 R:R
    - Together: Smoother equity curve
    """
    
    # Indicator settings
    RSI_LENGTH = 14
    RSI_BUY_LEVEL = 40  # Buy when RSI drops below this
    SMA_LENGTH = 200
    
    # Risk settings
    PROFIT_TARGET_PERCENT = 0.02  # 2% target
    STOP_LOSS_PERCENT = 0.025     # 2.5% stop
    
    # Scaling
    SCALE_LEVELS = [0.0, 0.01, 0.02, 0.03]  # % drops for each scale
    
    def __init__(
        self,
        rsi_buy_level: float = 40,
        profit_target_percent: float = 0.02,
        stop_loss_percent: float = 0.025,
    ):
        self.RSI_BUY_LEVEL = rsi_buy_level
        self.PROFIT_TARGET_PERCENT = profit_target_percent
        self.STOP_LOSS_PERCENT = stop_loss_percent
    
    def calculate_rsi(self, df: "pd.DataFrame", length: int = 14) -> float:
        """
        Calculate RSI indicator.
        
        Returns:
            Current RSI value (0-100)
        """
        if not PANDAS_AVAILABLE or df is None or len(df) < length + 1:
            return 50.0  # Neutral
        
        close = df["close"] if "close" in df.columns else df["Close"]
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=length).mean()
        avg_loss = loss.rolling(window=length).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1])
    
    def calculate_200sma(self, df: "pd.DataFrame") -> float:
        """Calculate 200 SMA."""
        if not PANDAS_AVAILABLE or df is None or len(df) < self.SMA_LENGTH:
            return 0.0
        
        close = df["close"] if "close" in df.columns else df["Close"]
        sma = close.rolling(window=self.SMA_LENGTH).mean()
        return float(sma.iloc[-1])
    
    def is_macro_strong(self, df: "pd.DataFrame") -> bool:
        """Check if stock is above 200 SMA."""
        if not PANDAS_AVAILABLE or df is None:
            return False
        
        close = df["close"] if "close" in df.columns else df["Close"]
        current_price = float(close.iloc[-1])
        sma = self.calculate_200sma(df)
        
        return current_price > sma
    
    def is_dip_condition(self, df: "pd.DataFrame") -> tuple[bool, float]:
        """
        Check if stock is in dip condition.
        
        Returns:
            (is_dip, rsi_value)
        """
        rsi = self.calculate_rsi(df)
        is_dip = rsi < self.RSI_BUY_LEVEL
        return is_dip, rsi
    
    def generate_signal(
        self,
        df: "pd.DataFrame",
        symbol: str,
    ) -> Optional[ReversalSignal]:
        """
        Generate reversal (dip buying) signal.
        
        Only generates signal if:
        - Stock is ABOVE 200 SMA (macro strong)
        - RSI is BELOW 40 (in a dip)
        
        Args:
            df: OHLCV DataFrame
            symbol: Stock ticker
            
        Returns:
            ReversalSignal if conditions met
        """
        # Must be macro strong
        if not self.is_macro_strong(df):
            logger.debug(f"{symbol}: Below 200 SMA - not macro strong")
            return None
        
        # Must be in dip
        is_dip, rsi = self.is_dip_condition(df)
        if not is_dip:
            logger.debug(f"{symbol}: RSI {rsi:.1f} above 40 - not a dip")
            return None
        
        close = df["close"] if "close" in df.columns else df["Close"]
        current_price = float(close.iloc[-1])
        
        # Calculate entry zones for scaling
        entry_1 = current_price  # First entry
        entry_2 = current_price * (1 - self.SCALE_LEVELS[2])  # -1%
        entry_3 = current_price * (1 - self.SCALE_LEVELS[3])  # -2%
        
        # Stop and target
        stop_loss = current_price * (1 - self.STOP_LOSS_PERCENT)
        profit_target = current_price * (1 + self.PROFIT_TARGET_PERCENT)
        
        # Calculate distance from 200 SMA
        sma = self.calculate_200sma(df)
        distance = ((current_price - sma) / sma) * 100 if sma > 0 else 0
        
        return ReversalSignal(
            symbol=symbol,
            direction="long",
            entry_price_1=round(entry_1, 2),
            entry_price_2=round(entry_2, 2),
            entry_price_3=round(entry_3, 2),
            stop_loss=round(stop_loss, 2),
            profit_target=round(profit_target, 2),
            rsi_value=rsi,
            distance_from_200sma=distance,
        )
    
    def check_scale_trigger(
        self,
        signal: ReversalSignal,
        current_price: float,
    ) -> Optional[ScaleLevel]:
        """
        Check if should scale into position.
        
        Returns next scale level if triggered.
        """
        if signal.current_scale == ScaleLevel.FULL:
            return None
        
        current_level = signal.current_scale.value
        
        # Check each subsequent scale level
        if current_level < 2 and current_price <= signal.entry_price_2:
            return ScaleLevel.SECOND
        if current_level < 3 and current_price <= signal.entry_price_3:
            return ScaleLevel.THIRD
        
        return None
    
    def should_exit(
        self,
        signal: ReversalSignal,
        current_price: float,
    ) -> tuple[bool, str]:
        """
        Check if should exit position.
        
        Exit conditions:
        - Profit target hit
        - Stop loss hit
        
        Args:
            signal: Active signal
            current_price: Current price
            
        Returns:
            (should_exit, reason)
        """
        if signal.direction == "long":
            # Profit target
            if current_price >= signal.profit_target:
                signal.is_active = False
                return True, f"Profit target hit at {signal.profit_target}"
            
            # Stop loss
            if current_price <= signal.stop_loss:
                signal.is_active = False
                return True, f"Stop loss hit at {signal.stop_loss}"
        
        return False, ""
    
    def scan_for_dips(
        self,
        dfs: Dict[str, "pd.DataFrame"],
    ) -> List[tuple[str, float]]:
        """
        Scan for stocks in dip condition.
        
        Args:
            dfs: Dict of symbol -> DataFrame
            
        Returns:
            List of (symbol, rsi) for valid dips
        """
        results = []
        
        for symbol, df in dfs.items():
            if df is None or len(df) < self.SMA_LENGTH:
                continue
            
            if not self.is_macro_strong(df):
                continue
            
            is_dip, rsi = self.is_dip_condition(df)
            if is_dip:
                results.append((symbol, rsi))
        
        # Sort by RSI ascending (most oversold first)
        results.sort(key=lambda x: x[1])
        
        return results


def create_reversal_strategy(
    rsi_buy_level: float = 40,
) -> ReversalStrategy:
    """Create a reversal strategy instance."""
    return ReversalStrategy(rsi_buy_level=rsi_buy_level)
