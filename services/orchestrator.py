"""
Unified Orchestrator for the Unk Agent

Inspired by Confucius SDK, this orchestrator:
1. Coordinates HierarchicalWorkingMemory, PersistentNotes, and ToolExtensions
2. Manages the agent lifecycle across long-horizon tasks
3. Integrates with the UnkAiAgent persona logic
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Import Confucius-inspired components
from .memory import HierarchicalWorkingMemory, PersistentNotes
from .tools import CommandExecutor, FileEditor, ToolRegistry

# Import the LLM agent
try:
    from .llm.unk_agent import UnkAiAgent
except ImportError:
    UnkAiAgent = None


@dataclass
class AgentContext:
    """Context for the current agent session."""
    task_name: str
    task_description: str
    repo_path: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_steps: int = 0
    current_scope: str = "init"


class UnkOrchestrator:
    """
    Unified orchestrator for the Unk Agent ecosystem.

    This orchestrator manages:
    - Agent Experience (AX): Memory, context, tool results
    - User Experience (UX): Traces, diffs, readable output
    - Developer Experience (DX): Observability, debugging
    """

    def __init__(
        self,
        repo_path: str = ".",
        persona: str = "unk",
        max_context_tokens: int = 32000,
        notes_dir: str = "assets/notes"
    ):
        self.repo_path = os.path.abspath(repo_path)
        self.persona = persona

        # Initialize Confucius-inspired components
        self.memory = HierarchicalWorkingMemory(
            max_context_tokens=max_context_tokens
        )
        self.notes = PersistentNotes(notes_dir=notes_dir)
        self.tools = ToolRegistry()

        # Register default tools
        self._register_default_tools()

        # Initialize the LLM agent
        self.agent = None
        if UnkAiAgent:
            self.agent = UnkAiAgent(mode=persona)

        # Session context
        self.context: Optional[AgentContext] = None
        self.execution_trace: List[Dict[str, Any]] = []

        print(f"[UnkOrchestrator] Initialized for {repo_path} with {persona} persona")

    def _register_default_tools(self):
        """Register the default tool extensions."""
        self.tools.register(CommandExecutor(
            default_cwd=self.repo_path,
            timeout_seconds=60
        ))
        self.tools.register(FileEditor(repo_root=self.repo_path))

    def start_task(self, task_name: str, task_description: str) -> AgentContext:
        """Start a new task session."""
        self.context = AgentContext(
            task_name=task_name,
            task_description=task_description,
            repo_path=self.repo_path
        )

        # Start a new memory scope
        self.memory.start_scope(task_name)

        # Load relevant notes for this task
        keywords = task_name.lower().split() + task_description.lower().split()[:10]
        relevant_notes = self.notes.get_notes_for_context(keywords)
        if relevant_notes:
            notes_context = self.notes.format_notes_for_prompt(relevant_notes)
            print(f"[Orchestrator] Loaded {len(relevant_notes)} relevant notes")

        self.execution_trace = []

        print(f"[Orchestrator] Started task: {task_name}")
        return self.context

    async def execute_step(
        self,
        action: str,
        tool_name: Optional[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        llm_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a single step in the agent workflow.

        This can be a tool call or an LLM inference.
        """
        if not self.context:
            raise RuntimeError("No active task. Call start_task() first.")

        self.context.total_steps += 1
        step_id = self.context.total_steps

        result = {
            "step_id": step_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }

        if tool_name and tool_params is not None:
            # Execute a tool
            tool = self.tools.get(tool_name)
            if not tool:
                result["success"] = False
                result["error"] = f"Tool not found: {tool_name}"
            else:
                tool_result = await tool.safe_execute(**tool_params)
                result["success"] = tool_result.success
                result["output"] = tool_result.output
                result["error"] = tool_result.error
                result["retry_suggestion"] = tool_result.retry_suggestion

                # Add to memory
                is_key = tool_result.success and len(tool_result.output) > 100
                self.memory.add_step(
                    action=f"{tool_name}: {str(tool_params)[:100]}",
                    result=tool_result.output[:500] if tool_result.output else str(
                        tool_result.error),
                    is_key=is_key
                )

        elif llm_prompt:
            # Execute an LLM inference
            if self.agent:
                try:
                    # Build context from memory and notes
                    context = self._build_llm_context()

                    # Get response from agent
                    response = await self.agent.speak(llm_prompt, context=context)

                    result["success"] = True
                    result["output"] = response

                    # Add to memory
                    self.memory.add_step(
                        action=f"LLM: {llm_prompt[:100]}...",
                        result=response[:500] if response else "No response",
                        is_key=True
                    )
                except Exception as e:
                    result["success"] = False
                    result["error"] = str(e)
            else:
                result["success"] = False
                result["error"] = "No LLM agent configured"

        # Track in execution trace
        self.execution_trace.append(result)

        return result

    def _build_llm_context(self) -> str:
        """Build the context for LLM inference."""
        parts = []

        # Add memory context
        memory_context = self.memory.get_context_window(max_tokens=8000)
        if memory_context:
            parts.append(memory_context)

        # Add tool state summary
        tool_state = self.tools.get_state_summary()
        if tool_state:
            parts.append(f"\n## Tool State\n{tool_state}")

        return "\n".join(parts)

    async def complete_task(self, success: bool, summary: str):
        """Complete the current task and generate notes."""
        if not self.context:
            return

        # Generate notes from the execution trace
        if self.execution_trace:
            await self.notes.generate_notes_from_trace(
                trace=self.execution_trace,
                task_context=f"{self.context.task_name}: {summary}"
            )

        # Save memory state
        memory_file = os.path.join(
            "assets", "memory",
            f"{self.context.task_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        )
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        self.memory.save_to_file(memory_file)

        print(f"[Orchestrator] Completed task: {self.context.task_name}")
        print(f"  Steps: {self.context.total_steps}")
        print(f"  Success: {success}")

        self.context = None

    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """Get the execution trace for the current session."""
        return self.execution_trace

    def get_memory_snapshot(self) -> str:
        """Get a snapshot of the current memory state."""
        return self.memory.get_context_window()

    def switch_persona(self, persona: str):
        """Switch the agent persona."""
        if self.agent:
            self.agent.switch_mode(persona)
            self.persona = persona
            print(f"[Orchestrator] Switched to {persona} persona")
