import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

from services.strategies.strategy import Strategy, Signal, TimeFrame
from services.strategies.support_resistance import SupportResistanceStrategy
from services.models.market_data import MarketData
from services.levels import PivotPoint, LevelType

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)

class WarriorMomentum(Strategy):
    """
    Warrior Momentum Strategy
    =========================
    Based on insights extracted from Ross Cameron (Warrior Trading).
    
    Key Principles:
    1.  **Blue Sky Breakouts**: Trading stocks attempting to break All-Time Highs or 52-Week Highs.
    2.  **Micro Pullbacks**: Buying the first dip on a strong momentum stock (1-minute timeframe).
    3.  **Whole Dollar/Half Dollar Levels**: Respecting psychological levels (e.g., $5.00, $5.50).
    4.  **Prediction Market/Hot Themes**: Boosting score for stocks in 'hot' sectors (Crypto, AI, Prediction Markets).
    5.  **Quality over Quantity**: Aggressive sizing on 'A+ Setups', conservative on 'Cold' days.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "WarriorMomentum"
        self.sr_analyzer = SupportResistanceStrategy()
        
        # Configuration from collected rules
        self.daily_goal_hot = config.get("daily_goal_hot", 20000.0)
        self.daily_goal_cold = config.get("daily_goal_cold", 5000.0)
        self.hot_market_threshold = config.get("hot_market_threshold", 0.7) # Fear/Greed index > 70 or similar
        
        # Hot themes (dynamic, should be updated from news analysis)
        self.hot_themes = ["prediction", "crypto", "ai", "gambling", "bitcoin"]
        
    async def analyze(self, data: MarketData) -> Optional[Signal]:
        """
        Analyze market data for Warrior Trading setups.
        """
        if not self._is_market_open():
            return None
            
        # 1. Check for Momentum (Gap Up + Volume)
        # Warrior likes stocks up > 20% with high Relative Volume
        change_pct = data.change_percent
        if change_pct < 10.0:  # Minimum 10% move to even look
            return None
            
        # 2. Level Analysis (Support/Resistance)
        levels = self.sr_analyzer.calculate_levels(data.history)
        current_price = data.price
        
        # 3. Detect "Blue Sky" or Breakout
        # If price is near the high of day or 52-week high
        high_of_day = data.day_high
        dist_to_hod = (high_of_day - current_price) / current_price
        
        is_breakout_setup = dist_to_hod < 0.02 and dist_to_hod > -0.01 # Within 2% of HOD
        
        # 4. Detect "Micro Pullback"
        # Price is above VWAP but pulled back from recent 1-min peak
        vwap = data.indicators.get('vwap')
        if not vwap or current_price < vwap:
            # Warrior rarely longs below VWAP on momentum
            return None
            
        # Check for pullback pattern (simple: last candle red, previous 3 green)
        # This requires candle history access
        is_pullback = self._check_micro_pullback(data.history)
        
        score = 0.0
        details = []
        
        if is_breakout_setup:
            score += 40
            details.append("approaching_HOD")
            
        if is_pullback:
            score += 30
            details.append("micro_pullback_vwap")
            
        # 5. Whole Dollar / Half Dollar Check
        # Price crossing or bouncing off X.00 or X.50
        decimal_part = current_price % 1
        if 0.95 <= decimal_part <= 0.99 or 0.45 <= decimal_part <= 0.49:
             # Approaching breakout level
             score += 15
             details.append("approaching_psychological_level")
        
        # 6. Sector/News Boost
        # We assume data has a 'news_keywords' or similar field populated by the news ingester
        if hasattr(data, 'news_keywords'):
            matched_themes = [t for t in self.hot_themes if t in data.news_keywords]
            if matched_themes:
                score += 20
                details.append(f"hot_theme_{matched_themes[0]}")
        
        # Threshold for Entry
        if score >= 70:
            # Determine Sizing Aggression
            aggression = "HIGH" if score > 85 else "MEDIUM"
            
            return Signal(
                symbol=data.symbol,
                action="BUY",
                price=current_price,
                confidence=score / 100.0,
                strategy=self.name,
                metadata={
                    "setup": "+".join(details),
                    "aggression": aggression,
                    "stop_loss": vwap * 0.98, # Tight stop below VWAP
                    "target": current_price * 1.10 # 10% squeeze target
                }
            )
            
        return None

    def _check_micro_pullback(self, history: pd.DataFrame) -> bool:
        """
        Simple heuristic for 1-min micro pullback.
        Returns true if recent action shows consolidation/dip in an uptrend.
        """
        if history is None or len(history) < 5:
            return False
            
        # Get last 5 candles
        last_5 = history.tail(5)
        
        # Check if we are generally uptrending (Move avg rising)
        ma5 = last_5['close'].mean()
        if last_5.iloc[-1]['close'] < ma5:
            # Current price is below 5-period average (Dip)
            # But ensure the trend previous to this was strong
            prev_trend = last_5.iloc[0]['close'] < last_5.iloc[2]['close']
            return prev_trend
            
        return False

    def _is_market_open(self) -> bool:
        # Simple time check or assume valid if data is streaming
        return True
