"""
Backtester Engine
=================
Simple bar-by-bar backtesting engine that uses existing strategy logic.
Designed for future Walk-Forward Optimization (WFO) integration.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf
    import pandas as pd
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None
    pd = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Record of a single trade."""
    symbol: str
    strategy: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    shares: int = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""  # "stop", "target", "signal", "end"


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    starting_equity: float
    ending_equity: float
    total_return_pct: float
    
    # Core metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Risk metrics
    max_drawdown_pct: float = 0.0
    max_drawdown_amount: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    recovery_factor: float = 0.0
    
    # Trade stats
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Data
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "starting_equity": self.starting_equity,
            "ending_equity": round(self.ending_equity, 2),
            "total_return_pct": round(self.total_return_pct, 2),
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate * 100, 1),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "profit_factor": round(self.profit_factor, 2),
            "recovery_factor": round(self.recovery_factor, 2),
            "avg_win": round(self.avg_win, 2),
            "avg_loss": round(self.avg_loss, 2),
        }


class Backtester:
    """
    Simple backtesting engine for Unk trading strategies.
    
    Uses existing strategy.decide() logic per bar.
    Designed for Walk-Forward Optimization integration.
    """
    
    def __init__(
        self,
        starting_equity: float = 10000,
        risk_pct: float = 0.02,
        commission: float = 0.0,
        slippage_pct: float = 0.001,
    ):
        self.starting_equity = starting_equity
        self.risk_pct = risk_pct
        self.commission = commission
        self.slippage_pct = slippage_pct
        
        # State
        self.equity = starting_equity
        self.cash = starting_equity
        self.position: Optional[Trade] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.peak_equity = starting_equity
        self.max_drawdown = 0.0
    
    def run(
        self,
        symbol: str,
        strategy_name: str,
        start: str,
        end: str,
    ) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
            strategy_name: Strategy to use ("DayTrader", "SwingTrader", "Scalper")
            start: Start date "YYYY-MM-DD"
            end: End date "YYYY-MM-DD"
            
        Returns:
            BacktestResult with metrics and trade log
        """
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance not available for backtesting")
            return self._empty_result(symbol, strategy_name, start, end)
        
        # Reset state
        self._reset()
        
        # Load data
        logger.info(f"Loading {symbol} data from {start} to {end}")
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start, end=end)
            
            if data.empty:
                logger.error(f"No data for {symbol} in date range")
                return self._empty_result(symbol, strategy_name, start, end)
        except Exception as e:
            logger.exception(f"Failed to load data for {symbol}: {e}")
            return self._empty_result(symbol, strategy_name, start, end)
        
        # Load strategy
        try:
            strategy = self._load_strategy(strategy_name)
        except Exception as e:
            logger.exception(f"Failed to load strategy {strategy_name}: {e}")
            return self._empty_result(symbol, strategy_name, start, end)
        
        # Iterate bars
        logger.info(f"Running backtest: {len(data)} bars")
        
        for date, bar in data.iterrows():
            self._process_bar(
                symbol=symbol,
                strategy=strategy,
                strategy_name=strategy_name,
                date=str(date.date()),
                open_price=float(bar["Open"]),
                high=float(bar["High"]),
                low=float(bar["Low"]),
                close=float(bar["Close"]),
                volume=int(bar["Volume"]),
            )
        
        # Close any open position at end
        if self.position:
            self._close_position(
                date=str(data.index[-1].date()),
                price=float(data["Close"].iloc[-1]),
                reason="end"
            )
        
        # Calculate metrics
        return self._calculate_results(symbol, strategy_name, start, end)
    
    def _reset(self) -> None:
        """Reset backtester state."""
        self.equity = self.starting_equity
        self.cash = self.starting_equity
        self.position = None
        self.trades = []
        self.equity_curve = []
        self.peak_equity = self.starting_equity
        self.max_drawdown = 0.0
    
    def _load_strategy(self, name: str):
        """Lazy load strategy class."""
        from services.trading import TRADING_STRATEGY_REGISTRY, _load_trading_strategies
        _load_trading_strategies()
        
        if name not in TRADING_STRATEGY_REGISTRY:
            raise ValueError(f"Unknown strategy: {name}")
        
        return TRADING_STRATEGY_REGISTRY[name]()
    
    def _process_bar(
        self,
        symbol: str,
        strategy,
        strategy_name: str,
        date: str,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int,
    ) -> None:
        """Process a single bar."""
        
        # Check stops/targets on open position
        if self.position:
            if self.position.stop_loss and low <= self.position.stop_loss:
                self._close_position(date, self.position.stop_loss, "stop")
            elif self.position.take_profit and high >= self.position.take_profit:
                self._close_position(date, self.position.take_profit, "target")
        
        # Update equity
        if self.position:
            position_value = self.position.shares * close
            self.equity = self.cash + position_value
        else:
            self.equity = self.cash
        
        # Track drawdown
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        drawdown = (self.peak_equity - self.equity) / self.peak_equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # Record equity curve
        self.equity_curve.append({
            "date": date,
            "equity": round(self.equity, 2),
            "drawdown_pct": round(drawdown * 100, 2),
        })
        
        # Skip strategy decision if already in position
        if self.position:
            return
        
        # Get strategy decision
        try:
            from services.trading_types import TradingRequest
            
            req = TradingRequest(
                strategy=strategy_name,
                symbol=symbol,
                market="stocks",
                portfolio_value=self.equity,
            )
            
            decision = strategy.decide(req)
            
            if decision.action == "buy" and decision.entry_price:
                self._open_position(
                    symbol=symbol,
                    strategy=strategy_name,
                    date=date,
                    price=close,  # Enter at close
                    stop_loss=decision.stop_loss,
                    take_profit=decision.take_profit,
                )
                
        except Exception as e:
            logger.warning(f"Strategy decision failed on {date}: {e}")
    
    def _open_position(
        self,
        symbol: str,
        strategy: str,
        date: str,
        price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
    ) -> None:
        """Open a new position."""
        # Apply slippage
        fill_price = price * (1 + self.slippage_pct)
        
        # Calculate position size based on risk
        if stop_loss:
            risk_per_share = abs(fill_price - stop_loss)
            risk_amount = self.cash * self.risk_pct
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        else:
            shares = int((self.cash * 0.95) / fill_price)  # 95% of cash
        
        if shares <= 0:
            return
        
        cost = shares * fill_price + self.commission
        if cost > self.cash:
            shares = int((self.cash - self.commission) / fill_price)
            cost = shares * fill_price + self.commission
        
        if shares <= 0:
            return
        
        self.cash -= cost
        self.position = Trade(
            symbol=symbol,
            strategy=strategy,
            entry_date=date,
            entry_price=fill_price,
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        logger.debug(f"OPEN {symbol}: {shares} @ ${fill_price:.2f}")
    
    def _close_position(
        self,
        date: str,
        price: float,
        reason: str,
    ) -> None:
        """Close current position."""
        if not self.position:
            return
        
        # Apply slippage
        fill_price = price * (1 - self.slippage_pct)
        
        proceeds = self.position.shares * fill_price - self.commission
        self.cash += proceeds
        
        # Calculate P&L
        cost_basis = self.position.shares * self.position.entry_price
        pnl = proceeds - cost_basis
        pnl_pct = (fill_price / self.position.entry_price - 1) * 100
        
        # Record trade
        self.position.exit_date = date
        self.position.exit_price = fill_price
        self.position.pnl = pnl
        self.position.pnl_pct = pnl_pct
        self.position.exit_reason = reason
        self.trades.append(self.position)
        
        logger.debug(
            f"CLOSE {self.position.symbol}: {reason} @ ${fill_price:.2f} "
            f"P&L: ${pnl:.2f} ({pnl_pct:.1f}%)"
        )
        
        self.position = None
    
    def _calculate_results(
        self,
        symbol: str,
        strategy: str,
        start: str,
        end: str,
    ) -> BacktestResult:
        """Calculate final metrics."""
        result = BacktestResult(
            symbol=symbol,
            strategy=strategy,
            start_date=start,
            end_date=end,
            starting_equity=self.starting_equity,
            ending_equity=self.equity,
            total_return_pct=(self.equity / self.starting_equity - 1) * 100,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )
        
        if not self.trades:
            return result
        
        # Trade counts
        result.total_trades = len(self.trades)
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = len(wins) / len(self.trades) if self.trades else 0
        
        # Win/loss stats
        if wins:
            result.avg_win = sum(t.pnl for t in wins) / len(wins)
            result.largest_win = max(t.pnl for t in wins)
        if losses:
            result.avg_loss = sum(t.pnl for t in losses) / len(losses)
            result.largest_loss = min(t.pnl for t in losses)
        
        result.avg_trade = sum(t.pnl for t in self.trades) / len(self.trades)
        
        # Drawdown
        result.max_drawdown_pct = self.max_drawdown * 100
        result.max_drawdown_amount = self.peak_equity * self.max_drawdown
        
        # Profit factor
        gross_profit = sum(t.pnl for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl for t in losses)) if losses else 1
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Recovery factor
        net_profit = self.equity - self.starting_equity
        if result.max_drawdown_amount > 0:
            result.recovery_factor = net_profit / result.max_drawdown_amount
        
        # Sharpe ratio (simplified: daily returns)
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev = self.equity_curve[i-1]["equity"]
                curr = self.equity_curve[i]["equity"]
                if prev > 0:
                    returns.append((curr - prev) / prev)
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = math.sqrt(
                    sum((r - avg_return) ** 2 for r in returns) / len(returns)
                ) if len(returns) > 1 else 1
                
                # Annualized Sharpe (252 trading days)
                if std_return > 0:
                    result.sharpe_ratio = (avg_return / std_return) * math.sqrt(252)
        
        return result
    
    def _empty_result(
        self,
        symbol: str,
        strategy: str,
        start: str,
        end: str,
    ) -> BacktestResult:
        """Return empty result for error cases."""
        return BacktestResult(
            symbol=symbol,
            strategy=strategy,
            start_date=start,
            end_date=end,
            starting_equity=self.starting_equity,
            ending_equity=self.starting_equity,
            total_return_pct=0.0,
        )


def run_backtest(
    symbol: str,
    strategy: str,
    start: str,
    end: str,
    starting_equity: float = 10000,
    risk_pct: float = 0.02,
) -> BacktestResult:
    """
    Convenience function to run a backtest.
    
    Example:
        result = run_backtest("AAPL", "DayTrader", "2024-01-01", "2025-01-01")
        print(f"Return: {result.total_return_pct:.1f}%")
        print(f"Sharpe: {result.sharpe_ratio:.2f}")
    """
    backtester = Backtester(
        starting_equity=starting_equity,
        risk_pct=risk_pct,
    )
    return backtester.run(symbol, strategy, start, end)
