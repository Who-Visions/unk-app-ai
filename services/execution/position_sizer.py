"""
Position Sizer
==============
Ross Cameron's cushion-based position sizing system.

Rules:
1. Start with 1/4 max position size
2. Build profit cushion (1/4 of daily goal)
3. Size up only after cushion built
4. Size back down if cushion lost
5. Add to winners, cut losers fast
6. 3 consecutive losers = done for day

Small Account Risk Rules:
- Risk $50 to make $100 (2:1 R:R)
- Daily max loss: 5% of account
- 3 consecutive losers = stop
"""
from __future__ import annotations

import logging
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SizeMode(Enum):
    """Position sizing mode."""
    QUARTER = 0.25   # Building cushion
    HALF = 0.50      # Small cushion
    THREE_QUARTER = 0.75  # Good cushion
    FULL = 1.0       # Fully sized up


@dataclass
class TradeResult:
    """Result of a single trade."""
    symbol: str
    pnl: float
    shares: int
    entry_price: float
    exit_price: float
    is_winner: bool = False
    
    def __post_init__(self):
        """Determine win/loss."""
        self.is_winner = self.pnl > 0


@dataclass
class DayStats:
    """Daily trading statistics."""
    realized_pnl: float = 0.0
    trades_taken: int = 0
    winners: int = 0
    losers: int = 0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    
    # State tracking
    hit_daily_max_loss: bool = False
    hit_consecutive_loss_limit: bool = False
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.trades_taken == 0:
            return 0.0
        return self.winners / self.trades_taken
    
    @property
    def should_stop_trading(self) -> bool:
        """Check if trading should stop for the day."""
        return self.hit_daily_max_loss or self.hit_consecutive_loss_limit


