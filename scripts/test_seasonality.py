
import requests
import datetime
import statistics

def check_seasonality(symbol="BTC"):
    print(f"--- Seasonality Check: {symbol} ---")
    
    # 1. Fetch 2000 days of history (approx 5-6 years)
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&limit=2000"
    res = requests.get(url).json()
    
    if res['Response'] == 'Success':
        data = res['Data']['Data']
        print(f"Fetched {len(data)} days of history.")
        
        # 2. Filter by Current Month (e.g., January)
        current_month = datetime.datetime.now().month
        print(f"Analyzing Month: {current_month} (January)")
        
        monthly_returns = []
        wins = 0
        total_years = 0
        
        # Group by year
        # We need to find the specific month in the data
        # Data is a list of days.
        
        # Let's organize by [Year][Month] -> Return %
        # Simplification: Just find all days that fall in this month and calculate the month's open/close?
        # Better: iterate years.
        
        years = {} # {2020: {open: x, close: y}}
        
        for day in data:
            dt = datetime.datetime.fromtimestamp(day['time'])
            if dt.month == current_month:
                y = dt.year
                if y not in years:
                    years[y] = {'open': 0, 'close': 0, 'first_day': 32, 'last_day': 0}
                
                # Capture first available day stats
                if dt.day < years[y]['first_day']:
                    years[y]['open'] = day['open']
                    years[y]['first_day'] = dt.day
                
                # Capture last available day stats
                if dt.day > years[y]['last_day']:
                    years[y]['close'] = day['close']
                    years[y]['last_day'] = dt.day
        
        # Calculate Returns
        for y, stats in years.items():
            if stats['open'] > 0:
                ret = (stats['close'] - stats['open']) / stats['open'] * 100
                monthly_returns.append(ret)
                icon = "🟢" if ret > 0 else "🔴"
                print(f"{y}: {icon} {ret:+.2f}%")
                if ret > 0: wins += 1
                total_years += 1
        
        if total_years > 0:
            avg_ret = statistics.mean(monthly_returns)
            win_rate = (wins / total_years) * 100
            print(f"--- Results ---")
            print(f"Win Rate: {win_rate:.0f}%")
            print(f"Avg Return: {avg_ret:+.2f}%")
            
            score = 0
            if win_rate >= 70: score += 1
            if avg_ret > 5.0: score += 1
            if avg_ret < 0: score = -1
            
            print(f"Seasonality Score: {score}/2")
            return score
            
check_seasonality("BTC")
check_seasonality("ETH")
check_seasonality("SHIB")
check_seasonality("BONK")
