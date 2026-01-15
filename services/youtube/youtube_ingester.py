"""
YouTube Video Ingester
======================
Auto-ingest trading videos from YouTube channels.

Extracts transcripts, parses trading insights, and stores
them for the Unk trading system.

Primary target: @DaytradeWarrior (Ross Cameron)
"""
from __future__ import annotations

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Try imports - these are optional dependencies
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    YouTubeTranscriptApi = None

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    yt_dlp = None


@dataclass
class VideoMetadata:
    """Metadata for a YouTube video."""
    video_id: str
    title: str
    channel: str
    upload_date: str
    duration_seconds: int = 0
    view_count: int = 0
    description: str = ""
    url: str = ""
    
    def __post_init__(self):
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass
class TradingInsight:
    """Extracted trading insight from video."""
    insight_type: str  # stock_pick, pattern, rule, strategy, mindset
    content: str
    timestamp: Optional[str] = None
    confidence: float = 0.7
    symbols: List[str] = field(default_factory=list)
    
    # Additional context
    keywords: List[str] = field(default_factory=list)
    price_levels: List[float] = field(default_factory=list)


@dataclass
class ProcessedVideo:
    """A fully processed YouTube video with extracted insights."""
    metadata: VideoMetadata
    transcript: str
    insights: List[TradingInsight] = field(default_factory=list)
    
    # Processing metadata
    processed_at: str = ""
    word_count: int = 0
    
    def __post_init__(self):
        if not self.processed_at:
            self.processed_at = datetime.now().isoformat()
        if not self.word_count:
            self.word_count = len(self.transcript.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "metadata": asdict(self.metadata),
            "transcript": self.transcript,
            "insights": [asdict(i) for i in self.insights],
            "processed_at": self.processed_at,
            "word_count": self.word_count,
        }


