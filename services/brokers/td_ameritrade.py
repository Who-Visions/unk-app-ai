"""
TD Ameritrade Integration via robin_stocks
============================================
TD Ameritrade broker integration for stocks and options.

Note: TD Ameritrade merged with Schwab in 2023. This API may have limitations.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import robin_stocks.tda as tda
    TDA_AVAILABLE = True
except ImportError:
    TDA_AVAILABLE = False
    tda = None


@dataclass
class TDAOrder:
    """TD Ameritrade order."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    status: str


class TDAmeritradeBroker:
    """
    TD Ameritrade broker via robin_stocks.
    
    Supports stocks and options trading.
    
    Setup:
    1. Get API key from TD Ameritrade developer portal
    2. Set SCHWAB_CLIENT_ID and SCHWAB_REDIRECT_URI env vars
    3. Run first-time login to get tokens
    
    Usage:
        broker = TDAmeritradeBroker()
        broker.login()
        quote = broker.get_quote("AAPL")
    """
    
    def __init__(self):
        if not TDA_AVAILABLE:
            raise ImportError("robin_stocks not installed. Run: pip install robin_stocks")
        
        self.logged_in = False
        self.account_id: Optional[str] = None
    
    def login_first_time(
        self,
        client_id: str = None,
        redirect_uri: str = None,
        credentials_path: str = "tda_credentials.pkl",
    ) -> bool:
        """
        First-time login - opens browser for OAuth.
        
        Args:
            client_id: API client ID (or SCHWAB_CLIENT_ID env var)
            redirect_uri: OAuth redirect URI (or SCHWAB_REDIRECT_URI env var)
            credentials_path: Path to store credentials
        """
        client_id = client_id or os.getenv("SCHWAB_CLIENT_ID")
        redirect_uri = redirect_uri or os.getenv("SCHWAB_REDIRECT_URI")
        
        if not client_id or not redirect_uri:
            raise ValueError("Client ID and redirect URI required")
        
        try:
            tda.login_first_time(
                client_id=client_id,
                redirect_uri=redirect_uri,
                credentials_path=credentials_path,
            )
            self.logged_in = True
            return True
        except Exception as e:
            logger.error(f"First-time login failed: {e}")
            return False
    
    def login(
        self,
        client_id: str = None,
        redirect_uri: str = None,
        credentials_path: str = "tda_credentials.pkl",
        passcode: str = None,
    ) -> bool:
        """
        Login with existing credentials.
        """
        client_id = client_id or os.getenv("SCHWAB_CLIENT_ID")
        redirect_uri = redirect_uri or os.getenv("SCHWAB_REDIRECT_URI")
        passcode = passcode or os.getenv("TDA_PASSCODE")
        
        try:
            tda.login(
                client_id=client_id,
                redirect_uri=redirect_uri,
                credentials_path=credentials_path,
                encryption_passcode=passcode,
            )
            self.logged_in = True
            logger.info("Logged into TD Ameritrade")
            return True
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _ensure_login(self):
        if not self.logged_in:
            raise RuntimeError("Not logged in")
    
    # ==================== Quotes ====================
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get stock quote."""
        self._ensure_login()
        return tda.get_quote(symbol)
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get multiple quotes."""
        self._ensure_login()
        return tda.get_quotes(symbols)
    
    def get_price_history(
        self,
        symbol: str,
        period_type: str = "day",
        period: int = 10,
        frequency_type: str = "minute",
        frequency: int = 1,
    ) -> Dict:
        """Get historical prices."""
        self._ensure_login()
        return tda.get_price_history(
            symbol,
            period_type=period_type,
            period=period,
            frequency_type=frequency_type,
            frequency=frequency,
        )
    
    # ==================== Account ====================
    
    def get_accounts(self) -> List[Dict]:
        """Get all accounts."""
        self._ensure_login()
        return tda.get_accounts()
    
    def get_account(self, account_id: str = None) -> Dict:
        """Get specific account."""
        self._ensure_login()
        account_id = account_id or self.account_id
        return tda.get_account(account_id)
    
    def get_transactions(self, account_id: str = None) -> List[Dict]:
        """Get transactions."""
        self._ensure_login()
        account_id = account_id or self.account_id
        return tda.get_transactions(account_id)
    
    # ==================== Orders ====================
    
    def place_order(
        self,
        account_id: str,
        order_spec: Dict,
    ) -> Optional[Dict]:
        """Place an order with full order spec."""
        self._ensure_login()
        return tda.place_order(account_id, order_spec)
    
    def get_orders(self, account_id: str = None) -> List[Dict]:
        """Get orders for account."""
        self._ensure_login()
        account_id = account_id or self.account_id
        return tda.get_orders_for_account(account_id)
    
    def cancel_order(self, account_id: str, order_id: str) -> bool:
        """Cancel an order."""
        self._ensure_login()
        try:
            tda.cancel_order(account_id, order_id)
            return True
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
            return False
    
    # ==================== Options ====================
    
    def get_option_chains(
        self,
        symbol: str,
        strike_count: int = 10,
    ) -> Dict:
        """Get option chains."""
        self._ensure_login()
        return tda.get_option_chains(symbol, strike_count=strike_count)
    
    # ==================== Market Info ====================
    
    def get_movers(self, index: str = "$SPX.X", direction: str = "up") -> List[Dict]:
        """Get top movers."""
        self._ensure_login()
        return tda.get_movers(index, direction=direction)
    
    def get_market_hours(self, market: str = "EQUITY") -> Dict:
        """Get market hours."""
        self._ensure_login()
        return tda.get_hours_for_market(market)


def create_tda_broker() -> TDAmeritradeBroker:
    """Create TD Ameritrade broker."""
    return TDAmeritradeBroker()


TDA_SETUP = """
## TD Ameritrade Setup (via robin_stocks)

### Install
```bash
pip install robin_stocks
```

### Get API Credentials
1. Go to developer.tdameritrade.com
2. Create an app to get Client ID
3. Set redirect URI (e.g., https://localhost)

### First-Time Login
```python
from services.brokers import TDAmeritradeBroker

broker = TDAmeritradeBroker()
broker.login_first_time(
    client_id="YOUR_CLIENT_ID",
    redirect_uri="https://localhost",
)
# This opens browser for OAuth
```

### Subsequent Logins
```python
broker = TDAmeritradeBroker()
broker.login()  # Uses saved credentials
```

### Note
TD Ameritrade merged with Schwab in 2023.
Some API features may have changed.
"""