class CushionPositionSizer:
    """
    Position sizing with profit cushion management.
    
    Ross Cameron's approach:
    1. Start with 1/4 max position
    2. Size up only after 1/4 daily goal reached
    3. Size back down if cushion lost
    4. Add to winners, cut losers
    
    Usage:
        sizer = CushionPositionSizer(
            daily_goal=200.0,
            max_position_value=2000.0,
            account_size=2000.0,
        )
        
        # Get initial position size
        size = sizer.get_position_size(price=5.0, quality="A")
        
        # After trade completes
        sizer.record_trade(pnl=50.0, is_winner=True)
        
        # Check if can size up
        if sizer.can_size_up():
            size = sizer.get_position_size(price=5.0, quality="A")
    """
    
    def __init__(
        self,
        daily_goal: float = 200.0,
        max_position_value: float = 2000.0,
        account_size: float = 2000.0,
        max_daily_loss: float = None,
        consecutive_loss_limit: int = 3,
        cushion_target: float = 0.25,  # 1/4 of daily goal
    ):
        """
        Initialize position sizer.
        
        Args:
            daily_goal: Daily profit target
            max_position_value: Maximum position value (buying power)
            account_size: Current account size
            max_daily_loss: Maximum loss before stopping (default: daily_goal)
            consecutive_loss_limit: Stop after this many losses in a row
            cushion_target: Fraction of daily goal needed to size up
        """
        self.daily_goal = daily_goal
        self.max_position_value = max_position_value
        self.account_size = account_size
        self.max_daily_loss = max_daily_loss or daily_goal
        self.consecutive_loss_limit = consecutive_loss_limit
        self.cushion_target = cushion_target
        
        # State
        self.day_stats = DayStats()
        self.current_mode = SizeMode.QUARTER
        self.trades: List[TradeResult] = []
    
    def reset_day(self):
        """Reset for new trading day."""
        self.day_stats = DayStats()
        self.current_mode = SizeMode.QUARTER
        self.trades = []
    
    @property
    def current_pnl(self) -> float:
        """Get current realized PnL."""
        return self.day_stats.realized_pnl
    
    @property
    def cushion_amount(self) -> float:
        """Amount of profit cushion built."""
        return max(0.0, self.day_stats.realized_pnl)
    
    @property
    def cushion_threshold(self) -> float:
        """Profit needed to size up."""
        return self.daily_goal * self.cushion_target
    
    @property
    def size_multiplier(self) -> float:
        """Current position size multiplier (0.25 - 1.0)."""
        return self.current_mode.value
    
    def can_size_up(self) -> bool:
        """Check if we can increase position size."""
        # Can't size up if at max
        if self.current_mode == SizeMode.FULL:
            return False
        
        # Need cushion to size up
        return self.cushion_amount >= self.cushion_threshold
    
    def should_size_down(self) -> bool:
        """Check if we should reduce position size."""
        # Size down if cushion lost
        return self.cushion_amount < self.cushion_threshold * 0.5
    
    def can_trade(self) -> bool:
        """Check if trading is allowed."""
        if self.day_stats.should_stop_trading:
            return False
        
        # Check daily max loss
        if self.current_pnl <= -self.max_daily_loss:
            self.day_stats.hit_daily_max_loss = True
            logger.warning(f"Daily max loss hit: ${self.current_pnl:.2f}")
            return False
        
        return True
    
    def get_position_size(
        self,
        price: float,
        quality: str = "B",
        risk_per_share: float = None,
    ) -> dict:
        """
        Calculate position size based on current state.
        
        Args:
            price: Current stock price
            quality: Setup quality (A, B, C, D)
            risk_per_share: Distance to stop loss
            
        Returns:
            Dict with shares, value, risk info
        """
        if not self.can_trade():
            return {
                "shares": 0,
                "value": 0,
                "reason": "Trading stopped for day",
                "can_trade": False,
            }
        
        # Update sizing mode
        self._update_mode()
        
        # Base position value
        base_value = self.max_position_value * self.size_multiplier
        
        # Adjust for quality
        quality_multiplier = {
            "A": 1.0,
            "B": 0.75,
            "C": 0.5,
            "D": 0.25,
        }.get(quality.upper(), 0.5)
        
        adjusted_value = base_value * quality_multiplier
        
        # Calculate shares
        if price > 0:
            shares = int(adjusted_value / price)
        else:
            shares = 0
        
        # Calculate risk if stop loss provided
        risk_amount = 0.0
        if risk_per_share and shares > 0:
            risk_amount = shares * risk_per_share
        
        return {
            "shares": shares,
            "value": round(shares * price, 2),
            "mode": self.current_mode.name,
            "multiplier": self.size_multiplier,
            "quality": quality,
            "risk_amount": round(risk_amount, 2),
            "can_trade": True,
        }
    
    def record_trade(
        self,
        symbol: str = "",
        pnl: float = 0.0,
        shares: int = 0,
        entry_price: float = 0.0,
        exit_price: float = 0.0,
    ):
        """
        Record completed trade and update stats.
        
        Args:
            symbol: Stock symbol
            pnl: Profit/loss from trade
            shares: Number of shares traded
            entry_price: Entry price
            exit_price: Exit price
        """
        trade = TradeResult(
            symbol=symbol,
            pnl=pnl,
            shares=shares,
            entry_price=entry_price,
            exit_price=exit_price,
        )
        self.trades.append(trade)
        
        # Update stats
        self.day_stats.realized_pnl += pnl
        self.day_stats.trades_taken += 1
        
        if trade.is_winner:
            self.day_stats.winners += 1
            self.day_stats.consecutive_losses = 0
        else:
            self.day_stats.losers += 1
            self.day_stats.consecutive_losses += 1
            self.day_stats.max_consecutive_losses = max(
                self.day_stats.max_consecutive_losses,
                self.day_stats.consecutive_losses
            )
            
            # Check consecutive loss limit
            if self.day_stats.consecutive_losses >= self.consecutive_loss_limit:
                self.day_stats.hit_consecutive_loss_limit = True
                logger.warning(
                    f"Consecutive loss limit hit: "
                    f"{self.day_stats.consecutive_losses} losses"
                )
        
        # Update sizing mode
        self._update_mode()
        
        logger.info(
            f"Trade recorded: {symbol} PnL=${pnl:.2f}, "
            f"Day total=${self.day_stats.realized_pnl:.2f}, "
            f"Mode={self.current_mode.name}"
        )
    
    def _update_mode(self):
        """Update position sizing mode based on cushion."""
        if self.cushion_amount >= self.cushion_threshold * 3:
            self.current_mode = SizeMode.FULL
        elif self.cushion_amount >= self.cushion_threshold * 2:
            self.current_mode = SizeMode.THREE_QUARTER
        elif self.cushion_amount >= self.cushion_threshold:
            self.current_mode = SizeMode.HALF
        else:
            self.current_mode = SizeMode.QUARTER
    
    def get_status(self) -> dict:
        """Get current status summary."""
        return {
            "daily_goal": self.daily_goal,
            "current_pnl": round(self.day_stats.realized_pnl, 2),
            "cushion": round(self.cushion_amount, 2),
            "cushion_threshold": round(self.cushion_threshold, 2),
            "trades_taken": self.day_stats.trades_taken,
            "win_rate": round(self.day_stats.win_rate * 100, 1),
            "consecutive_losses": self.day_stats.consecutive_losses,
            "size_mode": self.current_mode.name,
            "size_multiplier": self.size_multiplier,
            "can_trade": self.can_trade(),
            "should_stop": self.day_stats.should_stop_trading,
        }


