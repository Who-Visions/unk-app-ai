#!/usr/bin/env python3
"""
Credit Burn Rate Calculator
===========================
Calculates how long GCP credits will last based on pricing and usage patterns.

Usage:
    python scripts/credit_burn_calculator.py
"""

import sys
from pathlib import Path

# Credit information from the screenshot
CREDITS = {
    "GenAI App Builder Trial": {
        "original": 1000.00,
        "remaining": 1000.00,
        "status": "Available"
    },
    "Free Trial 1": {
        "original": 300.00,
        "remaining": 268.50,
        "status": "Available"
    },
    "Free Trial 2": {
        "original": 300.00,
        "remaining": 0.00,
        "status": "Expired"
    }
}

# Pricing from the CSV analysis
PRICING = {
    "gemini_2_5_flash": {
        "input_per_1m": 0.30,
        "output_per_1m": 2.50,
        "caching_input_per_1m": 0.03
    },
    "gemini_2_5_pro": {
        "input_per_1m": 1.25,
        "output_per_1m": 10.00,
        "caching_input_per_1m": 0.125
    },
    "gemini_3_0_pro": {
        "input_per_1m": 2.00,
        "output_per_1m": 12.00
    },
    "storage": {
        "standard_per_gib_month": 0.02,
        "egress_per_gib": 0.12
    },
    "logging": {
        "per_gib": 0.50
    }
}

def calculate_cost_per_request(model: str, input_tokens: int, output_tokens: int, use_caching: bool = False) -> float:
    """Calculate cost for a single request."""
    if model not in PRICING:
        return 0.0
    
    pricing = PRICING[model]
    
    if use_caching and "caching_input_per_1m" in pricing:
        input_cost = (input_tokens / 1_000_000) * pricing["caching_input_per_1m"]
    else:
        input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]
    
    return round(input_cost + output_cost, 6)


def calculate_requests_per_dollar(model: str, avg_input_tokens: int, avg_output_tokens: int, use_caching: bool = False) -> float:
    """Calculate how many requests you can make per dollar."""
    cost_per_request = calculate_cost_per_request(model, avg_input_tokens, avg_output_tokens, use_caching)
    if cost_per_request == 0:
        return 0.0
    return round(1.0 / cost_per_request, 2)


def calculate_days_remaining(total_credits: float, daily_spend: float) -> float:
    """Calculate how many days credits will last."""
    if daily_spend == 0:
        return float('inf')
    return round(total_credits / daily_spend, 1)


