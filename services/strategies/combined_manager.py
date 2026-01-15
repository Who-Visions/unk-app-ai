"""
Combined Strategy Manager
=========================
Trade multiple strategies simultaneously for smoother P&L curves.

Philosophy from Trey's Framework:
- Continuation + Reversal strategies together
- Continuation: 38% win rate, 3:1 R:R
- Reversal: 72% win rate, 0.8:1 R:R
- Combined: Offsetting negatives for consistent profits

Account Type Considerations (Ross Cameron PDT insights):
- Cash Account: Limited to settled funds, slower growth
- Margin Account: Unlimited trading, no leverage
- Leverage Account: 4-6x buying power, fastest growth
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Local imports
from .continuation_strategy import ContinuationStrategy, ContinuationSignal
from .reversal_strategy import ReversalStrategy, ReversalSignal
from .momentum_scanner import MomentumStrategy, MomentumSignal


class AccountType(Enum):
    """
    Account type determines trading capability.
    
    Based on Ross Cameron's PDT rule insights:
    - Cash: Wait for settlement, ~1 trade/day
    - Margin: Unlimited trades, 1x capital
    - Leverage: Unlimited trades, 4-6x capital
    """
    CASH = "cash"           # T+1 settlement, limited trades
    MARGIN = "margin"       # Unlimited trades, 1x buying power
    LEVERAGE = "leverage"   # Unlimited trades, 4-6x buying power


@dataclass
class PortfolioState:
    """
    Current portfolio state.
    
    Tracks account balance, daily P&L, and active positions.
    """
    account_balance: float
    buying_power: float
    daily_pnl: float = 0.0
    daily_trades: int = 0
    
    # Active signals
    momentum_signals: List[MomentumSignal] = field(default_factory=list)
    continuation_signals: List[ContinuationSignal] = field(default_factory=list)
    reversal_signals: List[ReversalSignal] = field(default_factory=list)
    
    # Daily limits
    max_daily_loss: float = 200.0
    daily_goal: float = 200.0
    max_trades_per_day: int = 10
    
    # Account type
    account_type: AccountType = AccountType.MARGIN
    
    @property
    def is_at_daily_goal(self) -> bool:
        return self.daily_pnl >= self.daily_goal
    
    @property
    def is_at_max_loss(self) -> bool:
        return self.daily_pnl <= -self.max_daily_loss
    
    @property
    def should_stop_trading(self) -> bool:
        """Check if should stop trading for the day."""
        if self.is_at_max_loss:
            return True
        if self.account_type == AccountType.CASH:
            # Cash accounts limited by settlement
            return self.daily_trades >= 1
        return self.daily_trades >= self.max_trades_per_day
    
    @property
    def total_active_positions(self) -> int:
        return (
            len(self.momentum_signals) +
            len(self.continuation_signals) +
            len(self.reversal_signals)
        )
    
    def reset_daily(self) -> None:
        """Reset daily counters (call at market open)."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.momentum_signals.clear()
        self.continuation_signals.clear()
        self.reversal_signals.clear()


