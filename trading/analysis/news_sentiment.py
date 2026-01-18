"""
News Sentiment Analysis Module
==============================
Multi-source news sentiment analysis using:
- CryptoCompare (primary, free, high volume)
- NewsData.io (secondary, verification, 200 credits/day)

Ported from Gold Standard: trading/core/unk_trader_cli.py:news_worker
"""
import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional
import threading

# API Configuration
NEWSDATA_API_KEY = os.getenv('NEWSDATA_API_KEY', 'pub_4fded9b3d86342fa94a5484b626f4486')
CC_URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
ND_URL = "https://newsdata.io/api/1/latest"

# Keywords to search for
KEYWORDS = ["bitcoin", "ethereum", "xrp", "solana", "dogecoin", "pepe", "shib", "bonk", "crypto"]

# Sentiment Themes
THEMES_BULLISH = [
    "sovereign", "pension", "microsoft", "bill gates",
    "strategic reserve", "blackrock", "etf", "stablecoin",
    "approval", "partnership", "launch", "bull", "record",
    "adoption", "institutional", "milestone", "breakout"
]

THEMES_BEARISH = [
    "quantum", "bear market", "recession", "liquidity drying",
    "end of cycle", "ban", "hack", "lawsuit", "crash",
    "insolvency", "fraud", "investigation", "sell-off", "dump"
]

# Cache to avoid hitting rate limits
_cache = {
    "last_fetch": 0,
    "data": None,
    "last_nd_call": 0
}
_cache_lock = threading.Lock()


def analyze_text(text: str, bullish_themes: List[str] = None, bearish_themes: List[str] = None) -> tuple:
    """
    Analyze text for bullish/bearish sentiment.
    
    Args:
        text: Text to analyze
        bullish_themes: List of bullish keywords
        bearish_themes: List of bearish keywords
    
    Returns:
        Tuple of (score, bullish_signals, bearish_signals)
    """
    if bullish_themes is None:
        bullish_themes = THEMES_BULLISH
    if bearish_themes is None:
        bearish_themes = THEMES_BEARISH
    
    score = 0
    bullish_count = 0
    bearish_count = 0
    text = text.lower()
    
    # Check bullish keywords
    for keyword in bullish_themes:
        if keyword in text:
            score += 1
            bullish_count += 1
    
    # Check bearish keywords
    for keyword in bearish_themes:
        if keyword in text:
            score -= 1
            bearish_count += 1
    
    return score, bullish_count, bearish_count


def fetch_cryptocompare_news() -> List[Dict]:
    """
    Fetch news from CryptoCompare (primary, free source).
    
    Returns:
        List of article dicts with title, url, source, sentiment_score
    """
    articles = []
    
    try:
        with urllib.request.urlopen(CC_URL, timeout=10) as res:
            data = json.loads(res.read().decode())
        
        if data.get('Message') == 'News list successfully returned':
            for art in data.get('Data', [])[:15]:
                title = art.get('title', "")
                body = art.get('body', "")
                url = art.get('url', "")
                source = art.get('source', "CryptoCompare")
                pub_time = art.get('published_on', 0)
                
                score, bulls, bears = analyze_text(title + " " + body)
                
                articles.append({
                    "title": title,
                    "url": url,
                    "source": source,
                    "sentiment_score": score,
                    "bullish_signals": bulls,
                    "bearish_signals": bears,
                    "published_on": pub_time
                })
    except Exception as e:
        print(f"CryptoCompare fetch error: {e}")
    
    return articles


