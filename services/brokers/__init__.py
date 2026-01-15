"""
Broker Integrations Package
============================
Live broker connections for executing trades.

Available Brokers:
1. RobinhoodCryptoAPI - Official Robinhood Crypto API (recommended for crypto)
2. RobinhoodBroker - Unofficial robin_stocks (stocks, options, crypto)
3. PyrhBroker - Alternative unofficial pyrh library (stocks)
4. TDAmeritradeBroker - TD Ameritrade/Schwab via robin_stocks
5. GeminiBroker - Gemini crypto exchange via robin_stocks
"""

# ==================== Robinhood Official Crypto API ====================
from .robinhood_crypto import (
    RobinhoodCryptoAPI,
    CryptoOrder,
    CryptoHolding,
    generate_keypair,
    create_crypto_api,
    ROBINHOOD_CRYPTO_SETUP,
)

# ==================== Robinhood via robin_stocks ====================
from .robinhood import (
    RobinhoodBroker,
    RobinhoodOrder,
    RobinhoodPosition,
    OrderSide,
    OrderType,
    TimeInForce,
    create_robinhood_broker,
    ROBINHOOD_SETUP,
)

# ==================== Robinhood via pyrh ====================
from .pyrh_broker import (
    PyrhBroker,
    PyrhOrder,
    PyrhPosition,
    create_pyrh_broker,
    PYRH_SETUP,
)

# ==================== TD Ameritrade ====================
from .td_ameritrade import (
    TDAmeritradeBroker,
    TDAOrder,
    create_tda_broker,
    TDA_SETUP,
)

# ==================== Gemini Exchange ====================
from .gemini_exchange import (
    GeminiBroker,
    GeminiOrder,
    create_gemini_broker,
    GEMINI_SETUP,
)

__all__ = [
    # Official Robinhood Crypto API (recommended for crypto)
    "RobinhoodCryptoAPI",
    "CryptoOrder",
    "CryptoHolding",
    "generate_keypair",
    "create_crypto_api",
    "ROBINHOOD_CRYPTO_SETUP",
    # Robinhood via robin_stocks (stocks + options + crypto)
    "RobinhoodBroker",
    "RobinhoodOrder",
    "RobinhoodPosition",
    "OrderSide",
    "OrderType",
    "TimeInForce",
    "create_robinhood_broker",
    "ROBINHOOD_SETUP",
    # Robinhood via pyrh (simpler alternative)
    "PyrhBroker",
    "PyrhOrder",
    "PyrhPosition",
    "create_pyrh_broker",
    "PYRH_SETUP",
    # TD Ameritrade / Schwab
    "TDAmeritradeBroker",
    "TDAOrder",
    "create_tda_broker",
    "TDA_SETUP",
    # Gemini Exchange
    "GeminiBroker",
    "GeminiOrder",
    "create_gemini_broker",
    "GEMINI_SETUP",
]
