#!/usr/bin/env python3
"""
Gemini 2.5 Flash Image vs Other Options Comparison
==================================================
Compares Gemini 2.5 Flash Image with Imagen and Gemini 3 Pro.

Usage:
    python scripts/flash_image_comparison.py [--images N]
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

# Updated pricing - Gemini 2.5 Flash Image
IMAGE_PRICING = {
    "imagen3": {
        "price_per_image": 0.04,
        "description": "Imagen 3",
        "model_id": "imagen-3",
        "capabilities": "Image generation only"
    },
    "imagen4": {
        "price_per_image": 0.04,
        "description": "Imagen 4",
        "model_id": "imagen-4",
        "capabilities": "Image generation only"
    },
    "imagen4_fast": {
        "price_per_image": 0.02,
        "description": "Imagen 4 Fast",
        "model_id": "imagen-4-fast",
        "capabilities": "Fast image generation"
    },
    "gemini_2_5_flash_image": {
        "price_per_image": 0.0387,  # 1290 tokens * $30/1M tokens for 1024x1024
        "description": "Gemini 2.5 Flash Image",
        "model_id": "gemini-2.5-flash-image",
        "tokens_per_image_1k": 1290,
        "capabilities": "Image generation + understanding, multimodal (text+image input)"
    },
    "gemini3_pro_1k": {
        "price_per_image": 0.134,  # 1120 tokens * $120/1M tokens
        "description": "Gemini 3 Pro (1K/2K)",
        "model_id": "gemini-3-pro",
        "capabilities": "Advanced multimodal, highest quality"
    },
    "gemini3_pro_4k": {
        "price_per_image": 0.24,  # 2000 tokens * $120/1M tokens
        "description": "Gemini 3 Pro (4K)",
        "model_id": "gemini-3-pro",
        "capabilities": "Advanced multimodal, 4K resolution"
    }
}


def calculate_costs(num_images: int, model: str) -> dict:
    """Calculate costs for image generation."""
    
    if model not in IMAGE_PRICING:
        model = "imagen4"
    
    pricing = IMAGE_PRICING[model]
    cost_per_image = pricing["price_per_image"]
    total_cost = num_images * cost_per_image
    
    return {
        "model": model,
        "num_images": num_images,
        "cost_per_image": cost_per_image,
        "total_cost": round(total_cost, 2),
        "images_per_dollar": round(1.0 / cost_per_image, 2) if cost_per_image > 0 else 0,
        "credits_remaining": round(TOTAL_AVAILABLE - total_cost, 2),
        "percent_used": round((total_cost / TOTAL_AVAILABLE) * 100, 2),
        "description": pricing["description"],
        "capabilities": pricing.get("capabilities", "")
    }


def generate_comparison_report(num_images: int = 300):
    """Generate comprehensive comparison report."""
    
    report = []
    report.append("=" * 80)
    report.append("🎨 IMAGE GENERATION MODEL COMPARISON")
    report.append("=" * 80)
    report.append("")
    
    report.append("💰 CURRENT CREDIT STATUS")
    report.append("-" * 80)
    report.append(f"  Total Available: ${TOTAL_AVAILABLE:.2f}")
    report.append("")
    
    # Cost Comparison Table
    report.append(f"📊 COST COMPARISON FOR {num_images:,} IMAGES")
    report.append("-" * 80)
    report.append("")
    
    models = [
        "imagen4_fast",
        "gemini_2_5_flash_image",
        "imagen3",
        "imagen4",
        "gemini3_pro_1k",
        "gemini3_pro_4k"
    ]
    
    results = []
    for model in models:
        costs = calculate_costs(num_images, model)
        results.append(costs)
    
    # Sort by cost
    results.sort(key=lambda x: x["total_cost"])
    
    report.append("  Rank | Model                      | Cost/Image | Total Cost  | Images/$1")
    report.append("  " + "-" * 75)
    
    for i, result in enumerate(results, 1):
        model_name = result["description"][:25].ljust(25)
        cost_per = f"${result['cost_per_image']:.4f}".ljust(12)
        total = f"${result['total_cost']:.2f}".ljust(12)
        per_dollar = f"{result['images_per_dollar']:,.0f}".ljust(12)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        report.append(f"  {medal} {i}  | {model_name} | {cost_per} | {total} | {per_dollar}")
    
    report.append("")
    
    # Detailed Analysis
    report.append("💵 DETAILED ANALYSIS")
    report.append("-" * 80)
    report.append("")
    
    # Gemini 2.5 Flash Image
    flash_image = calculate_costs(num_images, "gemini_2_5_flash_image")
    imagen4 = calculate_costs(num_images, "imagen4")
    gemini3 = calculate_costs(num_images, "gemini3_pro_1k")
    
    report.append("  🆕 Gemini 2.5 Flash Image:")
    report.append(f"    Cost: ${flash_image['total_cost']:.2f} ({flash_image['cost_per_image']:.4f}/image)")
    report.append(f"    Capabilities: {flash_image['capabilities']}")
    report.append(f"    Model ID: {IMAGE_PRICING['gemini_2_5_flash_image']['model_id']}")
    report.append(f"    Tokens per 1K image: {IMAGE_PRICING['gemini_2_5_flash_image']['tokens_per_image_1k']}")
    report.append("")
    
    report.append("  vs Imagen 4:")
    savings_vs_imagen = imagen4['total_cost'] - flash_image['total_cost']
    report.append(f"    Savings: ${savings_vs_imagen:.2f} ({savings_vs_imagen / imagen4['total_cost'] * 100:.1f}%)")
    report.append(f"    → {int(savings_vs_imagen / flash_image['cost_per_image']):,} more images possible")
    report.append("")
    
    report.append("  vs Gemini 3 Pro:")
    savings_vs_gemini3 = gemini3['total_cost'] - flash_image['total_cost']
    report.append(f"    Savings: ${savings_vs_gemini3:.2f} ({savings_vs_gemini3 / gemini3['total_cost'] * 100:.1f}%)")
    report.append(f"    → {int(savings_vs_gemini3 / flash_image['cost_per_image']):,} more images possible")
    report.append("")
    
    # Key Advantages
    report.append("✨ KEY ADVANTAGES OF GEMINI 2.5 FLASH IMAGE")
    report.append("-" * 80)
    report.append("")
    report.append("  ✅ CHEAPER than Imagen 4 ($0.0387 vs $0.04)")
    report.append("  ✅ 3.5x CHEAPER than Gemini 3 Pro ($0.0387 vs $0.134)")
    report.append("  ✅ MULTIMODAL: Can take text + image input (unlike Imagen)")
    report.append("  ✅ IMAGE UNDERSTANDING: Can analyze images, not just generate")
    report.append("  ✅ FAST: Built on Gemini 2.5 Flash architecture")
    report.append("  ✅ UP TO 10 IMAGES per prompt")
    report.append("  ✅ MULTIPLE ASPECT RATIOS: 1:1, 16:9, 21:9, etc.")
    report.append("")
    
    # Maximum Images Possible
    report.append("🚀 MAXIMUM IMAGES POSSIBLE WITH YOUR CREDITS")
    report.append("-" * 80)
    
    for model in ["imagen4_fast", "gemini_2_5_flash_image", "imagen4", "gemini3_pro_1k"]:
        costs = calculate_costs(1, model)
        max_images = int(TOTAL_AVAILABLE / costs["cost_per_image"])
        report.append(f"  {costs['description']}:")
        report.append(f"    Maximum images: {max_images:,}")
        report.append(f"    Cost per image: ${costs['cost_per_image']:.4f}")
        report.append("")
    
    # Your 300 Images Analysis
    report.append("📊 YOUR 300 IMAGES ANALYSIS")
    report.append("-" * 80)
    
    for model in ["gemini_2_5_flash_image", "imagen4", "gemini3_pro_1k"]:
        costs = calculate_costs(300, model)
        report.append(f"  {costs['description']}:")
        report.append(f"    Total cost: ${costs['total_cost']:.2f}")
        report.append(f"    Credits remaining: ${costs['credits_remaining']:.2f}")
        report.append(f"    % of credits used: {costs['percent_used']:.2f}%")
        report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    report.append("")
    report.append("  🥇 BEST CHOICE: Gemini 2.5 Flash Image")
    report.append("     • Cheaper than Imagen")
    report.append("     • Multimodal capabilities (text + image input)")
    report.append("     • Image understanding + generation")
    report.append("     • Perfect for your use case!")
    report.append("")
    report.append("  🥈 SECOND CHOICE: Imagen 4 Fast ($0.02/image)")
    report.append("     • Cheapest option")
    report.append("     • But no multimodal capabilities")
    report.append("")
    report.append("  ⚠️  AVOID: Gemini 3 Pro (unless you need 4K)")
    report.append("     • 3.5x more expensive than Flash Image")
    report.append("     • Only use if you need highest quality or 4K")
    report.append("")
    
    # Cost Projections
    report.append("📅 COST PROJECTIONS (Gemini 2.5 Flash Image)")
    report.append("-" * 80)
    
    flash_cost_per = flash_image['cost_per_image']
    scenarios = [
        {"name": "Light", "images_per_day": 50},
        {"name": "Moderate", "images_per_day": 100},
        {"name": "Heavy", "images_per_day": 200},
        {"name": "Stress Test", "images_per_day": 500},
    ]
    
    for scenario in scenarios:
        daily_cost = scenario["images_per_day"] * flash_cost_per
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30
        days_remaining = TOTAL_AVAILABLE / daily_cost if daily_cost > 0 else float('inf')
        
        report.append(f"  {scenario['name']} ({scenario['images_per_day']} images/day):")
        report.append(f"    Daily: ${daily_cost:.2f}")
        report.append(f"    Weekly: ${weekly_cost:.2f}")
        report.append(f"    Monthly: ${monthly_cost:.2f}")
        
        if days_remaining != float('inf'):
            if days_remaining > 365:
                report.append(f"    ⏰ Credits last: {days_remaining / 365:.1f} years")
            elif days_remaining > 30:
                report.append(f"    ⏰ Credits last: {days_remaining / 30:.1f} months")
            else:
                report.append(f"    ⏰ Credits last: {days_remaining:.1f} days")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Compare image generation models")
    parser.add_argument(
        "--images",
        type=int,
        default=300,
        help="Number of images (default: 300)"
    )
    
    args = parser.parse_args()
    
    report = generate_comparison_report(args.images)
    print(report)
    
    # Save report
    report_file = Path("data/flash_image_comparison.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

