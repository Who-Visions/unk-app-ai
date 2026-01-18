"""
Gemini Crypto Exchange Integration via robin_stocks
=====================================================
Gemini exchange for crypto trading.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import robin_stocks.gemini as gem
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    gem = None


@dataclass
class GeminiOrder:
    """Gemini order."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    status: str


class GeminiBroker:
    """
    Gemini crypto exchange via robin_stocks.
    
    Setup:
    1. Get API key from Gemini exchange
    2. Set GEMINI_API_KEY and GEMINI_SECRET env vars
    
    Usage:
        broker = GeminiBroker()
        broker.login()
        price = broker.get_price("btcusd")
    """
    
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ImportError("robin_stocks not installed. Run: pip install robin_stocks")
        
        self.logged_in = False
    
    def login(
        self,
        api_key: str = None,
        api_secret: str = None,
    ) -> bool:
        """
        Login to Gemini.
        
        Args:
            api_key: Gemini API key (or GEMINI_EXCHANGE_KEY env var)
            api_secret: Gemini API secret (or GEMINI_EXCHANGE_SECRET env var)
        """
        api_key = api_key or os.getenv("GEMINI_EXCHANGE_KEY")
        api_secret = api_secret or os.getenv("GEMINI_EXCHANGE_SECRET")
        
        if not api_key or not api_secret:
            raise ValueError("API key and secret required")
        
        try:
            gem.login(api_key=api_key, api_secret=api_secret)
            self.logged_in = True
            logger.info("Logged into Gemini")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _ensure_login(self):
        if not self.logged_in:
            raise RuntimeError("Not logged in")
    
    # ==================== Market Data ====================
    
    def get_symbols(self) -> List[str]:
        """Get all trading symbols."""
        return gem.get_symbols()
    
    def get_symbol_details(self, symbol: str) -> Dict:
        """Get symbol details (min/max order sizes, etc.)."""
        return gem.get_symbol_details(symbol)
    
    def get_price(self, symbol: str) -> Dict:
        """Get current price."""
        return gem.get_price(symbol)
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker info (bid, ask, last, volume)."""
        return gem.get_ticker(symbol)
    
    def get_pubticker(self, symbol: str) -> Dict:
        """Get public ticker."""
        return gem.get_pubticker(symbol)
    
    # ==================== Account ====================
    
    def get_balances(self) -> List[Dict]:
        """Get available balances."""
        self._ensure_login()
        return gem.check_available_balances()
    
    def get_notional_balances(self) -> Dict:
        """Get notional (USD) balances."""
        self._ensure_login()
        return gem.check_notional_balances()
    
    def get_account_detail(self) -> Dict:
        """Get account details."""
        self._ensure_login()
        return gem.get_account_detail()
    
    def get_transfers(self) -> List[Dict]:
        """Get transfer history."""
        self._ensure_login()
        return gem.check_transfers()
    
    # ==================== Orders ====================
    
    def place_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        price: float,
    ) -> Optional[Dict]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair (e.g., "btcusd")
            side: "buy" or "sell"
            quantity: Amount to buy/sell
            price: Limit price
        """
        self._ensure_login()
        return gem.order(symbol, side, quantity, price)
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Optional[Dict]:
        """Place a market order."""
        self._ensure_login()
        return gem.order_market(symbol, side, quantity)
    
    def get_active_orders(self) -> List[Dict]:
        """Get all active orders."""
        self._ensure_login()
        return gem.active_orders()
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status."""
        self._ensure_login()
        return gem.order_status(order_id)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        self._ensure_login()
        try:
            gem.cancel_order(order_id)
            return True
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """Cancel all active orders."""
        self._ensure_login()
        try:
            gem.cancel_all_active_orders()
            return True
        except Exception as e:
            logger.error(f"Cancel all failed: {e}")
            return False
    
    def get_trades(self, symbol: str) -> List[Dict]:
        """Get trade history for symbol."""
        self._ensure_login()
        return gem.get_trades_for_crypto(symbol)
    
    # ==================== Withdrawals ====================
    
    def get_deposit_addresses(self, network: str) -> Dict:
        """Get deposit addresses."""
        self._ensure_login()
        return gem.get_deposit_addresses(network)
    
    def withdraw(
        self,
        currency: str,
        address: str,
        amount: float,
    ) -> Optional[Dict]:
        """Withdraw crypto to external address."""
        self._ensure_login()
        return gem.withdraw_crypto_funds(currency, address, amount)
    
    # ==================== Volume ====================
    
    def get_trade_volume(self) -> Dict:
        """Get 30-day trade volume."""
        self._ensure_login()
        return gem.get_trade_volume()
    
    def get_notional_volume(self) -> Dict:
        """Get notional volume."""
        self._ensure_login()
        return gem.get_notional_volume()


def create_gemini_broker() -> GeminiBroker:
    """Create Gemini broker."""
    return GeminiBroker()


GEMINI_SETUP = """
## Gemini Exchange Setup (via robin_stocks)

### Install
```bash
pip install robin_stocks
```

### Get API Credentials
1. Go to exchange.gemini.com
2. Settings -> API -> Create API Key
3. Enable trading permissions
4. Save API key and secret

### Environment Variables
```bash
set GEMINI_EXCHANGE_KEY=your_api_key
set GEMINI_EXCHANGE_SECRET=your_api_secret
```

### Usage
```python
from services.brokers import GeminiBroker

broker = GeminiBroker()
broker.login()

# Get BTC price
price = broker.get_price("btcusd")
print(f"BTC: ${price}")

# Get balances
balances = broker.get_balances()
for b in balances:
    print(f"{b['currency']}: {b['amount']}")

# Place order
order = broker.place_order("btcusd", "buy", 0.001, 50000)
```
"""
