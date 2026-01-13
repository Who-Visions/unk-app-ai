# gemini_agent/models_spec.py
"""
GEMINI_MODELS Specification
============================
Central nervous system for cognitive tiering.
All agents reference this spec for model selection.

Who Visions LLC - Unk Agent System
"""

from typing import Any, Dict, List, Literal

# Type definitions for static analysis
ModelTier = Literal["flash", "pro", "ultra", "lite"]
Capability = Literal[
    "multimodal", "tools", "reasoning", "coding",
    "thinking_tokens", "thinking", "vision", "fast", "video_analysis",
    "complex_reasoning", "text_generation", "ocr", "search_grounding",
    "structured_outputs", "url_context", "grounding_google_maps",
    "audio_live", "affective_dialog", "proactive_audio"
]

GEMINI_MODELS: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════
    # TIER: GEMINI 3 - NEXT GEN INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════
    "default": {
        "model_id": "gemini-3-flash-preview",
        "tier": "flash",
        "release_date": "2025-12-01",
        "context_window": 1_048_576,
        "capabilities": [
            "multimodal", "tools", "fast", "thinking",
            "search_grounding", "structured_outputs", "url_context"
        ],
        "pricing": {
            "input_per_1m": 0.50,
            "output_per_1m": 3.00
        },
        "description": "Gemini 3 Flash. Pro-level intelligence at Flash speeds. Default driver.",
        "use_cases": ["general", "agentic_loops", "fast_reasoning", "high_throughput"],
        "flags": {
            "use_thinking_level": True,
            "default_thinking_level": "high"
        }
    },

    "gemini_3_flash": {
        "model_id": "gemini-3-flash-preview",
        "tier": "flash",
        "release_date": "2025-12-01",
        "context_window": 1_048_576,
        "capabilities": [
            "multimodal", "tools", "fast", "thinking",
            "search_grounding", "structured_outputs", "url_context"
        ],
        "pricing": {
            "input_per_1m": 0.50,
            "output_per_1m": 3.00
        },
        "description": "Gemini 3 Flash (Preview). Speed + Intelligence.",
        "use_cases": ["high_volume", "low_latency"],
        "flags": {
            "use_thinking_level": True,
            "default_thinking_level": "high"
        }
    },

    "gemini_3_pro": {
        "model_id": "gemini-3-pro-preview",
        "tier": "ultra",
        "release_date": "2025-11-01",
        "context_window": 1_048_576,  # 1M input / 64k output
        "capabilities": [
            "complex_reasoning", "coding", "thinking", "multimodal",
            "pdf_input", "search_grounding", "url_context"
        ],
        "pricing": {
            "input_per_1m": 2.00,  # < 200k tokens
            "output_per_1m": 12.00
        },
        "description": "Gemini 3 Pro. Best model for complex tasks and broad world knowledge.",
        "use_cases": ["complex_reasoning", "multimodal_analysis", "coding", "research"],
        "flags": {
            "requires_pro_subscription": True,
            "use_thinking_level": True,
            "default_thinking_level": "high"
        }
    },

    "nano_banana_pro": {
        "model_id": "gemini-3-pro-image-preview",
        "tier": "pro",
        "release_date": "2025-11-01",
        "context_window": 65_536,
        "capabilities": [
            "image_generation", "structured_outputs", "thinking", "search_grounding"
        ],
        "description": "Nano Banana Pro (Gemini 3 Image). Highest quality image generation.",
        "use_cases": ["image_generation", "visual_design", "multimodal_creation"],
        "flags": {
            "use_thinking_level": True
        }
    },

    "gemini_3_pro_image": {
        "model_id": "gemini-3-pro-image-preview",
        "tier": "pro",
        "description": "Alias for Nano Banana Pro."
    },

    "nano_banana": {
        "model_id": "gemini-2.5-flash-image",
        "tier": "flash",
        "release_date": "2025-08-01",
        "context_window": 1_048_576,
        "capabilities": ["image_generation", "fast"],
        "description": "Nano Banana (Gemini 2.5 Flash Image). Fast image generation.",
        "use_cases": ["thumbnails", "stickers", "fast_visuals"]
    },

    "veo_3_1": {
        "model_id": "veo-3.1-generate-preview",
        "tier": "pro",
        "release_date": "2025-09-01",
        "capabilities": ["video_generation", "audio_generation"],
        "description": "Veo 3.1 Preview. High-fidelity video with native audio.",
        "use_cases": ["cinematic_video", "marketing_assets"],
        "limits": {"duration_seconds": [4, 6, 8]}
    },

    # ═══════════════════════════════════════════════════════════════
    # TIER: GEMINI 2.5 - LEGACY WORKHORSE
    # ═══════════════════════════════════════════════════════════════
    "gemini_2_5_flash": {
        "model_id": "gemini-2.5-flash",
        "tier": "flash",
        "release_date": "2025-06-01",
        "context_window": 1_048_576,
        "capabilities": ["multimodal", "tools", "thinking", "grounding_google_maps"],
        "pricing": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "description": "Gemini 2.5 Flash. Best price-performance.",
        "use_cases": ["scaling", "processing"]
    },

    "live_preview": {
        "model_id": "gemini-2.5-flash-native-audio-preview-12-2025",
        "tier": "flash",
        "release_date": "2025-12-20",
        "context_window": 131_072,
        "capabilities": [
            "audio_live", "search_grounding", "tools", "thinking",
            "affective_dialog", "proactive_audio"
        ],
        "pricing": {
            "input_per_1m": 0.10,
            "output_per_1m": 0.40
        },
        "description": "Gemini 2.5 Flash Native Audio. Real-time voice/video interaction.",
        "use_cases": ["realtime_voice", "assistant", "live_interaction"],
        "flags": {
            "use_thinking_level": False,
            "enable_thinking_budget": True,
            "default_thinking_tokens": 1024
        }
    },

    "gemini_2_5_pro": {
        "model_id": "gemini-2.5-pro",
        "tier": "pro",
        "release_date": "2025-06-01",
        "context_window": 1_048_576,
        "capabilities": ["reasoning", "coding", "thinking", "multimodal"],
        "pricing": {
            "input_per_1m": 2.50,
            "output_per_1m": 10.00
        },
        "description": "Gemini 2.5 Pro. State-of-the-art thinking model.",
        "use_cases": ["math", "stem", "complex_analysis"]
    },

    "cost_saver": {
        "model_id": "gemini-2.5-flash-lite",
        "tier": "lite",
        "release_date": "2025-07-01",
        "context_window": 1_048_576,
        "capabilities": ["fast", "tools", "thinking", "multimodal"],
        "pricing": {
            "input_per_1m": 0.02,
            "output_per_1m": 0.08
        },
        "description": "Gemini 2.5 Flash-Lite. Ultra fast and cost efficient.",
        "use_cases": ["classification", "routing", "simple_tasks"]
    },

    # ═══════════════════════════════════════════════════════════════
    # TIER: SPECIALIST / ALIASES
    # ═══════════════════════════════════════════════════════════════
    "code_specialist": {
        "model_id": "gemini-3-pro-preview",
        "tier": "pro",
        "context_window": 1_048_576,
        "capabilities": ["coding", "reasoning", "tools", "thinking"],
        "description": "Code generation and review specialist (Gemini 3 Pro).",
        "flags": {
            "requires_pro_subscription": True,
            "system_prompt_override": "code_expert",
            "use_thinking_level": True
        }
    },

    "flash_thinking": {
        "model_id": "gemini-3-flash-preview",
        "tier": "flash",
        "description": "Alias for Flash with thinking enabled."
    },

    "gemini_2_5_flash_tts": {
        "model_id": "gemini-2.5-flash-native-audio-preview-12-2025",
        "tier": "flash",
        "description": "Alias for Native Audio model (best for TTS)."
    },

    "gemini-2.0-flash-thinking-exp": {
        "model_id": "gemini-2.0-flash-thinking-exp-1219",
        "tier": "flash_thinking",
        "capabilities": ["thinking", "multimodal"],
        "pricing": {"input": 0.0, "output": 0.0},
        "flags": {"system_prompt_override": "ultrathink"}
    },

    "yn_mode": {
        "model_id": "gemini-3-pro-preview",
        "tier": "ultra",
        "description": "Gemini 3 Pro - Young Nigga Mode.",
        "flags": {
            "requires_pro_subscription": True,
            "system_prompt_override": "yn_mode",
            "use_thinking_level": True,
            "default_thinking_level": "high"
        }
    },

    "unk_mode": {
        "model_id": "gemini-3-pro-preview",
        "tier": "pro",
        "description": "Unk Mode - Deep reasoning.",
        "flags": {
            "requires_pro_subscription": True,
            "system_prompt_override": "unk_mode",
            "use_thinking_level": True
        }
    },

    "ultrathink": {
        "model_id": "gemini-3-pro-preview",
        "tier": "ultra",
        "description": "Ultrathink - Maximum cognitive depth with Gemini 3 Pro.",
        "flags": {
            "requires_pro_subscription": True,
            "system_prompt_override": "ultrathink",
            "use_thinking_level": True
        }
    },

    # ═══════════════════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════════════════
    "embedder": {
        "model_id": "text-embedding-004",
        "tier": "utility",
        "description": "Vector embedding generation.",
        "pricing": {
            "input_per_1m": 0.00025
        }
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
    """Get thinking token budget for a mode (Gemini 2.5/Legacy)."""
    spec = get_model(mode)
    flags = spec.get("flags", {})
    if flags.get("enable_thinking_budget"):
        return flags.get("default_thinking_tokens", 0)
    return 0


def get_thinking_level(mode: str) -> str:
    """Get thinking level for a mode (Gemini 3+)."""
    spec = get_model(mode)
    flags = spec.get("flags", {})
    if flags.get("use_thinking_level"):
        return flags.get("default_thinking_level", "high")
    return None


def list_modes_by_tier(tier: str) -> List[str]:
    """List all modes in a specific tier."""
    return [k for k, v in GEMINI_MODELS.items() if v.get("tier") == tier]


def get_routing_recommendation(task_complexity: str) -> str:
    """
    Recommend a mode based on task complexity.

    Escalation path:
    1. Trivial/Simple -> gemini-2.5-flash-lite (cost_saver)
    2. Moderate -> gemini-3-flash-preview (default)
    3. Complex -> gemini-3-pro-preview (gemini_3_pro)
    4. Extreme -> gemini-3-pro-preview (ultrathink)

    Args:
        task_complexity: One of 'trivial', 'simple', 'moderate', 'complex', 'extreme'
    """
    routing_map = {
        "trivial": "cost_saver",
        "simple": "cost_saver",
        "moderate": "default",
        "complex": "gemini_3_pro",
        "extreme": "ultrathink"
    }
    return routing_map.get(task_complexity, "default")
