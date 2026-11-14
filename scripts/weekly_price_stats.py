#!/usr/bin/env python3
"""
Weekly Price Statistics
========================
Analyzes pricing data and generates weekly statistics.

Usage:
    python scripts/weekly_price_stats.py [csv_file]
"""

import sys
import csv
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

def analyze_pricing_csv(csv_path: str) -> Dict:
    """Analyze pricing CSV and generate statistics."""
    
    stats = {
        "total_skus": 0,
        "services": defaultdict(int),
        "price_types": defaultdict(int),
        "services_breakdown": defaultdict(lambda: {"skus": 0, "price_ranges": []}),
        "vertex_ai_models": {},
        "storage_pricing": {},
        "highest_prices": [],
        "free_tiers": [],
        "tiered_pricing": defaultdict(list)
    }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            service = row.get('Google service', '').strip()
            service_desc = row.get('Service description', '').strip()
            sku_id = row.get('SKU ID', '').strip()
            sku_desc = row.get('SKU description', '').strip()
            contract_price = row.get('Contract price ($)', '').strip()
            unit = row.get('Unit description', '').strip()
            tier_start = row.get('Tiered usage start', '').strip()
            
            if not service or not sku_id:
                continue
            
            try:
                price = float(contract_price) if contract_price else 0.0
                tier = float(tier_start) if tier_start else None
            except ValueError:
                continue
            
            stats["total_skus"] += 1
            stats["services"][service] += 1
            
            # Determine price type
            price_type = "unknown"
            if "input" in sku_desc.lower():
                price_type = "input"
            elif "output" in sku_desc.lower():
                price_type = "output"
            elif "storage" in sku_desc.lower():
                price_type = "storage"
            elif "egress" in sku_desc.lower() or "transfer" in sku_desc.lower():
                price_type = "egress"
            elif "operations" in sku_desc.lower() or "ops" in sku_desc.lower():
                price_type = "operations"
            elif "generation" in sku_desc.lower():
                price_type = "generation"
            elif "cpu" in sku_desc.lower():
                price_type = "cpu"
            elif "memory" in sku_desc.lower() or "ram" in sku_desc.lower():
                price_type = "memory"
            
            stats["price_types"][price_type] += 1
            
            # Service breakdown
            stats["services_breakdown"][service]["skus"] += 1
            if price > 0:
                stats["services_breakdown"][service]["price_ranges"].append(price)
            
            # Vertex AI specific tracking
            if service == "GCP" and service_desc == "Vertex AI":
                if "Gemini" in sku_desc:
                    model_name = "Unknown"
                    if "2.5 Flash" in sku_desc:
                        model_name = "Gemini 2.5 Flash"
                    elif "2.5 Pro" in sku_desc:
                        model_name = "Gemini 2.5 Pro"
                    elif "3.0 Pro" in sku_desc:
                        model_name = "Gemini 3.0 Pro"
                    
                    if model_name not in stats["vertex_ai_models"]:
                        stats["vertex_ai_models"][model_name] = {
                            "input": None,
                            "output": None,
                            "caching_input": None
                        }
                    
                    if "Input" in sku_desc and "Caching" not in sku_desc:
                        stats["vertex_ai_models"][model_name]["input"] = price
                    elif "Output" in sku_desc:
                        stats["vertex_ai_models"][model_name]["output"] = price
                    elif "Caching" in sku_desc:
                        stats["vertex_ai_models"][model_name]["caching_input"] = price
            
            # Storage pricing
            if service == "GCP" and service_desc == "Cloud Storage":
                if "Storage" in sku_desc and price > 0:
                    stats["storage_pricing"][sku_desc] = {
                        "price": price,
                        "unit": unit,
                        "tier_start": tier
                    }
            
            # Track highest prices
            if price > 0:
                stats["highest_prices"].append({
                    "service": service,
                    "sku": sku_desc,
                    "price": price,
                    "unit": unit
                })
            
            # Track free tiers
            if price == 0.0 and tier is not None:
                stats["free_tiers"].append({
                    "service": service,
                    "sku": sku_desc,
                    "free_up_to": tier,
                    "unit": unit
                })
            
            # Tiered pricing
            if tier is not None and price > 0:
                stats["tiered_pricing"][sku_desc].append({
                    "tier_start": tier,
                    "price": price
                })
    
    # Sort highest prices
    stats["highest_prices"].sort(key=lambda x: x["price"], reverse=True)
    
    return stats


