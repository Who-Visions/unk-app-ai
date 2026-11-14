#!/usr/bin/env python3
"""
Image Generation Cost Calculator (Yuki Stress Tests)
=====================================================
Calculates costs for image generation stress tests and credit impact.

Usage:
    python scripts/image_generation_cost_calculator.py [--images N] [--model imagen3|imagen4]
"""

import sys
import argparse
from pathlib import Path

# Credit information
CREDITS = {
    "GenAI App Builder Trial": {
        "remaining": 1000.00,
        "status": "Available"
    },
    "Free Trial 1": {
        "remaining": 268.50,
        "status": "Available"
    }
}

TOTAL_AVAILABLE = sum(c["remaining"] for c in CREDITS.values() if c["status"] == "Available")

# Image generation pricing from CSV
IMAGE_PRICING = {
    "imagen3": {
        "price_per_image": 0.04,
        "description": "Imagen 3 Generation"
    },
    "imagen4": {
        "price_per_image": 0.04,
        "description": "Imagen 4 Generation"
    },
    "gemini_3_pro_image_output": {
        "price_per_1m_images": 120.00,
        "description": "Gemini 3.0 Pro Image Output (very expensive!)"
    }
}


def calculate_image_generation_costs(num_images: int, model: str = "imagen3") -> dict:
    """Calculate costs for image generation."""
    
    if model not in IMAGE_PRICING:
        model = "imagen3"
    
    pricing = IMAGE_PRICING[model]
    
    if "price_per_image" in pricing:
        cost_per_image = pricing["price_per_image"]
        total_cost = num_images * cost_per_image
    else:
        # For per-1M pricing
        cost_per_image = pricing["price_per_1m_images"] / 1_000_000
        total_cost = num_images * cost_per_image
    
    return {
        "model": model,
        "num_images": num_images,
        "cost_per_image": cost_per_image,
        "total_cost": round(total_cost, 2),
        "images_per_dollar": round(1.0 / cost_per_image, 2) if cost_per_image > 0 else 0,
        "credits_remaining_after": round(TOTAL_AVAILABLE - total_cost, 2),
        "percent_of_credits_used": round((total_cost / TOTAL_AVAILABLE) * 100, 2) if TOTAL_AVAILABLE > 0 else 0
    }


def calculate_stress_test_scenarios():
    """Calculate various stress test scenarios."""
    
    scenarios = [
        {"name": "Small Test", "images": 100},
        {"name": "Medium Test", "images": 500},
        {"name": "Large Test", "images": 1000},
        {"name": "Stress Test", "images": 5000},
        {"name": "Extreme Stress Test", "images": 10000},
        {"name": "Maximum Burn Test", "images": 30000},
    ]
    
    results = []
    for scenario in scenarios:
        for model in ["imagen3", "imagen4"]:
            costs = calculate_image_generation_costs(scenario["images"], model)
            results.append({
                **scenario,
                **costs
            })
    
    return results


