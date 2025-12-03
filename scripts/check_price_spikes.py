#!/usr/bin/env python3
"""
Price Spike Detection Script
=============================
Checks for price spikes and generates reports.

Usage:
    python scripts/check_price_spikes.py [--threshold 10] [--service GCP] [--days 30]
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_agent.price_tracker import get_tracker, PriceSpike


def format_spike_report(spikes: list[PriceSpike]) -> str:
    """Format spike report for console output."""
    if not spikes:
        return "✅ No price spikes detected.\n"
    
    report = []
    report.append(f"\n🚨 PRICE SPIKE ALERT - {len(spikes)} spike(s) detected\n")
    report.append("=" * 80)
    
    for i, spike in enumerate(spikes, 1):
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }.get(spike.severity, "⚪")
        
        report.append(f"\n{i}. {severity_emoji} {spike.severity.upper()} SPIKE")
        report.append(f"   Service: {spike.service}")
        report.append(f"   SKU: {spike.sku_id}")
        report.append(f"   Description: {spike.sku_description}")
        report.append(f"   Price Type: {spike.price_type}")
        report.append(f"   Previous Price: ${spike.previous_price:.6f}")
        report.append(f"   Current Price:  ${spike.current_price:.6f}")
        report.append(f"   Increase: +${spike.absolute_increase:.6f} ({spike.percentage_increase:.2f}%)")
        report.append(f"   Detected: {spike.timestamp}")
        report.append(f"   Days since last check: {spike.days_since_last_check}")
        report.append("-" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Check for GCP price spikes")
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Minimum percentage increase to consider a spike (default: 10%%)"
    )
    parser.add_argument(
        "--service",
        type=str,
        default=None,
        help="Filter by service name (e.g., 'GCP')"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to look back for comparison (default: 30)"
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        default=None,
        help="Import pricing data from CSV file first"
    )
    parser.add_argument(
        "--trend",
        action="store_true",
        help="Show price trends for all tracked SKUs"
    )
    
    args = parser.parse_args()
    
    tracker = get_tracker()
    
    # Import CSV if specified
    if args.import_csv:
        print(f"📥 Importing pricing data from {args.import_csv}...")
        tracker.import_from_csv(args.import_csv)
        print("✅ Import complete.\n")
    
    # Show trends if requested
    if args.trend:
        print("\n📈 PRICE TRENDS\n")
        print("=" * 80)
        
        # Get unique service/sku/type combinations
        seen = set()
        for snapshot in tracker.history:
            key = (snapshot.service, snapshot.sku_id, snapshot.price_type)
            if key not in seen:
                seen.add(key)
                trend = tracker.get_price_trend(
                    service=snapshot.service,
                    sku_id=snapshot.sku_id,
                    price_type=snapshot.price_type,
                    days=args.days
                )
                
                if trend["data_points"] >= 2:
                    trend_emoji = {
                        "increasing": "📈",
                        "decreasing": "📉",
                        "stable": "➡️"
                    }.get(trend["trend"], "❓")
                    
                    print(f"\n{trend_emoji} {trend['service']} - {trend['sku_description'][:50]}")
                    print(f"   Type: {trend['price_type']}")
                    print(f"   Trend: {trend['trend']} ({trend['percentage_change']:.2f}%)")
                    print(f"   Price Range: ${trend['min_price']:.6f} - ${trend['max_price']:.6f}")
                    print(f"   Average: ${trend['average_price']:.6f}")
                    print(f"   Data Points: {trend['data_points']}")
                    print("-" * 80)
        
        print()
    
    # Detect spikes
    print(f"🔍 Checking for price spikes (threshold: {args.threshold}%%, lookback: {args.days} days)...")
    spikes = tracker.detect_spikes(
        service=args.service,
        threshold_percentage=args.threshold,
        days_lookback=args.days
    )
    
    # Print report
    report = format_spike_report(spikes)
    print(report)
    
    # Exit with error code if critical spikes found
    critical_spikes = [s for s in spikes if s.severity == "critical"]
    if critical_spikes:
        print(f"\n⚠️  {len(critical_spikes)} CRITICAL spike(s) detected!")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

