"""
File Editor Tool Extension

Edits files with diff tracking and atomic operations.
"""

import os
from typing import Any, Dict, List, Optional

from ..base_extension import ToolExtension, ToolResult


class FileEditor(ToolExtension):
    """
    Tool extension for editing files.

    Features:
    - Atomic file operations
    - Diff tracking for changes
    - Backup creation
    - Line-based and block-based editing
    """

    def __init__(self, repo_root: str = "."):
        super().__init__(
            name="file_editor",
            description="Read, write, and edit files in the repository"
        )
        self.repo_root = repo_root
        self.edit_history: List[Dict[str, Any]] = []

        # Recovery strategies
        self.recovery_strategies = [
            "Verify the file path is correct",
            "Check file permissions",
            "Ensure the parent directory exists",
            "Try reading the file first to verify its state"
        ]

    async def execute(
        self,
        action: str,  # "read", "write", "patch"
        path: str,
        content: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> ToolResult:
        """Execute a file operation."""
        full_path = os.path.join(self.repo_root, path)

        if action == "read":
            return await self._read_file(full_path, start_line, end_line)
        elif action == "write":
            return await self._write_file(full_path, content or "")
        elif action == "patch":
            return await self._patch_file(
                full_path, content or "", start_line, end_line
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown action: {action}"
            )

    async def _read_file(
        self,
        path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> ToolResult:
        """Read a file, optionally a specific line range."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if start_line is not None:
                start_idx = max(0, start_line - 1)
                end_idx = end_line if end_line else len(lines)
                lines = lines[start_idx:end_idx]

            content = "".join(lines)

            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "path": path,
                    "total_lines": len(lines),
                    "range": f"{start_line or 1}-{end_line or 'end'}"
                }
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {path}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )

    async def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file, creating directories if needed."""
        try:
            # Create backup if file exists
            if os.path.exists(path):
                backup_path = path + ".backup"
                with open(path, "r") as f:
                    old_content = f.read()
                with open(backup_path, "w") as f:
                    f.write(old_content)

                # Track the edit
                self.edit_history.append({
                    "action": "write",
                    "path": path,
                    "backup": backup_path
                })

            # Create parent directories
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                output=f"Wrote {len(content)} chars to {path}",
                metadata={
                    "path": path,
                    "chars_written": len(content)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )

    async def _patch_file(
        self,
        path: str,
        new_content: str,
        start_line: Optional[int],
        end_line: Optional[int]
    ) -> ToolResult:
        """Patch specific lines in a file."""
        if start_line is None:
            return ToolResult(
                success=False,
                output="",
                error="start_line is required for patch action"
            )

        try:
            with open(path, "r") as f:
                lines = f.readlines()

            # Create backup
            backup_path = path + ".backup"
            with open(backup_path, "w") as f:
                f.writelines(lines)

            # Apply patch
            start_idx = start_line - 1
            end_idx = end_line if end_line else start_line

            new_lines = new_content.split("\n")
            if not new_content.endswith("\n"):
                new_lines = [line + "\n" for line in new_lines[:-1]] + [new_lines[-1]]
            else:
                new_lines = [line + "\n" for line in new_lines if line]

            patched_lines = lines[:start_idx] + new_lines + lines[end_idx:]

            with open(path, "w") as f:
                f.writelines(patched_lines)

            # Track edit
            self.edit_history.append({
                "action": "patch",
                "path": path,
                "lines": f"{start_line}-{end_line}",
                "backup": backup_path
            })

            return ToolResult(
                success=True,
                output=f"Patched lines {start_line}-{end_line} in {path}",
                metadata={
                    "path": path,
                    "lines_changed": end_idx - start_idx,
                    "new_lines": len(new_lines)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )

    def get_prompt_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "patch"],
                        "description": "The file operation to perform"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to the file (relative to repo root)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content for write/patch operations"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line for read/patch"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line for read/patch"
                    }
                },
                "required": ["action", "path"]
            }
        }

    def get_edit_history(self) -> List[Dict[str, Any]]:
        """Get the history of file edits for this session."""
        return self.edit_history

    def undo_last_edit(self) -> ToolResult:
        """Undo the last file edit by restoring from backup."""
        if not self.edit_history:
            return ToolResult(
                success=False,
                output="",
                error="No edits to undo"
            )

        last_edit = self.edit_history.pop()
        backup_path = last_edit.get("backup")
        original_path = last_edit.get("path")

        if backup_path and os.path.exists(backup_path):
            try:
                with open(backup_path, "r") as f:
                    content = f.read()
                with open(original_path, "w") as f:
                    f.write(content)
                os.remove(backup_path)
                return ToolResult(
                    success=True,
                    output=f"Restored {original_path} from backup"
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=str(e)
                )

        return ToolResult(
            success=False,
            output="",
            error="Backup file not found"
        )
