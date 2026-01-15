"""
Gap Scanner
============
Real-time gap scanner using Ross Cameron's 5 Pillars of Stock Selection.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    from .scan_types import ScanResult, ScannerConfig, SetupQuality
except ImportError:
    from scan_types import ScanResult, ScannerConfig, SetupQuality


class GapScanner:
    """
    Gap scanner implementing Ross Cameron's 5 Pillars.
    
    The 5 Pillars of Stock Selection:
    1. Price: $2-$20 (small account: $1.50-$6)
    2. Gap %: Up 10%+ (small account: 25%+)
    3. Relative Volume: 5x+ average
    4. News: Breaking catalyst
    5. Float: Under 10M shares (small account: <5M)
    
    Usage:
        scanner = GapScanner()
        results = scanner.scan()
        for r in results:
            print(f"{r.symbol}: {r.gap_percent:.1f}% gap, {r.quality.value} quality")
    """
    
    # Default watchlist - high-volume small caps
    DEFAULT_WATCHLIST = [
        "AAPL", "AMD", "NVDA", "TSLA", "AMZN",  # For testing
    ]
    
    def __init__(self, config: ScannerConfig = None):
        """Initialize scanner with config."""
        self.config = config or ScannerConfig()
    
    def scan(
        self,
        symbols: List[str] = None,
        *,
        small_account: bool = False,
    ) -> List[ScanResult]:
        """
        Scan symbols for gap opportunities.
        
        Args:
            symbols: List of tickers to scan (default: top gainers)
            small_account: Use tighter criteria for small accounts
            
        Returns:
            List of ScanResult sorted by quality/gap
        """
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance not available, returning empty results")
            return []
        
        # Apply small account config if requested
        config = ScannerConfig.small_account() if small_account else self.config
        
        # Get symbols to scan
        if symbols is None:
            symbols = self._get_top_movers()
        
        results = []
        for symbol in symbols:
            try:
                result = self.score_stock(symbol, config)
                if result and result.criteria_met >= 3:  # At least C quality
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to scan {symbol}: {e}")
        
        # Sort by criteria met (quality) then gap percent
        results.sort(key=lambda r: (-r.criteria_met, -r.gap_percent))
        
        return results[:config.max_results]
    
    def score_stock(
        self,
        symbol: str,
        config: ScannerConfig = None,
    ) -> Optional[ScanResult]:
        """
        Score a single stock against the 5 Pillars.
        
        Returns:
            ScanResult with criteria_met count and quality rating
        """
        if not YFINANCE_AVAILABLE:
            return None
        
        config = config or self.config
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            
            # Get current and previous data
            price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev_close = info.get("regularMarketPreviousClose", price)
            volume = info.get("regularMarketVolume") or info.get("volume", 0)
            avg_volume = info.get("averageVolume", 1)
            float_shares = info.get("floatShares", 0)
            
            # Calculate metrics
            gap_percent = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            relative_volume = (volume / avg_volume) if avg_volume > 0 else 0
            
            # Score against 5 Pillars
            criteria_met = 0
            
            # 1. Price in range
            if config.price_min <= price <= config.price_max:
                criteria_met += 1
            
            # 2. Gap percent
            if gap_percent >= config.gap_percent_min:
                criteria_met += 1
            
            # 3. Relative volume
            if relative_volume >= config.relative_volume_min:
                criteria_met += 1
            
            # 4. News (simplified - check if significant move with volume)
            has_momentum = gap_percent >= 5.0 and relative_volume >= 2.0
            if has_momentum or not config.require_news:
                criteria_met += 1
            
            # 5. Float under threshold
            if 0 < float_shares <= config.float_max:
                criteria_met += 1
            elif float_shares == 0:
                # Unknown float - give benefit of doubt
                pass
            
            return ScanResult(
                symbol=symbol.upper(),
                price=price,
                gap_percent=gap_percent,
                relative_volume=relative_volume,
                float_shares=float_shares or 0,
                total_volume=volume,
                criteria_met=criteria_met,
                prev_close=prev_close,
                high_of_day=info.get("dayHigh"),
                low_of_day=info.get("dayLow"),
                avg_volume=avg_volume,
            )
            
        except Exception as e:
            logger.warning(f"Error scoring {symbol}: {e}")
            return None
    
    def _get_top_movers(self) -> List[str]:
        """
        Get top moving stocks.
        
        Note: yfinance doesn't have a direct "top gainers" endpoint.
        In production, you'd use a proper market data feed.
        For now, returns a static watchlist.
        """
        # TODO: Integrate with real-time scanner API
        return self.DEFAULT_WATCHLIST
    
    def filter_a_quality(self, results: List[ScanResult]) -> List[ScanResult]:
        """Return only A-quality setups (5/5 criteria)."""
        return [r for r in results if r.quality == SetupQuality.A]
    
    def get_best_setup(self, results: List[ScanResult]) -> Optional[ScanResult]:
        """
        Get the single best setup for a one-trade-per-day approach.
        
        Ross Cameron's small account strategy: Pick ONE high-quality setup.
        """
        a_quality = self.filter_a_quality(results)
        if a_quality:
            # Return highest gap among A-quality
            return max(a_quality, key=lambda r: r.gap_percent)
        
        # Fallback to best available
        return results[0] if results else None


def run_scan(small_account: bool = False) -> List[ScanResult]:
    """
    Convenience function to run a gap scan.
    
    Example:
        from services.scanners import run_scan
        results = run_scan(small_account=True)
        for r in results:
            print(f"{r.symbol}: {r.quality.value} quality")
    """
    scanner = GapScanner()
    return scanner.scan(small_account=small_account)


if __name__ == "__main__":
    # Quick test
    print("Running Gap Scanner...")
    results = run_scan()
    for r in results:
        print(f"  {r.symbol}: {r.gap_percent:.1f}% gap, RV {r.relative_volume:.1f}x, {r.quality.value}")
