"""
Stock Skill - Enhanced Edition
==============================
AI-powered stock analysis with technical indicators from stockstats,
real-time data from yfinance, and Gemini AI insights.

Patterns from:
- MachineLearningStocks (RandomForest, key financial features)
- NGYB/Stocks (yfinance integration, MCP patterns)
- stockstats (RSI, MACD, Bollinger, Supertrend, ATR, etc.)
"""
import asyncio
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import GOOGLE_GENAI_API_KEY, logger

# Try to import yfinance for real-time data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

# Try to import pandas and stockstats for technical indicators
try:
    import pandas as pd
    from stockstats import wrap
    STOCKSTATS_AVAILABLE = True
except ImportError:
    STOCKSTATS_AVAILABLE = False
    pd = None
    wrap = None

# Key financial features for stock analysis
FINANCIAL_FEATURES = [
    "Market Cap", "Trailing P/E", "Forward P/E", "PEG Ratio",
    "Price/Sales", "Price/Book", "Profit Margin", "Operating Margin",
    "Return on Assets", "Return on Equity", "Revenue Growth",
    "Quarterly Revenue Growth", "EBITDA", "Total Debt/Equity",
    "Current Ratio", "Book Value Per Share", "Beta",
    "52 Week High", "52 Week Low", "50-Day Moving Average",
    "200-Day Moving Average",
]

# Technical indicator thresholds
TECHNICALS = {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_signal_cross": True,
    "boll_squeeze": 0.05,
}


