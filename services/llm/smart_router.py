import random
from typing import Any, Dict, Optional, Tuple

# ==============================================================================
# CRITICAL CORE COMPONENT: Smart Router
# ==============================================================================
# This router is the CENTRAL BRAIN of the Agentic System.
# It defines the "Cognitive Architecture" - deciding when to think fast (Flash)
# and when to think slow (Pro).
#
# DO NOT MODIFY THIS LOGIC WITHOUT EXPLICIT AUTHORIZATION.
# ==============================================================================


class SmartRouter:
    """
    Routes prompts between Gemini 3 Flash and Pro based on heuristics,
    configuration, and probabilistic weights.

    Default Policy:
    - 60% Traffic -> Gemini 3 Flash (Thinking Level: LOW)
    - 40% Traffic -> Gemini 3 Pro (Thinking Level: HIGH)

    Overrides:
    - 'complex:', 'reason:', 'deep:' -> Force Pro
    - 'fast:', 'simple:', 'quick:' -> Force Flash
    - 'vision:', 'image:', 'draw:' -> Force Pro Vision
    """

    def __init__(self, flash_model: str = "gemini-3-flash-preview",
                 pro_model: str = "gemini-3-pro-preview",
                 vision_model: str = "gemini-3-pro-image-preview",
                 flash_weight: float = 0.6):
        self.flash_model = flash_model
        self.pro_model = pro_model
        self.vision_model = vision_model
        self.flash_weight = flash_weight

    def route(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Decides which model and configuration to use based on prompt complexity headers
        and linguistic features.
        """
        lower = prompt.lower().strip()

        # 1. explicit Overrides (Highest Priority)
        if any(lower.startswith(p) for p in ["complex:", "reason:", "deep:", "pro:"]):
            return self.pro_model, self._pro_config()

        if any(lower.startswith(p) for p in ["fast:", "simple:", "quick:", "flash:"]):
            return self.flash_model, self._flash_config()

        # 2. Vision/Multimodal Triggers
        if any(keyword in lower for keyword in ["draw", "generate image", "create a picture", "thumbnail"]):
            return self.vision_model, {}

        # 3. Complexity Heuristics (The "Smart" part)
        is_complex, reason = self._analyze_complexity(prompt)

        if is_complex:
            # print(f"[Router] Routing to PRO due to: {reason}")
            return self.pro_model, self._pro_config()

        # 4. Default to Flash (Speed/Efficiency)
        return self.flash_model, self._flash_config()

    def _analyze_complexity(self, prompt: str) -> Tuple[bool, str]:
        """
        Returns (is_complex, reason).
        True -> Gemini 3 Pro (High Thinking)
        False -> Gemini 3 Flash (Low Thinking)
        """
        # A. Length Check
        if len(prompt) > 1000:
            return True, "Length > 1000 chars"

        lower = prompt.lower()

        # B. Math / Logic / Science Indicators
        math_terms = ["math", "callculate", "solve", "proof", "theorem", "derivative", "integral",
                      "equation", "formula", "quantum", "physics", "chemistry", "logic puzzle", "riddle"]
        if any(term in lower for term in math_terms):
            return True, "Math/Science keywords detected"

        # C. Coding / Technical Indicators
        code_terms = ["write code", "debug", "python script", "algorithm",
                      "refactor", "function to", "class for", "api", "sdk"]
        if any(term in lower for term in code_terms):
            return True, "Coding keywords detected"

        # D. Reasoning Indicators
        reasoning_terms = ["analyze", "compare", "contrast", "evaluate",
                           "implications", "why does", "explain the difference", "synthesis"]
        # Be careful not to trigger on simple "why" questions
        if any(term in lower for term in reasoning_terms):
            return True, "Complex reasoning keywords detected"

        return False, "Simple query"

    def _flash_config(self) -> Dict[str, Any]:
        """Configuration for Flash (Speed/Efficiency)"""
        return {
            "thinking_config": {
                "thinking_level": "low",
                "include_thoughts": False
            }
        }

    def _pro_config(self) -> Dict[str, Any]:
        """Configuration for Pro (Deep Reasoning)"""
        return {
            "thinking_config": {
                "thinking_level": "high",
                "include_thoughts": True
            }
        }


# Singleton instance for easy import
router = SmartRouter()
