#!/usr/bin/env python3
"""
Gemini 3 Pro Image Generation Cost Calculator
==============================================
Compares Gemini 3 Pro image generation vs Imagen pricing.

Usage:
    python scripts/gemini3_pro_image_calculator.py [--images N] [--resolution 1k|2k|4k]
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

# Updated pricing from official docs
IMAGE_PRICING = {
    "imagen3": {
        "price_per_image": 0.04,
        "description": "Imagen 3 Generation",
        "resolution": "Standard"
    },
    "imagen4": {
        "price_per_image": 0.04,
        "description": "Imagen 4 Generation",
        "resolution": "Standard"
    },
    "imagen4_fast": {
        "price_per_image": 0.02,
        "description": "Imagen 4 Fast",
        "resolution": "Standard"
    },
    "imagen4_ultra": {
        "price_per_image": 0.06,
        "description": "Imagen 4 Ultra",
        "resolution": "Standard"
    },
    "gemini3_pro_1k": {
        "price_per_image": 0.134,  # 1120 tokens * $120/1M tokens
        "description": "Gemini 3 Pro Image Output (1K: 1024x1024)",
        "tokens_per_image": 1120,
        "resolution": "1K (1024x1024)"
    },
    "gemini3_pro_2k": {
        "price_per_image": 0.134,  # 1120 tokens * $120/1M tokens
        "description": "Gemini 3 Pro Image Output (2K: 2048x2048)",
        "tokens_per_image": 1120,
        "resolution": "2K (2048x2048)"
    },
    "gemini3_pro_4k": {
        "price_per_image": 0.24,  # 2000 tokens * $120/1M tokens
        "description": "Gemini 3 Pro Image Output (4K: 4096x4096)",
        "tokens_per_image": 2000,
        "resolution": "4K (4096x4096)"
    }
}


def calculate_image_costs(num_images: int, model: str = "imagen3") -> dict:
    """Calculate costs for image generation."""
    
    if model not in IMAGE_PRICING:
        model = "imagen3"
    
    pricing = IMAGE_PRICING[model]
    cost_per_image = pricing["price_per_image"]
    total_cost = num_images * cost_per_image
    
    return {
        "model": model,
        "num_images": num_images,
        "cost_per_image": cost_per_image,
        "total_cost": round(total_cost, 2),
        "images_per_dollar": round(1.0 / cost_per_image, 2) if cost_per_image > 0 else 0,
        "credits_remaining_after": round(TOTAL_AVAILABLE - total_cost, 2),
        "percent_of_credits_used": round((total_cost / TOTAL_AVAILABLE) * 100, 2) if TOTAL_AVAILABLE > 0 else 0,
        "description": pricing["description"],
        "resolution": pricing.get("resolution", "N/A")
    }


def generate_comparison_report(num_images: int = 300):
    """Generate comparison report for different image generation models."""
    
    report = []
    report.append("=" * 80)
    report.append("🎨 IMAGE GENERATION COST COMPARISON")
    report.append("=" * 80)
    report.append("")
    
    # Current Credits
    report.append("💰 CURRENT CREDIT STATUS")
    report.append("-" * 80)
    report.append(f"  Total Available: ${TOTAL_AVAILABLE:.2f}")
    report.append("")
    
    # Pricing Comparison
    report.append(f"📊 COST COMPARISON FOR {num_images:,} IMAGES")
    report.append("-" * 80)
    report.append("")
    
    models_to_compare = [
        "imagen4_fast",
        "imagen3",
        "imagen4",
        "imagen4_ultra",
        "gemini3_pro_1k",
        "gemini3_pro_2k",
        "gemini3_pro_4k"
    ]
    
    results = []
    for model in models_to_compare:
        costs = calculate_image_costs(num_images, model)
        results.append(costs)
    
    # Sort by cost
    results.sort(key=lambda x: x["total_cost"])
    
    report.append("  Model                          | Cost/Image | Total Cost  | Images/$1")
    report.append("  " + "-" * 70)
    
    for result in results:
        model_name = result["description"][:30].ljust(30)
        cost_per = f"${result['cost_per_image']:.4f}".ljust(12)
        total = f"${result['total_cost']:.2f}".ljust(12)
        per_dollar = f"{result['images_per_dollar']:,.0f}".ljust(12)
        report.append(f"  {model_name} | {cost_per} | {total} | {per_dollar}")
    
    report.append("")
    
    # Detailed Analysis
    report.append("💵 DETAILED ANALYSIS")
    report.append("-" * 80)
    report.append("")
    
    # Imagen vs Gemini 3 Pro
    imagen_cost = calculate_image_costs(num_images, "imagen4")
    gemini3_1k_cost = calculate_image_costs(num_images, "gemini3_pro_1k")
    gemini3_4k_cost = calculate_image_costs(num_images, "gemini3_pro_4k")
    
    report.append(f"  Imagen 4 ({num_images:,} images):")
    report.append(f"    Cost: ${imagen_cost['total_cost']:.2f}")
    report.append(f"    Cost per image: ${imagen_cost['cost_per_image']:.4f}")
    report.append("")
    
    report.append(f"  Gemini 3 Pro 1K/2K ({num_images:,} images):")
    report.append(f"    Cost: ${gemini3_1k_cost['total_cost']:.2f}")
    report.append(f"    Cost per image: ${gemini3_1k_cost['cost_per_image']:.4f}")
    report.append(f"    Tokens per image: {gemini3_1k_cost.get('tokens_per_image', 'N/A')}")
    report.append(f"    ⚠️  {gemini3_1k_cost['cost_per_image'] / imagen_cost['cost_per_image']:.1f}x more expensive than Imagen")
    report.append("")
    
    report.append(f"  Gemini 3 Pro 4K ({num_images:,} images):")
    report.append(f"    Cost: ${gemini3_4k_cost['total_cost']:.2f}")
    report.append(f"    Cost per image: ${gemini3_4k_cost['cost_per_image']:.4f}")
    report.append(f"    Tokens per image: {gemini3_4k_cost.get('tokens_per_image', 'N/A')}")
    report.append(f"    ⚠️  {gemini3_4k_cost['cost_per_image'] / imagen_cost['cost_per_image']:.1f}x more expensive than Imagen")
    report.append("")
    
    # Cost Difference
    cost_diff_1k = gemini3_1k_cost['total_cost'] - imagen_cost['total_cost']
    cost_diff_4k = gemini3_4k_cost['total_cost'] - imagen_cost['total_cost']
    
    report.append("📈 COST DIFFERENCE")
    report.append("-" * 80)
    report.append(f"  Gemini 3 Pro 1K/2K vs Imagen 4:")
    report.append(f"    Extra cost: ${cost_diff_1k:.2f} ({cost_diff_1k / TOTAL_AVAILABLE * 100:.2f}% of credits)")
    report.append(f"    You could generate {int(cost_diff_1k / imagen_cost['cost_per_image']):,} more images with Imagen")
    report.append("")
    report.append(f"  Gemini 3 Pro 4K vs Imagen 4:")
    report.append(f"    Extra cost: ${cost_diff_4k:.2f} ({cost_diff_4k / TOTAL_AVAILABLE * 100:.2f}% of credits)")
    report.append(f"    You could generate {int(cost_diff_4k / imagen_cost['cost_per_image']):,} more images with Imagen")
    report.append("")
    
    # Maximum Images Possible
    report.append("🚀 MAXIMUM IMAGES POSSIBLE WITH YOUR CREDITS")
    report.append("-" * 80)
    
    for model in ["imagen4_fast", "imagen4", "gemini3_pro_1k", "gemini3_pro_4k"]:
        costs = calculate_image_costs(1, model)
        max_images = int(TOTAL_AVAILABLE / costs["cost_per_image"])
        report.append(f"  {costs['description']}:")
        report.append(f"    Maximum images: {max_images:,}")
        report.append(f"    Cost per image: ${costs['cost_per_image']:.4f}")
        report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    report.append("")
    report.append("  ✅ BEST VALUE: Imagen 4 Fast ($0.02/image)")
    report.append("     • Cheapest option")
    report.append("     • Good for stress testing")
    report.append("")
    report.append("  ✅ STANDARD: Imagen 3/4 ($0.04/image)")
    report.append("     • Best balance of quality and cost")
    report.append("     • What Yuki currently uses")
    report.append("")
    report.append("  ⚠️  AVOID FOR STRESS TESTS: Gemini 3 Pro Image Output")
    report.append("     • 1K/2K: $0.134/image (3.35x more expensive)")
    report.append("     • 4K: $0.24/image (6x more expensive)")
    report.append("     • Use only when you need Gemini's multimodal capabilities")
    report.append("     • Not cost-effective for pure image generation")
    report.append("")
    
    # Your 300 Images Analysis
    report.append("📊 YOUR 300 IMAGES ANALYSIS")
    report.append("-" * 80)
    
    for model in ["imagen4", "gemini3_pro_1k", "gemini3_pro_4k"]:
        costs = calculate_image_costs(300, model)
        report.append(f"  {costs['description']}:")
        report.append(f"    Total cost: ${costs['total_cost']:.2f}")
        report.append(f"    Credits remaining: ${costs['credits_remaining_after']:.2f}")
        report.append(f"    % of credits used: {costs['percent_of_credits_used']:.2f}%")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Compare image generation costs")
    parser.add_argument(
        "--images",
        type=int,
        default=300,
        help="Number of images to calculate (default: 300)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["1k", "2k", "4k"],
        default="1k",
        help="Gemini 3 Pro resolution (default: 1k)"
    )
    
    args = parser.parse_args()
    
    report = generate_comparison_report(args.images)
    print(report)
    
    # Save report
    report_file = Path("data/gemini3_pro_image_comparison.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

