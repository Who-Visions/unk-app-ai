#!/usr/bin/env python3
"""
Gemini 3 Pro Image Generation Cost Optimizer
=============================================
Calculates costs and optimization strategies for Gemini 3 Pro image generation.

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

# Gemini 3 Pro pricing from official docs
GEMINI3_PRO_PRICING = {
    "image_1k_2k": {
        "price_per_image": 0.134,  # 1120 tokens * $120/1M tokens
        "tokens_per_image": 1120,
        "resolution": "1K (1024x1024) or 2K (2048x2048)",
        "description": "Gemini 3 Pro Image Output (1K/2K)"
    },
    "image_4k": {
        "price_per_image": 0.24,  # 2000 tokens * $120/1M tokens
        "tokens_per_image": 2000,
        "resolution": "4K (4096x4096)",
        "description": "Gemini 3 Pro Image Output (4K)"
    },
    "input_text": {
        "price_per_1m_tokens": 2.00,  # <= 200K tokens
        "price_per_1m_tokens_long": 4.00,  # > 200K tokens
        "description": "Gemini 3 Pro Input (text, image, video, audio)"
    },
    "output_text": {
        "price_per_1m_tokens": 12.00,  # <= 200K input tokens
        "price_per_1m_tokens_long": 18.00,  # > 200K input tokens
        "description": "Gemini 3 Pro Text Output"
    },
    "batch_api": {
        "image_1k_2k": 0.067,  # 50% discount
        "image_4k": 0.12,  # 50% discount
        "description": "Batch API (50% discount)"
    }
}


def calculate_gemini3_pro_costs(
    num_images: int,
    resolution: str = "1k",
    use_batch: bool = False,
    avg_input_tokens: int = 0,
    avg_output_tokens: int = 0
) -> dict:
    """Calculate total costs for Gemini 3 Pro image generation."""
    
    # Image generation cost
    if resolution == "4k":
        if use_batch:
            image_cost_per = GEMINI3_PRO_PRICING["batch_api"]["image_4k"]
        else:
            image_cost_per = GEMINI3_PRO_PRICING["image_4k"]["price_per_image"]
        image_desc = GEMINI3_PRO_PRICING["image_4k"]["description"]
    else:
        if use_batch:
            image_cost_per = GEMINI3_PRO_PRICING["batch_api"]["image_1k_2k"]
        else:
            image_cost_per = GEMINI3_PRO_PRICING["image_1k_2k"]["price_per_image"]
        image_desc = GEMINI3_PRO_PRICING["image_1k_2k"]["description"]
    
    image_total_cost = num_images * image_cost_per
    
    # Input/output token costs (if applicable)
    input_cost = 0.0
    output_cost = 0.0
    
    if avg_input_tokens > 0:
        # Determine if long context pricing applies
        if avg_input_tokens > 200_000:
            input_rate = GEMINI3_PRO_PRICING["input_text"]["price_per_1m_tokens_long"]
        else:
            input_rate = GEMINI3_PRO_PRICING["input_text"]["price_per_1m_tokens"]
        
        input_cost = (avg_input_tokens / 1_000_000) * input_rate * num_images
    
    if avg_output_tokens > 0:
        # Output pricing depends on input context length
        if avg_input_tokens > 200_000:
            output_rate = GEMINI3_PRO_PRICING["output_text"]["price_per_1m_tokens_long"]
        else:
            output_rate = GEMINI3_PRO_PRICING["output_text"]["price_per_1m_tokens"]
        
        output_cost = (avg_output_tokens / 1_000_000) * output_rate * num_images
    
    total_cost = image_total_cost + input_cost + output_cost
    
    return {
        "num_images": num_images,
        "resolution": resolution,
        "use_batch": use_batch,
        "image_cost_per": image_cost_per,
        "image_total_cost": round(image_total_cost, 2),
        "input_cost": round(input_cost, 2),
        "output_cost": round(output_cost, 2),
        "total_cost": round(total_cost, 2),
        "description": image_desc,
        "credits_remaining": round(TOTAL_AVAILABLE - total_cost, 2),
        "percent_used": round((total_cost / TOTAL_AVAILABLE) * 100, 2)
    }


def generate_optimization_report(num_images: int = 300, resolution: str = "1k"):
    """Generate cost optimization report."""
    
    report = []
    report.append("=" * 80)
    report.append("🎨 GEMINI 3 PRO IMAGE GENERATION - COST OPTIMIZATION GUIDE")
    report.append("=" * 80)
    report.append("")
    
    report.append("💰 CURRENT CREDIT STATUS")
    report.append("-" * 80)
    report.append(f"  Total Available: ${TOTAL_AVAILABLE:.2f}")
    report.append("")
    
    # Standard vs Batch API
    report.append(f"📊 COST COMPARISON FOR {num_images:,} IMAGES ({resolution.upper()})")
    report.append("-" * 80)
    report.append("")
    
    standard = calculate_gemini3_pro_costs(num_images, resolution, use_batch=False)
    batch = calculate_gemini3_pro_costs(num_images, resolution, use_batch=True)
    
    savings = standard["total_cost"] - batch["total_cost"]
    savings_pct = (savings / standard["total_cost"]) * 100 if standard["total_cost"] > 0 else 0
    
    report.append("  Standard API:")
    report.append(f"    Cost per image: ${standard['image_cost_per']:.4f}")
    report.append(f"    Total cost: ${standard['total_cost']:.2f}")
    report.append("")
    
    report.append("  Batch API (50% discount):")
    report.append(f"    Cost per image: ${batch['image_cost_per']:.4f}")
    report.append(f"    Total cost: ${batch['total_cost']:.2f}")
    report.append(f"    💰 Savings: ${savings:.2f} ({savings_pct:.1f}%)")
    report.append(f"    → You could generate {int(savings / standard['image_cost_per']):,} more images!")
    report.append("")
    
    # Your 300 Images Analysis
    report.append("📈 YOUR 300 IMAGES ANALYSIS")
    report.append("-" * 80)
    
    for res in ["1k", "2k", "4k"]:
        costs_standard = calculate_gemini3_pro_costs(300, res, use_batch=False)
        costs_batch = calculate_gemini3_pro_costs(300, res, use_batch=True)
        
        report.append(f"  {res.upper()} Resolution:")
        report.append(f"    Standard API: ${costs_standard['total_cost']:.2f}")
        report.append(f"    Batch API: ${costs_batch['total_cost']:.2f}")
        report.append(f"    Savings: ${costs_standard['total_cost'] - costs_batch['total_cost']:.2f}")
        report.append(f"    Credits remaining: ${costs_standard['credits_remaining']:.2f}")
        report.append("")
    
    # Maximum Images Possible
    report.append("🚀 MAXIMUM IMAGES POSSIBLE WITH YOUR CREDITS")
    report.append("-" * 80)
    
    for res in ["1k", "4k"]:
        for use_batch in [False, True]:
            costs = calculate_gemini3_pro_costs(1, res, use_batch=use_batch)
            max_images = int(TOTAL_AVAILABLE / costs["image_cost_per"])
            api_type = "Batch API" if use_batch else "Standard API"
            report.append(f"  {res.upper()} - {api_type}:")
            report.append(f"    Maximum images: {max_images:,}")
            report.append(f"    Cost per image: ${costs['image_cost_per']:.4f}")
            report.append("")
    
    # Cost Optimization Strategies
    report.append("💡 COST OPTIMIZATION STRATEGIES")
    report.append("-" * 80)
    report.append("")
    
    report.append("  1. ✅ USE BATCH API WHENEVER POSSIBLE")
    report.append("     • 50% discount on image generation")
    report.append("     • Best for non-real-time generation")
    report.append("     • Your 300 images: Save ${:.2f}".format(
        calculate_gemini3_pro_costs(300, resolution, False)["total_cost"] - 
        calculate_gemini3_pro_costs(300, resolution, True)["total_cost"]
    ))
    report.append("")
    
    report.append("  2. ✅ USE 1K/2K RESOLUTION WHEN POSSIBLE")
    report.append("     • 1K/2K: $0.134/image (standard) or $0.067/image (batch)")
    report.append("     • 4K: $0.24/image (standard) or $0.12/image (batch)")
    report.append("     • 4K is 1.8x more expensive")
    report.append("")
    
    report.append("  3. ✅ MINIMIZE INPUT TOKENS")
    report.append("     • Keep prompts concise")
    report.append("     • Avoid long context windows (>200K tokens triggers higher rates)")
    report.append("     • Input: $2/1M tokens (standard) or $4/1M tokens (long context)")
    report.append("")
    
    report.append("  4. ✅ MINIMIZE TEXT OUTPUT")
    report.append("     • If you only need images, avoid text responses")
    report.append("     • Output: $12/1M tokens (standard) or $18/1M tokens (long context)")
    report.append("")
    
    report.append("  5. ✅ BATCH YOUR REQUESTS")
    report.append("     • Group multiple image generations together")
    report.append("     • Use async/batch processing when possible")
    report.append("     • Reduces overhead and enables batch API discounts")
    report.append("")
    
    # Projected Usage Scenarios
    report.append("📅 PROJECTED USAGE SCENARIOS")
    report.append("-" * 80)
    report.append("")
    
    scenarios = [
        {"name": "Light Usage", "images_per_day": 50, "resolution": "1k", "batch": True},
        {"name": "Moderate Usage", "images_per_day": 100, "resolution": "1k", "batch": True},
        {"name": "Heavy Usage", "images_per_day": 200, "resolution": "1k", "batch": True},
        {"name": "Heavy Usage (4K)", "images_per_day": 100, "resolution": "4k", "batch": True},
    ]
    
    for scenario in scenarios:
        daily_cost = calculate_gemini3_pro_costs(
            scenario["images_per_day"],
            scenario["resolution"],
            scenario["batch"]
        )["total_cost"]
        
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30
        days_remaining = TOTAL_AVAILABLE / daily_cost if daily_cost > 0 else float('inf')
        
        report.append(f"  {scenario['name']} ({scenario['images_per_day']} images/day, {scenario['resolution'].upper()}, Batch API):")
        report.append(f"    Daily cost: ${daily_cost:.2f}")
        report.append(f"    Weekly cost: ${weekly_cost:.2f}")
        report.append(f"    Monthly cost: ${monthly_cost:.2f}")
        
        if days_remaining != float('inf'):
            if days_remaining > 365:
                report.append(f"    ⏰ Credits last: {days_remaining / 365:.1f} years ({days_remaining:.0f} days)")
            elif days_remaining > 30:
                report.append(f"    ⏰ Credits last: {days_remaining / 30:.1f} months ({days_remaining:.0f} days)")
            else:
                report.append(f"    ⏰ Credits last: {days_remaining:.1f} days")
        report.append("")
    
    # Realistic Budget Planning
    report.append("💰 REALISTIC BUDGET PLANNING")
    report.append("-" * 80)
    report.append("")
    
    # Calculate what they can do with remaining credits
    remaining_after_300 = TOTAL_AVAILABLE - calculate_gemini3_pro_costs(300, resolution, True)["total_cost"]
    
    report.append(f"  After generating 300 images ({resolution.upper()}, Batch API):")
    report.append(f"    Credits remaining: ${remaining_after_300:.2f}")
    
    # How many more images can they generate?
    cost_per_image_batch = calculate_gemini3_pro_costs(1, resolution, True)["image_cost_per"]
    max_additional = int(remaining_after_300 / cost_per_image_batch)
    
    report.append(f"    Can generate {max_additional:,} more images")
    report.append(f"    Total possible: {300 + max_additional:,} images")
    report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Gemini 3 Pro cost optimizer")
    parser.add_argument(
        "--images",
        type=int,
        default=300,
        help="Number of images (default: 300)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["1k", "2k", "4k"],
        default="1k",
        help="Resolution (default: 1k)"
    )
    
    args = parser.parse_args()
    
    report = generate_optimization_report(args.images, args.resolution)
    print(report)
    
    # Save report
    report_file = Path("data/gemini3_pro_cost_optimization.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

