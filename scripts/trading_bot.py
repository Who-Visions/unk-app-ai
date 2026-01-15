"""
Unk Autonomous Trading Bot v2
==============================
Runs continuously, buys dips, sells profits.
NO HUMAN INTERACTION NEEDED.
"""
import sys
sys.path.insert(0, 'c:/Users/super/Watchtower/unk-app-ai')

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI
import time
import uuid
from datetime import datetime

# =============================================================================
# CONFIG
# =============================================================================
API_KEY = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
PRIVATE_KEY = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

WATCHLIST = ['PEPE-USD', 'BONK-USD', 'SHIB-USD', 'DOGE-USD', 'XRP-USD', 'SOL-USD', 'LTC-USD', 'HBAR-USD', 'LINK-USD', 'ADA-USD', 'ETH-USD']
DIP_BUY_PCT = -0.5       # Buy when down 0.5% from session high (AGGRESSIVE)
PROFIT_TARGET = 5.0       # Sell at 5% profit
STOP_LOSS = -3.0          # Cut losses at 3%
CHECK_INTERVAL = 2        # Check every 2 seconds
GOAL = 100.0

# =============================================================================
# BOT
# =============================================================================
api = RobinhoodCryptoAPI(api_key=API_KEY, private_key_base64=PRIVATE_KEY)

# State
high_prices = {}
positions = {}  # symbol -> {qty, entry_price}
scan_count = 0

def get_prices(symbol):
    """Get bid and ask prices."""
    try:
        p = api._request('GET', f'/api/v1/crypto/marketdata/best_bid_ask/?symbol={symbol}')
        if p and p.get('results'):
            r = p['results'][0]
            return (
                float(r.get('bid_inclusive_of_sell_spread', 0)),
                float(r.get('ask_inclusive_of_buy_spread', 0))
            )
    except:
        pass
    return None, None

def get_cash():
    try:
        acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
        return float(acc.get('buying_power', 0))
    except:
        return 0

def buy(symbol, qty):
    """Buy crypto by quantity."""
    try:
        body = {
            "client_order_id": str(uuid.uuid4()),
            "side": "buy",
            "symbol": symbol,
            "type": "market",
            "market_order_config": {"asset_quantity": str(qty)}
        }
        result = api._request('POST', '/api/v1/crypto/trading/orders/', body)
        return result and result.get('id')
    except Exception as e:
        print(f"  BUY ERROR: {e}")
        return False

def sell(symbol, qty):
    """Sell crypto by quantity."""
    try:
        body = {
            "client_order_id": str(uuid.uuid4()),
            "side": "sell",
            "symbol": symbol,
            "type": "market",
            "market_order_config": {"asset_quantity": str(qty)}
        }
        result = api._request('POST', '/api/v1/crypto/trading/orders/', body)
        return result and result.get('id')
    except Exception as e:
        print(f"  SELL ERROR: {e}")
        return False

print("=" * 60)
print("   UNK AUTONOMOUS TRADING BOT v2")
print("   Goal: $5 -> $100")
print("=" * 60)
print(f"\nCash: ${get_cash():.2f}")
print(f"Watching: {WATCHLIST}")
print(f"Buy on {DIP_BUY_PCT}% dip | Sell on {PROFIT_TARGET}% gain | Stop at {STOP_LOSS}%")
print("\nRUNNING AUTONOMOUSLY...")
print("-" * 60)

# Initialize high prices
for sym in WATCHLIST:
    bid, ask = get_prices(sym)
    if ask:
        high_prices[sym] = ask
        print(f"  {sym}: ${ask:.10f}")

print("-" * 60)

try:
    while True:
        scan_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        
        # Check existing positions for profit/loss
        for sym in list(positions.keys()):
            bid, ask = get_prices(sym)
            if not bid:
                continue
            
            pos = positions[sym]
            pnl_pct = (bid - pos['entry']) / pos['entry'] * 100
            
            if pnl_pct >= PROFIT_TARGET:
                print(f"\n[{now}] PROFIT SELL {sym} +{pnl_pct:.1f}%")
                if sell(sym, pos['qty']):
                    del positions[sym]
                    print(f"  SOLD!")
            elif pnl_pct <= STOP_LOSS:
                print(f"\n[{now}] STOP LOSS {sym} {pnl_pct:.1f}%")
                if sell(sym, pos['qty']):
                    del positions[sym]
                    print(f"  SOLD!")
        
        # Scan for dips
        # Check News Sentiment
        sentiment_mod = 0
        try:
            with open("market_sentiment.json", "r") as f:
                news_data = json.load(f)
                s_score = news_data.get('score', 0)
                if s_score > 0:
                    sentiment_mod = 0.5  # Make dip trigger smaller (stricter buy) -> actually we want MORE buys.
                    # If Bullish, we want to buy on SMALLER dips (e.g. -0.5%).
                    # Default is -0.5 (Aggressive). 
                    # Let's make it:
                    # Bullish (>0) -> -0.5% (Buy small pullbacks)
                    # Neutral (0)  -> -1.5% (Buy normal pullbacks)
                    # Bearish (<0) -> -3.0% (Only buy deep crashes)
                    
                    if s_score > 0: current_dip_trigger = -0.5
                    elif s_score < 0: current_dip_trigger = -3.0
                    else: current_dip_trigger = -1.5
                    
                    # Print only if changed significantly or periodcally
                    if scan_count % 30 == 0:
                        print(f"[{now}] News Sentiment: {news_data['sentiment']} (Trigger: {current_dip_trigger}%)")
                else:
                    current_dip_trigger = -1.5 # Neutral default
        except:
             current_dip_trigger = DIP_BUY_PCT # Fallback to config
        
        cash = get_cash()
        for sym in WATCHLIST:
            if sym in positions:
                continue  # Already have position
            
            bid, ask = get_prices(sym)
            if not ask:
                continue
            
            # Update high
            if ask > high_prices.get(sym, 0):
                high_prices[sym] = ask
            
            # Check for dip
            high = high_prices[sym]
            dip_pct = (ask - high) / high * 100
            
            if dip_pct <= current_dip_trigger and cash >= 1.0:
                buy_usd = min(cash * 0.4, 2.50)  # Use 40% of cash, max $2.50
                qty = buy_usd / ask
                
                print(f"\n[{now}] DIP DETECTED: {sym} {dip_pct:.2f}% (Trigger: {current_dip_trigger}%)")
                print(f"  Buying ${buy_usd:.2f} ({qty:.0f} coins)...")
                
                if buy(sym, qty):
                    positions[sym] = {'qty': qty, 'entry': ask}
                    print(f"  BOUGHT @ ${ask:.10f}")
                    high_prices[sym] = ask  # Reset high
                    cash = get_cash()
        
        # Status every 30 scans
        if scan_count % 30 == 0:
            cash = get_cash()
            pos_value = sum(
                pos['qty'] * (get_prices(sym)[0] or 0)
                for sym, pos in positions.items()
            )
            total = cash + pos_value
            
            pos_str = ", ".join(f"{s}:{p['qty']:.0f}" for s, p in positions.items()) or "none"
            print(f"[{now}] #{scan_count} | Cash: ${cash:.2f} | Pos: {pos_str} | Total: ~${total:.2f}")
            
            if total >= GOAL:
                print(f"\n*** GOAL REACHED: ${total:.2f} ***")
                break
        
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\n\nBot stopped.")

finally:
    cash = get_cash()
    print(f"Final cash: ${cash:.2f}")
    print(f"Open positions: {positions}")
