"""
Robinhood Official Crypto Trading API
======================================
Official API for crypto trading on Robinhood (US only).

This uses Ed25519 signatures for authentication, not the unofficial robin_stocks.

Setup:
1. Go to Robinhood crypto account settings -> API credentials
2. Generate a keypair (public/private Ed25519)
3. Create API credentials with your public key
4. Store your private key securely (NEVER share it)

Environment Variables:
- ROBINHOOD_API_KEY: Your API key from Robinhood (e.g., rh-api-xxxx-xxxx)
- ROBINHOOD_PRIVATE_KEY: Your base64-encoded Ed25519 private key

Features:
- Get account info, holdings, orders
- Get market data (bid/ask, estimated price)
- Place market/limit/stop orders for crypto
- Cancel orders

Note: This is for CRYPTO only. For stocks, use robin_stocks or another method.
"""
from __future__ import annotations

import base64
import datetime
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing pynacl for Ed25519 signatures
try:
    from nacl.signing import SigningKey, VerifyKey
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    SigningKey = None
    VerifyKey = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class OrderState(Enum):
    OPEN = "open"
    CANCELED = "canceled"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    FAILED = "failed"
    PENDING = "pending"


class TimeInForce(Enum):
    GTC = "gtc"  # Good til cancelled


@dataclass
class CryptoHolding:
    """Crypto holding from Robinhood."""
    asset_code: str  # e.g., "BTC", "ETH"
    total_quantity: float
    available_quantity: float


@dataclass
class CryptoOrder:
    """Crypto order from Robinhood."""
    order_id: str
    account_number: str
    symbol: str  # e.g., "BTC-USD"
    client_order_id: str
    side: str
    order_type: str
    state: str
    
    # Pricing
    average_price: Optional[float] = None
    filled_quantity: float = 0.0
    
    # Fees (v2 only)
    fee_charged: Optional[float] = None
    estimated_fee_remaining: Optional[float] = None
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    
    @property
    def is_filled(self) -> bool:
        return self.state == "filled"
    
    @property
    def is_open(self) -> bool:
        return self.state == "open"


