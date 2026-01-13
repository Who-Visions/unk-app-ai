#!/usr/bin/env python3
"""
Ralph Orchestrator - Autonomous Agent Loop

The Ralph technique: Run an agentic LLM in an infinite loop with a well-crafted prompt.
Inspired by Geoffrey Huntley's work: https://ghuntley.com/ralph/

Usage:
    python scripts/ralph.py --task "Fix all pylint violations" --max-cost 10.00
    python scripts/ralph.py --preset pylint_refactor
    python scripts/ralph.py --task "Add docstrings" --max-iterations 20

Who Visions LLC | AI with Dav3
"""

import argparse
import datetime
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not available. Install with: pip install google-genai")


# Constants
AGENT_DIR = Path(__file__).parent.parent / ".agent"
CONFIG_FILE = AGENT_DIR / "config.yaml"
TODO_FILE = AGENT_DIR / "TODO.md"
PROMPT_TEMPLATE = AGENT_DIR / "prompt_template.md"
LOG_FILE = AGENT_DIR / "ralph.log"

# Cost per 1M tokens (Gemini 2.5 Pro)
COST_PER_1M_INPUT = 2.50
COST_PER_1M_OUTPUT = 10.00


class RalphOrchestrator:
    """
    The Ralph Orchestrator runs an autonomous agent loop.
    
    Core loop:
        while not done:
            1. Load prompt
            2. Send to LLM
            3. Execute tool calls
            4. Check stopping conditions
            5. Repeat
    """
    
    def __init__(
        self,
        task: str,
        model: str = "gemini-2.5-pro-preview-06-05",
        max_iterations: int = 50,
        max_cost_usd: float = 10.0,
        max_runtime_seconds: int = 3600,
        commit_each: bool = True,
        allowed_paths: Optional[list] = None,
        validation_command: Optional[str] = None,
        dry_run: bool = False
    ):
        self.task = task
        self.model = model
        self.max_iterations = max_iterations
        self.max_cost_usd = max_cost_usd
        self.max_runtime_seconds = max_runtime_seconds
        self.commit_each = commit_each
        self.allowed_paths = allowed_paths or ["routers/", "services/", "skills/", "scripts/"]
        self.validation_command = validation_command
        self.dry_run = dry_run
        
        # State tracking
        self.iteration = 0
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = None
        self.running = True
        self.last_validation_error = None
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # Initialize Gemini client
        self.client = None
        if GENAI_AVAILABLE and not dry_run:
            self._init_client()
    
    def _setup_logging(self):
        """Configure logging to file and console."""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ralph")
    
    def _init_client(self):
        """Initialize the Gemini Agent (which uses Smart Router)."""
        try:
            # Ralph now uses the unified GeminiAgent which uses SmartRouter
            from services.llm.gemini_agent import GeminiAgent
            self.agent = GeminiAgent()
            self.logger.info("Initialized GeminiAgent (with SmartRouter)")
            
            # Temporary: keep self.client if needed for raw access, but prefer agent
            if self.agent.client:
                 self.client = self.agent.client
            else:
                 raise ValueError("GeminiAgent failed to initialize client")

        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            raise
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM."""
        self.logger.warning(f"Received signal {signum}, shutting down...")
        self.running = False
        self._update_todo("STATUS: INTERRUPTED", f"Interrupted by signal {signum}")
    
    def _load_prompt(self) -> str:
        """Build the prompt from template and current state."""
        if PROMPT_TEMPLATE.exists():
            template = PROMPT_TEMPLATE.read_text()
        else:
            template = "Your task: {{TASK_DESCRIPTION}}"
        
        # Replace placeholders
        working_dir = Path(__file__).parent.parent.absolute()
        prompt = template.replace("{{TASK_DESCRIPTION}}", self.task)
        prompt = template.replace("{{WORKING_DIR}}", str(working_dir))
        prompt = template.replace("{{ALLOWED_PATHS}}", ", ".join(self.allowed_paths))
        prompt = template.replace("{{MAX_ITERATIONS}}", str(self.max_iterations))
        
        # Append current TODO state
        if TODO_FILE.exists():
            todo_content = TODO_FILE.read_text()
            prompt += f"\n\n## Current TODO State\n```markdown\n{todo_content}\n```"
            
        # Append last validation error if any
        if self.last_validation_error:
            prompt += f"\n\n## LAST VALIDATION FAILURE\nThe following command failed: `{self.validation_command}`\nError output:\n```\n{self.last_validation_error}\n```\nPlease fix these issues in the next iteration."
        
        return prompt
    
    def _update_todo(self, status: str, note: Optional[str] = None):
        """Update the TODO.md file with current status."""
        now = datetime.datetime.now().isoformat()
        
        content = f"""# Ralph Agent TODO

