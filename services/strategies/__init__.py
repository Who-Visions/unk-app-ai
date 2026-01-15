"""
Trading Strategies Package
==========================
Contains trading strategies from YouTube research.
"""

from .momentum_scanner import (
    MomentumStrategy,
    MomentumSignal,
    SetupQuality,
    create_momentum_strategy,
)

from .continuation_strategy import (
    ContinuationStrategy,
    ContinuationSignal,
    create_continuation_strategy,
)

from .reversal_strategy import (
    ReversalStrategy,
    ReversalSignal,
    ScaleLevel,
    create_reversal_strategy,
)

from .combined_manager import (
    CombinedStrategyManager,
    AccountType,
    PortfolioState,
    create_combined_manager,
)

from .support_resistance import (
    SupportResistanceStrategy,
    PriceZone,
    ZoneSignal,
    ZoneType,
    create_sr_strategy,
    SUPPORT_RESISTANCE_CHECKLIST,
)

from .pattern_scalp import (
    PatternScalpStrategy,
    OpeningRange,
    PatternScalpSignal,
    ReversalCandle,
    create_pattern_scalp,
    PATTERN_SCALP_CHECKLIST,
)

__all__ = [
    # Momentum (Ross Cameron)
    "MomentumStrategy",
    "MomentumSignal", 
    "SetupQuality",
    "create_momentum_strategy",
    # Continuation (Trey)
    "ContinuationStrategy",
    "ContinuationSignal",
    "create_continuation_strategy",
    # Reversal (Trey)
    "ReversalStrategy",
    "ReversalSignal",
    "ScaleLevel",
    "create_reversal_strategy",
    # Combined Manager
    "CombinedStrategyManager",
    "AccountType",
    "PortfolioState",
    "create_combined_manager",
    # Support/Resistance (2026 Strategy)
    "SupportResistanceStrategy",
    "PriceZone",
    "ZoneSignal",
    "ZoneType",
    "create_sr_strategy",
    "SUPPORT_RESISTANCE_CHECKLIST",
    # Pattern Scalp (Opening Range)
    "PatternScalpStrategy",
    "OpeningRange",
    "PatternScalpSignal",
    "ReversalCandle",
    "create_pattern_scalp",
    "PATTERN_SCALP_CHECKLIST",
]
