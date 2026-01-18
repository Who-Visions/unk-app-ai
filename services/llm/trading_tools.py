"""
Trading Tools for Unk
=====================
This module provides function definitions that Gemini can use to execute trades.
All trades are validated by the SafeGovernor before being sent to Robinhood.
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional

# Ensure we can import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from trading.api.brokers.robinhood_crypto import RobinhoodCryptoAPI
from trading.core.governor import SafeGovernor
from trading.integrations.memory import TradingMemory
from trading.core.shared import enterprise_throttle
from trading.analysis.indicators import calculate_rsi, calculate_sma, calculate_macd, calculate_bollinger_bands
from trading.analysis.fibonacci import calculate_retracement_levels, get_fibo_context
from trading.analysis.news_sentiment import get_market_sentiment, get_sentiment_signal
from trading.analysis.analyzer import TechnicalAnalyzer
import logging
import os
import sys
import traceback

# Setup detailed error logging
error_handler = logging.FileHandler("tool_errors.log")
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger("UnkTools")
logger.addHandler(error_handler)
logger.setLevel(logging.ERROR)

# Shared component storage (Lazy)
_api_inst = None
_gov_inst = None
_tm_inst = None

def _get_api():
    global _api_inst
    if _api_inst is None:
        _api_inst = RobinhoodCryptoAPI()
    return _api_inst

def _get_gov():
    global _gov_inst
    if _gov_inst is None:
        _gov_inst = SafeGovernor(config_path="healing_config.json")
    return _gov_inst

def _get_tm():
    global _tm_inst
    if _tm_inst is None:
        _tm_inst = TradingMemory()
    return _tm_inst

def get_holdings() -> str:
    """
    Returns current portfolio holdings. Uses BATCH pricing for speed.
    """
    try:
        enterprise_throttle.acquire()
        api = _get_api()
        holdings = api.get_holdings()
        if not holdings:
            return "You currently have no active positions."
        
        # Senior Pattern: Batch fetch prices to avoid 429 errors
        # API returns List[CryptoHolding], so we must list comprehension carefully
        symbols = [h.asset_code + "-USD" for h in holdings]
        prices = api.get_best_bid_ask(*symbols)
        
        output = "### Current Holdings\n"
        for h in holdings:
            sym = h.asset_code + "-USD"
            qty = float(h.total_quantity)
            if qty == 0:
                continue
            
            p_data = prices.get(sym, {})
            price = float(p_data.get('mark_price', p_data.get('ask_price', 0)))
            value = float(qty) * price
            output += f"- **{sym}**: {qty:.6f} ($ {value:.2f})\n"
        return output
    except Exception as e:
        logger.error(f"Holdings Error: {e}")
        return f"Error fetching holdings: {e}"

def get_price(symbol: str) -> str:
    """
    Returns the current market price for a symbol (e.g., 'BTC-USD').
    """
    try:
        enterprise_throttle.acquire()
        api = _get_api()
        # V2 API uses get_best_bid_ask
        data = api.get_best_bid_ask(symbol)
        if not data or symbol not in data:
            return f"Could not fetch price for {symbol}."
            
        quote = data[symbol]
        price = float(quote.get('ask_price', 0))
        return f"The current price for **{symbol}** is `${price:.2f}`."
    except Exception as e:
        logger.error(f"Price Error: {e}")
        return f"Error fetching price for {symbol}: {e}"

def buy_crypto(symbol: str, amount_usd: float) -> str:
    """
    Executes a market buy order for a specified USD amount.
    All buys are filtered through the Governor's safety checks.
    """
    try:
        enterprise_throttle.acquire()
        gov = _get_gov()
        api = _get_api()
        tm = _get_tm()

        # 1. Check Governor
        can_trade, reason = gov.can_trade(symbol, "buy", amount_usd)
        if not can_trade:
            return f"❌ **Trade Blocked by Governor**: {reason}"
        
        # 2. Execute Trade
        # For simplicity in tools, we use market orders
        result = api.place_order(symbol, "buy", "market", amount_usd=amount_usd)
        
        if result and result.get("id"):
            order_id = result["id"]
            # 3. Log to Memory
            tm.log_trade(
                symbol=symbol,
                side="buy",
                quantity=0, # Will be updated by periodic sync
                price=0,    # Will be updated by periodic sync
                strategy="UnkDirect"
            )
            return f"✅ **Order Placed**: Buying `${amount_usd}` of **{symbol}**. Order ID: `{order_id}`."
        else:
            return f"❌ **Order Failed**: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"Error executing buy: {e}"

def sell_crypto(symbol: str, quantity: float) -> str:
    """
    Executes a market sell order for a specified quantity.
    """
    try:
        enterprise_throttle.acquire()
        gov = _get_gov()
        api = _get_api()
        tm = _get_tm()

        # 1. Check Governor
        can_trade, reason = gov.can_trade(symbol, "sell", quantity)
        if not can_trade:
            return f"❌ **Trade Blocked by Governor**: {reason}"
        
        # 2. Execute Trade
        result = api.place_order(symbol, "sell", "market", quantity=quantity)
        
        if result and result.get("id"):
            order_id = result["id"]
            # 3. Log to Memory
            tm.log_trade(
                symbol=symbol,
                side="sell",
                quantity=quantity,
                price=0, # Updated by sync
                strategy="UnkDirect"
            )
            return f"✅ **Order Placed**: Selling `{quantity}` of **{symbol}**. Order ID: `{order_id}`."
        else:
            return f"❌ **Order Failed**: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Sell Crypto Error: {e}")
        return f"Error executing sell: {e}"

# =============================================================================
# TECHNICAL ANALYSIS TOOLS
# =============================================================================

# Shared analyzer instance
_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = TechnicalAnalyzer()
    return _analyzer

def get_rsi(symbol: str) -> str:
    """
    Returns the RSI (Relative Strength Index) for a symbol.
    RSI > 70 = overbought, RSI < 30 = oversold.
    """
    try:
        analyzer = _get_analyzer()
        history = analyzer.price_history.get(symbol, [])
        
        if len(history) < 14:
            # Try to build history from API
            enterprise_throttle.acquire()
            api = _get_api()
            # V2 API pattern
            data = api.get_best_bid_ask(symbol)
            if data and symbol in data:
                current_price = float(data[symbol].get('ask_price', 0))
                if current_price > 0:
                    analyzer.add_price(symbol, current_price)
                    history = analyzer.price_history.get(symbol, [])
        
        if len(history) < 14:
            return f"Need more price data for {symbol}. Have {len(history)}/14 data points."
        
        rsi = calculate_rsi(history)
        
        status = "NEUTRAL"
        if rsi > 70:
            status = "OVERBOUGHT ⚠️"
        elif rsi < 30:
            status = "OVERSOLD 📉"
        elif rsi > 50:
            status = "BULLISH"
        else:
            status = "BEARISH"
        
        return f"**{symbol} RSI (14)**: `{rsi:.1f}` - {status}"
    except Exception as e:
        logger.error(f"RSI Error: {e}")
        return f"Error calculating RSI: {e}"


def get_fibonacci_levels(symbol: str) -> str:
    """
    Returns Fibonacci retracement levels for a symbol based on recent price action.
    Key levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
    """
    try:
        analyzer = _get_analyzer()
        history = analyzer.price_history.get(symbol, [])
        
        if len(history) < 20:
            return f"Need more price data for {symbol}. Have {len(history)}/20 data points."
        
        swing_high = max(history[-50:]) if len(history) >= 50 else max(history)
        swing_low = min(history[-50:]) if len(history) >= 50 else min(history)
        current_price = history[-1]
        
        fibo = get_fibo_context(current_price, swing_high, swing_low)
        levels = fibo.get("levels", {})
        
        output = f"**{symbol} Fibonacci Levels**\n"
        output += f"- Swing High: `${swing_high:.2f}`\n"
        output += f"- Swing Low: `${swing_low:.2f}`\n"
        output += f"- Current: `${current_price:.2f}`\n\n"
        output += "**Retracement Levels:**\n"
        for level in [0.236, 0.382, 0.5, 0.618, 0.786]:
            price = levels.get(level, 0)
            marker = " ◀️" if abs(current_price - price) / price < 0.02 else ""
            output += f"- {level*100:.1f}%: `${price:.2f}`{marker}\n"
        
        return output
    except Exception as e:
        logger.error(f"Fibonacci Error: {e}")
        return f"Error calculating Fibonacci: {e}"


def get_news_sentiment() -> str:
    """
    Returns the current market news sentiment from CryptoCompare and NewsData.io.
    """
    try:
        data = get_market_sentiment()
        sentiment = data.get("sentiment", "NEUTRAL")
        score = data.get("score", 0)
        articles = data.get("articles", [])[:5]
        
        output = f"**Market Sentiment**: `{sentiment}` (Score: {score})\n\n"
        output += "**Top Headlines:**\n"
        for art in articles:
            title = art.get("title", "")[:60]
            s_score = art.get("sentiment_score", 0)
            indicator = "🟢" if s_score > 0 else "🔴" if s_score < 0 else "⚪"
            output += f"{indicator} {title}...\n"
        
        signal = get_sentiment_signal()
        output += f"\n**Signal**: `{signal}`"
        return output
    except Exception as e:
        return f"Error fetching sentiment: {e}"


def get_technical_analysis(symbol: str) -> str:
    """
    Returns a full technical analysis for a symbol including RSI, MACD, Bollinger Bands,
    Fibonacci levels, and news sentiment.
    """
    try:
        analyzer = _get_analyzer()
        history = analyzer.price_history.get(symbol, [])
        
        if len(history) < 20:
            # Try to add current price
            enterprise_throttle.acquire()
            api = _get_api()
            # V2 API pattern
            data = api.get_best_bid_ask(symbol)
            if data and symbol in data:
                current_price = float(data[symbol].get('ask_price', 0))
                if current_price > 0:
                    analyzer.add_price(symbol, current_price)
                    history = analyzer.price_history.get(symbol, [])
        
        if len(history) < 14:
            return f"Need more price data for {symbol}. Have {len(history)}/14 data points."
        
        analysis = analyzer.analyze(symbol, history)
        
        output = f"## {symbol} Technical Analysis\n\n"
        output += "### Indicators\n"
        output += f"- **RSI (14)**: `{analysis.rsi:.1f}`\n"
        output += f"- **SMA 20**: `${analysis.sma_20:.2f}`\n"
        output += f"- **MACD**: `{analysis.macd.get('histogram', 0):.4f}`\n"
        output += f"- **Bollinger**: Upper `${analysis.bollinger.get('upper', 0):.2f}` | Lower `${analysis.bollinger.get('lower', 0):.2f}`\n\n"
        
        output += "### Fibonacci\n"
        output += f"- Support: `${analysis.nearest_support:.2f}`\n"
        output += f"- Resistance: `${analysis.nearest_resistance:.2f}`\n\n"
        
        output += "### Signals\n"
        for sig in analysis.signals[:5]:
            output += f"- {sig}\n"
        
        output += f"\n### Overall: **{analysis.overall_signal}** (Confidence: {analysis.confidence:.0%})"
        return output
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        return f"Error running analysis: {e}"


# Tool Definitions for Gemini SDK
TRADING_TOOLS = [
    # Trading Actions
    get_holdings,
    get_price,
    buy_crypto,
    sell_crypto,
    # Technical Analysis
    get_rsi,
    get_fibonacci_levels,
    get_news_sentiment,
    get_technical_analysis,
]