class TradingInsightExtractor:
    """
    Extract trading insights from video transcripts.
    
    Looks for:
    - Stock symbols (ticker mentions)
    - Price levels and targets
    - Trading rules and strategies
    - Pattern mentions (bull flag, VWAP, etc.)
    - Risk management rules
    - Mindset/psychology insights
    """
    
    # Common trading patterns to detect
    PATTERNS = [
        "bull flag", "pullback", "breakout", "VWAP", "opening range",
        "micro pullback", "ABCD", "red to green", "gap up", "gap down",
        "squeeze", "consolidation", "reversal", "double bottom",
        "higher low", "lower high", "ascending triangle",
    ]
    
    # Trading rules keywords
    RULE_KEYWORDS = [
        "max loss", "daily goal", "stop loss", "profit target",
        "risk reward", "position size", "share size", "cushion",
        "discipline", "walk away", "breakout or bailout",
        "first candle", "five pillars", "quality over quantity",
    ]
    
    # Mindset/psychology keywords
    MINDSET_KEYWORDS = [
        "FOMO", "patience", "discipline", "emotion", "frustration",
        "greed", "fear", "confidence", "consistency", "psychology",
        "break even", "draw down", "recovery", "hot market", "cold market",
    ]
    
    # Ticker pattern - matches $AAPL or just AAPL in context
    TICKER_PATTERN = re.compile(r'\$?([A-Z]{2,5})(?:\s|,|\.)')
    
    # Price pattern - matches $5.50, 5.50, $10, etc.
    PRICE_PATTERN = re.compile(r'\$?(\d+(?:\.\d{1,2})?)\s*(?:share|dollar|buck)?')
    
    def extract_insights(self, transcript: str) -> List[TradingInsight]:
        """Extract all trading insights from transcript."""
        insights = []
        
        # Split into sentences for analysis
        sentences = self._split_sentences(transcript)
        
        for sentence in sentences:
            # Check for stock mentions
            symbols = self._extract_symbols(sentence)
            if symbols:
                insights.append(TradingInsight(
                    insight_type="stock_pick",
                    content=sentence,
                    symbols=symbols,
                    confidence=0.6,
                ))
            
            # Check for patterns
            for pattern in self.PATTERNS:
                if pattern.lower() in sentence.lower():
                    insights.append(TradingInsight(
                        insight_type="pattern",
                        content=sentence,
                        keywords=[pattern],
                        confidence=0.7,
                    ))
                    break
            
            # Check for rules
            for rule in self.RULE_KEYWORDS:
                if rule.lower() in sentence.lower():
                    prices = self._extract_prices(sentence)
                    insights.append(TradingInsight(
                        insight_type="rule",
                        content=sentence,
                        keywords=[rule],
                        price_levels=prices,
                        confidence=0.8,
                    ))
                    break
            
            # Check for mindset insights
            for keyword in self.MINDSET_KEYWORDS:
                if keyword.lower() in sentence.lower():
                    insights.append(TradingInsight(
                        insight_type="mindset",
                        content=sentence,
                        keywords=[keyword],
                        confidence=0.6,
                    ))
                    break
        
        # Deduplicate by content
        seen = set()
        unique_insights = []
        for insight in insights:
            if insight.content not in seen:
                seen.add(insight.content)
                unique_insights.append(insight)
        
        return unique_insights
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock ticker symbols from text."""
        matches = self.TICKER_PATTERN.findall(text)
        
        # Filter out common words that look like tickers
        common_words = {
            "THE", "AND", "FOR", "NOT", "BUT", "ARE", "YOU", "ALL",
            "CAN", "HAD", "HER", "WAS", "ONE", "OUR", "OUT", "DAY",
            "GET", "HAS", "HIM", "HIS", "HOW", "ITS", "MAY", "NEW",
            "NOW", "OLD", "SEE", "TWO", "WAY", "WHO", "BOY", "DID",
            "EMA", "RSI", "ATR", "PDT", "ETF", "CEO", "IPO", "PDF",
        }
        
        symbols = [s for s in matches if s.upper() not in common_words]
        return list(set(symbols))
    
    def _extract_prices(self, text: str) -> List[float]:
        """Extract price levels from text."""
        matches = self.PRICE_PATTERN.findall(text)
        prices = []
        for match in matches:
            try:
                price = float(match)
                if 0.5 <= price <= 1000:  # Reasonable stock price range
                    prices.append(price)
            except ValueError:
                continue
        return prices


class YouTubeIngester:
    """
    Ingest YouTube videos and extract trading insights.
    
    Usage:
        ingester = YouTubeIngester()
        
        # Ingest a single video
        video = ingester.ingest_video("video_id_here")
        
        # Ingest recent videos from channel
        videos = ingester.ingest_channel_recent(
            channel_url="https://www.youtube.com/@DaytradeWarrior",
            days=90
        )
        
        # Save to disk
        ingester.save_videos(videos, "warrior_trading_insights.json")
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize ingester.
        
        Args:
            storage_dir: Directory to store processed videos
        """
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self.extractor = TradingInsightExtractor()
        
        if not TRANSCRIPT_API_AVAILABLE:
            logger.warning(
                "youtube-transcript-api not installed. "
                "Run: pip install youtube-transcript-api"
            )
        
        if not YT_DLP_AVAILABLE:
            logger.warning(
                "yt-dlp not installed. Run: pip install yt-dlp"
            )
    
    def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Get metadata for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            VideoMetadata or None
        """
        if not YT_DLP_AVAILABLE:
            # Return basic metadata without yt-dlp
            return VideoMetadata(
                video_id=video_id,
                title="Unknown",
                channel="Unknown",
                upload_date=datetime.now().strftime("%Y%m%d"),
            )
        
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            return VideoMetadata(
                video_id=video_id,
                title=info.get("title", "Unknown"),
                channel=info.get("channel", info.get("uploader", "Unknown")),
                upload_date=info.get("upload_date", ""),
                duration_seconds=info.get("duration", 0),
                view_count=info.get("view_count", 0),
                description=info.get("description", "")[:500],
            )
            
        except Exception as e:
            logger.error(f"Error getting metadata for {video_id}: {e}")
            return None
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Full transcript text or None
        """
        if not TRANSCRIPT_API_AVAILABLE:
            logger.error("youtube-transcript-api not available")
            return None
        
        try:
            # New API uses .fetch() on an instance
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.fetch(video_id)
            
            # Combine all transcript segments
            full_text = " ".join(
                segment.text for segment in transcript_list
            )
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error getting transcript for {video_id}: {e}")
            return None
    
    def ingest_video(self, video_id: str) -> Optional[ProcessedVideo]:
        """
        Fully ingest and process a single video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            ProcessedVideo with insights
        """
        # Get metadata
        metadata = self.get_video_metadata(video_id)
        if not metadata:
            return None
        
        # Get transcript
        transcript = self.get_transcript(video_id)
        if not transcript:
            return None
        
        # Extract insights
        insights = self.extractor.extract_insights(transcript)
        
        logger.info(
            f"Processed video {video_id}: "
            f"{len(insights)} insights from {len(transcript.split())} words"
        )
        
        return ProcessedVideo(
            metadata=metadata,
            transcript=transcript,
            insights=insights,
        )
    
    def get_channel_video_ids(
        self,
        channel_url: str,
        max_videos: int = 50,
        days: int = 90,
    ) -> List[str]:
        """
        Get recent video IDs from a YouTube channel.
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum videos to fetch
            days: Only include videos from last N days
            
        Returns:
            List of video IDs
        """
        if not YT_DLP_AVAILABLE:
            logger.error("yt-dlp not available for channel fetching")
            return []
        
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "playlistend": max_videos,
            }
            
            # Append /videos to get the videos tab
            if not channel_url.endswith("/videos"):
                channel_url = channel_url.rstrip("/") + "/videos"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
            
            video_ids = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in info.get("entries", []):
                if not entry:
                    continue
                
                video_id = entry.get("id")
                if not video_id:
                    continue
                
                # Check upload date if available
                upload_date_str = entry.get("upload_date")
                if upload_date_str:
                    try:
                        upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
                        if upload_date < cutoff_date:
                            continue
                    except ValueError:
                        pass
                
                video_ids.append(video_id)
            
            logger.info(
                f"Found {len(video_ids)} videos from {channel_url} "
                f"in last {days} days"
            )
            return video_ids
            
        except Exception as e:
            logger.error(f"Error fetching channel videos: {e}")
            return []
    
    def ingest_channel_recent(
        self,
        channel_url: str,
        days: int = 90,
        max_videos: int = 50,
    ) -> List[ProcessedVideo]:
        """
        Ingest recent videos from a YouTube channel.
        
        Args:
            channel_url: YouTube channel URL
            days: Only include videos from last N days
            max_videos: Maximum videos to process
            
        Returns:
            List of ProcessedVideos
        """
        video_ids = self.get_channel_video_ids(
            channel_url=channel_url,
            max_videos=max_videos,
            days=days,
        )
        
        processed = []
        for i, video_id in enumerate(video_ids):
            logger.info(f"Processing video {i+1}/{len(video_ids)}: {video_id}")
            
            video = self.ingest_video(video_id)
            if video:
                processed.append(video)
        
        return processed
    
    def save_videos(
        self,
        videos: List[ProcessedVideo],
        filename: str = "trading_insights.json",
    ) -> Path:
        """
        Save processed videos to JSON file.
        
        Args:
            videos: List of ProcessedVideos
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.storage_dir / filename
        else:
            output_path = Path(filename)
        
        data = {
            "ingested_at": datetime.now().isoformat(),
            "video_count": len(videos),
            "total_insights": sum(len(v.insights) for v in videos),
            "videos": [v.to_dict() for v in videos],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(videos)} videos to {output_path}")
        return output_path
    
    def load_videos(self, filename: str) -> List[ProcessedVideo]:
        """Load previously saved videos."""
        path = Path(filename)
        if not path.exists():
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        videos = []
        for v_data in data.get("videos", []):
            metadata = VideoMetadata(**v_data["metadata"])
            insights = [TradingInsight(**i) for i in v_data.get("insights", [])]
            videos.append(ProcessedVideo(
                metadata=metadata,
                transcript=v_data["transcript"],
                insights=insights,
                processed_at=v_data.get("processed_at", ""),
                word_count=v_data.get("word_count", 0),
            ))
        
        return videos


# Convenience function for quick ingestion
def ingest_warrior_trading(days: int = 90) -> List[ProcessedVideo]:
    """
    Ingest recent videos from Ross Cameron's Warrior Trading channel.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of processed videos with trading insights
    """
    ingester = YouTubeIngester()
    return ingester.ingest_channel_recent(
        channel_url="https://www.youtube.com/@DaytradeWarrior",
        days=days,
        max_videos=100,
    )
