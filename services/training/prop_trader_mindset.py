"""
Prop Trader Mindset & Discipline Module
========================================
Based on Kyle's story (Broke to Millionaire Day Trader video).

Key Insights:
- Trading is 90% psychology, 10% strategy
- Stop overtrading, revenge trading, overleveraging
- Focus on process, not P&L
- Build discipline outside of trading (physical, mental)
- Trade robotically - no highs or lows
- Environment matters - reduce chaos in life
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum

logger = logging.getLogger(__name__)


class TradingMistake(Enum):
    """Common trading mistakes to track."""
    OVERTRADING = "overtrading"
    REVENGE_TRADING = "revenge_trading"
    OVERLEVERAGING = "overleveraging"
    FOMO = "fomo"
    NOT_FOLLOWING_RULES = "not_following_rules"
    EMOTIONAL_ENTRY = "emotional_entry"
    MOVING_STOP = "moving_stop"
    NO_PLAN = "no_plan"
    TRADING_NOISE = "trading_noise"  # Trading between zones/setups


@dataclass
class DailyMindset:
    """
    Daily mindset check-in before trading.
    
    Kyle's insight: "When I was trading in the zone, I was at peace.
    The numbers on the screen didn't matter. P&L didn't matter.
    All that mattered was taking good trades."
    """
    date: str
    
    # Pre-trade checklist
    slept_well: bool = False
    exercised: bool = False
    ate_healthy: bool = False
    no_stress: bool = False
    
    # Environment check
    quiet_space: bool = False
    no_distractions: bool = False
    relationships_good: bool = False
    
    # Mental state
    feeling_patient: bool = False
    not_desperate_for_money: bool = False
    accepting_of_losses: bool = False
    
    # Trading rules
    have_plan: bool = False
    know_max_risk: bool = False
    defined_entry_exit: bool = False
    
    notes: str = ""
    
    @property
    def ready_to_trade(self) -> bool:
        """Check if mentally ready to trade."""
        critical = [
            self.slept_well,
            self.not_desperate_for_money,
            self.have_plan,
            self.know_max_risk,
        ]
        return all(critical)
    
    @property
    def optimal_state(self) -> bool:
        """Check if in optimal trading state."""
        return all([
            self.slept_well,
            self.exercised,
            self.ate_healthy,
            self.no_stress,
            self.quiet_space,
            self.no_distractions,
            self.feeling_patient,
            self.not_desperate_for_money,
            self.have_plan,
        ])
    
    @property
    def readiness_score(self) -> int:
        """0-100 score of trading readiness."""
        checks = [
            self.slept_well,
            self.exercised,
            self.ate_healthy,
            self.no_stress,
            self.quiet_space,
            self.no_distractions,
            self.relationships_good,
            self.feeling_patient,
            self.not_desperate_for_money,
            self.accepting_of_losses,
            self.have_plan,
            self.know_max_risk,
            self.defined_entry_exit,
        ]
        return round(sum(checks) / len(checks) * 100)


@dataclass
class TradingJournal:
    """
    Trading journal entry.
    
    Kyle's insight: "Trading is a mirror. It forces you to address
    things about yourself that you would never think of before."
    """
    date: str
    symbol: str
    direction: str
    
    # Trade details
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    
    # Result
    pnl: float
    pnl_percent: float
    
    # Self-assessment
    followed_plan: bool = False
    proper_risk: bool = False  # Was it 1-2% max?
    waited_for_setup: bool = False
    patient_entry: bool = False
    patient_exit: bool = False
    
    # Mistakes made
    mistakes: List[TradingMistake] = field(default_factory=list)
    
    # Reflection
    what_went_well: str = ""
    what_to_improve: str = ""
    lesson_learned: str = ""
    
    @property
    def execution_score(self) -> int:
        """Score how well the trade was executed (not P&L)."""
        checks = [
            self.followed_plan,
            self.proper_risk,
            self.waited_for_setup,
            self.patient_entry,
            self.patient_exit,
        ]
        return round(sum(checks) / len(checks) * 100)
    
    @property
    def was_good_trade(self) -> bool:
        """A good trade follows the process, regardless of outcome."""
        return self.execution_score >= 80


@dataclass
class PropTraderDiscipline:
    """
    Prop trader discipline tracker.
    
    The 3 killers Kyle identified:
    1. Overtrading
    2. Revenge trading
    3. Overleveraging
    
    The solution:
    - Focus on probabilities and risk-reward
    - Trade robotically (no highs or lows)
    - Environment and lifestyle matter
    """
    
    # Daily tracking
    daily_mindsets: List[DailyMindset] = field(default_factory=list)
    trades: List[TradingJournal] = field(default_factory=list)
    
    # Mistake counters
    mistake_counts: Dict[str, int] = field(default_factory=dict)
    
    # Streaks
    days_without_overtrading: int = 0
    days_without_revenge: int = 0
    days_without_overleveraging: int = 0
    
    def log_mindset(self, mindset: DailyMindset) -> None:
        """Log daily mindset check-in."""
        self.daily_mindsets.append(mindset)
        logger.info(f"Mindset logged: readiness {mindset.readiness_score}%")
    
    def log_trade(self, trade: TradingJournal) -> None:
        """Log a trade and update mistake tracking."""
        self.trades.append(trade)
        
        # Track mistakes
        for mistake in trade.mistakes:
            key = mistake.value
            self.mistake_counts[key] = self.mistake_counts.get(key, 0) + 1
            
            # Reset relevant streaks
            if mistake == TradingMistake.OVERTRADING:
                self.days_without_overtrading = 0
            elif mistake == TradingMistake.REVENGE_TRADING:
                self.days_without_revenge = 0
            elif mistake == TradingMistake.OVERLEVERAGING:
                self.days_without_overleveraging = 0
        
        # Update streaks if clean day
        if TradingMistake.OVERTRADING not in trade.mistakes:
            self.days_without_overtrading += 1
        if TradingMistake.REVENGE_TRADING not in trade.mistakes:
            self.days_without_revenge += 1
        if TradingMistake.OVERLEVERAGING not in trade.mistakes:
            self.days_without_overleveraging += 1
    
    def get_execution_avg(self) -> float:
        """Get average execution score."""
        if not self.trades:
            return 0.0
        return sum(t.execution_score for t in self.trades) / len(self.trades)
    
    def get_good_trade_rate(self) -> float:
        """Get percentage of trades that were executed well."""
        if not self.trades:
            return 0.0
        good = sum(1 for t in self.trades if t.was_good_trade)
        return good / len(self.trades) * 100
    
    def get_top_mistakes(self, n: int = 3) -> List[tuple]:
        """Get most common mistakes."""
        sorted_mistakes = sorted(
            self.mistake_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_mistakes[:n]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get discipline summary."""
        return {
            "total_trades": len(self.trades),
            "avg_execution_score": round(self.get_execution_avg(), 1),
            "good_trade_rate": round(self.get_good_trade_rate(), 1),
            "top_mistakes": self.get_top_mistakes(),
            "streak_no_overtrading": self.days_without_overtrading,
            "streak_no_revenge": self.days_without_revenge,
            "streak_no_overleveraging": self.days_without_overleveraging,
        }