def verify_with_newsdata(keywords: List[str] = None) -> Dict:
    """
    Verify sentiment with NewsData.io (200 credits/day limit).
    
    Only call this for EXTREME signals to save credits.
    
    Args:
        keywords: List of keywords to search
    
    Returns:
        Dict with score and articles
    """
    global _cache
    
    if keywords is None:
        keywords = KEYWORDS
    
    with _cache_lock:
        # Rate limit: max 1 call per 30 minutes
        if time.time() - _cache["last_nd_call"] < 1800:
            return {"status": "rate_limited", "score": 0, "articles": []}
        _cache["last_nd_call"] = time.time()
    
    result = {"status": "ok", "score": 0, "articles": []}
    
    try:
        q = " OR ".join(keywords[:5])  # Limit query length
        params = urllib.parse.urlencode({
            "apikey": NEWSDATA_API_KEY,
            "q": q,
            "language": "en"
        })
        url = f"{ND_URL}?{params}"
        
        with urllib.request.urlopen(url, timeout=10) as res:
            data = json.loads(res.read().decode())
        
        if data.get('status') == 'success':
            for art in data.get('results', [])[:10]:
                title = art.get('title') or ""
                desc = art.get('description') or ""
                link = art.get('link') or ""
                
                score, bulls, bears = analyze_text(title + " " + desc)
                result["score"] += score
                
                result["articles"].append({
                    "title": f"[VERIFY] {title}",
                    "url": link,
                    "source": "NewsData.io",
                    "sentiment_score": score
                })
    except Exception as e:
        result["status"] = f"error: {e}"
    
    return result


def get_market_sentiment(force_refresh: bool = False) -> Dict:
    """
    Get overall market sentiment from news sources.
    
    Args:
        force_refresh: Force fetch even if cache is valid
    
    Returns:
        Dict with sentiment, score, articles, and consensus info
    """
    global _cache
    
    with _cache_lock:
        # Use cache if fresh (3 minutes)
        if not force_refresh and _cache["data"] and time.time() - _cache["last_fetch"] < 180:
            return _cache["data"]
    
    # Fetch from primary source
    articles = fetch_cryptocompare_news()
    
    # Calculate total score
    total_score = sum(a.get("sentiment_score", 0) for a in articles)
    
    # Determine sentiment level
    if total_score >= 5:
        sentiment = "JEFF_PARK_BULLISH"  # Strong bullish
    elif total_score > 0:
        sentiment = "BULLISH"
    elif total_score <= -3:
        sentiment = "WILLY_WOO_BEARISH"  # Strong bearish
    elif total_score < 0:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"
    
    # Verify extreme signals with secondary source
    consensus = False
    if sentiment in ["JEFF_PARK_BULLISH", "WILLY_WOO_BEARISH"]:
        verification = verify_with_newsdata()
        if verification.get("status") == "ok":
            nd_score = verification.get("score", 0)
            
            # Check consensus
            if sentiment == "JEFF_PARK_BULLISH" and nd_score > 0:
                consensus = True
            elif sentiment == "WILLY_WOO_BEARISH" and nd_score < 0:
                consensus = True
            else:
                # Downgrade if no consensus
                sentiment = "BULLISH" if total_score > 0 else "BEARISH"
            
            # Add verification articles
            articles = verification.get("articles", []) + articles
    
    result = {
        "sentiment": sentiment,
        "score": total_score,
        "articles": articles[:20],  # Limit to 20 articles
        "consensus": consensus,
        "last_updated": datetime.now().strftime("%H:%M"),
        "sources": ["CryptoCompare", "NewsData.io"] if consensus else ["CryptoCompare"]
    }
    
    # Update cache
    with _cache_lock:
        _cache["data"] = result
        _cache["last_fetch"] = time.time()
    
    return result


def get_sentiment_signal() -> str:
    """
    Get a simple trading signal based on sentiment.
    
    Returns:
        "BUY", "SELL", or "HOLD" signal
    """
    data = get_market_sentiment()
    sentiment = data.get("sentiment", "NEUTRAL")
    consensus = data.get("consensus", False)
    
    if sentiment == "JEFF_PARK_BULLISH" and consensus:
        return "STRONG_BUY"
    elif sentiment == "BULLISH":
        return "BUY"
    elif sentiment == "WILLY_WOO_BEARISH" and consensus:
        return "STRONG_SELL"
    elif sentiment == "BEARISH":
        return "SELL"
    else:
        return "HOLD"