def generate_report(num_images: int = None, model: str = "imagen3"):
    """Generate cost analysis report."""
    
    report = []
    report.append("=" * 80)
    report.append("🎨 IMAGE GENERATION COST ANALYSIS (Yuki Stress Tests)")
    report.append("=" * 80)
    report.append("")
    
    # Current Credits
    report.append("💰 CURRENT CREDIT STATUS")
    report.append("-" * 80)
    report.append(f"  Total Available: ${TOTAL_AVAILABLE:.2f}")
    report.append("")
    
    # Pricing Information
    report.append("📊 IMAGE GENERATION PRICING")
    report.append("-" * 80)
    for model_key, pricing in IMAGE_PRICING.items():
        if "price_per_image" in pricing:
            report.append(f"  {pricing['description']}: ${pricing['price_per_image']:.4f} per image")
            report.append(f"    → {int(1.0 / pricing['price_per_image']):,} images per $1")
        else:
            cost_per_image = pricing["price_per_1m_images"] / 1_000_000
            report.append(f"  {pricing['description']}: ${cost_per_image:.6f} per image")
            report.append(f"    → {int(1.0 / cost_per_image):,} images per $1")
            report.append(f"    ⚠️  VERY EXPENSIVE - Avoid for stress tests!")
        report.append("")
    
    # Specific Calculation
    if num_images:
        costs = calculate_image_generation_costs(num_images, model)
        report.append(f"📈 COST ANALYSIS FOR {num_images:,} IMAGES ({costs['model'].upper()})")
        report.append("-" * 80)
        report.append(f"  Images to generate: {costs['num_images']:,}")
        report.append(f"  Cost per image: ${costs['cost_per_image']:.6f}")
        report.append(f"  Total cost: ${costs['total_cost']:.2f}")
        report.append(f"  Images per $1: {costs['images_per_dollar']:,}")
        report.append(f"  Credits remaining: ${costs['credits_remaining_after']:.2f}")
        report.append(f"  % of credits used: {costs['percent_of_credits_used']:.2f}%")
        report.append("")
    
    # Stress Test Scenarios
    report.append("🎯 STRESS TEST SCENARIOS")
    report.append("-" * 80)
    report.append("")
    
    scenarios = calculate_stress_test_scenarios()
    
    # Group by scenario name
    scenario_groups = {}
    for result in scenarios:
        name = result["name"]
        if name not in scenario_groups:
            scenario_groups[name] = []
        scenario_groups[name].append(result)
    
    for scenario_name in ["Small Test", "Medium Test", "Large Test", "Stress Test", "Extreme Stress Test", "Maximum Burn Test"]:
        if scenario_name not in scenario_groups:
            continue
        
        results = scenario_groups[scenario_name]
        report.append(f"  📌 {scenario_name}:")
        
        for result in results:
            model_display = result["model"].replace("imagen", "Imagen ").upper()
            report.append(f"     {model_display}:")
            report.append(f"       {result['num_images']:,} images = ${result['total_cost']:.2f}")
            report.append(f"       Remaining credits: ${result['credits_remaining_after']:.2f}")
            report.append(f"       Credit usage: {result['percent_of_credits_used']:.2f}%")
        
        report.append("")
    
    # Maximum Images Possible
    report.append("🚀 MAXIMUM IMAGES POSSIBLE")
    report.append("-" * 80)
    
    for model_key, pricing in IMAGE_PRICING.items():
        if "price_per_image" in pricing:
            max_images = int(TOTAL_AVAILABLE / pricing["price_per_image"])
            report.append(f"  {pricing['description']}:")
            report.append(f"    Maximum images: {max_images:,}")
            report.append(f"    Cost: ${TOTAL_AVAILABLE:.2f}")
            report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS FOR STRESS TESTING")
    report.append("-" * 80)
    report.append("")
    report.append("  1. ✅ Use Imagen 3 or 4 for stress tests ($0.04/image)")
    report.append("  2. ✅ Start with small batches (100-500 images)")
    report.append("  3. ✅ Monitor credit burn rate after each test")
    report.append("  4. ⚠️  Avoid Gemini 3.0 Pro for image generation ($120/1M images)")
    report.append("  5. 💰 At $0.04/image, you can generate:")
    report.append(f"     • {int(TOTAL_AVAILABLE / 0.04):,} images total")
    report.append(f"     • {int((TOTAL_AVAILABLE / 0.04) / 30):,} images/day for 30 days")
    report.append(f"     • {int((TOTAL_AVAILABLE / 0.04) / 7):,} images/day for 7 days")
    report.append("")
    
    # Daily Burn Rate Analysis
    if num_images:
        costs = calculate_image_generation_costs(num_images, model)
        daily_burn = costs["total_cost"]
        days_remaining = TOTAL_AVAILABLE / daily_burn if daily_burn > 0 else float('inf')
        
        report.append("📅 DAILY BURN RATE ANALYSIS")
        report.append("-" * 80)
        report.append(f"  If generating {num_images:,} images/day:")
        report.append(f"  Daily cost: ${daily_burn:.2f}")
        report.append(f"  Weekly cost: ${daily_burn * 7:.2f}")
        report.append(f"  Monthly cost: ${daily_burn * 30:.2f}")
        
        if days_remaining != float('inf'):
            if days_remaining > 365:
                report.append(f"  ⏰ Credits will last: {days_remaining / 365:.1f} years ({days_remaining:.0f} days)")
            elif days_remaining > 30:
                report.append(f"  ⏰ Credits will last: {days_remaining / 30:.1f} months ({days_remaining:.0f} days)")
            else:
                report.append(f"  ⏰ Credits will last: {days_remaining:.1f} days")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Calculate image generation costs")
    parser.add_argument(
        "--images",
        type=int,
        default=None,
        help="Number of images to calculate cost for"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="imagen3",
        choices=["imagen3", "imagen4"],
        help="Model to use (default: imagen3)"
    )
    
    args = parser.parse_args()
    
    report = generate_report(args.images, args.model)
    print(report)
    
    # Save report
    report_file = Path("data/image_generation_costs.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

