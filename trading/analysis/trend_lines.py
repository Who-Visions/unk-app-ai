"""
Trend Line Analysis Module
==========================
Automated detection of support and resistance trend lines.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class TrendLine:
    """Represents a trend line (support or resistance)."""
    line_type: str  # "support" or "resistance"
    slope: float
    intercept: float
    strength: int  # Number of price touches
    start_idx: int
    end_idx: int
    start_price: float
    end_price: float
    
    def price_at(self, idx: int) -> float:
        """Calculate the trend line price at a given index."""
        return self.slope * idx + self.intercept


def find_pivot_points(prices: List[float], window: int = 5) -> Tuple[List[Tuple], List[Tuple]]:
    """
    Find pivot highs and lows in price data.
    
    Args:
        prices: List of closing prices
        window: Number of bars to look left/right
    
    Returns:
        Tuple of (pivot_highs, pivot_lows) where each is [(idx, price), ...]
    """
    if len(prices) < window * 2 + 1:
        return [], []
    
    pivot_highs = []
    pivot_lows = []
    
    for i in range(window, len(prices) - window):
        # Check for pivot high
        is_pivot_high = True
        for j in range(1, window + 1):
            if prices[i] < prices[i - j] or prices[i] < prices[i + j]:
                is_pivot_high = False
                break
        if is_pivot_high:
            pivot_highs.append((i, prices[i]))
        
        # Check for pivot low
        is_pivot_low = True
        for j in range(1, window + 1):
            if prices[i] > prices[i - j] or prices[i] > prices[i + j]:
                is_pivot_low = False
                break
        if is_pivot_low:
            pivot_lows.append((i, prices[i]))
    
    return pivot_highs, pivot_lows


def calculate_line(points: List[Tuple[int, float]]) -> Tuple[float, float]:
    """
    Calculate slope and intercept using least squares regression.
    
    Args:
        points: List of (x, y) points
    
    Returns:
        Tuple of (slope, intercept)
    """
    if len(points) < 2:
        return 0.0, 0.0
    
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)
    
    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        return 0.0, sum_y / n
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    return slope, intercept


def find_support_line(prices: List[float], window: int = 5) -> Optional[TrendLine]:
    """
    Find the best support trend line.
    
    Args:
        prices: List of closing prices
        window: Pivot detection window
    
    Returns:
        TrendLine object or None if no valid line found
    """
    _, pivot_lows = find_pivot_points(prices, window)
    
    if len(pivot_lows) < 2:
        return None
    
    # Use the last 3-5 pivot lows to form support line
    recent_lows = pivot_lows[-5:] if len(pivot_lows) >= 5 else pivot_lows
    
    slope, intercept = calculate_line(recent_lows)
    
    # Count how many times price "touches" this line
    touches = 0
    tolerance = 0.02  # 2% tolerance
    for idx, price in enumerate(prices):
        line_price = slope * idx + intercept
        if abs(price - line_price) / line_price < tolerance:
            touches += 1
    
    return TrendLine(
        line_type="support",
        slope=slope,
        intercept=intercept,
        strength=min(touches, 10),  # Cap at 10
        start_idx=recent_lows[0][0],
        end_idx=recent_lows[-1][0],
        start_price=recent_lows[0][1],
        end_price=recent_lows[-1][1]
    )


def find_resistance_line(prices: List[float], window: int = 5) -> Optional[TrendLine]:
    """
    Find the best resistance trend line.
    
    Args:
        prices: List of closing prices
        window: Pivot detection window
    
    Returns:
        TrendLine object or None if no valid line found
    """
    pivot_highs, _ = find_pivot_points(prices, window)
    
    if len(pivot_highs) < 2:
        return None
    
    # Use the last 3-5 pivot highs to form resistance line
    recent_highs = pivot_highs[-5:] if len(pivot_highs) >= 5 else pivot_highs
    
    slope, intercept = calculate_line(recent_highs)
    
    # Count touches
    touches = 0
    tolerance = 0.02
    for idx, price in enumerate(prices):
        line_price = slope * idx + intercept
        if abs(price - line_price) / line_price < tolerance:
            touches += 1
    
    return TrendLine(
        line_type="resistance",
        slope=slope,
        intercept=intercept,
        strength=min(touches, 10),
        start_idx=recent_highs[0][0],
        end_idx=recent_highs[-1][0],
        start_price=recent_highs[0][1],
        end_price=recent_highs[-1][1]
    )


def is_at_support(
    current_price: float,
    support: TrendLine,
    current_idx: int,
    tolerance: float = 0.02
) -> bool:
    """Check if price is at or near support line."""
    if not support:
        return False
    line_price = support.price_at(current_idx)
    return abs(current_price - line_price) / line_price < tolerance


def is_at_resistance(
    current_price: float,
    resistance: TrendLine,
    current_idx: int,
    tolerance: float = 0.02
) -> bool:
    """Check if price is at or near resistance line."""
    if not resistance:
        return False
    line_price = resistance.price_at(current_idx)
    return abs(current_price - line_price) / line_price < tolerance


def get_trend_line_context(prices: List[float], window: int = 5) -> Dict:
    """
    Get complete trend line analysis for current price.
    
    Returns:
        Dict with support, resistance, and price position info
    """
    if len(prices) < 20:
        return {
            "status": "INSUFFICIENT_DATA",
            "support": None,
            "resistance": None,
            "at_support": False,
            "at_resistance": False
        }
    
    support = find_support_line(prices, window)
    resistance = find_resistance_line(prices, window)
    
    current_price = prices[-1]
    current_idx = len(prices) - 1
    
    at_support = is_at_support(current_price, support, current_idx) if support else False
    at_resistance = is_at_resistance(current_price, resistance, current_idx) if resistance else False
    
    # Determine trend direction from slope
    trend = "NEUTRAL"
    if support and resistance:
        avg_slope = (support.slope + resistance.slope) / 2
        if avg_slope > 0.001:
            trend = "UPTREND"
        elif avg_slope < -0.001:
            trend = "DOWNTREND"
    
    return {
        "status": "OK",
        "trend": trend,
        "support": {
            "price": support.price_at(current_idx) if support else None,
            "strength": support.strength if support else 0,
            "slope": support.slope if support else 0
        } if support else None,
        "resistance": {
            "price": resistance.price_at(current_idx) if resistance else None,
            "strength": resistance.strength if resistance else 0,
            "slope": resistance.slope if resistance else 0
        } if resistance else None,
        "at_support": at_support,
        "at_resistance": at_resistance,
        "signals": [
            "AT SUPPORT - Potential bounce" if at_support else None,
            "AT RESISTANCE - Potential rejection" if at_resistance else None
        ]
    }