# Kyle's key lessons
PROP_TRADER_LESSONS = """
## Kyle's Journey: Broke to Millionaire Day Trader

### The 3 Killers (What Blows Accounts)
1. **Overtrading** - Taking too many trades
2. **Revenge Trading** - Trying to win back losses
3. **Overleveraging** - Risking too much per trade

### The Solution
- Focus on **probabilities** and **risk-reward**
- Trade **robotically** - no celebrating wins, no mourning losses
- Same routine every day regardless of results

### Environment Matters
- Hostile home environment = bad trading
- Relationship stress = bad trading
- Poor diet = bad trading
- No exercise = bad trading
- Chaos in life = chaos in trading

### The Mindset Shift
> "When I sat in front of the charts, I was at peace.
> The numbers on the screen didn't matter. The P&L didn't matter.
> All that mattered was that I was taking good trades."

### Why Traders Fail (It's NOT Strategy)
- Their personality (impulsive, impatient)
- Their environment (stress, chaos)
- Their relationships (fights, drama)
- Their diet (garbage food = garbage decisions)
- No exercise (low energy, poor focus)
- No discipline (can't follow rules)

### The Mirror Effect
> "Trading is a mirror. It forces you to address things about yourself
> and your environment that you would never think of before.
> I became a better PERSON, not just a better trader."

### Key Stats (After Getting Discipline)
- 7+ years trading
- $4.5M from prop firms
- $2.5M single payout (Apex record)
- Trades NQ, ES, YM futures

### Final Advice
> "The worst case scenario is you're in the exact same position you started.
> At least you tried. Take the leap of faith."
"""


def create_discipline_tracker() -> PropTraderDiscipline:
    """Create a new discipline tracker."""
    return PropTraderDiscipline()
