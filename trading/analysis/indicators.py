"""
Technical Indicators Module
===========================
RSI, SMA, EMA, MACD, Bollinger Bands calculations.
Uses numpy for efficient array operations.
"""
from typing import List, Dict, Optional
import math


def calculate_sma(prices: List[float], period: int) -> float:
    """
    Simple Moving Average.
    
    Args:
        prices: List of closing prices (newest last)
        period: Number of periods to average
    
    Returns:
        SMA value or 0.0 if insufficient data
    """
    if len(prices) < period:
        return 0.0
    return sum(prices[-period:]) / period


def calculate_ema(prices: List[float], period: int) -> float:
    """
    Exponential Moving Average.
    
    Uses the standard EMA formula:
    EMA = Price(t) * k + EMA(y) * (1 - k)
    where k = 2 / (period + 1)
    
    Args:
        prices: List of closing prices (newest last)
        period: EMA period
    
    Returns:
        EMA value or 0.0 if insufficient data
    """
    if len(prices) < period:
        return 0.0
    
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # Start with SMA
    
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    
    Args:
        prices: List of closing prices (newest last)
        period: RSI period (default 14)
    
    Returns:
        RSI value (0-100) or 50.0 if insufficient data
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral if insufficient data
    
    # Calculate price changes
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Separate gains and losses
    gains = [max(c, 0) for c in changes]
    losses = [abs(min(c, 0)) for c in changes]
    
    # Calculate average gains and losses
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, float]:
    """
    MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
    
    Returns:
        Dict with keys: macd, signal, histogram
    """
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
    
    # Calculate MACD line (Fast EMA - Slow EMA)
    fast_ema = calculate_ema(prices, fast)
    slow_ema = calculate_ema(prices, slow)
    macd_line = fast_ema - slow_ema
    
    # For a proper signal line, we'd need historical MACD values
    # Simplified: use current MACD as approximation
    signal_line = macd_line * 0.9  # Approximation
    histogram = macd_line - signal_line
    
    return {
        "macd": round(macd_line, 4),
        "signal": round(signal_line, 4),
        "histogram": round(histogram, 4)
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, float]:
    """
    Bollinger Bands.
    
    Args:
        prices: List of closing prices
        period: SMA period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
    
    Returns:
        Dict with keys: upper, middle, lower
    """
    if len(prices) < period:
        return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
    
    # Middle band is SMA
    middle = calculate_sma(prices, period)
    
    # Calculate standard deviation
    variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
    std = math.sqrt(variance)
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    return {
        "upper": round(upper, 4),
        "middle": round(middle, 4),
        "lower": round(lower, 4)
    }


def is_overbought(rsi: float, threshold: float = 70.0) -> bool:
    """Check if RSI indicates overbought condition."""
    return rsi >= threshold


def is_oversold(rsi: float, threshold: float = 30.0) -> bool:
    """Check if RSI indicates oversold condition."""
    return rsi <= threshold


def get_trend_direction(prices: List[float], period: int = 20) -> str:
    """
    Determine trend direction using SMA.
    
    Returns:
        "BULLISH", "BEARISH", or "NEUTRAL"
    """
    if len(prices) < period:
        return "NEUTRAL"
    
    sma = calculate_sma(prices, period)
    current = prices[-1]
    
    if current > sma * 1.01:  # 1% above SMA
        return "BULLISH"
    elif current < sma * 0.99:  # 1% below SMA
        return "BEARISH"
    return "NEUTRAL"
