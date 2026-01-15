"""
Paper Broker
=============
In-memory simulated broker for paper trading.
Tracks positions, orders, PnL with realistic fills.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.execution.broker_interface import (
    AccountInfo,
    ExecutionClient,
    Order,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Record of a completed trade for journal."""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    timestamp: str
    pnl: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PaperBroker(ExecutionClient):
    """
    Paper trading broker with in-memory ledger.
    
    Features:
    - Simulated market/limit order execution
    - Slippage modeling
    - Commission tracking
    - Position management
    - Trade journal with export
    
    Usage:
        broker = PaperBroker(starting_cash=10000)
        result = broker.create_order(Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10
        ))
    """
    
    def __init__(
        self,
        starting_cash: float = 10000.0,
        commission_per_trade: float = 0.0,
        slippage_pct: float = 0.001,
        journal_path: Optional[str] = None,
    ):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.commission_per_trade = commission_per_trade
        self.slippage_pct = slippage_pct
        self.journal_path = journal_path
        
        # Ledger
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, OrderResult] = {}
        self._pending_orders: Dict[str, Order] = {}
        self._trade_journal: List[TradeRecord] = []
        
        # Totals
        self._realized_pnl = 0.0
        self._total_commission = 0.0
    
    def create_order(self, order: Order) -> OrderResult:
        """Execute order with simulated fill."""
        order_id = order.client_order_id or str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Get current price (from metadata or default)
        market_price = order.metadata.get("current_price", 100.0)
        
        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = market_price * (1 + self.slippage_pct)
        else:
            fill_price = market_price * (1 - self.slippage_pct)
        
        # Check if order can be filled
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and order.limit_price:
                if fill_price > order.limit_price:
                    # Limit not hit
                    result = OrderResult(
                        order_id=order_id,
                        symbol=order.symbol,
                        side=order.side,
                        status=OrderStatus.PENDING,
                        timestamp=timestamp,
                        message="Limit price not reached",
                    )
                    self._orders[order_id] = result
                    self._pending_orders[order_id] = order
                    return result
        
        # Calculate cost/proceeds
        total_value = order.quantity * fill_price
        commission = self.commission_per_trade
        
        # Validate buy order
        if order.side == OrderSide.BUY:
            required_cash = total_value + commission
            if required_cash > self.cash:
                return OrderResult(
                    order_id=order_id,
                    symbol=order.symbol,
                    side=order.side,
                    status=OrderStatus.REJECTED,
                    timestamp=timestamp,
                    message=f"Insufficient cash: need ${required_cash:.2f}, have ${self.cash:.2f}",
                )
            
            # Execute buy
            self.cash -= required_cash
            self._update_position_buy(order.symbol, order.quantity, fill_price)
            
        else:  # SELL
            position = self._positions.get(order.symbol)
            if not position or position.quantity < order.quantity:
                return OrderResult(
                    order_id=order_id,
                    symbol=order.symbol,
                    side=order.side,
                    status=OrderStatus.REJECTED,
                    timestamp=timestamp,
                    message=f"Insufficient shares to sell",
                )
            
            # Execute sell
            pnl = self._update_position_sell(order.symbol, order.quantity, fill_price)
            self.cash += total_value - commission
            self._realized_pnl += pnl
        
        self._total_commission += commission
        
        # Create result
        result = OrderResult(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            status=OrderStatus.FILLED,
            filled_qty=order.quantity,
            filled_price=round(fill_price, 4),
            commission=commission,
            timestamp=timestamp,
            message="Order filled",
            metadata=order.metadata,
        )
        
        self._orders[order_id] = result
        
        # Record trade
        trade = TradeRecord(
            trade_id=str(uuid.uuid4())[:8],
            order_id=order_id,
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            timestamp=timestamp,
            pnl=pnl if order.side == OrderSide.SELL else 0.0,
            metadata=order.metadata,
        )
        self._trade_journal.append(trade)
        
        logger.info(
            f"PAPER {order.side.value.upper()} {order.symbol}: "
            f"{order.quantity} @ ${fill_price:.2f}"
        )
        
        return result
    
    def _update_position_buy(
        self,
        symbol: str,
        quantity: int,
        price: float
    ) -> None:
        """Update position after buy."""
        if symbol in self._positions:
            pos = self._positions[symbol]
            total_qty = pos.quantity + quantity
            total_cost = (pos.quantity * pos.avg_entry_price) + (quantity * price)
            new_avg = total_cost / total_qty
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=total_qty,
                avg_entry_price=new_avg,
                current_price=price,
            )
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=price,
                current_price=price,
            )
    
    def _update_position_sell(
        self,
        symbol: str,
        quantity: int,
        price: float
    ) -> float:
        """Update position after sell. Returns realized PnL."""
        pos = self._positions[symbol]
        pnl = quantity * (price - pos.avg_entry_price)
        
        new_qty = pos.quantity - quantity
        if new_qty <= 0:
            del self._positions[symbol]
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=new_qty,
                avg_entry_price=pos.avg_entry_price,
                current_price=price,
                realized_pnl=pos.realized_pnl + pnl,
            )
        
        return pnl
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        if order_id in self._pending_orders:
            del self._pending_orders[order_id]
            if order_id in self._orders:
                self._orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    def get_open_orders(self) -> List[OrderResult]:
        """Get pending orders."""
        return [
            self._orders[oid]
            for oid in self._pending_orders
            if oid in self._orders
        ]
    
    def get_positions(self) -> List[Position]:
        """Get all positions."""
        return list(self._positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        return self._positions.get(symbol)
    
    def get_account(self) -> AccountInfo:
        """Get account summary."""
        positions_value = sum(
            p.quantity * p.current_price
            for p in self._positions.values()
        )
        equity = self.cash + positions_value
        
        return AccountInfo(
            cash=round(self.cash, 2),
            equity=round(equity, 2),
            buying_power=round(self.cash, 2),
            positions_value=round(positions_value, 2),
            unrealized_pnl=round(
                sum(p.unrealized_pnl for p in self._positions.values()), 2
            ),
            realized_pnl=round(self._realized_pnl, 2),
        )
    
    def get_cash(self) -> float:
        """Get available cash."""
        return self.cash
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices for positions."""
        for symbol, price in prices.items():
            if symbol in self._positions:
                pos = self._positions[symbol]
                unrealized = pos.quantity * (price - pos.avg_entry_price)
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=pos.quantity,
                    avg_entry_price=pos.avg_entry_price,
                    current_price=price,
                    unrealized_pnl=unrealized,
                    realized_pnl=pos.realized_pnl,
                )
    
    def get_trade_journal(self) -> List[TradeRecord]:
        """Get all trade records."""
        return self._trade_journal
    
    def export_journal(self, path: Optional[str] = None) -> str:
        """Export trade journal to JSON."""
        export_path = path or self.journal_path or "paper_trades.json"
        
        data = {
            "starting_cash": self.starting_cash,
            "ending_cash": self.cash,
            "realized_pnl": self._realized_pnl,
            "total_commission": self._total_commission,
            "trade_count": len(self._trade_journal),
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "order_id": t.order_id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "quantity": t.quantity,
                    "price": t.price,
                    "commission": t.commission,
                    "timestamp": t.timestamp,
                    "pnl": t.pnl,
                }
                for t in self._trade_journal
            ],
        }
        
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Trade journal exported to {export_path}")
        return export_path
    
    def reset(self) -> None:
        """Reset broker to initial state."""
        self.cash = self.starting_cash
        self._positions.clear()
        self._orders.clear()
        self._pending_orders.clear()
        self._trade_journal.clear()
        self._realized_pnl = 0.0
        self._total_commission = 0.0
