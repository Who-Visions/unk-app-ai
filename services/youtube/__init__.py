"""
YouTube Ingestion Package
=========================
Auto-ingest trading videos and extract insights.
"""
from .youtube_ingester import (
    VideoMetadata,
    TradingInsight,
    ProcessedVideo,
    TradingInsightExtractor,
    YouTubeIngester,
    ingest_warrior_trading,
)

__all__ = [
    "VideoMetadata",
    "TradingInsight",
    "ProcessedVideo",
    "TradingInsightExtractor",
    "YouTubeIngester",
    "ingest_warrior_trading",
]
