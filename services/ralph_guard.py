"""
Ralph Guard - Safety Layer for Autonomous Agent Operations

Provides safety mechanisms for Ralph loops:
- Budget tracking and limits
- Path whitelisting/blacklisting
- Iteration counters
- Emergency shutdown

Who Visions LLC | AI with Dav3
"""

import datetime
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RalphBudget:
    """Tracks API spending for a Ralph session."""

    max_cost_usd: float = 10.0
    current_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Cost rates (Gemini 2.5 Pro)
    input_rate_per_1m: float = 2.50
    output_rate_per_1m: float = 10.00

    def add_usage(self, input_tokens: int, output_tokens: int) -> float:
        """Record token usage and return the cost."""
        input_cost = (input_tokens / 1_000_000) * self.input_rate_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_rate_per_1m
        cost = input_cost + output_cost

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.current_cost += cost

        return cost

    def is_over_budget(self) -> bool:
        """Check if current spending exceeds the limit."""
        return self.current_cost >= self.max_cost_usd

    def remaining_budget(self) -> float:
        """Get remaining budget in USD."""
        return max(0, self.max_cost_usd - self.current_cost)

    def usage_percentage(self) -> float:
        """Get percentage of budget used."""
        if self.max_cost_usd == 0:
            return 100.0
        return (self.current_cost / self.max_cost_usd) * 100


@dataclass
class RalphGuard:
    """
    Safety guard for autonomous agent operations.

    Enforces:
    - Budget limits
    - Path restrictions
    - Iteration limits
    - Runtime limits
    """

    # Limits
    max_iterations: int = 50
    max_runtime_seconds: int = 3600

    # Path restrictions
    allowed_paths: list = field(default_factory=lambda: [
        "routers/",
        "services/",
        "skills/",
        "scripts/",
        "tests/",
        ".agent/",
        "gemini_agent/"
    ])

    forbidden_paths: list = field(default_factory=lambda: [
        ".env",
        ".git/",
        "venv/",
        "*.key",
        "*.pem",
        "*credentials*",
        "*secret*",
        "*.sqlite",
        "*.db"
    ])

    # Budget tracker
    budget: RalphBudget = field(default_factory=RalphBudget)

    # State
    current_iteration: int = 0
    start_time: Optional[float] = None
    is_running: bool = False

    def start(self):
        """Mark the guard as active."""
        import time
        self.start_time = time.time()
        self.is_running = True
        self.current_iteration = 0

    def stop(self):
        """Mark the guard as inactive."""
        self.is_running = False

    def increment_iteration(self) -> bool:
        """
        Increment iteration counter.
        Returns True if we can continue, False if limit reached.
        """
        self.current_iteration += 1
        return self.current_iteration < self.max_iterations

    def check_runtime(self) -> bool:
        """
        Check if we're within runtime limits.
        Returns True if we can continue, False if limit reached.
        """
        if self.start_time is None:
            return True

        import time
        elapsed = time.time() - self.start_time
        return elapsed < self.max_runtime_seconds

    def is_path_allowed(self, path: str) -> bool:
        """
        Check if a path is allowed for modification.

        Args:
            path: Relative or absolute path to check

        Returns:
            True if the path is allowed, False otherwise
        """
        # Normalize path
        path_obj = Path(path)
        path_str = str(path_obj).replace("\\", "/")

        # Check forbidden paths first (deny takes priority)
        for pattern in self.forbidden_paths:
            if self._matches_pattern(path_str, pattern):
                return False

        # Check allowed paths
        for allowed in self.allowed_paths:
            if path_str.startswith(allowed) or path_str == allowed.rstrip("/"):
                return True

        return False

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches a glob-like pattern."""
        # Simple glob matching
        if "*" in pattern:
            # Convert glob to regex
            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.search(regex, path, re.IGNORECASE))
        else:
            return pattern in path

    def can_continue(self) -> tuple[bool, str]:
        """
        Check all safety conditions.

        Returns:
            Tuple of (can_continue, reason_if_not)
        """
        if not self.is_running:
            return False, "Guard not running"

        if self.current_iteration >= self.max_iterations:
            return False, f"Max iterations reached ({self.max_iterations})"

        if not self.check_runtime():
            return False, f"Max runtime reached ({self.max_runtime_seconds}s)"

        if self.budget.is_over_budget():
            return False, f"Budget exhausted (${self.budget.max_cost_usd:.2f})"

        return True, ""

    def get_status(self) -> dict:
        """Get current guard status as a dictionary."""
        import time

        elapsed = 0
        if self.start_time:
            elapsed = time.time() - self.start_time

        return {
            "is_running": self.is_running,
            "iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "elapsed_seconds": elapsed,
            "max_runtime_seconds": self.max_runtime_seconds,
            "budget": {
                "current_cost": self.budget.current_cost,
                "max_cost": self.budget.max_cost_usd,
                "remaining": self.budget.remaining_budget(),
                "usage_percent": self.budget.usage_percentage()
            },
            "tokens": {
                "input": self.budget.total_input_tokens,
                "output": self.budget.total_output_tokens
            }
        }


class RalphPathValidator:
    """
    Validates file paths for Ralph operations.

    This is a stricter validator that runs before any file operation.
    """

    # Absolute forbidden patterns (security critical)
    CRITICAL_FORBIDDEN = [
        r"\.env$",
        r"\.env\.",
        r"credentials",
        r"secrets?",
        r"\.pem$",
        r"\.key$",
        r"private",
        r"password",
        r"token",
        r"\.sqlite$",
        r"\.db$",
    ]

    @classmethod
    def is_safe(cls, path: str) -> bool:
        """
        Check if a path is safe for modification.

        This is a security-critical check that should be called
        before any file write operation.
        """
        path_lower = path.lower()

        for pattern in cls.CRITICAL_FORBIDDEN:
            if re.search(pattern, path_lower):
                return False

        return True

    @classmethod
    def validate_operation(cls, operation: str, path: str) -> tuple[bool, str]:
        """
        Validate a file operation.

        Args:
            operation: One of 'read', 'write', 'delete', 'execute'
            path: The file path

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.is_safe(path):
            return False, f"Path '{path}' matches forbidden pattern"

        if operation == "delete":
            # Extra caution for delete operations
            if not path.startswith(".agent/"):
                return False, "Delete operations only allowed in .agent/ directory"

        if operation == "execute":
            # Only allow execution in specific directories
            allowed_exec = ["scripts/", ".agent/"]
            if not any(path.startswith(d) for d in allowed_exec):
                return False, f"Execution only allowed in: {allowed_exec}"

        return True, ""


def create_guard_from_config(config: dict) -> RalphGuard:
    """
    Create a RalphGuard from a configuration dictionary.

    Args:
        config: Dictionary with 'safety' and 'defaults' keys

    Returns:
        Configured RalphGuard instance
    """
    safety = config.get("safety", {})
    defaults = config.get("defaults", {})

    budget = RalphBudget(
        max_cost_usd=defaults.get("max_cost_usd", 10.0)
    )

    return RalphGuard(
        max_iterations=defaults.get("max_iterations", 50),
        max_runtime_seconds=safety.get("max_runtime_seconds", 3600),
        allowed_paths=safety.get("allowed_paths", []),
        forbidden_paths=safety.get("forbidden_paths", []),
        budget=budget
    )
