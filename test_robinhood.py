"""Find the most volatile/cheap cryptos - penny stock style."""
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key='rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814',
    private_key_base64='bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='
)

print("=== PENNY CRYPTO SCANNER ===")
print("Looking for cheap, volatile plays...\n")

# Meme coins and low-cap cryptos (penny stock equivalents)
penny_cryptos = [
    'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD', 'FLOKI-USD',
    'PNUT-USD', 'TRUMP-USD', 'MEW-USD', 'PENGU-USD', 'POPCAT-USD',
    'MOODENG-USD', 'WIF-USD', 'HYPE-USD', 'XCN-USD', 'ZORA-USD',
]

print(f"{'SYMBOL':<12} {'BID':>12} {'ASK':>12} {'SPREAD':>8}")
print("-" * 46)

for sym in penny_cryptos:
    try:
        p = api._request('GET', f'/api/v1/crypto/marketdata/best_bid_ask/?symbol={sym}')
        if p and p.get('results'):
            r = p['results'][0]
            bid = float(r.get('bid_inclusive_of_sell_spread', 0))
            ask = float(r.get('ask_inclusive_of_buy_spread', 0))
            spread = ((ask - bid) / bid * 100) if bid > 0 else 0
            
            # Format based on price
            if bid < 0.001:
                print(f"{sym:<12} ${bid:>11.8f} ${ask:>11.8f} {spread:>6.2f}%")
            elif bid < 1:
                print(f"{sym:<12} ${bid:>11.6f} ${ask:>11.6f} {spread:>6.2f}%")
            else:
                print(f"{sym:<12} ${bid:>11.4f} ${ask:>11.4f} {spread:>6.2f}%")
    except Exception as e:
        print(f"{sym:<12} ERROR: {e}")

print("\n=== $5 BUYING POWER ===")
print("Best penny plays: PEPE, SHIB, BONK (millions of coins)")
print("Meme coin volatility: 10-50% swings possible")
