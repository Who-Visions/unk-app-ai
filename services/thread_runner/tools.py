"""
Thread Runner Tools
===================
The "Shipping Layer" tools exposed to the agent.
Matches the photographer's assistant metaphor.
"""

import os
import subprocess
from typing import Dict, Any, List

# Placeholder implementations - in a real scenario, these would call actual logic
# or be imported from `skills/` if they exist.

def repo_read(file_path: str, line_range: str = None) -> str:
    """Reads a file from the repo. Optionally reads a range (e.g., '10-20')."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if line_range:
            start, end = map(int, line_range.split("-"))
            # 1-based indexing for user friendly interface
            content = "".join(lines[start-1:end])
        else:
            content = "".join(lines)
        return content
    except Exception as e:  # pylint: disable=W0718
        return f"Error reading file: {e}"

def repo_search(query: str, path: str = ".") -> List[str]:
    """Searches the repo for a text pattern (recursive)."""
    matches = []
    try:
        # Using grep for speed if available, or python fallback?
        # Python fallback is safer for cross-platform (Windows) without depending on grep
        for root, _, files in os.walk(path):
            if "venv" in root or "__pycache__" in root or ".git" in root:
                continue
            for file in files:
                if file.endswith((".py", ".md", ".txt", ".json")):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if query in content:
                                matches.append(f"Found in {full_path}")
                                if len(matches) > 20: # Limit results
                                    return matches
                    except:
                        pass
        return matches if matches else ["No matches found."]
    except Exception as e:  # pylint: disable=W0718
        return [f"Search error: {e}"]

def repo_edit_apply_patch(target_file: str, patch_content: str) -> str:
    """
    Overwrites a file with new content.
    For refactoring, we currently support full-file replacement for safety,
    or simple string replacement if patch_content has specific markers.
    """
    try:
        # Backup first
        if os.path.exists(target_file):
            import shutil
            shutil.copy(target_file, f"{target_file}.bak")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(patch_content)
        return f"Successfully updated {target_file} (Backup saved as .bak)"
    except Exception as e:  # pylint: disable=W0718
        return f"Edit failed: {e}"

def run_tests(command: str = "pytest") -> Dict[str, Any]:
    """Runs tests locally."""
    try:
        # Security: In strict environment, validate command. For now we assume isolated container
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return {
            "status": "pass" if result.returncode == 0 else "fail",
            "output": result.stdout + "\n" + result.stderr
        }
    except Exception as e:  # pylint: disable=W0718
        return {"status": "error", "output": str(e)}

def lint_format(path: str = ".") -> str:
    """Runs styling checks (black/isort)."""
    try:
        # Try black
        r_black = subprocess.run(f"python -m black --check {path}", shell=True, capture_output=True, text=True)
        if r_black.returncode == 0:
            return "✅ formatting checks passed."
        else:
            return f"❌ formatting issues:\n{r_black.stderr[:500]}"
    except Exception as e:  # pylint: disable=W0718
        return f"Lint failed: {e}"

def create_branch_commit(branch_name: str, message: str) -> str:
    """Creates a git branch and commits changes."""
    return f"Created branch {branch_name} with commit '{message}'"

def open_pr(title: str, description: str) -> str:
    """Opens a Pull Request."""
    return "PR #123 opened: " + title

def fetch_ticket_context(ticket_id: str) -> str:
    """Fetches context from Jira/Linear/GitHub Issues."""
    return f"Ticket {ticket_id}: Fix the login bug..."

def retrieve_docs_rag(query: str) -> str:
    """Retrieves relevant documentation via Vertex AI RAG."""
    return f"Documentation for {query}..."

def notify_user(message: str, channel: str = "slack") -> str:
    """Sends a notification to the user."""
    return f"Sent to {channel}: {message}"

# Export tool list for the agent
THREAD_TOOLS = [
    repo_read,
    repo_search,
    repo_edit_apply_patch,
    run_tests,
    lint_format,
    create_branch_commit,
    open_pr,
    fetch_ticket_context,
    retrieve_docs_rag,
    notify_user # ,
    # search_codebase_semantically # Added below via dynamic append to avoid cycle if imported at top
]

# Lazy Import Helper
def _add_lazy_tools():
    try:
        from tools.vector_store_bigquery import search_codebase_semantically
        THREAD_TOOLS.append(search_codebase_semantically)
    except ImportError:
        pass

_add_lazy_tools()
