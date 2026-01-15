"""
Robinhood Broker Integration
============================
Uses `robin_stocks` library for Robinhood API access.

IMPORTANT: This uses the unofficial API. Robinhood may change it without warning.
For crypto trading, consider the official Robinhood Crypto API instead.

Setup:
1. pip install robin_stocks pyotp
2. Enable 2FA on Robinhood (use authenticator app, not SMS)
3. Get your TOTP secret from Robinhood settings
4. Set environment variables: ROBINHOOD_USER, ROBINHOOD_PASS, ROBINHOOD_TOTP

Note: As of 2025, Robinhood authentication has become stricter.
You may need to handle in-app confirmation popups manually.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing robin_stocks
try:
    import robin_stocks.robinhood as rh
    ROBIN_STOCKS_AVAILABLE = True
except ImportError:
    ROBIN_STOCKS_AVAILABLE = False
    rh = None

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    pyotp = None


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(Enum):
    GFD = "gfd"  # Good for day
    GTC = "gtc"  # Good til cancelled
    IOC = "ioc"  # Immediate or cancel
    OPG = "opg"  # Market on open


@dataclass
class RobinhoodOrder:
    """Order result from Robinhood."""
    order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    created_at: str
    
    # Filled details
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    
    @property
    def is_filled(self) -> bool:
        return self.status == "filled"
    
    @property
    def is_pending(self) -> bool:
        return self.status in ["queued", "confirmed", "pending"]


@dataclass 
class RobinhoodPosition:
    """Current position in a stock."""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    equity: float
    percent_change: float
    
    @property
    def pnl(self) -> float:
        return (self.current_price - self.average_cost) * self.quantity


class RobinhoodBroker:
    """
    Robinhood broker integration using robin_stocks.
    
    Features:
    - Login with 2FA (TOTP)
    - Get account info and positions
    - Place market/limit/stop orders
    - Get real-time quotes
    - Get historical data
    
    Usage:
        broker = RobinhoodBroker()
        broker.login()
        
        # Get quote
        quote = broker.get_quote("AAPL")
        
        # Buy stock
        order = broker.buy("AAPL", quantity=1, order_type="market")
        
        # Sell stock
        order = broker.sell("AAPL", quantity=1, limit_price=150.0)
    """
    
    def __init__(
        self,
        username: str = None,
        password: str = None,
        totp_secret: str = None,
    ):
        """
        Initialize Robinhood broker.
        
        Args:
            username: Robinhood email (or ROBINHOOD_USER env var)
            password: Robinhood password (or ROBINHOOD_PASS env var)
            totp_secret: TOTP secret for 2FA (or ROBINHOOD_TOTP env var)
        """
        if not ROBIN_STOCKS_AVAILABLE:
            raise ImportError(
                "robin_stocks not installed. Run: pip install robin_stocks pyotp"
            )
        
        self.username = username or os.getenv("ROBINHOOD_USER")
        self.password = password or os.getenv("ROBINHOOD_PASS")
        self.totp_secret = totp_secret or os.getenv("ROBINHOOD_TOTP")
        
        self.logged_in = False
        self.account_info: Dict[str, Any] = {}
    
    def login(self, store_session: bool = True) -> bool:
        """
        Login to Robinhood with 2FA.
        
        Args:
            store_session: Store session for faster re-login
            
        Returns:
            True if login successful
        """
        if not self.username or not self.password:
            raise ValueError(
                "Username and password required. "
                "Set ROBINHOOD_USER and ROBINHOOD_PASS environment variables."
            )
        
        try:
            # Generate TOTP code if secret provided
            mfa_code = None
            if self.totp_secret and PYOTP_AVAILABLE:
                totp = pyotp.TOTP(self.totp_secret)
                mfa_code = totp.now()
                logger.info(f"Generated TOTP code: {mfa_code[:2]}****")
            
            # Login
            login_result = rh.login(
                username=self.username,
                password=self.password,
                mfa_code=mfa_code,
                store_session=store_session,
            )
            
            if login_result:
                self.logged_in = True
                logger.info("Successfully logged into Robinhood")
                return True
            else:
                logger.error("Login failed - check credentials")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def logout(self) -> None:
        """Logout from Robinhood."""
        if ROBIN_STOCKS_AVAILABLE:
            rh.logout()
            self.logged_in = False
            logger.info("Logged out of Robinhood")
    
    def _ensure_logged_in(self) -> None:
        """Ensure we're logged in before API calls."""
        if not self.logged_in:
            raise RuntimeError("Not logged in. Call login() first.")
    
    # ==================== Account Info ====================
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        self._ensure_logged_in()
        
        profile = rh.profiles.load_account_profile()
        portfolio = rh.profiles.load_portfolio_profile()
        
        self.account_info = {
            "buying_power": float(profile.get("buying_power", 0)),
            "cash": float(profile.get("cash", 0)),
            "portfolio_value": float(portfolio.get("equity", 0)),
            "market_value": float(portfolio.get("market_value", 0)),
            "account_type": profile.get("type", "unknown"),
            "is_gold": profile.get("is_gold", False),
        }
        
        return self.account_info
    
    def get_buying_power(self) -> float:
        """Get available buying power."""
        self._ensure_logged_in()
        profile = rh.profiles.load_account_profile()
        return float(profile.get("buying_power", 0))
    
    def get_positions(self) -> List[RobinhoodPosition]:
        """Get all current positions."""
        self._ensure_logged_in()
        
        positions = []
        holdings = rh.account.build_holdings()
        
        for symbol, data in holdings.items():
            positions.append(RobinhoodPosition(
                symbol=symbol,
                quantity=float(data.get("quantity", 0)),
                average_cost=float(data.get("average_buy_price", 0)),
                current_price=float(data.get("price", 0)),
                equity=float(data.get("equity", 0)),
                percent_change=float(data.get("percent_change", 0)),
            ))
        
        return positions
    
    # ==================== Market Data ====================
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol.
        
        Returns:
            Dict with bid, ask, last_price, etc.
        """
        self._ensure_logged_in()
        
        quote = rh.stocks.get_stock_quote_by_symbol(symbol)
        
        return {
            "symbol": symbol,
            "last_price": float(quote.get("last_trade_price", 0)),
            "bid_price": float(quote.get("bid_price", 0)),
            "ask_price": float(quote.get("ask_price", 0)),
            "bid_size": int(quote.get("bid_size", 0)),
            "ask_size": int(quote.get("ask_size", 0)),
            "previous_close": float(quote.get("previous_close", 0)),
            "updated_at": quote.get("updated_at", ""),
        }
    
    def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get quotes for multiple symbols."""
        self._ensure_logged_in()
        
        quotes = rh.stocks.get_stock_quote_by_symbol(symbols)
        results = []
        
        for i, quote in enumerate(quotes):
            results.append({
                "symbol": symbols[i],
                "last_price": float(quote.get("last_trade_price", 0)),
                "bid_price": float(quote.get("bid_price", 0)),
                "ask_price": float(quote.get("ask_price", 0)),
            })
        
        return results
    
    def get_historical(
        self,
        symbol: str,
        interval: str = "day",  # 5minute, 10minute, hour, day, week
        span: str = "year",      # day, week, month, 3month, year, 5year
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data.
        
        Args:
            symbol: Stock symbol
            interval: Candle interval (5minute, 10minute, hour, day, week)
            span: Time span (day, week, month, 3month, year, 5year)
            
        Returns:
            List of OHLCV candles
        """
        self._ensure_logged_in()
        
        historicals = rh.stocks.get_stock_historicals(
            symbol,
            interval=interval,
            span=span,
        )
        
        candles = []
        for h in historicals:
            candles.append({
                "timestamp": h.get("begins_at", ""),
                "open": float(h.get("open_price", 0)),
                "high": float(h.get("high_price", 0)),
                "low": float(h.get("low_price", 0)),
                "close": float(h.get("close_price", 0)),
                "volume": int(h.get("volume", 0)),
            })
        
        return candles
    
    # ==================== Orders ====================
    
    def buy(
        self,
        symbol: str,
        quantity: float = None,
        amount_in_dollars: float = None,
        limit_price: float = None,
        stop_price: float = None,
        time_in_force: str = "gfd",
    ) -> Optional[RobinhoodOrder]:
        """
        Place a buy order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (or use amount_in_dollars)
            amount_in_dollars: Dollar amount to buy
            limit_price: Limit price (for limit/stop-limit orders)
            stop_price: Stop price (for stop/stop-limit orders)
            time_in_force: Order duration (gfd, gtc, ioc, opg)
            
        Returns:
            RobinhoodOrder if successful
        """
        self._ensure_logged_in()
        
        try:
            if amount_in_dollars:
                # Fractional shares by dollar amount
                result = rh.orders.order_buy_fractional_by_price(
                    symbol,
                    amount_in_dollars,
                    timeInForce=time_in_force,
                )
            elif limit_price and stop_price:
                result = rh.orders.order_buy_stop_limit(
                    symbol,
                    quantity,
                    limit_price,
                    stop_price,
                    timeInForce=time_in_force,
                )
            elif limit_price:
                result = rh.orders.order_buy_limit(
                    symbol,
                    quantity,
                    limit_price,
                    timeInForce=time_in_force,
                )
            elif stop_price:
                result = rh.orders.order_buy_stop_loss(
                    symbol,
                    quantity,
                    stop_price,
                    timeInForce=time_in_force,
                )
            else:
                result = rh.orders.order_buy_market(
                    symbol,
                    quantity,
                    timeInForce=time_in_force,
                )
            
            if result and "id" in result:
                return RobinhoodOrder(
                    order_id=result["id"],
                    symbol=symbol,
                    side="buy",
                    order_type=self._determine_order_type(limit_price, stop_price),
                    quantity=quantity or 0,
                    price=limit_price,
                    status=result.get("state", "unknown"),
                    created_at=result.get("created_at", ""),
                )
            
            logger.error(f"Buy order failed: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Buy order error: {e}")
            return None
    
    def sell(
        self,
        symbol: str,
        quantity: float = None,
        amount_in_dollars: float = None,
        limit_price: float = None,
        stop_price: float = None,
        time_in_force: str = "gfd",
    ) -> Optional[RobinhoodOrder]:
        """
        Place a sell order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (or use amount_in_dollars)
            amount_in_dollars: Dollar amount to sell
            limit_price: Limit price (for limit/stop-limit orders)
            stop_price: Stop price (for stop/stop-limit orders)
            time_in_force: Order duration (gfd, gtc, ioc, opg)
            
        Returns:
            RobinhoodOrder if successful
        """
        self._ensure_logged_in()
        
        try:
            if amount_in_dollars:
                result = rh.orders.order_sell_fractional_by_price(
                    symbol,
                    amount_in_dollars,
                    timeInForce=time_in_force,
                )
            elif limit_price and stop_price:
                result = rh.orders.order_sell_stop_limit(
                    symbol,
                    quantity,
                    limit_price,
                    stop_price,
                    timeInForce=time_in_force,
                )
            elif limit_price:
                result = rh.orders.order_sell_limit(
                    symbol,
                    quantity,
                    limit_price,
                    timeInForce=time_in_force,
                )
            elif stop_price:
                result = rh.orders.order_sell_stop_loss(
                    symbol,
                    quantity,
                    stop_price,
                    timeInForce=time_in_force,
                )
            else:
                result = rh.orders.order_sell_market(
                    symbol,
                    quantity,
                    timeInForce=time_in_force,
                )
            
            if result and "id" in result:
                return RobinhoodOrder(
                    order_id=result["id"],
                    symbol=symbol,
                    side="sell",
                    order_type=self._determine_order_type(limit_price, stop_price),
                    quantity=quantity or 0,
                    price=limit_price,
                    status=result.get("state", "unknown"),
                    created_at=result.get("created_at", ""),
                )
            
            logger.error(f"Sell order failed: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Sell order error: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        self._ensure_logged_in()
        
        try:
            result = rh.orders.cancel_stock_order(order_id)
            return result is not None
        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[RobinhoodOrder]:
        """Get order status by ID."""
        self._ensure_logged_in()
        
        try:
            order = rh.orders.get_stock_order_info(order_id)
            if order:
                return RobinhoodOrder(
                    order_id=order["id"],
                    symbol=order.get("symbol", ""),
                    side=order.get("side", ""),
                    order_type=order.get("type", ""),
                    quantity=float(order.get("quantity", 0)),
                    price=float(order.get("price", 0)) if order.get("price") else None,
                    status=order.get("state", ""),
                    created_at=order.get("created_at", ""),
                    filled_quantity=float(order.get("cumulative_quantity", 0)),
                    average_price=float(order.get("average_price", 0)) if order.get("average_price") else None,
                )
            return None
        except Exception as e:
            logger.error(f"Get order error: {e}")
            return None
    
    def get_open_orders(self) -> List[RobinhoodOrder]:
        """Get all open orders."""
        self._ensure_logged_in()
        
        orders = []
        open_orders = rh.orders.get_all_open_stock_orders()
        
        for order in open_orders:
            orders.append(RobinhoodOrder(
                order_id=order["id"],
                symbol=order.get("symbol", ""),
                side=order.get("side", ""),
                order_type=order.get("type", ""),
                quantity=float(order.get("quantity", 0)),
                price=float(order.get("price", 0)) if order.get("price") else None,
                status=order.get("state", ""),
                created_at=order.get("created_at", ""),
            ))
        
        return orders
    
    def _determine_order_type(
        self,
        limit_price: float = None,
        stop_price: float = None,
    ) -> str:
        """Determine order type from prices."""
        if limit_price and stop_price:
            return "stop_limit"
        elif limit_price:
            return "limit"
        elif stop_price:
            return "stop"
        return "market"


# Quick usage example
def create_robinhood_broker(
    username: str = None,
    password: str = None,
    totp_secret: str = None,
) -> RobinhoodBroker:
    """
    Create and login to Robinhood broker.
    
    Set these environment variables:
    - ROBINHOOD_USER: Your Robinhood email
    - ROBINHOOD_PASS: Your Robinhood password
    - ROBINHOOD_TOTP: Your 2FA TOTP secret (from authenticator setup)
    """
    broker = RobinhoodBroker(username, password, totp_secret)
    return broker


# Setup instructions
ROBINHOOD_SETUP = """
## Robinhood API Setup

### Step 1: Install Dependencies
```bash
pip install robin_stocks pyotp
```

### Step 2: Enable 2FA on Robinhood
1. Open Robinhood app
2. Go to Settings > Security
3. Enable Two-Factor Authentication
4. Choose "Authenticator App" (NOT SMS)
5. When shown the QR code, also get the "secret key" text
6. Save this secret key - you'll need it for ROBINHOOD_TOTP

### Step 3: Set Environment Variables
```bash
# Windows
set ROBINHOOD_USER=your_email@example.com
set ROBINHOOD_PASS=your_password
set ROBINHOOD_TOTP=your_totp_secret_key

# Linux/Mac
export ROBINHOOD_USER=your_email@example.com
export ROBINHOOD_PASS=your_password
export ROBINHOOD_TOTP=your_totp_secret_key
```

### Step 4: Test Connection
```python
from services.brokers.robinhood import RobinhoodBroker

broker = RobinhoodBroker()
if broker.login():
    print("Connected!")
    print(f"Buying Power: ${broker.get_buying_power():.2f}")
    
    # Get a quote
    quote = broker.get_quote("AAPL")
    print(f"AAPL: ${quote['last_price']}")
    
    # View positions
    for pos in broker.get_positions():
        print(f"{pos.symbol}: {pos.quantity} shares @ ${pos.average_cost:.2f}")
```

### Note on Authentication Issues
Robinhood has made authentication stricter in 2025. If you encounter issues:
1. Make sure you're using the latest robin_stocks from GitHub
2. Try logging in through the app first to clear any security flags
3. You may need to approve the login in the Robinhood app
"""
