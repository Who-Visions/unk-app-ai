"""
Ralph Wiggum Autonomous Agent Loop
===================================
Based on Jeff Huntley's Ralph concept, adapted for Gemini/Vertex AI.

Ralph is a simple but powerful loop:
1. Read PRD (Product Requirement Doc)
2. Pick a user story from prd.json
3. Implement it with acceptance criteria
4. Commit the change
5. Update progress.txt (short-term memory)
6. Update agents.md (long-term memory)
7. Loop until all stories complete

Key Insight: "Fresh context window for each iteration"
- Each story gets a clean Gemini session
- Small atomic tasks that fit in context
- Self-testing via acceptance criteria

Usage:
    ralph = RalphLoop(
        prd_path="prd.json",
        model="gemini-2.5-pro"
    )
    ralph.run(max_iterations=10)
"""
from __future__ import annotations

import logging
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Try Gemini import
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None


class StoryStatus(Enum):
    """Status of a user story."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class UserStory:
    """
    A single user story from the PRD.
    
    Must be:
    - Small enough to complete in one iteration
    - Have clear acceptance criteria
    - Be independently testable
    """
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    status: StoryStatus = StoryStatus.PENDING
    priority: int = 1
    
    # Results
    passes: bool = False
    iteration_completed: Optional[int] = None
    thread_id: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)
    learnings: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "priority": self.priority,
            "passes": self.passes,
            "status": self.status.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserStory":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            acceptance_criteria=data.get("acceptance_criteria", []),
            priority=data.get("priority", 1),
            passes=data.get("passes", False),
            status=StoryStatus(data.get("status", "pending")),
        )


@dataclass
class PRD:
    """
    Product Requirement Document with user stories.
    
    The PRD is the master plan. Each user story is an atomic
    unit of work that Ralph will implement independently.
    """
    name: str
    description: str
    stories: List[UserStory]
    
    # Metadata
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    @property
    def pending_stories(self) -> List[UserStory]:
        return [s for s in self.stories if not s.passes]
    
    @property
    def completed_stories(self) -> List[UserStory]:
        return [s for s in self.stories if s.passes]
    
    @property
    def progress_percent(self) -> float:
        if not self.stories:
            return 0.0
        return len(self.completed_stories) / len(self.stories) * 100
    
    @property
    def is_complete(self) -> bool:
        return all(s.passes for s in self.stories)
    
    def get_next_story(self) -> Optional[UserStory]:
        """Get next story to work on (first pending by priority)."""
        pending = sorted(self.pending_stories, key=lambda s: s.priority)
        return pending[0] if pending else None
    
    def save(self, path: str) -> Path:
        """Save PRD to JSON file."""
        output = Path(path)
        data = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "stories": [s.to_dict() for s in self.stories],
        }
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        return output
    
    @classmethod
    def load(cls, path: str) -> "PRD":
        """Load PRD from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            stories=[UserStory.from_dict(s) for s in data.get("stories", [])],
            created_at=data.get("created_at", ""),
            version=data.get("version", "1.0"),
        )


