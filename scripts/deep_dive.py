"""
Deep Dive: Robinhood Crypto Account Analysis
=============================================
"""
import os
import json
from datetime import datetime

os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

print("=" * 60)
print("DEEP DIVE: ROBINHOOD CRYPTO ACCOUNT")
print("=" * 60)
print()

# 1. ACCOUNT INFO
print(">>> 1. ACCOUNT INFO")
print("-" * 40)
try:
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    print(f"Account Number: {acc.get('account_number', 'N/A')}")
    print(f"Buying Power: ${acc.get('buying_power', 'N/A')}")
    print(f"Currency: {acc.get('buying_power_currency', 'N/A')}")
    print(f"Status: {acc.get('status', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")
print()

# 2. ALL HOLDINGS
print(">>> 2. ALL CRYPTO HOLDINGS")
print("-" * 40)
try:
    holdings = api.get_holdings()
    total_value = 0
    for h in holdings:
        qty = float(h.total_quantity) if h.total_quantity else 0
        if qty > 0:
            print(f"  {h.asset_code}: {qty} (available: {h.available_quantity})")
    if not any(float(h.total_quantity) > 0 for h in holdings):
        print("  (No holdings with quantity > 0)")
except Exception as e:
    print(f"Error: {e}")
print()

# 3. ORDER HISTORY
print(">>> 3. ORDER HISTORY (Last 20)")
print("-" * 40)
try:
    orders = api._request('GET', '/api/v1/crypto/trading/orders/')
    results = orders.get('results', [])
    print(f"Total orders in history: {len(results)}")
    print()
    
    buys = 0
    sells = 0
    total_bought = 0
    total_sold = 0
    
    for order in results[:20]:
        side = order.get('side', '?')
        symbol = order.get('symbol', '?')
        state = order.get('state', '?')
        qty = order.get('filled_asset_quantity') or order.get('quantity', '0')
        price = order.get('average_price', '0')
        created = order.get('created_at', '')[:19] if order.get('created_at') else ''
        
        if state == 'filled':
            if side == 'buy':
                buys += 1
                try:
                    total_bought += float(qty) * float(price) if price else 0
                except:
                    pass
            else:
                sells += 1
                try:
                    total_sold += float(qty) * float(price) if price else 0
                except:
                    pass
        
        emoji = "🟢 BUY " if side == "buy" else "🔴 SELL"
        status_emoji = "✅" if state == "filled" else "⏳" if state == "pending" else "❌"
        print(f"  {status_emoji} {emoji} {symbol:12} qty:{str(qty):12} @${str(price):12} | {state:10} | {created}")
except Exception as e:
    print(f"Error: {e}")
print()

# 4. SUMMARY
print(">>> 4. SUMMARY")
print("-" * 40)
print(f"  Filled Buys: {buys}")
print(f"  Filled Sells: {sells}")
print(f"  Total Bought: ~${total_bought:.2f}")
print(f"  Total Sold: ~${total_sold:.2f}")
print(f"  Net: ~${total_sold - total_bought:.2f}")
print()

# 5. COMPARE WITH BOT STATE
print(">>> 5. BOT STATE vs REALITY")
print("-" * 40)
try:
    with open('trading_state.json', 'r') as f:
        bot_state = json.load(f)
    print("Bot thinks:")
    print(f"  Cash: ${bot_state.get('cash', 0):.2f}")
    print(f"  Positions: {list(bot_state.get('positions', {}).keys())}")
    for sym, pos in bot_state.get('positions', {}).items():
        print(f"    {sym}: qty={pos.get('qty', 0)}, entry=${pos.get('entry', 0):.6f}")
except Exception as e:
    print(f"Error reading bot state: {e}")
print()

print("=" * 60)
print("DEEP DIVE COMPLETE")
print("=" * 60)
