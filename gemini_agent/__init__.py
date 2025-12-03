# gemini_agent/__init__.py
"""
Unk Agent - Multi-Model Cognitive System
=========================================
Enterprise-grade AI agent with cognitive tiering.

Who Visions LLC - AI with Dav3
"""

from .models_spec import (
    GEMINI_MODELS,
    get_model,
    get_model_id,
    has_capability,
    requires_subscription,
    estimate_cost,
    get_thinking_budget,
    get_routing_recommendation,
    list_modes_by_tier
)

from .agent import (
    UnkAgent,
    AgentFactory,
    AgentResponse,
    ReasonedStep,
    IntentClassification,
    ThoughtType,
    # Example tools
    calculate_growth_metrics,
    analyze_code_complexity,
    get_current_timestamp
)

from .memory import (
    VectorMemory,
    MemoryType,
    MemoryEntry,
    create_memory_search_tool,
    create_memory_store_tool
)

__version__ = "1.0.0"
__author__ = "Who Visions LLC"
__all__ = [
    # Models
    "GEMINI_MODELS",
    "get_model",
    "get_model_id",
    "has_capability",
    "requires_subscription",
    "estimate_cost",
    "get_thinking_budget",
    "get_routing_recommendation",
    "list_modes_by_tier",
    # Agent
    "UnkAgent",
    "AgentFactory",
    "AgentResponse",
    "ReasonedStep",
    "IntentClassification",
    "ThoughtType",
    # Memory
    "VectorMemory",
    "MemoryType",
    "MemoryEntry",
    "create_memory_search_tool",
    "create_memory_store_tool",
    # Tools
    "calculate_growth_metrics",
    "analyze_code_complexity",
    "get_current_timestamp"
]
