"""
Execution Client Interface
==========================
Abstract interface for order execution (paper or live).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order request."""
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "day"
    client_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderResult:
    """Result of order execution."""
    order_id: str
    symbol: str
    side: OrderSide
    status: OrderStatus
    filled_qty: int = 0
    filled_price: float = 0.0
    commission: float = 0.0
    timestamp: str = ""
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED
    
    @property
    def total_cost(self) -> float:
        return (self.filled_qty * self.filled_price) + self.commission


@dataclass
class Position:
    """Current position in a security."""
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_entry_price


@dataclass
class AccountInfo:
    """Account information."""
    cash: float
    equity: float
    buying_power: float
    positions_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class ExecutionClient(ABC):
    """
    Abstract execution client interface.
    
    Implementations:
    - PaperBroker: Simulated execution for testing
    - AlpacaBroker: Real execution via Alpaca API
    """
    
    @abstractmethod
    def create_order(self, order: Order) -> OrderResult:
        """Submit an order for execution."""
        raise NotImplementedError
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        raise NotImplementedError
    
    @abstractmethod
    def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order status by ID."""
        raise NotImplementedError
    
    @abstractmethod
    def get_open_orders(self) -> List[OrderResult]:
        """Get all open/pending orders."""
        raise NotImplementedError
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get all current positions."""
        raise NotImplementedError
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        raise NotImplementedError
    
    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Get account information."""
        raise NotImplementedError
    
    @abstractmethod
    def get_cash(self) -> float:
        """Get available cash."""
        raise NotImplementedError