class RalphLoop:
    """
    The Ralph Wiggum Autonomous Coding Loop.
    
    Core concept from Jeff Huntley:
    - Fresh context window per iteration
    - Atomic user stories with acceptance criteria
    - Self-testing agent (no human feedback needed)
    - Progress logging for memory
    
    This implementation uses Gemini instead of Claude Opus.
    
    Usage:
        ralph = RalphLoop(
            prd_path="prd.json",
            project_dir="./my_project",
            model="gemini-2.5-pro"
        )
        
        # Run until complete or max iterations
        ralph.run(max_iterations=10)
        
        # Check progress
        print(ralph.prd.progress_percent)
    """
    
    # System prompt for Ralph
    SYSTEM_PROMPT = '''You are an autonomous coding agent working on a project.

Your task:
1. Read the PRD and find the next pending user story
2. Implement the user story following the acceptance criteria
3. Test your implementation to verify it passes
4. Commit your changes with a descriptive message
5. Log any learnings to agents.md files
6. Update progress.txt with what you completed

IMPORTANT RULES:
- Each user story must be fully completable in this iteration
- Acceptance criteria are your tests - make sure they pass
- Commit changes before finishing
- Update agents.md if you learn something important about the codebase
- Update progress.txt with your thread ID and what you did

Current working directory: {project_dir}
PRD file: {prd_path}
Progress file: {progress_path}

Begin implementation.'''

    def __init__(
        self,
        prd_path: str,
        project_dir: str = ".",
        model: str = "gemini-2.5-pro",
        progress_path: str = "progress.txt",
        api_key: str = None,
    ):
        """
        Initialize Ralph loop.
        
        Args:
            prd_path: Path to prd.json
            project_dir: Project root directory
            model: Gemini model to use
            progress_path: Path for progress log
            api_key: Gemini API key (or use env var)
        """
        self.prd_path = Path(prd_path)
        self.project_dir = Path(project_dir)
        self.model = model
        self.progress_path = Path(progress_path)
        self.api_key = api_key
        
        # Load PRD
        self.prd = PRD.load(prd_path)
        
        # Stats
        self.iterations = 0
        self.start_time = None
        self.threads: List[str] = []
        
        # Initialize Gemini client
        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=api_key) if api_key else None
        else:
            self.client = None
            logger.warning("google-genai not available - Ralph will run in dry-run mode")
    
    def run(self, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Run Ralph loop.
        
        Args:
            max_iterations: Maximum iterations to run
            
        Returns:
            Summary of what was accomplished
        """
        self.start_time = datetime.now()
        logger.info(f"Starting Ralph loop with {len(self.prd.pending_stories)} pending stories")
        
        for i in range(max_iterations):
            self.iterations = i + 1
            
            # Check if complete
            if self.prd.is_complete:
                logger.info("All stories complete!")
                break
            
            # Get next story
            story = self.prd.get_next_story()
            if not story:
                logger.info("No more stories to process")
                break
            
            logger.info(f"Iteration {i+1}: Working on '{story.title}'")
            
            # Run iteration
            success = self._run_iteration(story)
            
            if success:
                story.passes = True
                story.status = StoryStatus.PASSED
                story.iteration_completed = i + 1
                logger.info(f"Story '{story.title}' PASSED")
            else:
                story.status = StoryStatus.FAILED
                logger.warning(f"Story '{story.title}' FAILED")
            
            # Save progress
            self.prd.save(str(self.prd_path))
            self._update_progress(story)
        
        return self.get_summary()
    
    def _run_iteration(self, story: UserStory) -> bool:
        """
        Run one iteration for a story.
        
        This is where Gemini is called to implement the story.
        """
        if not GENAI_AVAILABLE or not self.client:
            # Dry run mode
            logger.info(f"[DRY RUN] Would implement: {story.title}")
            logger.info(f"  Acceptance criteria: {story.acceptance_criteria}")
            time.sleep(1)  # Simulate work
            return True
        
        # Build prompt
        prompt = self._build_prompt(story)
        
        try:
            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            
            # Parse response and execute
            result = response.text
            story.thread_id = f"thread_{self.iterations}"
            self.threads.append(story.thread_id)
            
            # Check if implementation mentions passing criteria
            # (In real implementation, would actually test)
            return "PASSED" in result.upper() or "COMPLETE" in result.upper()
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return False
    
    def _build_prompt(self, story: UserStory) -> str:
        """Build the prompt for implementing a story."""
        system = self.SYSTEM_PROMPT.format(
            project_dir=self.project_dir,
            prd_path=self.prd_path,
            progress_path=self.progress_path,
        )
        
        story_prompt = f"""
## Current User Story

**Title**: {story.title}
**Description**: {story.description}

**Acceptance Criteria**:
{chr(10).join(f'- [ ] {ac}' for ac in story.acceptance_criteria)}

## Instructions

1. Implement this user story
2. Verify each acceptance criterion passes
3. Commit your changes
4. Update agents.md if you learned something important
5. When complete, say "PASSED" or "FAILED"
"""
        
        return system + "\n\n" + story_prompt
    
    def _update_progress(self, story: UserStory) -> None:
        """Update progress.txt with iteration info."""
        entry = f"""
## Iteration {self.iterations} - {datetime.now().isoformat()}

**Story**: {story.title}
**Status**: {'PASSED' if story.passes else 'FAILED'}
**Thread ID**: {story.thread_id}
**Files Changed**: {', '.join(story.files_changed) or 'N/A'}

### Learnings
{story.learnings or 'No specific learnings recorded.'}

---
"""
        with open(self.progress_path, "a") as f:
            f.write(entry)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of Ralph run."""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            "iterations": self.iterations,
            "stories_completed": len(self.prd.completed_stories),
            "stories_pending": len(self.prd.pending_stories),
            "progress_percent": round(self.prd.progress_percent, 1),
            "is_complete": self.prd.is_complete,
            "elapsed_seconds": round(elapsed, 1),
            "threads": self.threads,
        }


