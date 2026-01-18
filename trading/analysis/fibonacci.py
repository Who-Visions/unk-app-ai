"""
Fibonacci Retracement Module
=============================
Calculates Fibonacci retracement and extension levels for support/resistance.
"""
from typing import Dict, List, Tuple

# Standard Fibonacci Retracement Levels
FIBO_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

# Fibonacci Extension Levels (for profit targets)
FIBO_EXTENSIONS = [1.0, 1.272, 1.618, 2.0, 2.618]


def calculate_retracement_levels(swing_high: float, swing_low: float) -> Dict[float, float]:
    """
    Calculate Fibonacci retracement levels from swing high to swing low.
    
    In an UPTREND: swing_low is the start, swing_high is the top.
    Retracement levels show where price might find support during pullback.
    
    Args:
        swing_high: The highest price in the swing
        swing_low: The lowest price in the swing
    
    Returns:
        Dict mapping Fib level (0.236, 0.382, etc.) to price level
    """
    if swing_high <= swing_low:
        return {}
    
    price_range = swing_high - swing_low
    
    levels = {}
    for fib in FIBO_LEVELS:
        # Retracement from the high
        level_price = swing_high - (price_range * fib)
        levels[fib] = round(level_price, 4)
    
    return levels


def calculate_extension_levels(
    swing_high: float,
    swing_low: float,
    retracement_low: float = None
) -> Dict[float, float]:
    """
    Calculate Fibonacci extension levels for price targets.
    
    Extensions project where price might go after a retracement completes.
    
    Args:
        swing_high: Original swing high
        swing_low: Original swing low
        retracement_low: Where the retracement ended (default: swing_low)
    
    Returns:
        Dict mapping extension level to price
    """
    if swing_high <= swing_low:
        return {}
    
    price_range = swing_high - swing_low
    start = retracement_low if retracement_low else swing_low
    
    levels = {}
    for ext in FIBO_EXTENSIONS:
        level_price = start + (price_range * ext)
        levels[ext] = round(level_price, 4)
    
    return levels


def find_nearest_support(current_price: float, levels: Dict[float, float]) -> Tuple[float, float]:
    """
    Find the nearest Fibonacci support level below current price.
    
    Args:
        current_price: Current market price
        levels: Fibonacci levels dict from calculate_retracement_levels
    
    Returns:
        Tuple of (fib_level, price) or (0.0, 0.0) if none found
    """
    support_levels = [
        (fib, price) for fib, price in levels.items()
        if price < current_price
    ]
    
    if not support_levels:
        return (0.0, 0.0)
    
    # Return the highest support (closest below current price)
    return max(support_levels, key=lambda x: x[1])


def find_nearest_resistance(current_price: float, levels: Dict[float, float]) -> Tuple[float, float]:
    """
    Find the nearest Fibonacci resistance level above current price.
    
    Args:
        current_price: Current market price
        levels: Fibonacci levels dict from calculate_retracement_levels
    
    Returns:
        Tuple of (fib_level, price) or (0.0, 0.0) if none found
    """
    resistance_levels = [
        (fib, price) for fib, price in levels.items()
        if price > current_price
    ]
    
    if not resistance_levels:
        return (0.0, 0.0)
    
    # Return the lowest resistance (closest above current price)
    return min(resistance_levels, key=lambda x: x[1])


def get_fibo_context(
    current_price: float,
    swing_high: float,
    swing_low: float
) -> Dict:
    """
    Get complete Fibonacci context for current price.
    
    Returns:
        Dict with levels, nearest support, nearest resistance, and zone info
    """
    levels = calculate_retracement_levels(swing_high, swing_low)
    
    if not levels:
        return {"error": "Invalid swing points"}
    
    support_fib, support_price = find_nearest_support(current_price, levels)
    resist_fib, resist_price = find_nearest_resistance(current_price, levels)
    
    # Determine which zone we're in
    zone = "NEUTRAL"
    if support_fib >= 0.618:
        zone = "DEEP_RETRACEMENT"
    elif support_fib >= 0.382:
        zone = "GOLDEN_ZONE"  # 38.2% - 61.8% is the "golden zone"
    elif support_fib > 0:
        zone = "SHALLOW_RETRACEMENT"
    
    return {
        "levels": levels,
        "current_price": current_price,
        "nearest_support": {"fib": support_fib, "price": support_price},
        "nearest_resistance": {"fib": resist_fib, "price": resist_price},
        "zone": zone,
        "swing_high": swing_high,
        "swing_low": swing_low,
    }
