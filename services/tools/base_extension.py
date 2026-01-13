"""
Base Tool Extension for Modular Agent Tools

Inspired by Confucius SDK, each tool extension:
1. Maintains its own state across calls
2. Has structured output handling
3. Implements error recovery logic
4. Provides prompt wiring for the LLM
"""

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class ToolResult:
    """Structured result from a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_suggestion: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class ToolState:
    """State maintained by a tool across executions."""
    call_count: int = 0
    last_call_time: Optional[str] = None
    last_result: Optional[ToolResult] = None
    error_count: int = 0
    consecutive_errors: int = 0
    custom_state: Dict[str, Any] = field(default_factory=dict)


class ToolExtension(ABC):
    """
    Base class for modular tool extensions.

    Each extension maintains state, handles errors,
    and provides structured prompts for the LLM.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.state = ToolState()
        self.max_retries = 3
        self.recovery_strategies: List[str] = []

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    def get_prompt_schema(self) -> Dict[str, Any]:
        """
        Return the schema for LLM prompt wiring.
        This tells the LLM how to call this tool.
        """
        pass

    def get_prompt_description(self) -> str:
        """Return a description for the LLM prompt."""
        return f"**{self.name}**: {self.description}"

    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Execute with error handling and state tracking.
        """
        import time
        start_time = time.time()

        self.state.call_count += 1
        self.state.last_call_time = datetime.now().isoformat()

        try:
            result = await self.execute(**kwargs)
            result.execution_time_ms = (time.time() - start_time) * 1000

            if result.success:
                self.state.consecutive_errors = 0
            else:
                self.state.error_count += 1
                self.state.consecutive_errors += 1
                result.retry_suggestion = self._get_recovery_suggestion()

            self.state.last_result = result
            return result

        except Exception as e:
            self.state.error_count += 1
            self.state.consecutive_errors += 1

            result = ToolResult(
                success=False,
                output="",
                error=str(e),
                metadata={"traceback": traceback.format_exc()},
                retry_suggestion=self._get_recovery_suggestion(),
                execution_time_ms=(time.time() - start_time) * 1000
            )
            self.state.last_result = result
            return result

    def _get_recovery_suggestion(self) -> str:
        """Get a recovery suggestion based on error history."""
        if self.state.consecutive_errors >= self.max_retries:
            return "Max retries reached. Consider a different approach."

        if self.recovery_strategies:
            idx = min(
                self.state.consecutive_errors - 1,
                len(self.recovery_strategies) - 1
            )
            return self.recovery_strategies[idx]

        return f"Retry attempt {self.state.consecutive_errors}/{self.max_retries}"

    def reset_state(self):
        """Reset the tool state."""
        self.state = ToolState()

    def get_state_summary(self) -> str:
        """Get a summary of the tool state for context."""
        return (
            f"[{self.name}] Calls: {self.state.call_count}, "
            f"Errors: {self.state.error_count}, "
            f"Last: {self.state.last_call_time or 'never'}"
        )


class ToolRegistry:
    """Registry for managing multiple tool extensions."""

    def __init__(self):
        self.tools: Dict[str, ToolExtension] = {}

    def register(self, tool: ToolExtension):
        """Register a tool extension."""
        self.tools[tool.name] = tool
        print(f"[ToolRegistry] Registered: {tool.name}")

    def get(self, name: str) -> Optional[ToolExtension]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_all_prompts(self) -> str:
        """Get combined prompt descriptions for all tools."""
        return "\n".join([
            tool.get_prompt_description()
            for tool in self.tools.values()
        ])

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool schemas for function calling."""
        return {
            name: tool.get_prompt_schema()
            for name, tool in self.tools.items()
        }

    def get_state_summary(self) -> str:
        """Get state summary for all tools."""
        return "\n".join([
            tool.get_state_summary()
            for tool in self.tools.values()
        ])
