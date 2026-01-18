"""Full order history to file"""
import os
os.environ['ROBINHOOD_API_KEY'] = 'rh-api-1dc5a886-11e5-459f-84ad-7f00b97f7814'
os.environ['ROBINHOOD_PRIVATE_KEY'] = 'bByzmdzZcHSEJOMeAo40Gk8CX21yL8gPWijXI0CaWo0='

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI(
    api_key=os.environ['ROBINHOOD_API_KEY'],
    private_key_base64=os.environ['ROBINHOOD_PRIVATE_KEY']
)

with open('pnl_report.txt', 'w') as f:
    # Get account
    acc = api._request('GET', '/api/v1/crypto/trading/accounts/')
    f.write(f"BUYING POWER: ${acc.get('buying_power')}\n\n")

    # Get orders
    orders = api._request('GET', '/api/v1/crypto/trading/orders/')
    results = orders.get('results', [])

    buys = []
    sells = []

    for o in results:
        side = o.get('side', '?')
        sym = o.get('symbol', '?')
        state = o.get('state', '?')
        qty = o.get('filled_asset_quantity') or o.get('quantity') or '0'
        price = o.get('average_price') or '0'
        created = o.get('created_at', '')[:10]
        
        if state == 'filled':
            if side == 'buy':
                buys.append((sym, float(qty), float(price), created))
            else:
                sells.append((sym, float(qty), float(price), created))

    f.write("=== FILLED BUYS ===\n")
    total_buy = 0
    for sym, qty, price, dt in buys:
        val = qty * price
        total_buy += val
        f.write(f"  {dt} BUY  {sym:12} qty:{qty:.6f} @ ${price:.6f} = ${val:.2f}\n")
    f.write(f"  TOTAL BOUGHT: ${total_buy:.2f}\n\n")

    f.write("=== FILLED SELLS ===\n")
    total_sell = 0
    for sym, qty, price, dt in sells:
        val = qty * price
        total_sell += val
        f.write(f"  {dt} SELL {sym:12} qty:{qty:.6f} @ ${price:.6f} = ${val:.2f}\n")
    f.write(f"  TOTAL SOLD: ${total_sell:.2f}\n\n")

    f.write("=== NET P/L ===\n")
    f.write(f"  Sold - Bought = ${total_sell - total_buy:.2f}\n")

print("Report saved to pnl_report.txt")
