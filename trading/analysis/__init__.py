"""
Technical Analysis Module
=========================
Comprehensive technical analysis tools for trading.

Components:
- indicators: RSI, SMA, EMA, MACD, Bollinger Bands
- fibonacci: Retracement and extension levels
- elliott_wave: Wave pattern detection
- trend_lines: Support/resistance detection
- news_sentiment: NewsData.io + CryptoCompare integration
- analyzer: Unified analyzer combining all tools
"""

from trading.analysis.indicators import (
    calculate_rsi,
    calculate_sma,
    calculate_ema,
    calculate_macd,
    calculate_bollinger_bands,
    is_overbought,
    is_oversold,
)
from trading.analysis.fibonacci import (
    calculate_retracement_levels,
    calculate_extension_levels,
    find_nearest_support,
    find_nearest_resistance,
    FIBO_LEVELS,
    FIBO_EXTENSIONS,
)
from trading.analysis.analyzer import TechnicalAnalyzer, TechnicalAnalysis

__all__ = [
    # Indicators
    "calculate_rsi",
    "calculate_sma",
    "calculate_ema",
    "calculate_macd",
    "calculate_bollinger_bands",
    "is_overbought",
    "is_oversold",
    # Fibonacci
    "calculate_retracement_levels",
    "calculate_extension_levels",
    "find_nearest_support",
    "find_nearest_resistance",
    "FIBO_LEVELS",
    "FIBO_EXTENSIONS",
    # Analyzer
    "TechnicalAnalyzer",
    "TechnicalAnalysis",
]