def format_stats_report(stats: Dict) -> str:
    """Format statistics as a readable report."""
    
    report = []
    report.append("=" * 80)
    report.append("📊 WEEKLY PRICING STATISTICS")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Overview
    report.append("📈 OVERVIEW")
    report.append("-" * 80)
    report.append(f"Total SKUs Tracked: {stats['total_skus']}")
    report.append(f"Services: {len(stats['services'])}")
    report.append("")
    
    # Services breakdown
    report.append("🏢 SERVICES BREAKDOWN")
    report.append("-" * 80)
    for service, count in sorted(stats["services"].items(), key=lambda x: x[1], reverse=True):
        price_ranges = stats["services_breakdown"][service]["price_ranges"]
        if price_ranges:
            avg_price = sum(price_ranges) / len(price_ranges)
            min_price = min(price_ranges)
            max_price = max(price_ranges)
            report.append(f"  {service}: {count} SKUs")
            report.append(f"    Price Range: ${min_price:.6f} - ${max_price:.6f}")
            report.append(f"    Average Price: ${avg_price:.6f}")
        else:
            report.append(f"  {service}: {count} SKUs (free tier only)")
        report.append("")
    
    # Vertex AI Models
    if stats["vertex_ai_models"]:
        report.append("🤖 VERTEX AI MODEL PRICING")
        report.append("-" * 80)
        for model, pricing in sorted(stats["vertex_ai_models"].items()):
            report.append(f"  {model}:")
            if pricing["input"]:
                report.append(f"    Input: ${pricing['input']:.6f} per 1M tokens")
            if pricing["output"]:
                report.append(f"    Output: ${pricing['output']:.6f} per 1M tokens")
            if pricing["caching_input"]:
                report.append(f"    Caching Input: ${pricing['caching_input']:.6f} per 1M tokens")
                if pricing["input"]:
                    savings = ((pricing["input"] - pricing["caching_input"]) / pricing["input"]) * 100
                    report.append(f"    💰 Caching Savings: {savings:.1f}%")
            report.append("")
    
    # Price Types
    report.append("💰 PRICE TYPE DISTRIBUTION")
    report.append("-" * 80)
    for ptype, count in sorted(stats["price_types"].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {ptype.capitalize()}: {count} SKUs")
    report.append("")
    
    # Top 5 Highest Prices
    if stats["highest_prices"]:
        report.append("🔝 TOP 5 HIGHEST PRICES")
        report.append("-" * 80)
        for i, item in enumerate(stats["highest_prices"][:5], 1):
            report.append(f"  {i}. {item['sku'][:60]}")
            report.append(f"     ${item['price']:.6f} per {item['unit']}")
            report.append(f"     Service: {item['service']}")
            report.append("")
    
    # Free Tiers
    if stats["free_tiers"]:
        report.append("🆓 FREE TIERS")
        report.append("-" * 80)
        for tier in stats["free_tiers"][:10]:
            report.append(f"  {tier['sku'][:60]}")
            report.append(f"     Free up to: {tier['free_up_to']} {tier['unit']}")
            report.append(f"     Service: {tier['service']}")
            report.append("")
    
    # Cost Optimization Insights
    report.append("💡 COST OPTIMIZATION INSIGHTS")
    report.append("-" * 80)
    
    # Caching savings
    caching_savings = []
    for model, pricing in stats["vertex_ai_models"].items():
        if pricing["input"] and pricing["caching_input"]:
            savings_pct = ((pricing["input"] - pricing["caching_input"]) / pricing["input"]) * 100
            savings_abs = pricing["input"] - pricing["caching_input"]
            caching_savings.append({
                "model": model,
                "savings_pct": savings_pct,
                "savings_abs": savings_abs
            })
    
    if caching_savings:
        report.append("  Caching Discounts Available:")
        for item in caching_savings:
            report.append(f"    {item['model']}: {item['savings_pct']:.1f}% off (${item['savings_abs']:.6f} per 1M tokens)")
        report.append("")
    
    # Tiered pricing opportunities
    tiered_count = len([k for k, v in stats["tiered_pricing"].items() if len(v) > 1])
    if tiered_count > 0:
        report.append(f"  {tiered_count} SKUs have tiered pricing (volume discounts available)")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    # Default CSV path
    default_csv = Path("c:/Users/super/Downloads/Pricing for Who Visions LLC (1).csv")
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    elif default_csv.exists():
        csv_path = str(default_csv)
    else:
        print("❌ Error: CSV file not found.")
        print(f"   Expected: {default_csv}")
        print("   Usage: python scripts/weekly_price_stats.py [csv_file]")
        sys.exit(1)
    
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"📥 Analyzing pricing data from: {csv_file}")
    print("")
    
    stats = analyze_pricing_csv(str(csv_file))
    report = format_stats_report(stats)
    
    print(report)
    
    # Save report to file
    report_file = Path("data/weekly_price_stats.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

