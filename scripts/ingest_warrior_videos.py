#!/usr/bin/env python3
"""
Ingest Ross Cameron's Warrior Trading Videos
============================================

Auto-downloads transcripts from the last 90 days of videos
and extracts trading insights.

Usage:
    python scripts/ingest_warrior_videos.py
    python scripts/ingest_warrior_videos.py --days 30
    python scripts/ingest_warrior_videos.py --output insights.json
"""
import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.youtube import YouTubeIngester, ingest_warrior_trading


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Warrior Trading YouTube videos"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days to look back (default: 90)"
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        default=100,
        help="Maximum videos to process (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/warrior_trading_insights.json",
        help="Output file path"
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="https://www.youtube.com/@DaytradeWarrior",
        help="YouTube channel URL"
    )
    
    args = parser.parse_args()
    
    print(f"[VIDEO] Ingesting videos from {args.channel}")
    print(f"   Looking back {args.days} days, max {args.max_videos} videos")
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize ingester
    ingester = YouTubeIngester(storage_dir=str(output_path.parent))
    
    # Ingest videos
    videos = ingester.ingest_channel_recent(
        channel_url=args.channel,
        days=args.days,
        max_videos=args.max_videos,
    )
    
    if not videos:
        print("[ERROR] No videos were processed")
        print("   Make sure you have these packages installed:")
        print("   pip install youtube-transcript-api yt-dlp")
        return 1
    
    # Save results
    saved_path = ingester.save_videos(videos, output_path.name)
    
    # Print summary
    total_insights = sum(len(v.insights) for v in videos)
    total_words = sum(v.word_count for v in videos)
    
    print(f"\n[OK] Successfully processed {len(videos)} videos")
    print(f"   [TEXT] {total_words:,} words transcribed")
    print(f"   [INSIGHT] {total_insights} trading insights extracted")
    print(f"   [FILE] Saved to: {saved_path}")
    
    # Print insight breakdown
    insight_types = {}
    for video in videos:
        for insight in video.insights:
            insight_types[insight.insight_type] = (
                insight_types.get(insight.insight_type, 0) + 1
            )
    
    if insight_types:
        print("\n   Insight breakdown:")
        for itype, count in sorted(insight_types.items(), key=lambda x: -x[1]):
            print(f"     - {itype}: {count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

