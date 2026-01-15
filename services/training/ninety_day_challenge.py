"""
90-Day Trading Roadmap Protocol
================================
Based on Hindi trading video: "How to Build a Profitable Trading System in 90 Days"

The 7 Rules for the 90-Day Challenge:
1. Cut All Noise - Remove social media, signals, others' analysis
2. Backtest & Master ONE Setup - Pick one strategy, master it
3. One Trade Per Day - No overtrading, no revenge trading
4. Risk Only 1% Per Trade - No exceptions, build discipline
5. Physical Challenge Daily - 30 min exercise (gym, boxing, running)
6. Mental Challenge Daily - Chess, reading, brain training
7. Daily Self-Audit - Journal and review all rules

Key Insight: "3 years to learn what could be done in 90 days if focused"
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ChallengeStatus(Enum):
    """Status of the 90-day challenge."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RESET = "reset"  # Had to restart


@dataclass
class DailyCheckIn:
    """
    Daily check-in for the 90-day challenge.
    
    All 7 rules must be met every day.
    If any rule is broken, challenge resets.
    """
    day_number: int
    date: str
    
    # Rule 1: Cut Noise
    social_media_avoided: bool = False
    no_external_signals: bool = False
    
    # Rule 2: One Setup Only
    only_traded_master_setup: bool = False
    setup_name: str = ""
    
    # Rule 3: One Trade Per Day
    trades_taken: int = 0
    no_revenge_trading: bool = False
    
    # Rule 4: 1% Risk Only
    max_risk_percent: float = 0.0
    stayed_under_1_percent: bool = False
    
    # Rule 5: Physical Challenge
    physical_activity: str = ""
    physical_minutes: int = 0
    physical_completed: bool = False
    
    # Rule 6: Mental Challenge
    mental_activity: str = ""
    mental_minutes: int = 0
    mental_completed: bool = False
    
    # Rule 7: Self Audit
    journaled: bool = False
    reviewed_rules: bool = False
    
    # Trade details
    trade_result: float = 0.0  # P&L
    notes: str = ""
    
    @property
    def all_rules_met(self) -> bool:
        """Check if all 7 rules were followed."""
        return all([
            self.social_media_avoided,
            self.no_external_signals,
            self.only_traded_master_setup,
            self.trades_taken <= 1,
            self.no_revenge_trading,
            self.stayed_under_1_percent,
            self.physical_completed,
            self.mental_completed,
            self.journaled,
            self.reviewed_rules,
        ])
    
    @property
    def rules_summary(self) -> Dict[str, bool]:
        """Get summary of rule compliance."""
        return {
            "1_cut_noise": self.social_media_avoided and self.no_external_signals,
            "2_one_setup": self.only_traded_master_setup,
            "3_one_trade": self.trades_taken <= 1 and self.no_revenge_trading,
            "4_one_percent_risk": self.stayed_under_1_percent,
            "5_physical_challenge": self.physical_completed,
            "6_mental_challenge": self.mental_completed,
            "7_daily_audit": self.journaled and self.reviewed_rules,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_number": self.day_number,
            "date": self.date,
            "all_rules_met": self.all_rules_met,
            "rules_summary": self.rules_summary,
            "trades_taken": self.trades_taken,
            "trade_result": self.trade_result,
            "physical_activity": self.physical_activity,
            "mental_activity": self.mental_activity,
            "notes": self.notes,
        }