def generate_report():
    """Generate credit burn rate report."""
    
    total_available = sum(c["remaining"] for c in CREDITS.values() if c["status"] == "Available")
    total_used = sum(c["original"] - c["remaining"] for c in CREDITS.values() if c["status"] == "Available")
    
    report = []
    report.append("=" * 80)
    report.append("💰 GCP CREDIT BURN RATE ANALYSIS")
    report.append("=" * 80)
    report.append("")
    
    # Current Credit Status
    report.append("📊 CURRENT CREDIT STATUS")
    report.append("-" * 80)
    for name, credit in CREDITS.items():
        if credit["status"] == "Available":
            percent_used = ((credit["original"] - credit["remaining"]) / credit["original"]) * 100
            report.append(f"  {name}:")
            report.append(f"    Remaining: ${credit['remaining']:.2f} / ${credit['original']:.2f}")
            report.append(f"    Used: {percent_used:.1f}%")
            report.append("")
    
    report.append(f"  💵 TOTAL AVAILABLE: ${total_available:.2f}")
    report.append(f"  📉 TOTAL USED THIS WEEK: ${total_used:.2f}")
    report.append("")
    
    # Usage Scenarios
    report.append("🎯 USAGE SCENARIOS & CREDIT LIFESPAN")
    report.append("-" * 80)
    report.append("")
    
    # Scenario 1: Light Usage (Flash, no caching)
    scenarios = [
        {
            "name": "Light Usage (Flash, No Caching)",
            "model": "gemini_2_5_flash",
            "requests_per_day": 1000,
            "avg_input": 500,
            "avg_output": 200,
            "caching": False
        },
        {
            "name": "Light Usage (Flash, With Caching)",
            "model": "gemini_2_5_flash",
            "requests_per_day": 1000,
            "avg_input": 500,
            "avg_output": 200,
            "caching": True
        },
        {
            "name": "Moderate Usage (Flash, No Caching)",
            "model": "gemini_2_5_flash",
            "requests_per_day": 5000,
            "avg_input": 1000,
            "avg_output": 500,
            "caching": False
        },
        {
            "name": "Moderate Usage (Flash, With Caching)",
            "model": "gemini_2_5_flash",
            "requests_per_day": 5000,
            "avg_input": 1000,
            "avg_output": 500,
            "caching": True
        },
        {
            "name": "Heavy Usage (Pro, No Caching)",
            "model": "gemini_2_5_pro",
            "requests_per_day": 1000,
            "avg_input": 2000,
            "avg_output": 1000,
            "caching": False
        },
        {
            "name": "Heavy Usage (Pro, With Caching)",
            "model": "gemini_2_5_pro",
            "requests_per_day": 1000,
            "avg_input": 2000,
            "avg_output": 1000,
            "caching": True
        },
        {
            "name": "Ultra Heavy (3.0 Pro)",
            "model": "gemini_3_0_pro",
            "requests_per_day": 500,
            "avg_input": 3000,
            "avg_output": 2000,
            "caching": False
        }
    ]
    
    for scenario in scenarios:
        cost_per_request = calculate_cost_per_request(
            scenario["model"],
            scenario["avg_input"],
            scenario["avg_output"],
            scenario["caching"]
        )
        daily_cost = cost_per_request * scenario["requests_per_day"]
        days_remaining = calculate_days_remaining(total_available, daily_cost)
        requests_per_dollar = calculate_requests_per_dollar(
            scenario["model"],
            scenario["avg_input"],
            scenario["avg_output"],
            scenario["caching"]
        )
        
        report.append(f"  📌 {scenario['name']}:")
        report.append(f"     Requests/day: {scenario['requests_per_day']:,}")
        report.append(f"     Avg tokens: {scenario['avg_input']:,} input + {scenario['avg_output']:,} output")
        report.append(f"     Cost/request: ${cost_per_request:.6f}")
        report.append(f"     Daily cost: ${daily_cost:.2f}")
        report.append(f"     Requests per $1: {requests_per_dollar:,}")
        
        if days_remaining == float('inf'):
            report.append(f"     ⏰ Credits will last: Forever (no usage)")
        elif days_remaining > 365:
            years = days_remaining / 365
            report.append(f"     ⏰ Credits will last: {years:.1f} years ({days_remaining:.0f} days)")
        elif days_remaining > 30:
            months = days_remaining / 30
            report.append(f"     ⏰ Credits will last: {months:.1f} months ({days_remaining:.0f} days)")
        else:
            report.append(f"     ⏰ Credits will last: {days_remaining:.1f} days")
        
        if scenario["caching"]:
            report.append(f"     💡 Using caching: 90% savings on input tokens")
        report.append("")
    
    # Cost Breakdown
    report.append("💵 COST BREAKDOWN BY MODEL")
    report.append("-" * 80)
    report.append("")
    
    # Example: 1M input + 500K output tokens
    example_input = 1_000_000
    example_output = 500_000
    
    for model_name, model_key in [
        ("Gemini 2.5 Flash", "gemini_2_5_flash"),
        ("Gemini 2.5 Pro", "gemini_2_5_pro"),
        ("Gemini 3.0 Pro", "gemini_3_0_pro")
    ]:
        cost_no_cache = calculate_cost_per_request(model_key, example_input, example_output, False)
        cost_with_cache = calculate_cost_per_request(model_key, example_input, example_output, True) if model_key != "gemini_3_0_pro" else None
        
        report.append(f"  {model_name} (1M input + 500K output tokens):")
        report.append(f"    Without caching: ${cost_no_cache:.4f}")
        if cost_with_cache:
            savings = ((cost_no_cache - cost_with_cache) / cost_no_cache) * 100
            report.append(f"    With caching: ${cost_with_cache:.4f} (save {savings:.1f}%)")
        report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    report.append("")
    report.append("  1. ✅ Use Gemini 2.5 Flash for 90%+ of requests (cost-efficient)")
    report.append("  2. ✅ Enable caching for repeated queries (90% discount on input)")
    report.append("  3. ✅ Reserve Pro models for complex tasks only")
    report.append("  4. ✅ Monitor daily spend to track burn rate")
    report.append("  5. ⚠️  Avoid Gemini 3.0 Pro unless absolutely necessary (2x cost)")
    report.append("")
    
    # Weekly Burn Rate Analysis
    if total_used > 0:
        report.append("📈 WEEKLY BURN RATE ANALYSIS")
        report.append("-" * 80)
        report.append(f"  Credits used this week: ${total_used:.2f}")
        report.append(f"  Daily average: ${total_used / 7:.2f}")
        report.append(f"  Projected monthly burn: ${(total_used / 7) * 30:.2f}")
        
        if total_used > 0:
            projected_days = calculate_days_remaining(total_available, total_used / 7)
            if projected_days < 365:
                report.append(f"  ⏰ At current rate, credits will last: {projected_days:.1f} days")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    report = generate_report()
    print(report)
    
    # Save report
    report_file = Path("data/credit_burn_analysis.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

