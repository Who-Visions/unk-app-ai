# gemini_agent/models_spec.py
"""
GEMINI_MODELS Specification
============================
Central nervous system for cognitive tiering.
All agents reference this spec for model selection.

Who Visions LLC - Unk Agent System
"""

from typing import Dict, Any, Literal, List

# Type definitions for static analysis
ModelTier = Literal["flash", "pro", "ultra", "lite"]
Capability = Literal[
    "multimodal", "tools", "reasoning", "coding", 
    "thinking_tokens", "vision", "fast", "video_analysis",
    "complex_reasoning", "text_generation", "ocr"
]

GEMINI_MODELS: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════
    # TIER: FLASH - High-throughput, cost-efficient operations
    # ═══════════════════════════════════════════════════════════════
    "default": {
        "model_id": "gemini-2.0-flash-001",
        "tier": "flash",
        "release_date": "2025-02-05",
        "context_window": 1_000_000,
        "capabilities": ["multimodal", "tools", "fast"],
        "pricing": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "rate_limits": {
            "rpm": 1000,
            "tpm": 4_000_000
        },
        "description": "High-throughput driver. Default for standard interactions.",
        "use_cases": ["greetings", "simple_qa", "classification", "routing"]
    },
    
    "flash_thinking": {
        "model_id": "gemini-2.0-flash-thinking-exp",
        "tier": "flash",
        "release_date": "2025-01-21",
        "context_window": 1_000_000,
        "capabilities": ["reasoning", "tools", "thinking_tokens"],
        "pricing": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "rate_limits": {
            "rpm": 500,
            "tpm": 2_000_000
        },
        "description": "Flash with native chain-of-thought. Bridge between speed and reasoning.",
        "use_cases": ["moderate_reasoning", "step_by_step", "planning"]
    },

    # ═══════════════════════════════════════════════════════════════
    # TIER: PRO - Deep reasoning, complex problem solving
    # ═══════════════════════════════════════════════════════════════
    "unk_mode": {
        "model_id": "gemini-2.5-pro-preview-06-05",
        "tier": "pro",
        "release_date": "2025-06-05",
        "context_window": 2_000_000,
        "capabilities": ["complex_reasoning", "coding", "thinking_tokens", "multimodal"],
        "pricing": {
            "input_per_1m": 2.50,
            "output_per_1m": 10.00
        },
        "rate_limits": {
            "rpm": 150,
            "tpm": 1_000_000
        },
        "description": "THE BRAIN. Maximum intelligence. Uses thinking tokens for deep reasoning.",
        "use_cases": ["architecture", "complex_analysis", "code_generation", "research"],
        "flags": {
            "requires_pro_subscription": True,
            "enable_thinking_budget": True,
            "default_thinking_tokens": 8192
        }
    },
    
    "ultrathink": {
        "model_id": "gemini-2.5-pro-preview-06-05",
        "tier": "ultra",
        "release_date": "2025-06-05",
        "context_window": 2_000_000,
        "capabilities": ["complex_reasoning", "coding", "thinking_tokens", "multimodal"],
        "pricing": {
            "input_per_1m": 2.50,
            "output_per_1m": 10.00
        },
        "rate_limits": {
            "rpm": 60,
            "tpm": 500_000
        },
        "description": "ULTRATHINK. Extended thinking budget. Maximum cognitive depth.",
        "use_cases": ["system_design", "research_synthesis", "complex_debugging"],
        "flags": {
            "requires_pro_subscription": True,
            "enable_thinking_budget": True,
            "default_thinking_tokens": 32768,
            "max_thinking_tokens": 65536
        }
    },

    # ═══════════════════════════════════════════════════════════════
    # TIER: SPECIALIST - Domain-specific optimizations
    # ═══════════════════════════════════════════════════════════════
    "vision_specialist": {
        "model_id": "gemini-2.0-flash-001",
        "tier": "flash",
        "release_date": "2025-02-05",
        "context_window": 1_000_000,
        "capabilities": ["vision", "ocr", "video_analysis", "multimodal"],
        "pricing": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "rate_limits": {
            "rpm": 500,
            "tpm": 2_000_000
        },
        "description": "Optimized for image/video understanding tasks.",
        "use_cases": ["image_analysis", "document_ocr", "video_processing"]
    },
    
    "code_specialist": {
        "model_id": "gemini-2.5-pro-preview-06-05",
        "tier": "pro",
        "release_date": "2025-06-05",
        "context_window": 2_000_000,
        "capabilities": ["coding", "reasoning", "tools"],
        "pricing": {
            "input_per_1m": 2.50,
            "output_per_1m": 10.00
        },
        "rate_limits": {
            "rpm": 150,
            "tpm": 1_000_000
        },
        "description": "Code generation and review specialist.",
        "use_cases": ["code_generation", "code_review", "refactoring", "debugging"],
        "flags": {
            "requires_pro_subscription": True,
            "system_prompt_override": "code_expert"
        }
    },

    # ═══════════════════════════════════════════════════════════════
    # TIER: LITE - Maximum cost efficiency
    # ═══════════════════════════════════════════════════════════════
    "cost_saver": {
        "model_id": "gemini-2.0-flash-lite-001",
        "tier": "lite",
        "release_date": "2025-02-05",
        "context_window": 1_000_000,
        "capabilities": ["text_generation", "fast"],
        "pricing": {
            "input_per_1m": 0.02,
            "output_per_1m": 0.08
        },
        "rate_limits": {
            "rpm": 2000,
            "tpm": 8_000_000
        },
        "description": "Lowest cost. Simple summarization/classification only.",
        "use_cases": ["classification", "extraction", "simple_summarization"]
    },

    # ═══════════════════════════════════════════════════════════════
    # EMBEDDING MODELS
    # ═══════════════════════════════════════════════════════════════
    "embedder": {
        "model_id": "text-embedding-004",
        "tier": "utility",
        "release_date": "2024-05-14",
        "dimensions": 768,
        "capabilities": ["embedding"],
        "pricing": {
            "input_per_1m": 0.00025
        },
        "description": "Vector embedding generation for RAG.",
        "use_cases": ["semantic_search", "rag", "similarity"]
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_model(mode: str) -> Dict[str, Any]:
    """Retrieve model spec with fallback to default."""
    return GEMINI_MODELS.get(mode, GEMINI_MODELS["default"])


def get_model_id(mode: str) -> str:
    """Get just the model ID string."""
    return get_model(mode)["model_id"]


def has_capability(mode: str, capability: str) -> bool:
    """Check if a model mode has a specific capability."""
    spec = get_model(mode)
    return capability in spec.get("capabilities", [])


def requires_subscription(mode: str) -> bool:
    """Check if mode requires pro subscription."""
    spec = get_model(mode)
    return spec.get("flags", {}).get("requires_pro_subscription", False)


def estimate_cost(mode: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a generation request."""
    spec = get_model(mode)
    pricing = spec.get("pricing", {})
    input_cost = (input_tokens / 1_000_000) * pricing.get("input_per_1m", 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get("output_per_1m", 0)
    return round(input_cost + output_cost, 6)


def get_thinking_budget(mode: str) -> int:
    """Get thinking token budget for a mode."""
    spec = get_model(mode)
    flags = spec.get("flags", {})
    if flags.get("enable_thinking_budget"):
        return flags.get("default_thinking_tokens", 0)
    return 0


def list_modes_by_tier(tier: str) -> List[str]:
    """List all modes in a specific tier."""
    return [k for k, v in GEMINI_MODELS.items() if v.get("tier") == tier]


def get_routing_recommendation(task_complexity: str) -> str:
    """
    Recommend a mode based on task complexity.
    
    Args:
        task_complexity: One of 'trivial', 'simple', 'moderate', 'complex', 'extreme'
    """
    routing_map = {
        "trivial": "cost_saver",
        "simple": "default",
        "moderate": "flash_thinking",
        "complex": "unk_mode",
        "extreme": "ultrathink"
    }
    return routing_map.get(task_complexity, "default")
