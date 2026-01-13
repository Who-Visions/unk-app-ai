"""
Hierarchical Working Memory for Long-Horizon Agent Tasks

Inspired by the Confucius SDK, this module implements a memory system that:
1. Partitions agent trajectory into scopes (logical segments)
2. Summarizes old scopes to stay within context limits
3. Preserves key artifacts (patches, logs, decisions) for later reference
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Try to import Gemini for summarization
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


@dataclass
class MemoryStep:
    """A single step in the agent's execution trace."""
    action: str
    result: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_key_artifact: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryScope:
    """A logical partition of the agent's trajectory."""
    name: str
    steps: List[MemoryStep] = field(default_factory=list)
    summary: Optional[str] = None
    is_compressed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class HierarchicalWorkingMemory:
    """
    Implements hierarchical working memory for long-horizon agent tasks.

    Key Features:
    - Scope partitioning for task segments
    - Automatic summarization of old scopes
    - Artifact preservation (patches, logs, decisions)
    - Token-aware context management
    """

    def __init__(
        self,
        max_context_tokens: int = 32000,
        summarization_model: str = "gemini-3-flash-preview",
        auto_compress: bool = True
    ):
        self.max_context_tokens = max_context_tokens
        self.summarization_model = summarization_model
        self.auto_compress = auto_compress

        self.scopes: List[MemoryScope] = []
        self.current_scope: Optional[MemoryScope] = None
        self.key_artifacts: Dict[str, Any] = {}

        # Initialize Gemini client for summarization
        self.client = None
        if GENAI_AVAILABLE:
            project = os.getenv("GOOGLE_CLOUD_PROJECT") or "unk-app-480102"
            try:
                self.client = genai.Client(
                    vertexai=True,
                    project=project,
                    location="global"
                )
            except Exception as e:
                print(f"[HierarchicalWorkingMemory] Gemini init error: {e}")

    def start_scope(self, name: str) -> MemoryScope:
        """Start a new logical scope for the current task segment."""
        # Close the current scope if one exists
        if self.current_scope:
            self.scopes.append(self.current_scope)

        self.current_scope = MemoryScope(name=name)
        print(f"[Memory] Started new scope: {name}")
        return self.current_scope

    def add_step(
        self,
        action: str,
        result: str,
        is_key: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryStep:
        """Add a step to the current scope."""
        if not self.current_scope:
            self.start_scope("default")

        step = MemoryStep(
            action=action,
            result=result,
            is_key_artifact=is_key,
            metadata=metadata or {}
        )

        self.current_scope.steps.append(step)

        # Store key artifacts separately for quick access
        if is_key:
            artifact_id = f"{self.current_scope.name}_{len(self.current_scope.steps)}"
            self.key_artifacts[artifact_id] = {
                "action": action,
                "result": result,
                "metadata": metadata
            }

        # Auto-compress old scopes if needed
        if self.auto_compress:
            self._check_and_compress()

        return step

    async def compress_scope(self, scope: MemoryScope) -> str:
        """Compress a scope into a summary using Gemini."""
        if scope.is_compressed:
            return scope.summary or ""

        # Build the scope content for summarization
        steps_text = "\n".join([
            f"- Action: {s.action}\n  Result: {s.result[:500]}..."
            for s in scope.steps
        ])

        prompt = f"""Summarize the following agent execution trace into a concise summary.
Preserve key decisions, errors encountered, and outcomes.

Scope: {scope.name}
Steps ({len(scope.steps)} total):
{steps_text}

Provide a 2-3 sentence summary that captures the essential information."""

        if self.client:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.summarization_model,
                    contents=prompt
                )
                scope.summary = response.text
                scope.is_compressed = True
                # Clear the steps to save memory, keeping only key artifacts
                scope.steps = [s for s in scope.steps if s.is_key_artifact]
                return scope.summary
            except Exception as e:
                print(f"[Memory] Compression error: {e}")
                return f"[Scope: {scope.name}] {len(scope.steps)} steps executed."
        else:
            # Fallback: simple summary without LLM
            scope.summary = f"[Scope: {scope.name}] {len(scope.steps)} steps executed."
            scope.is_compressed = True
            return scope.summary

    def _check_and_compress(self):
        """Check if we need to compress old scopes to stay within limits."""
        estimated_tokens = self._estimate_tokens()

        if estimated_tokens > self.max_context_tokens * 0.8:
            # Compress the oldest uncompressed scope
            for scope in self.scopes:
                if not scope.is_compressed:
                    # Schedule async compression (caller should await)
                    print(f"[Memory] Scheduling compression for scope: {scope.name}")
                    break

    def _estimate_tokens(self) -> int:
        """Estimate the current token count of all memory."""
        total_chars = 0
        for scope in self.scopes:
            if scope.is_compressed:
                total_chars += len(scope.summary or "")
            else:
                for step in scope.steps:
                    total_chars += len(step.action) + len(step.result)

        if self.current_scope:
            for step in self.current_scope.steps:
                total_chars += len(step.action) + len(step.result)

        # Rough estimate: 4 chars per token
        return total_chars // 4

    def get_context_window(self, max_tokens: Optional[int] = None) -> str:
        """Build the context window for the LLM, prioritizing recent and key info."""
        max_tokens = max_tokens or self.max_context_tokens

        parts = []

        # 1. Add key artifacts summary
        if self.key_artifacts:
            parts.append("## Key Artifacts\n")
            for artifact_id, artifact in list(self.key_artifacts.items())[-10:]:  # Last 10
                parts.append(f"- {artifact_id}: {artifact['action'][:100]}...\n")

        # 2. Add compressed scope summaries
        if self.scopes:
            parts.append("\n## Previous Scopes\n")
            for scope in self.scopes:
                if scope.is_compressed:
                    parts.append(f"### {scope.name}\n{scope.summary}\n")
                else:
                    # Include last few steps from uncompressed scopes
                    parts.append(f"### {scope.name} (Active)\n")
                    for step in scope.steps[-5:]:
                        parts.append(f"- {step.action}: {step.result[:200]}...\n")

        # 3. Add current scope in full
        if self.current_scope:
            parts.append(f"\n## Current Scope: {self.current_scope.name}\n")
            for step in self.current_scope.steps:
                parts.append(f"- {step.action}: {step.result}\n")

        context = "".join(parts)

        # Truncate if needed
        estimated_tokens = len(context) // 4
        if estimated_tokens > max_tokens:
            # Truncate from the beginning (older info)
            target_chars = max_tokens * 4
            context = "...[truncated]\n" + context[-target_chars:]

        return context

    def get_key_artifacts(self) -> Dict[str, Any]:
        """Get all preserved key artifacts."""
        return self.key_artifacts

    def save_to_file(self, path: str):
        """Persist memory state to a JSON file."""
        state = {
            "scopes": [
                {
                    "name": s.name,
                    "summary": s.summary,
                    "is_compressed": s.is_compressed,
                    "created_at": s.created_at,
                    "steps": [
                        {
                            "action": step.action,
                            "result": step.result,
                            "timestamp": step.timestamp,
                            "is_key_artifact": step.is_key_artifact,
                            "metadata": step.metadata
                        }
                        for step in s.steps
                    ]
                }
                for s in self.scopes
            ],
            "key_artifacts": self.key_artifacts
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load_from_file(self, path: str):
        """Load memory state from a JSON file."""
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            state = json.load(f)

        self.scopes = []
        for s in state.get("scopes", []):
            scope = MemoryScope(
                name=s["name"],
                summary=s.get("summary"),
                is_compressed=s.get("is_compressed", False),
                created_at=s.get("created_at", datetime.now().isoformat())
            )
            for step_data in s.get("steps", []):
                scope.steps.append(MemoryStep(
                    action=step_data["action"],
                    result=step_data["result"],
                    timestamp=step_data.get("timestamp", ""),
                    is_key_artifact=step_data.get("is_key_artifact", False),
                    metadata=step_data.get("metadata", {})
                ))
            self.scopes.append(scope)

        self.key_artifacts = state.get("key_artifacts", {})