class RobinhoodCryptoAPI:
    """
    Official Robinhood Crypto Trading API Client.
    
    Features:
    - Ed25519 signature authentication
    - V1 and V2 API endpoints
    - Account info, holdings, orders
    - Market data (bid/ask, estimated prices)
    - Place/cancel crypto orders
    
    Usage:
        api = RobinhoodCryptoAPI()
        
        # Get account
        account = api.get_account()
        print(f"Buying Power: {account['buying_power']}")
        
        # Get BTC price
        price = api.get_best_bid_ask("BTC-USD")
        
        # Place market buy
        order = api.place_market_order("BTC-USD", "buy", asset_quantity=0.001)
    """
    
    BASE_URL = "https://trading.robinhood.com"
    
    def __init__(
        self,
        api_key: str = None,
        private_key_base64: str = None,
        api_version: int = 1,
    ):
        """
        Initialize Robinhood Crypto API client.
        
        Args:
            api_key: Robinhood API key (or ROBINHOOD_API_KEY env var)
            private_key_base64: Base64 Ed25519 private key (or ROBINHOOD_PRIVATE_KEY env var)
            api_version: API version (1 or 2). V2 includes fee tiers.
        """
        if not NACL_AVAILABLE:
            raise ImportError("pynacl not installed. Run: pip install pynacl")
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests not installed. Run: pip install requests")
        
        self.api_key = api_key or os.getenv("ROBINHOOD_API_KEY")
        private_key_b64 = private_key_base64 or os.getenv("ROBINHOOD_PRIVATE_KEY")
        
        if not self.api_key or not private_key_b64:
            raise ValueError(
                "API key and private key required. "
                "Set ROBINHOOD_API_KEY and ROBINHOOD_PRIVATE_KEY environment variables."
            )
        
        # Load Ed25519 private key
        private_key_seed = base64.b64decode(private_key_b64)
        self.private_key = SigningKey(private_key_seed)
        
        self.api_version = api_version
        self.account_number: Optional[str] = None
    
    # ==================== Authentication ====================
    
    def _get_timestamp(self) -> int:
        """Get current Unix timestamp."""
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    
    def _sign_request(
        self,
        method: str,
        path: str,
        body: str,
        timestamp: int,
    ) -> Dict[str, str]:
        """
        Create signed headers for API request.
        
        Signature format: {api_key}{timestamp}{path}{method}{body}
        """
        message = f"{self.api_key}{timestamp}{path}{method}{body}"
        signed = self.private_key.sign(message.encode("utf-8"))
        
        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signed.signature).decode("utf-8"),
            "x-timestamp": str(timestamp),
            "Content-Type": "application/json; charset=utf-8",
        }
    
    def _request(
        self,
        method: str,
        path: str,
        body: Dict = None,
        timeout: int = 10,
    ) -> Any:
        """Make authenticated API request."""
        timestamp = self._get_timestamp()
        body_str = json.dumps(body) if body else ""
        
        headers = self._sign_request(method, path, body_str, timestamp)
        url = self.BASE_URL + path
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=timeout,
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Handle errors
            if response.status_code >= 400:
                logger.error(f"API error {response.status_code}: {response.text}")
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": response.text, "status_code": response.status_code}
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
    
    def _get_api_path(self, endpoint: str) -> str:
        """Get versioned API path."""
        return f"/api/v{self.api_version}/crypto/{endpoint}"
    
    # ==================== Account ====================
    
    def get_account(self) -> Dict[str, Any]:
        """
        Get crypto trading account details.
        
        Returns:
            account_number, status, buying_power, buying_power_currency
        """
        path = self._get_api_path("trading/accounts/")
        result = self._request("GET", path)
        
        # V2 returns paginated results
        if self.api_version == 2 and result and "results" in result:
            if result["results"]:
                account = result["results"][0]
                self.account_number = account.get("account_number")
                return account
        elif result:
            self.account_number = result.get("account_number")
        
        return result or {}
    
    def get_holdings(self, *asset_codes: str) -> List[CryptoHolding]:
        """
        Get crypto holdings.
        
        Args:
            asset_codes: Filter by asset codes (e.g., "BTC", "ETH")
            
        Returns:
            List of CryptoHolding
        """
        # Build query params
        params = []
        for code in asset_codes:
            params.append(f"asset_code={code.upper()}")
        
        if self.api_version == 2 and self.account_number:
            params.append(f"account_number={self.account_number}")
        
        query = "?" + "&".join(params) if params else ""
        path = self._get_api_path(f"trading/holdings/{query}")
        
        result = self._request("GET", path)
        holdings = []
        
        if result and "results" in result:
            for h in result["results"]:
                holdings.append(CryptoHolding(
                    asset_code=h.get("asset_code", ""),
                    total_quantity=float(h.get("quantity", 0)),
                    available_quantity=float(h.get("quantity_available", 0)),
                ))
        
        return holdings
    
    # ==================== Market Data ====================
    
    def get_trading_pairs(self, *symbols: str) -> List[Dict]:
        """
        Get available trading pairs.
        
        Args:
            symbols: Filter by symbols (e.g., "BTC-USD", "ETH-USD")
            
        Returns:
            List of trading pair info
        """
        params = []
        for sym in symbols:
            params.append(f"symbol={sym.upper()}")
        
        query = "?" + "&".join(params) if params else ""
        path = self._get_api_path(f"trading/trading_pairs/{query}")
        
        result = self._request("GET", path)
        
        if result and "results" in result:
            return result["results"]
        return []
    
    def get_best_bid_ask(self, *symbols: str) -> Dict[str, Dict]:
        """
        Get best bid/ask prices.
        
        Args:
            symbols: Trading pairs (e.g., "BTC-USD", "ETH-USD")
            
        Returns:
            Dict mapping symbol to {bid_price, ask_price, timestamp}
        """
        if not symbols:
            raise ValueError("At least one symbol required")
        
        params = "&".join([f"symbol={s.upper()}" for s in symbols])
        path = self._get_api_path(f"marketdata/best_bid_ask/?{params}")
        
        result = self._request("GET", path)
        prices = {}
        
        if result and "results" in result:
            for r in result["results"]:
                prices[r["symbol"]] = {
                    "bid_price": float(r.get("bid_inclusive_of_sell_spread", 0) or r.get("bid_price", 0)),
                    "ask_price": float(r.get("ask_inclusive_of_buy_spread", 0) or r.get("ask_price", 0)),
                    "timestamp": r.get("timestamp", ""),
                }
        
        return prices
    
    def get_estimated_price(
        self,
        symbol: str,
        side: str,  # "bid", "ask", or "both"
        quantity: str,  # Can be comma-separated: "0.1,1,1.999"
    ) -> List[Dict]:
        """
        Get estimated execution price for a quantity.
        
        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            side: "bid" (sell), "ask" (buy), or "both"
            quantity: Amount(s) to estimate
            
        Returns:
            List of price estimates
        """
        endpoint = "trading/estimated_price" if self.api_version == 2 else "marketdata/estimated_price"
        path = self._get_api_path(
            f"{endpoint}/?symbol={symbol.upper()}&side={side}&quantity={quantity}"
        )
        
        result = self._request("GET", path)
        
        if result and "results" in result:
            return result["results"]
        return []
    
    # ==================== Orders ====================
    
    def place_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        order_type: str,  # "market", "limit", "stop_loss", "stop_limit"
        asset_quantity: float = None,
        quote_amount: float = None,  # USD amount
        limit_price: float = None,
        stop_price: float = None,
        time_in_force: str = "gtc",
        client_order_id: str = None,
    ) -> Optional[CryptoOrder]:
        """
        Place a crypto order.
        
        Args:
            symbol: Trading pair (e.g., "BTC-USD")
            side: "buy" or "sell"
            order_type: "market", "limit", "stop_loss", "stop_limit"
            asset_quantity: Amount of crypto to buy/sell
            quote_amount: USD amount (alternative to asset_quantity)
            limit_price: Limit price (for limit/stop-limit orders)
            stop_price: Stop price (for stop-loss/stop-limit orders)
            time_in_force: Order duration (default "gtc")
            client_order_id: Unique order ID (auto-generated if not provided)
            
        Returns:
            CryptoOrder if successful
        """
        if not client_order_id:
            client_order_id = str(uuid.uuid4())
        
        # Build order config based on type
        order_config = {}
        if asset_quantity:
            order_config["asset_quantity"] = str(asset_quantity)
        elif quote_amount:
            order_config["quote_amount"] = str(quote_amount)
        
        if limit_price:
            order_config["limit_price"] = str(limit_price)
        if stop_price:
            order_config["stop_price"] = str(stop_price)
        if order_type in ["stop_loss", "stop_limit", "limit"]:
            order_config["time_in_force"] = time_in_force
        
        body = {
            "client_order_id": client_order_id,
            "side": side.lower(),
            "symbol": symbol.upper(),
            "type": order_type.lower(),
            f"{order_type.lower()}_order_config": order_config,
        }
        
        # V2 requires account_number in query params
        if self.api_version == 2:
            if not self.account_number:
                self.get_account()  # Fetch account number
            path = self._get_api_path(f"trading/orders/?account_number={self.account_number}")
        else:
            path = self._get_api_path("trading/orders/")
        
        result = self._request("POST", path, body)
        
        if result and "id" in result:
            return CryptoOrder(
                order_id=result["id"],
                account_number=result.get("account_number", ""),
                symbol=result.get("symbol", symbol),
                client_order_id=result.get("client_order_id", client_order_id),
                side=result.get("side", side),
                order_type=result.get("type", order_type),
                state=result.get("state", "pending"),
                average_price=float(result["average_price"]) if result.get("average_price") else None,
                filled_quantity=float(result.get("filled_asset_quantity", 0)),
                fee_charged=float(result["fee_charged"]) if result.get("fee_charged") else None,
                created_at=result.get("created_at", ""),
                updated_at=result.get("updated_at", ""),
            )
        
        logger.error(f"Order failed: {result}")
        return None
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        asset_quantity: float = None,
        quote_amount: float = None,
    ) -> Optional[CryptoOrder]:
        """Place a market order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="market",
            asset_quantity=asset_quantity,
            quote_amount=quote_amount,
        )
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        limit_price: float,
        asset_quantity: float = None,
        quote_amount: float = None,
        time_in_force: str = "gtc",
    ) -> Optional[CryptoOrder]:
        """Place a limit order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="limit",
            asset_quantity=asset_quantity,
            quote_amount=quote_amount,
            limit_price=limit_price,
            time_in_force=time_in_force,
        )
    
    def place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        asset_quantity: float = None,
        quote_amount: float = None,
    ) -> Optional[CryptoOrder]:
        """Place a stop loss order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="stop_loss",
            asset_quantity=asset_quantity,
            quote_amount=quote_amount,
            stop_price=stop_price,
        )
    
    def get_orders(
        self,
        symbol: str = None,
        side: str = None,
        state: str = None,
    ) -> List[CryptoOrder]:
        """
        Get orders.
        
        Args:
            symbol: Filter by symbol
            side: Filter by side ("buy"/"sell")
            state: Filter by state ("open"/"filled"/"canceled")
        """
        params = []
        if symbol:
            params.append(f"symbol={symbol.upper()}")
        if side:
            params.append(f"side={side.lower()}")
        if state:
            params.append(f"state={state.lower()}")
        
        if self.api_version == 2:
            if not self.account_number:
                self.get_account()
            params.append(f"account_number={self.account_number}")
        
        query = "?" + "&".join(params) if params else ""
        path = self._get_api_path(f"trading/orders/{query}")
        
        result = self._request("GET", path)
        orders = []
        
        if result and "results" in result:
            for o in result["results"]:
                orders.append(CryptoOrder(
                    order_id=o["id"],
                    account_number=o.get("account_number", ""),
                    symbol=o.get("symbol", ""),
                    client_order_id=o.get("client_order_id", ""),
                    side=o.get("side", ""),
                    order_type=o.get("type", ""),
                    state=o.get("state", ""),
                    average_price=float(o["average_price"]) if o.get("average_price") else None,
                    filled_quantity=float(o.get("filled_asset_quantity", 0)),
                    created_at=o.get("created_at", ""),
                    updated_at=o.get("updated_at", ""),
                ))
        
        return orders
    
    def get_order(self, order_id: str) -> Optional[CryptoOrder]:
        """Get a specific order by ID."""
        if self.api_version == 2:
            if not self.account_number:
                self.get_account()
            path = self._get_api_path(
                f"trading/orders/{order_id}/?account_number={self.account_number}"
            )
        else:
            path = self._get_api_path(f"trading/orders/{order_id}/")
        
        result = self._request("GET", path)
        
        if result and "id" in result:
            return CryptoOrder(
                order_id=result["id"],
                account_number=result.get("account_number", ""),
                symbol=result.get("symbol", ""),
                client_order_id=result.get("client_order_id", ""),
                side=result.get("side", ""),
                order_type=result.get("type", ""),
                state=result.get("state", ""),
                average_price=float(result["average_price"]) if result.get("average_price") else None,
                filled_quantity=float(result.get("filled_asset_quantity", 0)),
                created_at=result.get("created_at", ""),
                updated_at=result.get("updated_at", ""),
            )
        return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        path = self._get_api_path(f"trading/orders/{order_id}/cancel/")
        result = self._request("POST", path)
        return result is not None


def generate_keypair() -> tuple[str, str]:
    """
    Generate Ed25519 keypair for Robinhood API.
    
    Returns:
        (private_key_base64, public_key_base64)
    
    Usage:
        private_key, public_key = generate_keypair()
        print(f"Public Key (paste in Robinhood): {public_key}")
        print(f"Private Key (keep SECRET): {private_key}")
    """
    if not NACL_AVAILABLE:
        raise ImportError("pynacl not installed. Run: pip install pynacl")
    
    import nacl.signing
    
    private_key = nacl.signing.SigningKey.generate()
    public_key = private_key.verify_key
    
    private_key_b64 = base64.b64encode(private_key.encode()).decode()
    public_key_b64 = base64.b64encode(public_key.encode()).decode()
    
    return private_key_b64, public_key_b64


# Setup instructions
ROBINHOOD_CRYPTO_SETUP = """
## Robinhood Official Crypto API Setup