class SmallAccountSizer(CushionPositionSizer):
    """
    Position sizer optimized for small accounts.
    
    Based on Ross Cameron's Small Account Worksheet:
    - Risk $50 to make $100 (2:1 R:R)
    - Daily max loss: $100 (5% of $2K account)
    - 3 consecutive losers = done
    - Focus on ONE high-quality trade per day
    """
    
    def __init__(
        self,
        account_size: float = 2000.0,
        risk_percent: float = 0.025,  # 2.5% risk per trade
    ):
        """
        Initialize small account sizer.
        
        Args:
            account_size: Current account balance
            risk_percent: Risk per trade as percentage
        """
        daily_goal = account_size * 0.10  # 10% daily target
        max_loss = account_size * 0.05    # 5% max loss
        
        super().__init__(
            daily_goal=daily_goal,
            max_position_value=account_size,  # Full account (cash account)
            account_size=account_size,
            max_daily_loss=max_loss,
            consecutive_loss_limit=3,
            cushion_target=0.25,
        )
        
        self.risk_percent = risk_percent
        self.risk_per_trade = account_size * risk_percent
    
    def get_position_for_setup(
        self,
        price: float,
        stop_loss: float,
        quality: str = "A",
    ) -> dict:
        """
        Calculate position size based on risk.
        
        Args:
            price: Entry price
            stop_loss: Stop loss price
            quality: Setup quality (A/B/C/D)
            
        Returns:
            Position sizing info
        """
        if quality not in ["A", "B"]:
            return {
                "shares": 0,
                "value": 0,
                "reason": f"Quality {quality} too low for small account",
                "can_trade": False,
            }
        
        risk_per_share = abs(price - stop_loss)
        if risk_per_share <= 0:
            return {
                "shares": 0,
                "value": 0,
                "reason": "Invalid stop loss",
                "can_trade": False,
            }
        
        # Calculate shares based on risk
        max_shares_by_risk = int(self.risk_per_trade / risk_per_share)
        
        # Also check buying power
        max_shares_by_capital = int(self.max_position_value / price)
        
        # Take the smaller of the two
        shares = min(max_shares_by_risk, max_shares_by_capital)
        
        # Apply size multiplier
        shares = int(shares * self.size_multiplier)
        
        return {
            "shares": shares,
            "value": round(shares * price, 2),
            "risk_amount": round(shares * risk_per_share, 2),
            "risk_per_share": round(risk_per_share, 2),
            "mode": self.current_mode.name,
            "can_trade": True,
        }