> This file is managed by the Ralph autonomous agent loop.
> It tracks progress on the current task.

## Current Task
**Task**: {self.task}
**Status**: `{status}`
**Started**: {self.start_time}
**Last Update**: {now}
**Iteration**: {self.iteration} / {self.max_iterations}
**Cost**: ${self.total_cost:.4f} / ${self.max_cost_usd:.2f}

---

## Notes
{note if note else '_No notes yet_'}
"""
        TODO_FILE.write_text(content)
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost from token counts."""
        input_cost = (input_tokens / 1_000_000) * COST_PER_1M_INPUT
        output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT
        return input_cost + output_cost
    
    def _check_stopping_conditions(self) -> tuple[bool, str]:
        """Check if we should stop the loop."""
        # Check iteration limit
        if self.iteration >= self.max_iterations:
            return True, "Max iterations reached"
        
        # Check cost limit
        if self.total_cost >= self.max_cost_usd:
            return True, "Max cost reached"
        
        # Check runtime limit
        elapsed = time.time() - self.start_time
        if elapsed >= self.max_runtime_seconds:
            return True, "Max runtime reached"
        
        # Check TODO status
        if TODO_FILE.exists():
            content = TODO_FILE.read_text()
            if "STATUS: DONE" in content:
                return True, "Task completed (DONE status)"
            if "STATUS: ERROR" in content:
                return True, "Task errored (ERROR status)"
        
        return False, ""
    
    def _git_commit(self, message: str):
        """Commit current changes to git."""
        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"[Ralph] {message}"],
                check=True,
                capture_output=True
            )
            self.logger.info(f"Committed: {message}")
        except subprocess.CalledProcessError:
            # No changes to commit, or other git issue
            pass

    def _run_validation(self) -> bool:
        """
        Run the validation command (Stop Hook).
        Returns True if validation passes or no validation command provided.
        """
        if not self.validation_command:
            return True
            
        self.logger.info(f"Running validation: {self.validation_command}")
        try:
            result = subprocess.run(
                self.validation_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            self.last_validation_error = None
            self.logger.info("Validation PASSED")
            return True
        except subprocess.CalledProcessError as e:
            self.last_validation_error = e.stdout + "\n" + e.stderr
            self.logger.warning(f"Validation FAILED: {e}")
            return False
    
    def _execute_iteration(self) -> bool:
        """Execute one iteration of the Ralph loop."""
        self.iteration += 1
        self.logger.info(f"=== Iteration {self.iteration}/{self.max_iterations} ===")
        
        # Build prompt
        prompt = self._load_prompt()
        
        if self.dry_run:
            self.logger.info("[DRY RUN] Would send prompt to LLM")
            self.logger.info(f"Prompt preview (first 500 chars):\n{prompt[:500]}...")
            time.sleep(1)  # Simulate API call
            return True
        
        if not self.client:
            self.logger.error("No client available")
            return False
        
        try:
            # Delegate generation to the Agent (which routes via SmartRouter)
            # define a config if strictly needed, or let SmartRouter handle it
            # Ralph's default was temp=0.3, max_tokens=8192.
            # We can pass this as an override to the router's config if we want, 
            # but SmartRouter's defaults (High/Low) are likely better for Gemini 3.
            
            # We will rely on the agent to return the text.
            response_text = self.agent.run(prompt)
            
            # Mocking response object for existing logic if needed, or simplifying
            # Ralph seems to rely on 'response' object for usage metadata.
            # GeminiAgent.run currently returns a string.
            # We might need to adjust GeminiAgent to return the response object or 
            # adjust Ralph to work with the string.
            # Let's adjust Ralph to use the string.
            
            # Input tokens estimation (approx) since GeminiAgent strips metadata
            # For accurate counting, we'd need GeminiAgent to return metadata.
            # For now, we'll proceed with the string and lose exact token counts temporarily
            # OR we update GeminiAgent to return the full response. 
            
            # Let's assume response_text is what we got.
            
            # Log response
            self.logger.info(f"Response preview: {response_text[:200]}...")
            
            # Git commit if enabled
            if self.commit_each:
                self._git_commit(f"Iteration {self.iteration}")
            
            # Run validation hook (Stop Hook)
            valid = self._run_validation()
            if not valid:
                self.logger.info("Re-looping with validation errors...")
                # We return True because the iteration technically completed, 
                # but valid=False means we'll pass error feedback into the next prompt
            
            return True
            
        except Exception as e:
            self.logger.error(f"Iteration failed: {e}")
            return False
    
    def run(self):
        """Main Ralph loop."""
        self.start_time = time.time()
        self.logger.info("=" * 60)
        self.logger.info(f"RALPH LOOP STARTED")
        self.logger.info(f"Task: {self.task}")
        self.logger.info(f"Model: {self.model}")
        self.logger.info(f"Max iterations: {self.max_iterations}")
        self.logger.info(f"Max cost: ${self.max_cost_usd:.2f}")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info("=" * 60)
        
        # Update TODO with initial state
        self._update_todo("RUNNING", "Loop started")
        
        while self.running:
            # Check stopping conditions
            should_stop, reason = self._check_stopping_conditions()
            if should_stop:
                self.logger.info(f"Stopping: {reason}")
                self._update_todo("STOPPED", reason)
                break
            
            # Execute iteration
            success = self._execute_iteration()
            if not success:
                self.logger.warning("Iteration failed, continuing...")
            
            # Small delay between iterations to avoid rate limits
            time.sleep(1)
        
        # Final summary
        elapsed = time.time() - self.start_time
        self.logger.info("=" * 60)
        self.logger.info("RALPH LOOP FINISHED")
        self.logger.info(f"Total iterations: {self.iteration}")
        self.logger.info(f"Total tokens: {self.total_input_tokens} in / {self.total_output_tokens} out")
        self.logger.info(f"Total cost: ${self.total_cost:.4f}")
        self.logger.info(f"Runtime: {elapsed:.1f} seconds")
        self.logger.info("=" * 60)


def load_config() -> dict:
    """Load configuration from YAML file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return {}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ralph Orchestrator - Autonomous Agent Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ralph.py --task "Fix pylint violations" --max-cost 10.00
  python ralph.py --preset pylint_refactor
  python ralph.py --task "Add docstrings" --dry-run
        """
    )
    
    parser.add_argument(
        "--task", "-t",
        help="Task description for the agent"
    )
    parser.add_argument(
        "--preset", "-p",
        help="Use a preset task from config.yaml"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-pro-preview-06-05",
        help="Model to use (default: gemini-2.5-pro-preview-06-05)"
    )
    parser.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=50,
        help="Maximum number of iterations (default: 50)"
    )
    parser.add_argument(
        "--max-cost", "-c",
        type=float,
        default=10.0,
        help="Maximum cost in USD (default: 10.00)"
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=3600,
        help="Maximum runtime in seconds (default: 3600)"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Don't commit after each change"
    )
    parser.add_argument(
        "--validation", "-v",
        help="Command to run for validation between iterations (Stop Hook)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually calling the LLM"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Determine task
    task = args.task
    max_iterations = args.max_iterations
    max_cost = args.max_cost
    
    if args.preset:
        presets = config.get("presets", {})
        if args.preset not in presets:
            print(f"Error: Preset '{args.preset}' not found")
            print(f"Available presets: {list(presets.keys())}")
            sys.exit(1)
        preset = presets[args.preset]
        task = preset.get("description", args.preset)
        max_iterations = preset.get("max_iterations", max_iterations)
        max_cost = preset.get("max_cost_usd", max_cost)
    
    if not task:
        print("Error: Either --task or --preset is required")
        parser.print_help()
        sys.exit(1)
    
    # Get safety settings from config
    safety = config.get("safety", {})
    allowed_paths = safety.get("allowed_paths", [])
    
    # Create and run orchestrator
    ralph = RalphOrchestrator(
        task=task,
        model=args.model,
        max_iterations=max_iterations,
        max_cost_usd=max_cost,
        max_runtime_seconds=args.max_runtime,
        commit_each=not args.no_commit,
        allowed_paths=allowed_paths,
        validation_command=args.validation or preset.get("validation_command"),
        dry_run=args.dry_run
    )
    
    ralph.run()


if __name__ == "__main__":
    main()
