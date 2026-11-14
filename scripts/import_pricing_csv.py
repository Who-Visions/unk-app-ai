#!/usr/bin/env python3
"""
Import Pricing CSV to Price Tracker
=====================================
Imports pricing data from CSV file into the price tracking system.

Usage:
    python scripts/import_pricing_csv.py "path/to/pricing.csv"
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gemini_agent.price_tracker import get_tracker


def main():
    parser = argparse.ArgumentParser(description="Import pricing data from CSV")
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to the pricing CSV file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing"
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    tracker = get_tracker()
    
    print(f"📥 Importing pricing data from: {csv_path}")
    print(f"📊 Current history size: {len(tracker.history)} records\n")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be saved\n")
        # Count what would be imported
        import csv
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                service = row.get('Google service', '').strip()
                sku_id = row.get('SKU ID', '').strip()
                contract_price = row.get('Contract price ($)', '').strip()
                if service and sku_id and contract_price:
                    try:
                        float(contract_price)
                        count += 1
                    except ValueError:
                        pass
        
        print(f"✅ Would import {count} price records")
    else:
        tracker.import_from_csv(str(csv_path))
        print(f"✅ Import complete!")
        print(f"📊 New history size: {len(tracker.history)} records")
        print(f"📈 Added {len(tracker.history) - len([s for s in tracker.history if s.metadata.get('source') != 'csv_import'])} new records")


if __name__ == "__main__":
    main()

