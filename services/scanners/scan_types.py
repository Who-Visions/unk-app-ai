"""
Scanner Type Definitions
=========================
Dataclasses for stock scanning results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class SetupQuality(Enum):
    """Setup quality rating based on criteria met."""
    A = "A"  # Meets all 5 criteria
    B = "B"  # Meets 4/5 criteria
    C = "C"  # Meets 3/5 criteria
    D = "D"  # Meets 2 or fewer


@dataclass
class ScanResult:
    """
    Result from gap scanner.
    
    Ross Cameron's 5 Pillars:
    1. Price: $2-$20 (small account: $1.50-$6)
    2. Gap %: Up 10%+ (small account: 25%+)
    3. Relative Volume: 5x+ average
    4. News: Breaking catalyst
    5. Float: Under 10M shares (small account: <5M)
    """
    symbol: str
    price: float
    gap_percent: float
    relative_volume: float
    float_shares: int
    total_volume: int
    
    # Scoring
    criteria_met: int = 0  # 0-5
    quality: SetupQuality = SetupQuality.D
    
    # Optional data
    news_catalyst: Optional[str] = None
    prev_close: Optional[float] = None
    high_of_day: Optional[float] = None
    low_of_day: Optional[float] = None
    avg_volume: Optional[int] = None
    
    def __post_init__(self):
        """Calculate quality from criteria met."""
        if self.criteria_met >= 5:
            self.quality = SetupQuality.A
        elif self.criteria_met == 4:
            self.quality = SetupQuality.B
        elif self.criteria_met == 3:
            self.quality = SetupQuality.C
        else:
            self.quality = SetupQuality.D
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "gap_percent": round(self.gap_percent, 2),
            "relative_volume": round(self.relative_volume, 2),
            "float_shares": self.float_shares,
            "total_volume": self.total_volume,
            "criteria_met": self.criteria_met,
            "quality": self.quality.value,
            "news_catalyst": self.news_catalyst,
        }


@dataclass
class ScannerConfig:
    """
    Configuration for gap scanner.
    
    Default: Ross Cameron's main account criteria.
    Small account mode uses tighter filters.
    """
    # Price range
    price_min: float = 2.0
    price_max: float = 20.0
    
    # Gap thresholds
    gap_percent_min: float = 10.0
    gap_percent_target: float = 25.0
    
    # Volume
    relative_volume_min: float = 5.0
    
    # Float
    float_max: int = 10_000_000
    
    # News requirement (soft)
    require_news: bool = False
    
    # Results
    max_results: int = 10
    sort_by: str = "gap_percent"  # or "relative_volume"
    
    @classmethod
    def small_account(cls) -> "ScannerConfig":
        """
        Tighter criteria for small accounts.
        From Ross Cameron's Small Account Worksheet.
        """
        return cls(
            price_min=1.50,
            price_max=6.0,
            gap_percent_min=25.0,
            gap_percent_target=50.0,
            relative_volume_min=5.0,
            float_max=5_000_000,
            require_news=True,
            max_results=5,
        )


@dataclass
class TopMover:
    """Simplified top mover for quick scans."""
    symbol: str
    price: float
    change_percent: float
    volume: int
    rank: int = 0
