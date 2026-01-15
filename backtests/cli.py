"""
Backtest CLI
============
Command-line interface for running backtests.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from backtests.backtester import run_backtest


def main():
    """Run backtest from command line."""
    parser = argparse.ArgumentParser(
        description="Run backtest on Unk trading strategies"
    )
    parser.add_argument(
        "--symbol", "-s",
        required=True,
        help="Stock symbol (e.g., AAPL, NVDA)"
    )
    parser.add_argument(
        "--strategy", "-t",
        default="DayTrader",
        choices=["DayTrader", "SwingTrader", "Scalper"],
        help="Trading strategy to test"
    )
    parser.add_argument(
        "--start",
        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        help="Start date YYYY-MM-DD (default: 1 year ago)"
    )
    parser.add_argument(
        "--end",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--equity", "-e",
        type=float,
        default=10000,
        help="Starting equity (default: 10000)"
    )
    parser.add_argument(
        "--risk", "-r",
        type=float,
        default=0.02,
        help="Risk per trade as decimal (default: 0.02 = 2%%)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--trades",
        action="store_true",
        help="Show individual trade log"
    )
    
    args = parser.parse_args()
    
    # Run backtest
    print(f"\n{'='*60}")
    print(f"UNK BACKTEST: {args.symbol} with {args.strategy}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Starting Equity: ${args.equity:,.2f}")
    print(f"Risk per Trade: {args.risk*100:.1f}%")
    print(f"{'='*60}\n")
    
    result = run_backtest(
        symbol=args.symbol.upper(),
        strategy=args.strategy,
        start=args.start,
        end=args.end,
        starting_equity=args.equity,
        risk_pct=args.risk,
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return
    
    # Print results
    print("\n📊 RESULTS")
    print("-" * 40)
    print(f"Ending Equity:     ${result.ending_equity:,.2f}")
    print(f"Total Return:      {result.total_return_pct:+.2f}%")
    print(f"Total Trades:      {result.total_trades}")
    print(f"Win Rate:          {result.win_rate*100:.1f}%")
    
    print("\n📈 PERFORMANCE METRICS")
    print("-" * 40)
    print(f"Sharpe Ratio:      {result.sharpe_ratio:.2f}")
    print(f"Profit Factor:     {result.profit_factor:.2f}")
    print(f"Recovery Factor:   {result.recovery_factor:.2f}")
    print(f"Max Drawdown:      {result.max_drawdown_pct:.2f}%")
    
    print("\n💰 TRADE STATS")
    print("-" * 40)
    print(f"Winning Trades:    {result.winning_trades}")
    print(f"Losing Trades:     {result.losing_trades}")
    print(f"Avg Win:           ${result.avg_win:,.2f}")
    print(f"Avg Loss:          ${result.avg_loss:,.2f}")
    print(f"Largest Win:       ${result.largest_win:,.2f}")
    print(f"Largest Loss:      ${result.largest_loss:,.2f}")
    
    # Quality assessment
    print("\n🎯 QUALITY ASSESSMENT")
    print("-" * 40)
    
    checks = []
    if result.sharpe_ratio >= 1.5:
        checks.append("✅ Sharpe > 1.5 (excellent risk-adjusted returns)")
    elif result.sharpe_ratio >= 1.0:
        checks.append("🟡 Sharpe 1.0-1.5 (acceptable)")
    else:
        checks.append("❌ Sharpe < 1.0 (poor risk-adjusted returns)")
    
    if result.max_drawdown_pct <= 20:
        checks.append("✅ Max Drawdown ≤ 20% (manageable)")
    else:
        checks.append("❌ Max Drawdown > 20% (high risk)")
    
    if result.profit_factor >= 1.8:
        checks.append("✅ Profit Factor ≥ 1.8 (strong edge)")
    elif result.profit_factor >= 1.2:
        checks.append("🟡 Profit Factor 1.2-1.8 (moderate edge)")
    else:
        checks.append("❌ Profit Factor < 1.2 (weak/no edge)")
    
    if result.win_rate >= 0.4:
        checks.append("✅ Win Rate ≥ 40%")
    else:
        checks.append("🟡 Win Rate < 40% (needs high R:R)")
    
    for check in checks:
        print(f"  {check}")
    
    # Trade log
    if args.trades and result.trades:
        print("\n📝 TRADE LOG")
        print("-" * 60)
        print(f"{'Date':<12} {'Entry':>10} {'Exit':>10} {'P&L':>12} {'Reason':<8}")
        print("-" * 60)
        for t in result.trades:
            print(
                f"{t.entry_date:<12} "
                f"${t.entry_price:>9.2f} "
                f"${t.exit_price:>9.2f} "
                f"${t.pnl:>+11.2f} "
                f"{t.exit_reason:<8}"
            )
    
    print("\n" + "=" * 60)
    print("Unk says: Numbers don't lie, nephew. Study the data!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
