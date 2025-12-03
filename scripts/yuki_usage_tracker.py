#!/usr/bin/env python3
"""
Yuki Image Generation Usage Tracker
====================================
Tracks Yuki's image generation usage and calculates costs.

Usage:
    python scripts/yuki_usage_tracker.py [--images N] [--update]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

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
IMAGE_COST_PER_SHOT = 0.04  # Imagen 3/4 pricing


def load_usage_history() -> dict:
    """Load usage history from file."""
    history_file = Path("data/yuki_usage.json")
    
    if history_file.exists():
        with open(history_file, 'r') as f:
            return json.load(f)
    
    return {
        "total_images_generated": 0,
        "total_cost": 0.0,
        "sessions": [],
        "created_at": datetime.now().isoformat()
    }


def save_usage_history(history: dict):
    """Save usage history to file."""
    history_file = Path("data/yuki_usage.json")
    history_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)


def add_usage_session(images: int, notes: str = ""):
    """Add a new usage session."""
    history = load_usage_history()
    
    session = {
        "timestamp": datetime.now().isoformat(),
        "images": images,
        "cost": round(images * IMAGE_COST_PER_SHOT, 2),
        "notes": notes
    }
    
    history["sessions"].append(session)
    history["total_images_generated"] += images
    history["total_cost"] = round(history["total_cost"] + session["cost"], 2)
    history["last_updated"] = datetime.now().isoformat()
    
    save_usage_history(history)
    return history


def generate_report(history: dict = None):
    """Generate usage report."""
    
    if history is None:
        history = load_usage_history()
    
    report = []
    report.append("=" * 80)
    report.append("🎨 YUKI IMAGE GENERATION USAGE REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Current Status
    report.append("💰 CURRENT STATUS")
    report.append("-" * 80)
    report.append(f"  Total Credits Available: ${TOTAL_AVAILABLE:.2f}")
    report.append(f"  Cost per Image: ${IMAGE_COST_PER_SHOT:.4f}")
    report.append("")
    
    # Usage Summary
    report.append("📊 USAGE SUMMARY")
    report.append("-" * 80)
    report.append(f"  Total Images Generated: {history['total_images_generated']:,}")
    report.append(f"  Total Cost: ${history['total_cost']:.2f}")
    report.append(f"  Credits Remaining: ${TOTAL_AVAILABLE - history['total_cost']:.2f}")
    report.append(f"  % of Credits Used: {(history['total_cost'] / TOTAL_AVAILABLE * 100):.2f}%")
    report.append("")
    
    # Recent Sessions
    if history["sessions"]:
        report.append("📅 RECENT SESSIONS")
        report.append("-" * 80)
        
        # Show last 10 sessions
        recent_sessions = history["sessions"][-10:]
        for i, session in enumerate(reversed(recent_sessions), 1):
            date = datetime.fromisoformat(session["timestamp"]).strftime("%Y-%m-%d %H:%M")
            report.append(f"  {i}. {date}: {session['images']:,} images = ${session['cost']:.2f}")
            if session.get("notes"):
                report.append(f"     Notes: {session['notes']}")
        report.append("")
    
    # Cost Analysis
    report.append("💵 COST ANALYSIS")
    report.append("-" * 80)
    
    if history["total_images_generated"] > 0:
        avg_cost_per_session = history["total_cost"] / len(history["sessions"]) if history["sessions"] else 0
        avg_images_per_session = history["total_images_generated"] / len(history["sessions"]) if history["sessions"] else 0
        
        report.append(f"  Average per session: {avg_images_per_session:.0f} images = ${avg_cost_per_session:.2f}")
        report.append(f"  Total sessions: {len(history['sessions'])}")
        report.append("")
        
        # Projections
        if len(history["sessions"]) > 0:
            # Calculate daily average if we have multiple days
            if len(history["sessions"]) >= 2:
                first_date = datetime.fromisoformat(history["sessions"][0]["timestamp"])
                last_date = datetime.fromisoformat(history["sessions"][-1]["timestamp"])
                days_diff = (last_date - first_date).days + 1
                daily_avg_images = history["total_images_generated"] / days_diff
                daily_avg_cost = history["total_cost"] / days_diff
                
                report.append("  📈 PROJECTIONS (based on current usage):")
                report.append(f"     Daily average: {daily_avg_images:.0f} images = ${daily_avg_cost:.2f}")
                report.append(f"     Weekly projection: {daily_avg_images * 7:.0f} images = ${daily_avg_cost * 7:.2f}")
                report.append(f"     Monthly projection: {daily_avg_images * 30:.0f} images = ${daily_avg_cost * 30:.2f}")
                
                # Days remaining
                remaining_credits = TOTAL_AVAILABLE - history["total_cost"]
                if daily_avg_cost > 0:
                    days_remaining = remaining_credits / daily_avg_cost
                    report.append(f"     ⏰ Credits will last: {days_remaining:.1f} days at current rate")
                report.append("")
    
    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    report.append("-" * 80)
    
    remaining_credits = TOTAL_AVAILABLE - history["total_cost"]
    max_images_remaining = int(remaining_credits / IMAGE_COST_PER_SHOT)
    
    report.append(f"  1. ✅ You can generate {max_images_remaining:,} more images")
    report.append(f"  2. ✅ Current burn rate: ${history['total_cost']:.2f} ({history['total_cost'] / TOTAL_AVAILABLE * 100:.2f}% of credits)")
    
    if history["total_cost"] > 0:
        cost_per_100 = (history["total_cost"] / history["total_images_generated"]) * 100
        report.append(f"  3. 💰 Average cost per 100 images: ${cost_per_100:.2f}")
    
    report.append("  4. 📊 Keep stress testing - you're using credits efficiently!")
    report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Track Yuki image generation usage")
    parser.add_argument(
        "--images",
        type=int,
        default=None,
        help="Number of images generated in this session"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update usage history with new session"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Notes for this session"
    )
    
    args = parser.parse_args()
    
    if args.update and args.images:
        print(f"📝 Recording session: {args.images} images")
        history = add_usage_session(args.images, args.notes)
        print(f"✅ Updated! Total: {history['total_images_generated']:,} images, ${history['total_cost']:.2f} cost")
        print("")
    
    report = generate_report()
    print(report)
    
    # Save report
    report_file = Path("data/yuki_usage_report.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()

