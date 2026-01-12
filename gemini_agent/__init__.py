# gemini_agent/__init__.py
"""
Unk Agent - Multi-Model Cognitive System
=========================================
Enterprise-grade AI agent with cognitive tiering.

Who Visions LLC - AI with Dav3
"""

from .agent import (AgentFactory, AgentResponse,  # Example tools
                    IntentClassification, ReasonedStep, ThoughtType, UnkAgent,
                    analyze_code_complexity, calculate_growth_metrics,
                    get_current_timestamp)
from .memory import (MemoryEntry, MemoryType, VectorMemory,
                     create_memory_search_tool, create_memory_store_tool)
from .models_spec import (GEMINI_MODELS, estimate_cost, get_model,
                          get_model_id, get_routing_recommendation,
                          get_thinking_budget, has_capability,
                          list_modes_by_tier, requires_subscription)

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