### Step 1: Install Dependencies
```bash
pip install pynacl requests
```

### Step 2: Generate Key Pair
```python
from services.brokers.robinhood_crypto import generate_keypair

private_key, public_key = generate_keypair()
print(f"Public Key (paste in Robinhood): {public_key}")
print(f"Private Key (store securely): {private_key}")
```

### Step 3: Create API Credentials on Robinhood
1. Go to robinhood.com -> Crypto -> Settings -> API Credentials
2. Click "Create Credential"
3. Paste your PUBLIC key (from Step 2)
4. Copy the API key provided (e.g., rh-api-xxxx-xxxx)

### Step 4: Set Environment Variables
```bash
# Windows
set ROBINHOOD_API_KEY=rh-api-xxxx-xxxx-xxxx
set ROBINHOOD_PRIVATE_KEY=your_base64_private_key

# Linux/Mac
export ROBINHOOD_API_KEY=rh-api-xxxx-xxxx-xxxx
export ROBINHOOD_PRIVATE_KEY=your_base64_private_key
```

### Step 5: Test Connection
```python
from services.brokers.robinhood_crypto import RobinhoodCryptoAPI

api = RobinhoodCryptoAPI()

# Get account info
account = api.get_account()
print(f"Account: {account['account_number']}")
print(f"Buying Power: ${account['buying_power']}")

# Get BTC price
prices = api.get_best_bid_ask("BTC-USD")
print(f"BTC Bid: ${prices['BTC-USD']['bid_price']}")
print(f"BTC Ask: ${prices['BTC-USD']['ask_price']}")

# Get holdings
for holding in api.get_holdings():
    print(f"{holding.asset_code}: {holding.total_quantity}")
```

### Step 6: Place Orders
```python
# Market buy 0.001 BTC
order = api.place_market_order("BTC-USD", "buy", asset_quantity=0.001)

# Or buy $100 worth
order = api.place_market_order("BTC-USD", "buy", quote_amount=100)

# Limit order
order = api.place_limit_order("ETH-USD", "buy", limit_price=3000, asset_quantity=0.1)

# Check order status
order = api.get_order(order.order_id)
print(f"Order Status: {order.state}")
```

### Important Notes
- This is for CRYPTO ONLY (BTC, ETH, etc.)
- For STOCKS, you need the unofficial robin_stocks library
- Rate limit: 100 requests/minute (300 burst)
- Timestamps valid for 30 seconds only
- US customers only
"""


def create_crypto_api(api_version: int = 1) -> RobinhoodCryptoAPI:
    """Create Robinhood Crypto API client."""
    return RobinhoodCryptoAPI(api_version=api_version)
