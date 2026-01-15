"""
Level Detection
===============
Key price level detection for breakout trading.
Implements PDH/PDL, PMH/PML, Opening Range, and Volume Profile levels.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    import pandas as pd
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None
    pd = None


@dataclass
class DayLevels:
    """
    Previous Day High/Low/Close (Tony & JDub ICT).
    
    Key levels for break and retest trading:
    - PDH: Previous Day High - resistance turned support after break
    - PDL: Previous Day Low - support turned resistance after break
    - PDC: Previous Day Close - gap reference
    """
    pdh: float  # Previous Day High
    pdl: float  # Previous Day Low
    pdc: float  # Previous Day Close
    
    # Additional context
    prev_date: Optional[str] = None
    gap_percent: float = 0.0  # Gap from PDC
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "PDH": round(self.pdh, 2),
            "PDL": round(self.pdl, 2),
            "PDC": round(self.pdc, 2),
        }


@dataclass
class PremarketLevels:
    """
    Pre-market High/Low (Tony & JDub).
    
    Levels established before market open:
    - PMH: Pre-market High - first resistance
    - PML: Pre-market Low - first support
    """
    pmh: float  # Pre-market High
    pml: float  # Pre-market Low
    
    # Pre-market stats
    pm_volume: int = 0
    pm_range: float = 0.0
    
    def __post_init__(self):
        """Calculate range."""
        self.pm_range = self.pmh - self.pml
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "PMH": round(self.pmh, 2),
            "PML": round(self.pml, 2),
        }


@dataclass
class OpeningRange:
    """
    Opening Range for ORB strategy (First Candle Rule).
    
    Defined by first X minutes of trading.
    - ORH: Opening Range High - breakout level for longs
    - ORL: Opening Range Low - breakout level for shorts
    """
    orh: float  # Opening Range High
    orl: float  # Opening Range Low
    
    # Range details
    timeframe_minutes: int = 5
    or_range: float = 0.0
    volume: int = 0
    
    def __post_init__(self):
        """Calculate range."""
        self.or_range = self.orh - self.orl
    
    def get_long_target(self, rr_ratio: float = 2.0) -> float:
        """Get long entry target price."""
        return self.orh + (self.or_range * rr_ratio)
    
    def get_short_target(self, rr_ratio: float = 2.0) -> float:
        """Get short entry target price."""
        return self.orl - (self.or_range * rr_ratio)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "ORH": round(self.orh, 2),
            "ORL": round(self.orl, 2),
            "OR_Range": round(self.or_range, 2),
        }


@dataclass
class VolumeProfileLevels:
    """
    Volume Profile levels (Fabio Valentino).
    
    Based on volume distribution:
    - VAH: Value Area High (70% of volume above)
    - VAL: Value Area Low (70% of volume below)
    - POC: Point of Control (highest volume price)
    - HVN: High Volume Nodes (support/resistance)
    - LVN: Low Volume Nodes (price magnets)
    """
    vah: float   # Value Area High
    val: float   # Value Area Low
    poc: float   # Point of Control
    
    hvn: List[float] = field(default_factory=list)  # High Volume Nodes
    lvn: List[float] = field(default_factory=list)  # Low Volume Nodes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "VAH": round(self.vah, 2),
            "VAL": round(self.val, 2),
            "POC": round(self.poc, 2),
            "HVN": [round(x, 2) for x in self.hvn],
            "LVN": [round(x, 2) for x in self.lvn],
        }


class LevelDetector:
    """
    Detect key price levels for breakout/retest trading.
    
    Levels detected:
    - PDH/PDL/PDC: Previous Day levels
    - PMH/PML: Pre-market levels
    - ORH/ORL: Opening Range levels
    - VAH/VAL/POC: Volume Profile levels
    
    Usage:
        detector = LevelDetector()
        day_levels = detector.get_previous_day_levels("AAPL")
        print(f"PDH: {day_levels.pdh}, PDL: {day_levels.pdl}")
    """
    
    def __init__(self, value_area_pct: float = 0.70):
        """
        Initialize detector.
        
        Args:
            value_area_pct: Percentage for value area (default 70%)
        """
        self.value_area_pct = value_area_pct
    
    def get_previous_day_levels(self, symbol: str) -> Optional[DayLevels]:
        """
        Get previous day high/low/close.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            DayLevels with PDH, PDL, PDC
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get last 5 days of daily data
            hist = ticker.history(period="5d", interval="1d")
            if hist is None or len(hist) < 2:
                return None
            
            # Previous day is second to last row
            prev_day = hist.iloc[-2]
            
            return DayLevels(
                pdh=float(prev_day["High"]),
                pdl=float(prev_day["Low"]),
                pdc=float(prev_day["Close"]),
                prev_date=str(hist.index[-2].date()),
            )
            
        except Exception as e:
            logger.warning(f"Failed to get day levels for {symbol}: {e}")
            return None
    
    def get_premarket_levels(self, symbol: str) -> Optional[PremarketLevels]:
        """
        Get pre-market high/low.
        
        Args:
            symbol: Stock ticker
            
        Returns:
            PremarketLevels with PMH, PML
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get today's 1-minute data including pre-market
            hist = ticker.history(period="1d", interval="1m", prepost=True)
            if hist is None or len(hist) < 1:
                return None
            
            # Filter for pre-market (before 9:30 AM ET)
            # Note: yfinance timestamps are in exchange timezone
            premarket = hist.between_time("04:00", "09:29")
            
            if len(premarket) < 1:
                # No pre-market data, use first available
                premarket = hist.head(10)
            
            return PremarketLevels(
                pmh=float(premarket["High"].max()),
                pml=float(premarket["Low"].min()),
                pm_volume=int(premarket["Volume"].sum()),
            )
            
        except Exception as e:
            logger.warning(f"Failed to get premarket levels for {symbol}: {e}")
            return None
    
    def get_opening_range(
        self,
        symbol: str,
        minutes: int = 5,
    ) -> Optional[OpeningRange]:
        """
        Get opening range (first X minutes).
        
        Args:
            symbol: Stock ticker
            minutes: Opening range timeframe (default 5)
            
        Returns:
            OpeningRange with ORH, ORL
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get today's minute data
            hist = ticker.history(period="1d", interval="1m")
            if hist is None or len(hist) < minutes:
                return None
            
            # Filter for regular market hours (after 9:30 AM ET)
            market_hours = hist.between_time("09:30", "16:00")
            if len(market_hours) < minutes:
                return None
            
            # First N minutes
            opening = market_hours.head(minutes)
            
            return OpeningRange(
                orh=float(opening["High"].max()),
                orl=float(opening["Low"].min()),
                timeframe_minutes=minutes,
                volume=int(opening["Volume"].sum()),
            )
            
        except Exception as e:
            logger.warning(f"Failed to get opening range for {symbol}: {e}")
            return None
    
    def get_volume_profile_levels(
        self,
        df: "pd.DataFrame",
        num_bins: int = 50,
    ) -> Optional[VolumeProfileLevels]:
        """
        Calculate volume profile levels from OHLCV data.
        
        Args:
            df: OHLCV DataFrame
            num_bins: Number of price bins
            
        Returns:
            VolumeProfileLevels with VAH, VAL, POC, HVN, LVN
        """
        if not YFINANCE_AVAILABLE or df is None or len(df) < 10:
            return None
        
        try:
            df = df.copy()
            df.columns = df.columns.str.lower()
            
            # Calculate typical price and volume at each level
            df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
            
            price_min = df["low"].min()
            price_max = df["high"].max()
            price_range = price_max - price_min
            
            if price_range <= 0:
                return None
            
            bin_size = price_range / num_bins
            
            # Create volume at price distribution
            volume_at_price = {}
            for _, row in df.iterrows():
                bin_idx = int((row["typical_price"] - price_min) / bin_size)
                bin_idx = min(bin_idx, num_bins - 1)
                bin_price = price_min + (bin_idx * bin_size) + (bin_size / 2)
                volume_at_price[bin_price] = volume_at_price.get(bin_price, 0) + row["volume"]
            
            if not volume_at_price:
                return None
            
            # Find POC (highest volume price)
            poc = max(volume_at_price, key=volume_at_price.get)
            total_volume = sum(volume_at_price.values())
            
            # Find Value Area (70% of volume)
            sorted_prices = sorted(volume_at_price.items(), key=lambda x: -x[1])
            cumulative = 0
            value_area_prices = []
            
            for price, vol in sorted_prices:
                cumulative += vol
                value_area_prices.append(price)
                if cumulative >= total_volume * self.value_area_pct:
                    break
            
            vah = max(value_area_prices)
            val = min(value_area_prices)
            
            # Find HVN and LVN
            avg_volume = total_volume / num_bins
            hvn = [p for p, v in volume_at_price.items() if v > avg_volume * 1.5]
            lvn = [p for p, v in volume_at_price.items() if v < avg_volume * 0.3]
            
            return VolumeProfileLevels(
                vah=vah,
                val=val,
                poc=poc,
                hvn=sorted(hvn)[:5],  # Top 5 HVN
                lvn=sorted(lvn)[:5],  # Top 5 LVN
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate volume profile: {e}")
            return None
    
    def get_all_levels(
        self,
        symbol: str,
        include_volume_profile: bool = False,
    ) -> Dict[str, float]:
        """
        Get all key levels in one call.
        
        Args:
            symbol: Stock ticker
            include_volume_profile: Include VP levels (slower)
            
        Returns:
            Dictionary of all levels
        """
        levels = {}
        
        # Previous day levels
        day = self.get_previous_day_levels(symbol)
        if day:
            levels.update(day.to_dict())
        
        # Pre-market levels
        pm = self.get_premarket_levels(symbol)
        if pm:
            levels.update(pm.to_dict())
        
        # Opening range
        orb = self.get_opening_range(symbol)
        if orb:
            levels.update(orb.to_dict())
        
        return levels


# Package-level convenience functions
def get_key_levels(symbol: str) -> Dict[str, float]:
    """Get all key levels for a symbol."""
    return LevelDetector().get_all_levels(symbol)