class CombinedStrategyManager:
    """
    Manages multiple strategies simultaneously.
    
    Strategy Combinations:
    1. Momentum (Ross Cameron) - Morning gap plays
    2. Continuation (Trey) - Buy strength, trail winners
    3. Reversal (Trey) - Buy dips on strong stocks
    
    Benefits of Combined Trading:
    - Smoother P&L curve
    - Different strategies work in different conditions
    - High win rate (reversal) offsets low win rate (continuation)
    - Multiple opportunities throughout the day
    
    Usage:
        manager = CombinedStrategyManager(
            account_balance=2000,
            account_type=AccountType.MARGIN
        )
        
        # Scan for opportunities
        signals = manager.scan_all(stock_data)
        
        # Execute best signal
        if signals:
            manager.execute_signal(signals[0])
        
        # Manage active positions
        manager.update_positions(current_prices)
    """
    
    def __init__(
        self,
        account_balance: float = 2000.0,
        account_type: AccountType = AccountType.MARGIN,
        leverage_ratio: float = 1.0,
        small_account_mode: bool = True,
    ):
        """
        Initialize combined strategy manager.
        
        Args:
            account_balance: Starting account balance
            account_type: Type of trading account
            leverage_ratio: Leverage multiplier (1x, 4x, 6x)
            small_account_mode: Use tighter criteria
        """
        self.account_type = account_type
        self.leverage_ratio = leverage_ratio
        self.small_account_mode = small_account_mode
        
        # Calculate buying power
        if account_type == AccountType.LEVERAGE:
            buying_power = account_balance * leverage_ratio
        else:
            buying_power = account_balance
        
        # Initialize portfolio state
        self.portfolio = PortfolioState(
            account_balance=account_balance,
            buying_power=buying_power,
            account_type=account_type,
            daily_goal=200.0 if small_account_mode else 500.0,
            max_daily_loss=account_balance * 0.05,  # 5% max daily loss
        )
        
        # Initialize strategies
        self.momentum = MomentumStrategy(
            small_account_mode=small_account_mode,
            daily_goal=self.portfolio.daily_goal,
            max_daily_loss=self.portfolio.max_daily_loss,
        )
        
        self.continuation = ContinuationStrategy()
        self.reversal = ReversalStrategy()
        
        logger.info(
            f"CombinedStrategyManager initialized: "
            f"${account_balance} {account_type.value} account, "
            f"${buying_power:.0f} buying power"
        )
    
    def scan_all(
        self,
        dfs: Dict[str, "pd.DataFrame"],
        stock_data: Dict[str, Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan all strategies for opportunities.
        
        Args:
            dfs: Dict of symbol -> OHLCV DataFrame
            stock_data: Dict of symbol -> stock info (price, float, etc.)
            
        Returns:
            List of signals ranked by quality
        """
        if self.portfolio.should_stop_trading:
            logger.info("Should stop trading for today")
            return []
        
        all_signals = []
        
        for symbol, df in dfs.items():
            if df is None or len(df) < 200:
                continue
            
            info = stock_data.get(symbol, {}) if stock_data else {}
            
            # 1. Momentum (morning gaps)
            momentum_signal = self.momentum.scan_for_entry(df, symbol, info)
            if momentum_signal and momentum_signal.is_valid:
                all_signals.append({
                    "type": "momentum",
                    "signal": momentum_signal,
                    "priority": 1,  # Highest priority
                    "symbol": symbol,
                })
            
            # 2. Continuation (buy strength)
            cont_signal = self.continuation.generate_signal(df, symbol)
            if cont_signal:
                all_signals.append({
                    "type": "continuation",
                    "signal": cont_signal,
                    "priority": 2,
                    "symbol": symbol,
                })
            
            # 3. Reversal (buy dips)
            rev_signal = self.reversal.generate_signal(df, symbol)
            if rev_signal:
                all_signals.append({
                    "type": "reversal",
                    "signal": rev_signal,
                    "priority": 3,
                    "symbol": symbol,
                })
        
        # Sort by priority then by quality metrics
        all_signals.sort(key=lambda x: (
            x["priority"],
            -getattr(x["signal"], "momentum_score", 0),
            -getattr(x["signal"], "distance_from_200sma", 0),
        ))
        
        return all_signals
    
    def execute_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Execute a trading signal.
        
        Args:
            signal_data: Signal dict from scan_all
            
        Returns:
            True if executed successfully
        """
        signal_type = signal_data["type"]
        signal = signal_data["signal"]
        
        if signal_type == "momentum":
            self.portfolio.momentum_signals.append(signal)
        elif signal_type == "continuation":
            self.portfolio.continuation_signals.append(signal)
        elif signal_type == "reversal":
            self.portfolio.reversal_signals.append(signal)
        
        self.portfolio.daily_trades += 1
        
        logger.info(
            f"Executed {signal_type} signal on {signal.symbol} "
            f"@ ${signal.entry_price if hasattr(signal, 'entry_price') else signal.avg_entry_price}"
        )
        
        return True
    
    def update_positions(
        self,
        current_prices: Dict[str, float],
        dfs: Dict[str, "pd.DataFrame"] = None,
    ) -> List[Dict[str, Any]]:
        """
        Update all active positions and check exits.
        
        Args:
            current_prices: Dict of symbol -> current price
            dfs: Optional DataFrame dict for indicator updates
            
        Returns:
            List of exit actions taken
        """
        exits = []
        
        # Update momentum positions
        for signal in list(self.portfolio.momentum_signals):
            if signal.symbol not in current_prices:
                continue
            
            price = current_prices[signal.symbol]
            df = dfs.get(signal.symbol) if dfs else None
            
            should_exit, reason = self.momentum.check_exit_conditions(
                df, signal.entry_price, price
            )
            
            if should_exit or price <= signal.stop_loss:
                pnl = (price - signal.entry_price) if signal.direction == "long" else (signal.entry_price - price)
                self.portfolio.daily_pnl += pnl * 100  # Assume 100 shares
                self.portfolio.momentum_signals.remove(signal)
                exits.append({
                    "type": "momentum",
                    "symbol": signal.symbol,
                    "reason": reason or "stop hit",
                    "pnl": pnl * 100,
                })
        
        # Update continuation positions
        for signal in list(self.portfolio.continuation_signals):
            if signal.symbol not in current_prices:
                continue
            
            price = current_prices[signal.symbol]
            df = dfs.get(signal.symbol) if dfs else None
            
            should_exit, reason = self.continuation.should_exit(signal, price, df)
            
            if should_exit:
                pnl = price - signal.entry_price
                self.portfolio.daily_pnl += pnl * 100
                self.portfolio.continuation_signals.remove(signal)
                exits.append({
                    "type": "continuation",
                    "symbol": signal.symbol,
                    "reason": reason,
                    "pnl": pnl * 100,
                })
        
        # Update reversal positions
        for signal in list(self.portfolio.reversal_signals):
            if signal.symbol not in current_prices:
                continue
            
            price = current_prices[signal.symbol]
            
            # Check for scale-in opportunity
            scale_level = self.reversal.check_scale_trigger(signal, price)
            if scale_level:
                signal.add_scale(price, scale_level)
            
            should_exit, reason = self.reversal.should_exit(signal, price)
            
            if should_exit:
                pnl = price - signal.avg_entry_price
                self.portfolio.daily_pnl += pnl * 100
                self.portfolio.reversal_signals.remove(signal)
                exits.append({
                    "type": "reversal",
                    "symbol": signal.symbol,
                    "reason": reason,
                    "pnl": pnl * 100,
                })
        
        return exits
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's trading."""
        return {
            "account_balance": self.portfolio.account_balance,
            "daily_pnl": round(self.portfolio.daily_pnl, 2),
            "daily_trades": self.portfolio.daily_trades,
            "active_positions": self.portfolio.total_active_positions,
            "at_daily_goal": self.portfolio.is_at_daily_goal,
            "at_max_loss": self.portfolio.is_at_max_loss,
            "should_stop": self.portfolio.should_stop_trading,
            "momentum_positions": len(self.portfolio.momentum_signals),
            "continuation_positions": len(self.portfolio.continuation_signals),
            "reversal_positions": len(self.portfolio.reversal_signals),
        }
    
    def reset_day(self) -> None:
        """Reset for new trading day."""
        self.portfolio.reset_daily()
        logger.info("Reset for new trading day")


def create_combined_manager(
    account_balance: float = 2000.0,
    account_type: str = "margin",
    leverage: float = 1.0,
    small_account: bool = True,
) -> CombinedStrategyManager:
    """
    Factory function to create combined strategy manager.
    
    Args:
        account_balance: Starting balance
        account_type: "cash", "margin", or "leverage"
        leverage: Leverage multiplier for leverage accounts
        small_account: Use small account rules
    """
    acc_type = AccountType(account_type.lower())
    
    return CombinedStrategyManager(
        account_balance=account_balance,
        account_type=acc_type,
        leverage_ratio=leverage,
        small_account_mode=small_account,
    )
