
import requests
import time
import json
from datetime import datetime

API_KEY = "pub_4fded9b3d86342fa94a5484b626f4486"
BASE_URL = "https://newsdata.io/api/1/latest"

KEYWORDS = {
    "bullish": ["approval", "approved", "partnership", "launch", "record high", "etf", "upgrade", "bull", "surge", "gain"],
    "bearish": ["ban", "hacked", "fraud", "lawsuit", "crash", "bear", "plummet", "drop", "investigation", "regulation"]
}

WATCHLIST = ["bitcoin", "ethereum", "xrp", "solana", "dogecoin", "pepe", "shib", "bonk"]

def fetch_crypto_news():
    """Fetch latest crypto news from NewsData.io"""
    try:
        # q = query for crypto keywords
        query = " OR ".join(WATCHLIST)
        params = {
            "apikey": API_KEY,
            "q": query,
            "language": "en",
            "category": "business,technology" 
        }
        res = requests.get(BASE_URL, params=params)
        data = res.json()
        
        if data.get('status') == 'success':
            return data.get('results', [])
        else:
            print(f"API Error: {data}")
            return []
    except Exception as e:
        print(f"Fetch error: {e}")
        return []

def analyze_sentiment(articles):
    """Simple keyword-based sentiment analysis."""
    score = 0
    bullish_count = 0
    bearish_count = 0
    
    print(f"\nScanning {len(articles)} new articles...")
    
    for article in articles:
        title = (article.get('title') or "").lower()
        desc = (article.get('description') or "").lower()
        content = f"{title} {desc}"
        
        # Check keywords
        found_bull = [k for k in KEYWORDS['bullish'] if k in content]
        found_bear = [k for k in KEYWORDS['bearish'] if k in content]
        
        if found_bull:
            score += 1
            bullish_count += 1
            print(f"  [+] BULLISH: {article['title'][:60]}...")
            
        elif found_bear:
            score -= 1
            bearish_count += 1
            print(f"  [-] BEARISH: {article['title'][:60]}...")

    # Normalize score between -1 and 1 roughly
    total_signals = bullish_count + bearish_count
    sentiment = "NEUTRAL"
    if score > 0: sentiment = "BULLISH"
    if score < 0: sentiment = "BEARISH"
    
    return sentiment, score, bullish_count, bearish_count

def run_scanner():
    print("="*60)
    print("   UNK NEWS SCANNER (NewsData.io)")
    print("="*60)
    
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")
        articles = fetch_crypto_news()
        
        if articles:
            sentiment, score, bulls, bears = analyze_sentiment(articles)
            print(f"\n[{timestamp}] Market Sentiment: {sentiment} (Score: {score})")
            print(f"Signals: {bulls} Bullish / {bears} Bearish")
            
            # Write to file for Trading Bot to read
            with open("market_sentiment.json", "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "sentiment": sentiment,
                    "score": score,
                    "bull_signals": bulls,
                    "bear_signals": bears
                }, f)
                
        else:
            print(f"[{timestamp}] No new articles found or API limit.")
            
        # Wait 30 minutes (safety limit)
        print("\nWaiting 30 minutes for next scan...")
        time.sleep(1800)

if __name__ == "__main__":
    run_scanner()