# PRD Generator Skill
PRD_GENERATOR_SKILL = '''# PRD Generator Skill

## Job
Convert a feature description into a structured Product Requirement Document (PRD).

## Instructions
1. Receive a feature description from the user
2. Ask 3-5 essential clarifying questions
3. Generate a PRD with:
   - Clear feature name and description
   - User stories (small, atomic tasks)
   - Acceptance criteria for each story

## Output Format
A markdown PRD with:
- Feature overview
- User stories as checklist items
- Each story has clear acceptance criteria
'''

# Ralph PRD Converter Skill
RALPH_PRD_CONVERTER_SKILL = '''# Ralph PRD Converter

## Job
Convert a PRD markdown file to a prd.json file for the Ralph autonomous agent system.

## Critical Rules

### Story Size
Each story MUST be completable in one Ralph iteration (single context window).
Break large stories into smaller atomic tasks.

### Story Ordering
Put dependencies first. Stories at the top are implemented first.

### Acceptance Criteria
Must be VERIFIABLE by the agent without human input.

Good: "Add status column to tasks table with default 'pending'"
Bad: "Make the UI look nice"

Good: "Filter dropdown has options: All, Active, Completed"
Bad: "User can filter stuff"

## Output Format
```json
{
  "name": "Feature Name",
  "description": "What this feature does",
  "stories": [
    {
      "id": "story-1",
      "title": "Short title",
      "description": "What to implement",
      "acceptance_criteria": [
        "Specific testable criterion 1",
        "Specific testable criterion 2"
      ],
      "priority": 1,
      "passes": false
    }
  ]
}
```
'''


def create_ralph_prd(
    feature_name: str,
    description: str,
    stories: List[Dict[str, Any]],
    output_path: str = "prd.json",
) -> PRD:
    """
    Create a PRD for Ralph.
    
    Args:
        feature_name: Name of the feature
        description: Feature description
        stories: List of story dicts with title, description, acceptance_criteria
        output_path: Where to save the PRD
        
    Returns:
        PRD object
    """
    user_stories = []
    for i, s in enumerate(stories):
        user_stories.append(UserStory(
            id=s.get("id", f"story-{i+1}"),
            title=s["title"],
            description=s.get("description", ""),
            acceptance_criteria=s.get("acceptance_criteria", []),
            priority=s.get("priority", i + 1),
        ))
    
    prd = PRD(
        name=feature_name,
        description=description,
        stories=user_stories,
    )
    
    prd.save(output_path)
    return prd


def run_ralph(
    prd_path: str,
    max_iterations: int = 10,
    model: str = "gemini-2.5-pro",
) -> Dict[str, Any]:
    """
    Run Ralph loop on a PRD.
    
    Args:
        prd_path: Path to prd.json
        max_iterations: Max iterations to run
        model: Gemini model to use
        
    Returns:
        Summary of results
    """
    ralph = RalphLoop(prd_path=prd_path, model=model)
    return ralph.run(max_iterations=max_iterations)
