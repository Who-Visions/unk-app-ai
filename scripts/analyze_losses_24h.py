
import re
from datetime import datetime, timedelta

LOG_FILE = "trader_activity.log"

def analyze_losses():
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    
    losses = []
    profits = []
    
    print(f"📊 Analyzing Trading Activity for Last 24 Hours")
    print(f"   (From {cutoff.strftime('%Y-%m-%d %H:%M:%S')} to {now.strftime('%Y-%m-%d %H:%M:%S')})")
    print("-" * 60)
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                # Parse Timestamp: [YYYY-MM-DD HH:MM:SS]
                match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.*)", line)
                if match:
                    ts_str, msg = match.groups()
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue
                        
                    if ts >= cutoff:
                        # Check for Stop Loss
                        # log(f"🛑 STOP: {sym} {pnl_pct:.2f}%")
                        if "🛑 STOP:" in msg or "STOP:" in msg:
                            # Extract details
                            # Example msg: "🛑 STOP: PEPE-USD -10.50%"
                            parts = msg.split()
                            try:
                                # Find percentage
                                pct_str = next((p for p in parts if "%" in p), "0%")
                                pct = float(pct_str.replace("%", "").replace("+", ""))
                                sym = next((p for p in parts if "-USD" in p), "UNKNOWN")
                                losses.append({"time": ts, "sym": sym, "pct": pct})
                            except:
                                pass
                                
                        # Check for Profit (for Context)
                        # log(f"💰 PROFIT: {sym} {pnl_pct:.2f}% ...")
                        elif "💰 PROFIT:" in msg or "PROFIT:" in msg:
                             parts = msg.split()
                             try:
                                pct_str = next((p for p in parts if "%" in p), "0%")
                                pct = float(pct_str.replace("%", "").replace("+", ""))
                                sym = next((p for p in parts if "-USD" in p), "UNKNOWN")
                                profits.append({"time": ts, "sym": sym, "pct": pct})
                             except:
                                pass

        # REPORT
        print(f"\n🛑 LOSSES (Stopped Out): {len(losses)}")
        if losses:
            print(f"   {'Time':<20} {'Asset':<10} {'Loss %':<10}")
            print("-" * 45)
            for l in losses:
                print(f"   {l['time'].strftime('%H:%M:%S'):<20} {l['sym']:<10} {l['pct']:+.2f}%")
        else:
            print("   (No realized losses found in logs for this period)")

        print(f"\n💰 PROFITS (Take Profit): {len(profits)}")
        if profits:
             for p in profits:
                print(f"   {p['time'].strftime('%H:%M:%S'):<20} {p['sym']:<10} {p['pct']:+.2f}%")
        else:
             print("   (No realized profits found in logs for this period)")
             
        # Summary
        total_loss_pct = sum(l['pct'] for l in losses)
        total_gain_pct = sum(p['pct'] for p in profits)
        print("-" * 60)
        print(f"📉 Cumulative Loss %: {total_loss_pct:.2f}%")
        print(f"📈 Cumulative Gain %: {total_gain_pct:.2f}%")
        print(f"⚖️  Net % Delta:      {total_gain_pct + total_loss_pct:.2f}%")
        
    except FileNotFoundError:
        print(f"❌ Error: {LOG_FILE} not found.")

if __name__ == "__main__":
    analyze_losses()
