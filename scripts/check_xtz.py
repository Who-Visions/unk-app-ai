"""Quick XTZ Pattern Check"""
import requests
import statistics

url = "https://min-api.cryptocompare.com/data/v2/histominute?fsym=XTZ&tsym=USD&limit=10"
res = requests.get(url).json()
candles = res['Data']['Data']

last_c = candles[-2]
is_uptrend = last_c['close'] > candles[-5]['close']
is_red = last_c['close'] < last_c['open']
av_vol = statistics.mean([c['volumeto'] for c in candles[:-2]]) if candles[:-2] else 1
rel_vol = last_c['volumeto'] / av_vol if av_vol > 0 else 0

print("XTZ Analysis:")
print(f"  Uptrend: {is_uptrend}")
print(f"  Last Candle Red: {is_red}")
print(f"  Relative Volume: {rel_vol:.1f}x")

if is_red and rel_vol > 1.5 and is_uptrend:
    print("  🚨 PULLBACK SIGNAL DETECTED!")
else:
    print("  Status: Wait for pullback")
