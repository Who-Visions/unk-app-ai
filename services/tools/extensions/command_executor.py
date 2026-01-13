"""
Command Executor Tool Extension

Executes shell commands with retry logic and error recovery.
"""

import asyncio
import subprocess
from typing import Any, Dict, Optional

from ..base_extension import ToolExtension, ToolResult


class CommandExecutor(ToolExtension):
    """
    Tool extension for executing shell commands.

    Features:
    - Timeout handling
    - Working directory management
    - Error recovery suggestions
    - Output truncation for large results
    """

    def __init__(
        self,
        default_cwd: str = ".",
        timeout_seconds: int = 30,
        max_output_chars: int = 10000
    ):
        super().__init__(
            name="command_executor",
            description="Execute shell commands in the repository"
        )
        self.default_cwd = default_cwd
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

        # Recovery strategies for common errors
        self.recovery_strategies = [
            "Check command syntax and try again",
            "Verify the working directory exists",
            "Check if required dependencies are installed",
            "Try a simpler command to diagnose the issue"
        ]

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> ToolResult:
        """Execute a shell command."""
        working_dir = cwd or self.default_cwd
        cmd_timeout = timeout or self.timeout_seconds

        try:
            # Run the command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=cmd_timeout
            )

            output = stdout.decode("utf-8", errors="replace")
            error_output = stderr.decode("utf-8", errors="replace")

            # Truncate if needed
            if len(output) > self.max_output_chars:
                output = output[:self.max_output_chars] + "\n...[truncated]"

            success = process.returncode == 0

            return ToolResult(
                success=success,
                output=output,
                error=error_output if not success else None,
                metadata={
                    "command": command,
                    "cwd": working_dir,
                    "return_code": process.returncode
                }
            )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {cmd_timeout} seconds",
                metadata={"command": command},
                retry_suggestion="Consider increasing timeout or optimizing the command"
            )

    def get_prompt_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (optional)"
                    }
                },
                "required": ["command"]
            }
        }
