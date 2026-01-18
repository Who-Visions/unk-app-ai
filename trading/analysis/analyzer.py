"""
Unified Technical Analyzer
==========================
Combines all analysis tools into a single interface.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from trading.analysis.indicators import (
    calculate_rsi,
    calculate_sma,
    calculate_ema,
    calculate_macd,
    calculate_bollinger_bands,
    is_overbought,
    is_oversold,
    get_trend_direction
)
from trading.analysis.fibonacci import (
    calculate_retracement_levels,
    find_nearest_support,
    find_nearest_resistance,
    get_fibo_context
)
from trading.analysis.elliott_wave import get_wave_context
from trading.analysis.trend_lines import get_trend_line_context
from trading.analysis.news_sentiment import get_market_sentiment, get_sentiment_signal


@dataclass
class TechnicalAnalysis:
    """Complete technical analysis result for a symbol."""
    symbol: str
    timestamp: datetime
    current_price: float
    
    # Indicators
    rsi: float = 50.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    macd: Dict = field(default_factory=dict)
    bollinger: Dict = field(default_factory=dict)
    
    # Fibonacci
    fibo_levels: Dict = field(default_factory=dict)
    nearest_support: float = 0.0
    nearest_resistance: float = 0.0
    fibo_zone: str = "NEUTRAL"
    
    # Elliott Wave
    wave_pattern: str = "UNKNOWN"
    current_wave: str = "N/A"
    wave_context: str = ""
    
    # Trend Lines
    trend_direction: str = "NEUTRAL"
    support_price: float = 0.0
    resistance_price: float = 0.0
    at_support: bool = False
    at_resistance: bool = False
    
    # News Sentiment
    sentiment: str = "NEUTRAL"
    sentiment_score: int = 0
    sentiment_signal: str = "HOLD"
    
    # Combined Signals
    signals: List[str] = field(default_factory=list)
    overall_signal: str = "HOLD"
    confidence: float = 0.0


class TechnicalAnalyzer:
    """
    Unified technical analyzer that combines all analysis modules.
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        self.price_history: Dict[str, List[float]] = {}
    
    def add_price(self, symbol: str, price: float):
        """Add a price point to history."""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
        # Keep last 200 prices
        if len(self.price_history[symbol]) > 200:
            self.price_history[symbol] = self.price_history[symbol][-200:]
    
    def analyze(self, symbol: str, prices: List[float] = None) -> TechnicalAnalysis:
        """
        Run complete technical analysis on a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "SOL-USD")
            prices: Optional price history (uses stored history if not provided)
        
        Returns:
            TechnicalAnalysis object with all results
        """
        if prices:
            self.price_history[symbol] = prices
        
        history = self.price_history.get(symbol, [])
        current_price = history[-1] if history else 0.0
        
        analysis = TechnicalAnalysis(
            symbol=symbol,
            timestamp=datetime.now(),
            current_price=current_price
        )
        
        if len(history) < 20:
            analysis.signals.append("INSUFFICIENT_DATA")
            return analysis
        
        # === INDICATORS ===
        analysis.rsi = calculate_rsi(history)
        analysis.sma_20 = calculate_sma(history, 20)
        analysis.sma_50 = calculate_sma(history, 50)
        analysis.ema_12 = calculate_ema(history, 12)
        analysis.ema_26 = calculate_ema(history, 26)
        analysis.macd = calculate_macd(history)
        analysis.bollinger = calculate_bollinger_bands(history)
        
        # RSI signals
        if is_oversold(analysis.rsi):
            analysis.signals.append("RSI OVERSOLD (<30)")
        elif is_overbought(analysis.rsi):
            analysis.signals.append("RSI OVERBOUGHT (>70)")
        
        # MACD signals
        if analysis.macd.get("histogram", 0) > 0:
            analysis.signals.append("MACD BULLISH")
        elif analysis.macd.get("histogram", 0) < 0:
            analysis.signals.append("MACD BEARISH")
        
        # Bollinger signals
        if current_price <= analysis.bollinger.get("lower", 0):
            analysis.signals.append("AT LOWER BOLLINGER")
        elif current_price >= analysis.bollinger.get("upper", 0):
            analysis.signals.append("AT UPPER BOLLINGER")
        
        # === FIBONACCI ===
        if len(history) >= 50:
            swing_high = max(history[-50:])
            swing_low = min(history[-50:])
            fibo = get_fibo_context(current_price, swing_high, swing_low)
            
            analysis.fibo_levels = fibo.get("levels", {})
            analysis.fibo_zone = fibo.get("zone", "NEUTRAL")
            
            support = fibo.get("nearest_support", {})
            resist = fibo.get("nearest_resistance", {})
            analysis.nearest_support = support.get("price", 0) if support else 0
            analysis.nearest_resistance = resist.get("price", 0) if resist else 0
            
            if analysis.fibo_zone == "GOLDEN_ZONE":
                analysis.signals.append("IN FIBONACCI GOLDEN ZONE (38.2%-61.8%)")
        
        # === ELLIOTT WAVE ===
        wave = get_wave_context(history)
        analysis.wave_pattern = wave.get("pattern", "UNKNOWN")
        analysis.current_wave = wave.get("current_wave", "N/A")
        analysis.wave_context = wave.get("context", "")
        
        if wave.get("pattern") == "IMPULSE":
            analysis.signals.append(f"ELLIOTT: {wave.get('context', '')}")
        
        # === TREND LINES ===
        trend = get_trend_line_context(history)
        analysis.trend_direction = trend.get("trend", "NEUTRAL")
        analysis.at_support = trend.get("at_support", False)
        analysis.at_resistance = trend.get("at_resistance", False)
        
        if trend.get("support"):
            analysis.support_price = trend["support"].get("price", 0)
        if trend.get("resistance"):
            analysis.resistance_price = trend["resistance"].get("price", 0)
        
        if analysis.at_support:
            analysis.signals.append("AT TREND SUPPORT")
        if analysis.at_resistance:
            analysis.signals.append("AT TREND RESISTANCE")
        
        # === NEWS SENTIMENT ===
        news = get_market_sentiment()
        analysis.sentiment = news.get("sentiment", "NEUTRAL")
        analysis.sentiment_score = news.get("score", 0)
        analysis.sentiment_signal = get_sentiment_signal()
        
        if analysis.sentiment in ["JEFF_PARK_BULLISH", "WILLY_WOO_BEARISH"]:
            analysis.signals.append(f"NEWS: {analysis.sentiment}")
        
        # === OVERALL SIGNAL ===
        analysis.overall_signal, analysis.confidence = self._calculate_overall_signal(analysis)
        
        return analysis
    
    def _calculate_overall_signal(self, analysis: TechnicalAnalysis) -> tuple:
        """
        Calculate overall trading signal from all indicators.
        
        Returns:
            Tuple of (signal, confidence)
        """
        bullish_count = 0
        bearish_count = 0
        total_signals = 0
        
        # RSI
        if analysis.rsi < 30:
            bullish_count += 1
        elif analysis.rsi > 70:
            bearish_count += 1
        total_signals += 1
        
        # Trend
        if analysis.trend_direction == "UPTREND":
            bullish_count += 1
        elif analysis.trend_direction == "DOWNTREND":
            bearish_count += 1
        total_signals += 1
        
        # MACD
        if analysis.macd.get("histogram", 0) > 0:
            bullish_count += 1
        elif analysis.macd.get("histogram", 0) < 0:
            bearish_count += 1
        total_signals += 1
        
        # News
        if analysis.sentiment in ["BULLISH", "JEFF_PARK_BULLISH"]:
            bullish_count += 1
        elif analysis.sentiment in ["BEARISH", "WILLY_WOO_BEARISH"]:
            bearish_count += 1
        total_signals += 1
        
        # Support/Resistance
        if analysis.at_support:
            bullish_count += 1
        if analysis.at_resistance:
            bearish_count += 1
        total_signals += 1
        
        # Determine signal
        if bullish_count >= 4:
            signal = "STRONG_BUY"
        elif bullish_count >= 3:
            signal = "BUY"
        elif bearish_count >= 4:
            signal = "STRONG_SELL"
        elif bearish_count >= 3:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        # Calculate confidence
        max_count = max(bullish_count, bearish_count)
        confidence = max_count / total_signals if total_signals > 0 else 0.0
        
        return signal, round(confidence, 2)
    
    def get_summary(self, symbol: str) -> str:
        """
        Get a human-readable summary of the analysis.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Formatted summary string
        """
        analysis = self.analyze(symbol)
        
        lines = [
            f"=== {symbol} Technical Analysis ===",
            f"Price: ${analysis.current_price:.2f}",
            f"RSI: {analysis.rsi:.1f}",
            f"Trend: {analysis.trend_direction}",
            f"Sentiment: {analysis.sentiment}",
            f"",
            f"Signals:",
        ]
        
        for signal in analysis.signals:
            lines.append(f"  • {signal}")
        
        lines.extend([
            f"",
            f"Overall: {analysis.overall_signal} (Confidence: {analysis.confidence:.0%})"
        ])
        
        return "\n".join(lines)