def get_stock_info_yfinance(symbol: str) -> Dict[str, Any]:
    """
    Get stock data from Yahoo Finance.
    """
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance not installed"}
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        price = info.get('currentPrice') or info.get('previousClose', 0)
        
        try:
            targets = ticker.analyst_price_targets
            target_mean = targets.get('mean') if targets else None
        except Exception as e:
            logger.warning(f"analyst_targets failed for {symbol}: {e}")
            target_mean = None
        
        return {
            "symbol": symbol.upper(),
            "price": price,
            "analyst_target": target_mean,
            "market_cap": info.get('marketCap'),
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "dividend_yield": info.get('dividendYield'),
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "roe": info.get('returnOnEquity'),
            "roa": info.get('returnOnAssets'),
            "revenue_growth": info.get('revenueGrowth'),
            "debt_to_equity": info.get('debtToEquity'),
            "current_ratio": info.get('currentRatio'),
            "beta": info.get('beta'),
            "52_week_high": info.get('fiftyTwoWeekHigh'),
            "52_week_low": info.get('fiftyTwoWeekLow'),
            "50_day_avg": info.get('fiftyDayAverage'),
            "200_day_avg": info.get('twoHundredDayAverage'),
            "volume": info.get('volume'),
            "avg_volume": info.get('averageVolume'),
            "sector": info.get('sector'),
            "industry": info.get('industry'),
            "recommendation": info.get('recommendationKey'),
            "short_interest": info.get('shortPercentOfFloat'),
        }
    except Exception as e:
        logger.error(f"yfinance error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def get_technical_indicators(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """
    Calculate technical indicators using stockstats.
    
    Returns RSI, MACD, Bollinger Bands, Supertrend, ATR, etc.
    """
    if not YFINANCE_AVAILABLE or not STOCKSTATS_AVAILABLE:
        return {"error": "yfinance or stockstats not available"}
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": "No historical data available"}
        
        # Rename columns to lowercase for stockstats
        hist.columns = [c.lower() for c in hist.columns]
        
        # Wrap with stockstats
        stock = wrap(hist)
        
        # Calculate indicators
        indicators = {}
        
        # RSI - Relative Strength Index
        try:
            indicators["rsi_14"] = float(stock["rsi_14"].iloc[-1])
            indicators["rsi_signal"] = (
                "oversold" if indicators["rsi_14"] < 30 else
                "overbought" if indicators["rsi_14"] > 70 else
                "neutral"
            )
        except Exception as e:
            logger.warning(f"RSI calculation failed for {symbol}: {e}")
            indicators["rsi_14"] = None
        
        # MACD
        try:
            indicators["macd"] = float(stock["macd"].iloc[-1])
            indicators["macd_signal"] = float(stock["macds"].iloc[-1])
            indicators["macd_hist"] = float(stock["macdh"].iloc[-1])
            indicators["macd_cross"] = (
                "bullish" if indicators["macd"] > indicators["macd_signal"] else
                "bearish"
            )
        except Exception as e:
            logger.warning(f"MACD calculation failed for {symbol}: {e}")
            indicators["macd"] = None
        
        # Bollinger Bands
        try:
            indicators["boll_upper"] = float(stock["boll_ub"].iloc[-1])
            indicators["boll_middle"] = float(stock["boll"].iloc[-1])
            indicators["boll_lower"] = float(stock["boll_lb"].iloc[-1])
            current = float(hist["close"].iloc[-1])
            indicators["boll_position"] = (
                "above_upper" if current > indicators["boll_upper"] else
                "below_lower" if current < indicators["boll_lower"] else
                "between"
            )
            # Squeeze detection
            band_width = (indicators["boll_upper"] - indicators["boll_lower"]) / indicators["boll_middle"]
            indicators["boll_squeeze"] = band_width < 0.05
        except Exception as e:
            logger.warning(f"Bollinger Bands calculation failed for {symbol}: {e}")
            indicators["boll_upper"] = None
        
        # ATR - Average True Range (volatility)
        try:
            indicators["atr_14"] = float(stock["atr_14"].iloc[-1])
            indicators["atr_percent"] = (indicators["atr_14"] / float(hist["close"].iloc[-1])) * 100
        except Exception as e:
            logger.warning(f"ATR calculation failed for {symbol}: {e}")
            indicators["atr_14"] = None
        
        # Stochastic RSI
        try:
            indicators["stochrsi"] = float(stock["stochrsi_14"].iloc[-1])
        except Exception as e:
            logger.warning(f"StochRSI calculation failed for {symbol}: {e}")
            indicators["stochrsi"] = None
        
        # Williams %R
        try:
            indicators["wr_14"] = float(stock["wr_14"].iloc[-1])
        except Exception as e:
            logger.warning(f"Williams R calculation failed for {symbol}: {e}")
            indicators["wr_14"] = None
        
        # CCI - Commodity Channel Index
        try:
            indicators["cci_14"] = float(stock["cci_14"].iloc[-1])
        except Exception as e:
            logger.warning(f"CCI calculation failed for {symbol}: {e}")
            indicators["cci_14"] = None
        
        # Moving Averages
        try:
            indicators["close"] = float(hist["close"].iloc[-1])
            indicators["sma_20"] = float(stock["close_20_sma"].iloc[-1])
            indicators["sma_50"] = float(stock["close_50_sma"].iloc[-1])
            indicators["ema_12"] = float(stock["close_12_ema"].iloc[-1])
            
            # Trend based on MAs
            if indicators["close"] > indicators["sma_20"] > indicators["sma_50"]:
                indicators["ma_trend"] = "bullish"
            elif indicators["close"] < indicators["sma_20"] < indicators["sma_50"]:
                indicators["ma_trend"] = "bearish"
            else:
                indicators["ma_trend"] = "mixed"
        except Exception as e:
            logger.warning(f"MA trend calculation failed for {symbol}: {e}")
            indicators["ma_trend"] = None
        
        # Volume
        try:
            indicators["volume"] = int(hist["volume"].iloc[-1])
            indicators["volume_sma_20"] = float(stock["volume_20_sma"].iloc[-1])
            indicators["volume_ratio"] = indicators["volume"] / indicators["volume_sma_20"]
        except Exception as e:
            logger.warning(f"Volume calculation failed for {symbol}: {e}")
            indicators["volume_ratio"] = None
        
        return indicators
        
    except Exception as e:
        logger.error(f"Technical indicators error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def calculate_technical_score(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a technical score based on indicators.
    """
    score = 0
    signals = []
    
    # RSI scoring
    rsi = indicators.get("rsi_14")
    if rsi:
        if rsi < 30:
            score += 2
            signals.append("RSI oversold (bullish reversal)")
        elif rsi < 40:
            score += 1
            signals.append("RSI approaching oversold")
        elif rsi > 70:
            score -= 2
            signals.append("RSI overbought (bearish reversal)")
        elif rsi > 60:
            score -= 1
            signals.append("RSI approaching overbought")
    
    # MACD scoring
    macd_cross = indicators.get("macd_cross")
    if macd_cross == "bullish":
        score += 1
        signals.append("MACD bullish crossover")
    elif macd_cross == "bearish":
        score -= 1
        signals.append("MACD bearish crossover")
    
    # Bollinger Bands
    boll_pos = indicators.get("boll_position")
    if boll_pos == "below_lower":
        score += 2
        signals.append("Price below Bollinger lower band")
    elif boll_pos == "above_upper":
        score -= 2
        signals.append("Price above Bollinger upper band")
    
    if indicators.get("boll_squeeze"):
        signals.append("Bollinger squeeze detected (expect breakout)")
    
    # Moving average trend
    ma_trend = indicators.get("ma_trend")
    if ma_trend == "bullish":
        score += 1
        signals.append("MA trend bullish")
    elif ma_trend == "bearish":
        score -= 1
        signals.append("MA trend bearish")
    
    # Volume
    vol_ratio = indicators.get("volume_ratio")
    if vol_ratio and vol_ratio > 1.5:
        score += 1 if score > 0 else -1  # Confirms trend
        signals.append("High volume confirming move")
    
    # Stochastic RSI
    stochrsi = indicators.get("stochrsi")
    if stochrsi:
        if stochrsi < 20:
            score += 1
            signals.append("Stochastic RSI oversold")
        elif stochrsi > 80:
            score -= 1
            signals.append("Stochastic RSI overbought")
    
    # Determine signal
    if score >= 3:
        signal = "strong_buy"
        confidence = min(0.85, 0.6 + (score * 0.05))
    elif score >= 1:
        signal = "buy"
        confidence = min(0.7, 0.5 + (score * 0.05))
    elif score <= -3:
        signal = "strong_sell"
        confidence = min(0.85, 0.6 + (abs(score) * 0.05))
    elif score <= -1:
        signal = "sell"
        confidence = min(0.7, 0.5 + (abs(score) * 0.05))
    else:
        signal = "neutral"
        confidence = 0.5
    
    return {
        "technical_score": score,
        "signal": signal,
        "confidence": confidence,
        "signals": signals
    }


def calculate_stock_score(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a fundamental score based on key metrics.
    """
    score = 0
    factors = []
    
    pe = info.get('pe_ratio')
    if pe:
        if pe < 15:
            score += 2
            factors.append("Low P/E (undervalued)")
        elif pe < 25:
            score += 1
            factors.append("Reasonable P/E")
        elif pe > 50:
            score -= 1
            factors.append("High P/E (expensive)")
    
    growth = info.get('revenue_growth')
    if growth:
        if growth > 0.2:
            score += 2
            factors.append("Strong revenue growth >20%")
        elif growth > 0.1:
            score += 1
            factors.append("Solid revenue growth >10%")
        elif growth < 0:
            score -= 1
            factors.append("Negative revenue growth")
    
    roe = info.get('roe')
    if roe:
        if roe > 0.2:
            score += 2
            factors.append("Excellent ROE >20%")
        elif roe > 0.1:
            score += 1
            factors.append("Good ROE >10%")
    
    margin = info.get('profit_margin')
    if margin:
        if margin > 0.15:
            score += 1
            factors.append("Strong profit margins")
    
    debt = info.get('debt_to_equity')
    if debt is not None:
        if debt < 0.5:
            score += 1
            factors.append("Low debt")
        elif debt > 2:
            score -= 1
            factors.append("High debt levels")
    
    current = info.get('current_ratio')
    if current:
        if current > 2:
            score += 1
            factors.append("Strong liquidity")
        elif current < 1:
            score -= 1
            factors.append("Liquidity concerns")
    
    price = info.get('price', 0)
    high52 = info.get('52_week_high', 0)
    low52 = info.get('52_week_low', 0)
    
    if price and high52 and low52 and high52 > low52:
        position = (price - low52) / (high52 - low52)
        if position < 0.3:
            score += 1
            factors.append("Near 52-week low (potential value)")
        elif position > 0.9:
            score -= 1
            factors.append("Near 52-week high (extended)")
    
    rec = info.get('recommendation')
    if rec:
        if rec in ['buy', 'strongBuy']:
            score += 1
            factors.append(f"Analyst: {rec}")
        elif rec in ['sell', 'strongSell']:
            score -= 1
            factors.append(f"Analyst: {rec}")
    
    if score >= 5:
        action = "strong_buy"
        confidence = min(0.9, 0.6 + (score * 0.05))
    elif score >= 3:
        action = "buy"
        confidence = min(0.8, 0.5 + (score * 0.05))
    elif score >= 1:
        action = "hold"
        confidence = 0.5
    elif score >= -1:
        action = "watch"
        confidence = 0.4
    else:
        action = "avoid"
        confidence = max(0.3, 0.6 - (abs(score) * 0.1))
    
    return {
        "fundamental_score": score,
        "action": action,
        "confidence": confidence,
        "factors": factors
    }


def get_combined_analysis(symbol: str) -> Dict[str, Any]:
    """
    Get combined fundamental + technical analysis.
    """
    result = {"symbol": symbol.upper()}
    
    # Fundamental data
    if YFINANCE_AVAILABLE:
        fund_data = get_stock_info_yfinance(symbol)
        if "error" not in fund_data:
            fund_score = calculate_stock_score(fund_data)
            result["fundamentals"] = fund_data
            result["fundamental_analysis"] = fund_score
    
    # Technical data
    if YFINANCE_AVAILABLE and STOCKSTATS_AVAILABLE:
        tech_data = get_technical_indicators(symbol)
        if "error" not in tech_data:
            tech_score = calculate_technical_score(tech_data)
            result["technicals"] = tech_data
            result["technical_analysis"] = tech_score
    
    # Combined score
    fund_score = result.get("fundamental_analysis", {}).get("fundamental_score", 0)
    tech_score = result.get("technical_analysis", {}).get("technical_score", 0)
    
    combined = fund_score + tech_score
    
    if combined >= 5:
        result["combined_signal"] = "STRONG BUY"
        result["combined_confidence"] = min(0.9, 0.65 + (combined * 0.03))
    elif combined >= 2:
        result["combined_signal"] = "BUY"
        result["combined_confidence"] = min(0.8, 0.55 + (combined * 0.03))
    elif combined >= -1:
        result["combined_signal"] = "HOLD"
        result["combined_confidence"] = 0.5
    elif combined >= -4:
        result["combined_signal"] = "SELL"
        result["combined_confidence"] = min(0.75, 0.5 + (abs(combined) * 0.03))
    else:
        result["combined_signal"] = "STRONG SELL"
        result["combined_confidence"] = min(0.85, 0.6 + (abs(combined) * 0.03))
    
    result["combined_score"] = combined
    
    return result


async def get_stock_quote(
    symbol: str,
    model_alias: str = "gemini_3_flash"
) -> Dict[str, Any]:
    """
    Get real-time stock quote + technicals.
    """
    if YFINANCE_AVAILABLE:
        # Get fundamental data
        yf_data = await asyncio.to_thread(get_stock_info_yfinance, symbol)
        
        if "error" not in yf_data:
            # Add fundamental scoring
            fund_score = calculate_stock_score(yf_data)
            yf_data.update(fund_score)
            
            # Add technical analysis if available
            if STOCKSTATS_AVAILABLE:
                tech_data = await asyncio.to_thread(get_technical_indicators, symbol)
                if "error" not in tech_data:
                    tech_score = calculate_technical_score(tech_data)
                    yf_data["technicals"] = tech_data
                    yf_data["technical_analysis"] = tech_score
            
            return yf_data
    
    # Fallback to Gemini
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)
    
    prompt = f"""Get the current stock price and trading data for {symbol}.
    Include: price, change, volume, day range, market cap."""

    def _run_search():
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )

    try:
        response = await asyncio.to_thread(_run_search)
        return {
            "symbol": symbol.upper(),
            "text": response.text,
            "raw_response": True
        }
    except Exception as e:
        logger.error(f"Stock quote error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


async def analyze_stock(
    symbol: str,
    analysis_type: str = "full",
    model_alias: str = "gemini_3_flash"
) -> Dict[str, Any]:
    """
    Comprehensive stock analysis with technicals + fundamentals + AI.
    """
    # Get combined analysis
    stock_data = {}
    if YFINANCE_AVAILABLE:
        stock_data = await asyncio.to_thread(get_combined_analysis, symbol)
    
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)
    
    # Build context
    context = ""
    if stock_data and "error" not in stock_data:
        fund = stock_data.get("fundamental_analysis", {})
        tech = stock_data.get("technical_analysis", {})
        
        context = f"""
Real-time data for {symbol}:
- Price: ${stock_data.get('fundamentals', {}).get('price', 'N/A')}
- Combined Signal: {stock_data.get('combined_signal', 'N/A')}
- Combined Score: {stock_data.get('combined_score', 0)}

FUNDAMENTAL ANALYSIS (Score: {fund.get('fundamental_score', 0)}):
{', '.join(fund.get('factors', [])[:5])}

TECHNICAL ANALYSIS (Score: {tech.get('technical_score', 0)}):
{', '.join(tech.get('signals', [])[:5])}

RSI: {stock_data.get('technicals', {}).get('rsi_14', 'N/A')}
MACD: {stock_data.get('technicals', {}).get('macd_cross', 'N/A')}
MA Trend: {stock_data.get('technicals', {}).get('ma_trend', 'N/A')}
"""

    prompt = f"""Comprehensive analysis for {symbol}.

{context}

Provide:
1. TRADING OUTLOOK - short term (1-5 days) and medium term (1-4 weeks)
2. KEY LEVELS - support and resistance
3. ENTRY/EXIT - specific price levels for trades
4. RISKS - what could go wrong
5. VERDICT - BUY/HOLD/SELL with confidence percentage

Be specific and actionable."""

    def _run_analysis():
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )

    try:
        response = await asyncio.to_thread(_run_analysis)
        
        return {
            "symbol": symbol.upper(),
            "analysis_type": analysis_type,
            "analysis": response.text,
            "stock_data": stock_data,
            "grounding_sources": []
        }
    except Exception as e:
        logger.error(f"Stock analysis error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


async def get_market_sentiment(
    symbol: str,
    model_alias: str = "gemini_3_flash"
) -> Dict[str, Any]:
    """
    Analyze market sentiment for a stock.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)
    
    prompt = f"""Analyze the current market sentiment for {symbol} stock:
    
    1. NEWS SENTIMENT: Recent headlines and impact
    2. SOCIAL SENTIMENT: Retail investor buzz  
    3. ANALYST SENTIMENT: Upgrades/downgrades
    4. INSTITUTIONAL ACTIVITY: Notable buying/selling
    
    Rate: Very Bullish / Bullish / Neutral / Bearish / Very Bearish"""

    def _run_sentiment():
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )

    try:
        response = await asyncio.to_thread(_run_sentiment)
        return {"symbol": symbol.upper(), "sentiment": response.text}
    except Exception as e:
        logger.error(f"Sentiment error for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


async def screen_stocks(
    criteria: str,
    market: str = "US",
    model_alias: str = "gemini_3_flash"
) -> Dict[str, Any]:
    """
    Screen stocks based on criteria.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)
    
    prompt = f"""Find {market} stocks matching: {criteria}
    
    For each: ticker, price, why it matches, key risks.
    List 3-5 stocks ranked by match quality."""

    def _run_screen():
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )

    try:
        response = await asyncio.to_thread(_run_screen)
        return {"criteria": criteria, "market": market, "results": response.text}
    except Exception as e:
        logger.error(f"Stock screening error: {e}")
        return {"criteria": criteria, "error": str(e)}


def get_historical_prices(symbol: str, period: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Get historical price data.
    """
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "start_price": float(hist['Close'].iloc[0]),
            "end_price": float(hist['Close'].iloc[-1]),
            "high": float(hist['High'].max()),
            "low": float(hist['Low'].min()),
            "avg_volume": float(hist['Volume'].mean()),
            "return_pct": float(
                (hist['Close'].iloc[-1] - hist['Close'].iloc[0])
                / hist['Close'].iloc[0] * 100
            ),
            "data_points": len(hist)
        }
    except Exception as e:
        logger.error(f"Historical data error for {symbol}: {e}")
        return None
