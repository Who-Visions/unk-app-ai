
SMALL_COINS = [
    'DOGE-USD', 'SHIB-USD', 'PEPE-USD', 'BONK-USD', 
    'XRP-USD', 'ADA-USD', 'XLM-USD', 'HBAR-USD'
]

def test_override(sym, current_price, high_price, entry_price, expected_buy, expected_sell_signal):
    # Mock Config
    buy_trigger_global = -1.5
    sell_target_global = 4.0
    
    # 1. Determine Effective Targets
    buy_trigger = buy_trigger_global
    sell_target = sell_target_global
    
    if sym in SMALL_COINS:
        buy_trigger = -3.0
        sell_target = 1.10
        
    print(f"Testing {sym} | Global Buy: {buy_trigger_global}% | Global Sell: {sell_target_global}%")
    print(f"   -> Effective Buy Trigger: {buy_trigger}%")
    print(f"   -> Effective Sell Target: {sell_target}%")
    
    # 2. Check Buy Logic
    dip = ((current_price - high_price) / high_price) * 100
    buy_signal = dip <= buy_trigger
    assert buy_signal == expected_buy, f"Buy Fail: Dip {dip:.2f}% <= {buy_trigger}%? Got {buy_signal}, Expected {expected_buy}"
    
    # 3. Check Sell Logic
    if entry_price > 0:
        pnl = ((current_price - entry_price) / entry_price) * 100
        sell_signal = pnl >= sell_target
        assert sell_signal == expected_sell_signal, f"Sell Fail: PnL {pnl:.2f}% >= {sell_target}%? Got {sell_signal}, Expected {expected_sell_signal}"
    
    print(f"   ✅ Passed. Buy Signal: {buy_signal} | Sell Signal: {expected_sell_signal if entry_price > 0 else 'N/A'}")
    print("-" * 40)

print("validating Small Coin Overrides...")
print("-" * 40)

# Case 1: PEPE (Small Coin) - Dip -2% (Global Buy) vs -3% (Small Buy)
# Should NOT buy at -2% (needs -3%)
test_override('PEPE-USD', 98, 100, 0, False, False)

# Case 2: PEPE (Small Coin) - Dip -3.5%
# Should BUY
test_override('PEPE-USD', 96.5, 100, 0, True, False)

# Case 3: PEPE (Small Coin) - Profit +1.5%
# Should SELL (Target 1.1%)
test_override('PEPE-USD', 101.5, 100, 100, False, True)

# Case 4: BTC (Major) - Profit +1.5%
# Should HOLD (Target 4.0%)
test_override('BTC-USD', 101.5, 100, 100, False, False)

# Case 5: BTC (Major) - Profit +4.1%
# Should SELL
test_override('BTC-USD', 104.1, 100, 100, False, True)

print("SUCCESS: Small Coin Override Logic Verified.")