@dataclass
class NinetyDayChallenge:
    """
    The 90-Day Profitable Trader Challenge.
    
    Philosophy:
    - "It took me 3 years to learn what can be done in 90 days"
    - Focus on PROCESS, not profits
    - Master ONE setup completely
    - Build discipline through physical/mental habits
    - No shortcuts - if you break a rule, restart at Day 1
    
    The 7 Rules (must follow ALL every day):
    1. Cut All Noise - Delete Telegram, unfollow trading influencers
    2. Master ONE Setup - Backtest until you know it in your sleep
    3. One Trade Per Day - No overtrading or revenge trading
    4. 1% Risk Maximum - No exceptions, even for "great" setups
    5. Physical Challenge - 30 min daily exercise
    6. Mental Challenge - Chess, reading, brain training
    7. Daily Self-Audit - Journal and check all rules
    
    Key Quote: "If you've done something for 21 days, you can do it long-term.
                If you've done it for 90 days, you can do it for life."
    """
    start_date: str
    master_setup: str
    
    # Progress
    current_day: int = 0
    check_ins: List[DailyCheckIn] = field(default_factory=list)
    
    # Stats
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    
    # Status
    status: ChallengeStatus = ChallengeStatus.NOT_STARTED
    reset_count: int = 0
    
    # Storage
    storage_path: Optional[str] = None
    
    def __post_init__(self):
        if not self.check_ins:
            self.check_ins = []
        if self.current_day > 0:
            self.status = ChallengeStatus.IN_PROGRESS
    
    def start(self) -> None:
        """Start the 90-day challenge."""
        self.start_date = date.today().isoformat()
        self.current_day = 1
        self.status = ChallengeStatus.IN_PROGRESS
        self.check_ins = []
        logger.info(f"Starting 90-Day Challenge with setup: {self.master_setup}")
    
    def check_in(self, daily: DailyCheckIn) -> bool:
        """
        Record daily check-in.
        
        Returns True if all rules met, False if challenge must reset.
        """
        daily.day_number = self.current_day
        daily.date = date.today().isoformat()
        
        if not daily.all_rules_met:
            logger.warning(f"Day {self.current_day}: Rules broken - CHALLENGE RESET")
            failed_rules = [k for k, v in daily.rules_summary.items() if not v]
            logger.warning(f"Failed rules: {failed_rules}")
            self.reset()
            return False
        
        # Rules met - record and advance
        self.check_ins.append(daily)
        self.total_trades += daily.trades_taken
        if daily.trade_result > 0:
            self.winning_trades += 1
        self.total_pnl += daily.trade_result
        
        self.current_day += 1
        
        if self.current_day > 90:
            self.status = ChallengeStatus.COMPLETED
            logger.info("90-Day Challenge COMPLETED! You are now a disciplined trader.")
        
        self.save()
        return True
    
    def reset(self) -> None:
        """Reset challenge to Day 1."""
        self.reset_count += 1
        self.current_day = 1
        self.status = ChallengeStatus.IN_PROGRESS
        self.check_ins = []
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.start_date = date.today().isoformat()
        logger.info(f"Challenge reset (attempt #{self.reset_count})")
        self.save()
    
    @property
    def days_remaining(self) -> int:
        return max(0, 90 - self.current_day + 1)
    
    @property
    def progress_percent(self) -> float:
        return min(100, (self.current_day - 1) / 90 * 100)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Get challenge summary."""
        return {
            "status": self.status.value,
            "current_day": self.current_day,
            "days_remaining": self.days_remaining,
            "progress_percent": round(self.progress_percent, 1),
            "master_setup": self.master_setup,
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate, 1),
            "total_pnl": round(self.total_pnl, 2),
            "reset_count": self.reset_count,
            "start_date": self.start_date,
        }
    
    def save(self, path: str = None) -> Path:
        """Save challenge state to JSON."""
        if path:
            self.storage_path = path
        elif not self.storage_path:
            self.storage_path = "data/90_day_challenge.json"
        
        output = Path(self.storage_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "start_date": self.start_date,
            "master_setup": self.master_setup,
            "current_day": self.current_day,
            "status": self.status.value,
            "reset_count": self.reset_count,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "total_pnl": self.total_pnl,
            "check_ins": [c.to_dict() for c in self.check_ins],
        }
        
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        
        return output
    
    @classmethod
    def load(cls, path: str = "data/90_day_challenge.json") -> "NinetyDayChallenge":
        """Load challenge from JSON."""
        p = Path(path)
        if not p.exists():
            return cls(start_date="", master_setup="")
        
        with open(p) as f:
            data = json.load(f)
        
        challenge = cls(
            start_date=data["start_date"],
            master_setup=data["master_setup"],
            current_day=data["current_day"],
            status=ChallengeStatus(data["status"]),
            reset_count=data.get("reset_count", 0),
            total_trades=data.get("total_trades", 0),
            winning_trades=data.get("winning_trades", 0),
            total_pnl=data.get("total_pnl", 0.0),
            storage_path=path,
        )
        
        return challenge


# Translation of the 7 Rules (Hindi to English)
NINETY_DAY_RULES = {
    1: {
        "hindi": "सारी नॉइज़ को कट कर दो",
        "english": "Cut All Noise",
        "description": (
            "Delete Telegram, Discord, YouTube trading channels. "
            "Unfollow all trading influencers. No external signals or analysis. "
            "For 90 days, the ONLY opinion you care about is YOUR OWN."
        ),
        "actions": [
            "Delete Telegram (especially signal groups)",
            "Unfollow trading influencers on Instagram/Twitter",
            "No watching live trading streams",
            "No reading others' market analysis",
        ],
    },
    2: {
        "hindi": "बैक टेस्ट एंड मास्टर ओनली वन सेटअप",
        "english": "Backtest and Master ONE Setup",
        "description": (
            "Pick ONE setup. Backtest it until you can identify it in your sleep. "
            "If someone wakes you at 3 AM and asks where your setup is forming, "
            "you should be able to answer immediately."
        ),
        "actions": [
            "Choose ONE strategy/setup",
            "Backtest 3 years of data (takes ~1 month)",
            "Trade ONLY this setup for remaining 60 days",
            "Become the best in the world at this ONE setup",
        ],
    },
    3: {
        "hindi": "वन ट्रेड अ डे",
        "english": "One Trade Per Day",
        "description": (
            "Maximum ONE trade per day. No overtrading. No revenge trading. "
            "If no setup appears, great - you followed your rules. "
            "If you accidentally open a position, close it immediately."
        ),
        "actions": [
            "Take maximum 1 trade per day",
            "No revenge trading after a loss",
            "If no setup, no trade - that's discipline",
            "Close accidental entries immediately",
        ],
    },
    4: {
        "hindi": "रिस्क 1% पर ट्रेड",
        "english": "Risk Only 1% Per Trade",
        "description": (
            "1% is your shield. No matter how 'good' the setup looks, "
            "never risk more than 1%. Write 'I will not risk more than 1%' "
            "1000 times in your journal if needed to build discipline."
        ),
        "actions": [
            "Calculate position size for 1% risk",
            "Never exceed 1% regardless of conviction",
            "Focus on PROCESS, not profits for 90 days",
            "Write affirmations if discipline is weak",
        ],
    },
    5: {
        "hindi": "चैलेंज योरसेल्फ फिजिकली",
        "english": "Challenge Yourself Physically",
        "description": (
            "30 minutes of physical challenge EVERY DAY. "
            "Gym, running, boxing, MMA, swimming, jump rope. "
            "Physical discipline builds trading discipline."
        ),
        "actions": [
            "30 min minimum physical activity daily",
            "Choose: gym, running, boxing, swimming, etc.",
            "Give 100% effort - no half-measures",
            "Track in your journal",
        ],
    },
    6: {
        "hindi": "डू समथिंग दैट चैलेंजेस यू मेंटली",
        "english": "Challenge Yourself Mentally",
        "description": (
            "Trading is mentally exhausting. Build mental stamina with "
            "activities like chess, reading, or brain training. "
            "This increases your capacity for focused trading."
        ),
        "actions": [
            "Play chess or solve puzzles daily",
            "Read books (not trading-related)",
            "Build mental stamina/focus",
            "Track in your journal",
        ],
    },
    7: {
        "hindi": "हर दिन खुद को एक ऑडिट करना है",
        "english": "Daily Self-Audit",
        "description": (
            "At end of each day, check ALL rules. "
            "Did you follow your setup? Take only 1 trade? Risk only 1%? "
            "Exercise? Mental challenge? If ANY rule broken, challenge RESETS."
        ),
        "actions": [
            "Check all 6 previous rules at day end",
            "Journal your trade (win or loss)",
            "Note physical and mental activities",
            "Be honest - one broken rule = restart at Day 1",
        ],
    },
}


def print_90_day_rules():
    """Print all 90-day challenge rules."""
    print("\n" + "=" * 60)
    print("90-DAY PROFITABLE TRADER CHALLENGE")
    print("=" * 60)
    print()
    
    for num, rule in NINETY_DAY_RULES.items():
        print(f"Rule {num}: {rule['english']}")
        print(f"         ({rule['hindi']})")
        print(f"         {rule['description']}")
        print()
        for action in rule["actions"]:
            print(f"         • {action}")
        print()
    
    print("=" * 60)
    print("KEY INSIGHT: 'It took me 3 years to learn what can be done in 90 days'")
    print("If you break ANY rule, the challenge RESETS to Day 1.")
    print("=" * 60)


def create_challenge(master_setup: str) -> NinetyDayChallenge:
    """
    Create and start a new 90-day challenge.
    
    Args:
        master_setup: The ONE setup you will master
    """
    challenge = NinetyDayChallenge(
        start_date=date.today().isoformat(),
        master_setup=master_setup,
    )
    challenge.start()
    return challenge
