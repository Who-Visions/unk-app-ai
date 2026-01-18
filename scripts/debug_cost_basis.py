
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

def calculate_cost_basis():
    load_dotenv()
    print("🧮 Calculating Cost Basis from Order History...")
    
    api = RobinhoodCryptoAPI()
    
    # 1. Fetch All Filled Orders
    print("Fetching order history (this may take a moment)...")
    # Note: get_orders might need pagination loop if many orders.
    # checking implementation... it fetches one page. 
    # Hopefully v1 returns enough.
    
    orders = api.get_orders(state="filled")
    print(f"Found {len(orders)} filled orders.")
    
    # Sort by date (oldest first)
    # created_at format: "2024-01-01T12:00:00.000000Z"
    # Some might be v1 or v2..
    
    orders.sort(key=lambda x: x.created_at)
    
    portfolio = {} # {symbol: {'qty': 0.0, 'cost_basis': 0.0}}
    
    for o in orders:
        sym = o.symbol
        side = o.side # 'buy' or 'sell'
        qty = o.filled_quantity
        price = o.average_price or 0.0
        
        if o.average_price is None:
             # Skip or error?
             print(f"Warning: Order {o.id} has no price.")
             continue
             
        if sym not in portfolio:
            portfolio[sym] = {'qty': 0.0, 'avg_price': 0.0}
            
        p = portfolio[sym]
        
        if side == 'buy':
            # Weighted Average
            new_qty = p['qty'] + qty
            if new_qty > 0:
                current_val = p['qty'] * p['avg_price']
                new_val = qty * price
                p['avg_price'] = (current_val + new_val) / new_qty
            p['qty'] = new_qty
            
        elif side == 'sell':
            # Selling doesn't change avg_price, just qty
            p['qty'] = max(0, p['qty'] - qty)
            if p['qty'] == 0:
                p['avg_price'] = 0.0

    print("\n-------- Calculated Cost Basis --------")
    print(f"{'Asset':<10} {'Qty':<15} {'Avg Price':<15} {'Current Est':<15}")
    
    # Get current quotes for comparison
    holdings = api.get_holdings()
    
    for sym, data in portfolio.items():
        if data['qty'] > 0.00001:
             print(f"{sym:<10} {data['qty']:<15.6f} ${data['avg_price']:<14.4f}")

if __name__ == "__main__":
    calculate_cost_basis()
