from __future__ import annotations

from .ace import AceStrategy
# Generated registry
from .alpha import AlphaStrategy
from .analyst import AnalystStrategy
from .architect import ArchitectStrategy
from .commissioner import CommissionerStrategy
from .executor import ExecutorStrategy
from .hustler import HustlerStrategy
from .oracle import OracleStrategy
from .pro import ProStrategy
from .quant import QuantStrategy
from .scalper import ScalperStrategy
from .shadow import ShadowStrategy
from .specialist import SpecialistStrategy
from .thehouse import TheHouseStrategy
from .thesyndicate import TheSyndicateStrategy

STRATEGY_REGISTRY = {
    "Alpha": AlphaStrategy,
    "Quant": QuantStrategy,
    "Specialist": SpecialistStrategy,
    "Pro": ProStrategy,
    "Analyst": AnalystStrategy,
    "Hustler": HustlerStrategy,
    "Oracle": OracleStrategy,
    "Ace": AceStrategy,
    "Shadow": ShadowStrategy,
    "Architect": ArchitectStrategy,
    "Commissioner": CommissionerStrategy,
    "TheHouse": TheHouseStrategy,
    "TheSyndicate": TheSyndicateStrategy,
    "Executor": ExecutorStrategy,
    "Scalper": ScalperStrategy,
}
