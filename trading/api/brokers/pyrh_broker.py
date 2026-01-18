"""
Pyrh Robinhood Integration
===========================
Alternative unofficial Robinhood library using pyrh.

This is simpler than robin_stocks but less actively maintained.
Supports stocks, options, and crypto.

Install: pip install pyrh
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Try importing pyrh
try:
    from pyrh import Robinhood
    PYRH_AVAILABLE = True
except ImportError:
    PYRH_AVAILABLE = False
    Robinhood = None


@dataclass
class PyrhOrder:
    """Order from pyrh."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    order_type: str
    state: str
    created_at: str


@dataclass
class PyrhPosition:
    """Position from pyrh."""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float


class PyrhBroker:
    """
    Robinhood broker using pyrh library.
    
    Simpler API than robin_stocks, good for basic trading.
    
    Usage:
        broker = PyrhBroker()
        broker.login("email", "password")
        
        # Get quote
        quote = broker.get_quote("AAPL")
        
        # Buy stock
        broker.buy("AAPL", quantity=1)
    """
    
    def __init__(self):
        if not PYRH_AVAILABLE:
            raise ImportError("pyrh not installed. Run: pip install pyrh")
        
        self.rh: Optional[Robinhood] = None
        self.logged_in = False
    
    def login(
        self,
        username: str = None,
        password: str = None,
        mfa_code: str = None,
    ) -> bool:
        """
        Login to Robinhood.
        
        Args:
            username: Email (or ROBINHOOD_USER env var)
            password: Password (or ROBINHOOD_PASS env var)
            mfa_code: Optional MFA code if 2FA enabled
        """
        username = username or os.getenv("ROBINHOOD_USER")
        password = password or os.getenv("ROBINHOOD_PASS")
        
        if not username or not password:
            raise ValueError("Username and password required")
        
        try:
            self.rh = Robinhood(username=username, password=password)
            
            if mfa_code:
                self.rh.login(mfa_code=mfa_code)
            else:
                self.rh.login()
            
            self.logged_in = True
            logger.info("Logged into Robinhood via pyrh")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def logout(self) -> None:
        """Logout."""
        if self.rh:
            self.rh.logout()
            self.logged_in = False
    
    def _ensure_login(self):
        if not self.logged_in or not self.rh:
            raise RuntimeError("Not logged in")
    
    # ==================== Quotes ====================
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote."""
        self._ensure_login()
        return self.rh.get_quote(symbol)
    
    def print_quote(self, symbol: str) -> None:
        """Print formatted quote."""
        self._ensure_login()
        self.rh.print_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get multiple quotes."""
        self._ensure_login()
        return [self.rh.get_quote(s) for s in symbols]
    
    # ==================== Account ====================
    
    def get_account(self) -> Dict[str, Any]:
        """Get account info."""
        self._ensure_login()
        return self.rh.get_account()
    
    def get_positions(self) -> List[PyrhPosition]:
        """Get current positions."""
        self._ensure_login()
        
        positions = []
        raw_positions = self.rh.positions()
        
        for pos in raw_positions.get("results", []):
            if float(pos.get("quantity", 0)) > 0:
                # Get instrument details
                instrument = self.rh.get_url(pos["instrument"])
                positions.append(PyrhPosition(
                    symbol=instrument.get("symbol", ""),
                    quantity=float(pos.get("quantity", 0)),
                    average_cost=float(pos.get("average_buy_price", 0)),
                    current_price=0,  # Would need separate quote call
                ))
        
        return positions
    
    # ==================== Orders ====================
    
    def buy(
        self,
        symbol: str,
        quantity: int,
        price: float = None,
    ) -> Optional[Dict]:
        """
        Buy stock.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price (None for market order)
        """
        self._ensure_login()
        
        if price:
            return self.rh.place_limit_buy_order(
                instrument_URL=self.rh.instruments(symbol)[0]["url"],
                symbol=symbol,
                quantity=quantity,
                price=price,
            )
        else:
            return self.rh.place_market_buy_order(
                instrument_URL=self.rh.instruments(symbol)[0]["url"],
                symbol=symbol,
                quantity=quantity,
            )
    
    def sell(
        self,
        symbol: str,
        quantity: int,
        price: float = None,
    ) -> Optional[Dict]:
        """
        Sell stock.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price (None for market order)
        """
        self._ensure_login()
        
        if price:
            return self.rh.place_limit_sell_order(
                instrument_URL=self.rh.instruments(symbol)[0]["url"],
                symbol=symbol,
                quantity=quantity,
                price=price,
            )
        else:
            return self.rh.place_market_sell_order(
                instrument_URL=self.rh.instruments(symbol)[0]["url"],
                symbol=symbol,
                quantity=quantity,
            )
    
    def get_orders(self) -> List[Dict]:
        """Get order history."""
        self._ensure_login()
        return self.rh.order_history().get("results", [])
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        self._ensure_login()
        try:
            self.rh.cancel_order(order_id)
            return True
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
            return False
    
    # ==================== Historical Data ====================
    
    def get_historical(
        self,
        symbol: str,
        interval: str = "day",
        span: str = "year",
    ) -> List[Dict]:
        """
        Get historical prices.
        
        Args:
            symbol: Stock symbol
            interval: 5minute, 10minute, hour, day, week
            span: day, week, month, 3month, year, 5year
        """
        self._ensure_login()
        return self.rh.get_historical_quotes(symbol, interval, span)
    
    # ==================== Crypto ====================
    
    def get_crypto_quote(self, symbol: str) -> Dict:
        """Get crypto quote (e.g., 'BTC')."""
        self._ensure_login()
        return self.rh.get_crypto_quote(symbol)
    
    def buy_crypto(
        self,
        symbol: str,
        quantity: float = None,
        amount_in_dollars: float = None,
    ) -> Optional[Dict]:
        """Buy crypto."""
        self._ensure_login()
        
        if amount_in_dollars:
            return self.rh.trade_crypto(
                symbol=symbol,
                side="buy",
                price_type="market",
                amount_in_dollars=amount_in_dollars,
            )
        elif quantity:
            return self.rh.trade_crypto(
                symbol=symbol,
                side="buy",
                price_type="market",
                quantity=quantity,
            )
        return None
    
    def sell_crypto(
        self,
        symbol: str,
        quantity: float = None,
        amount_in_dollars: float = None,
    ) -> Optional[Dict]:
        """Sell crypto."""
        self._ensure_login()
        
        if amount_in_dollars:
            return self.rh.trade_crypto(
                symbol=symbol,
                side="sell",
                price_type="market",
                amount_in_dollars=amount_in_dollars,
            )
        elif quantity:
            return self.rh.trade_crypto(
                symbol=symbol,
                side="sell",
                price_type="market",
                quantity=quantity,
            )
        return None


def create_pyrh_broker() -> PyrhBroker:
    """Create pyrh broker instance."""
    return PyrhBroker()


PYRH_SETUP = """
## Pyrh Setup (Alternative Unofficial Library)

### Install
```bash
pip install pyrh
```

### Usage
```python
from services.brokers import PyrhBroker

broker = PyrhBroker()
broker.login("your_email@example.com", "your_password")

# Get quote
broker.print_quote("AAPL")

# Buy stock
broker.buy("AAPL", quantity=1)

# Sell stock
broker.sell("AAPL", quantity=1)

# Get positions
for pos in broker.get_positions():
    print(f"{pos.symbol}: {pos.quantity} shares")
```

### Notes
- Simpler API than robin_stocks
- Less actively maintained
- May have 2FA issues similar to robin_stocks
- For crypto, consider the Official Crypto API instead
"""
