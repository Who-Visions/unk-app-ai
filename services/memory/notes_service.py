"""
Persistent Note-Taking for Cross-Session Continual Learning

Inspired by Confucius SDK, this module implements a note-taking system that:
1. Captures repo conventions, successful strategies, and failure patterns
2. Stores notes as long-term memory in structured markdown
3. Retrieves relevant notes based on context keywords
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Try to import Gemini for note generation
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


@dataclass
class Note:
    """A single note capturing learned knowledge."""
    id: str
    category: str  # "convention", "strategy", "failure", "gotcha"
    title: str
    content: str
    context: str  # What task/repo this was learned from
    keywords: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    relevance_score: float = 1.0


class PersistentNotes:
    """
    Implements persistent note-taking for cross-session learning.

    Key Features:
    - Auto-generates notes from execution traces
    - Categorizes notes (conventions, strategies, failures, gotchas)
    - Keyword-based retrieval for relevant context
    - Markdown storage for human readability
    """

    NOTES_DIR = "assets/notes"
    INDEX_FILE = "notes_index.json"

    CATEGORIES = {
        "convention": "Repo conventions and coding patterns",
        "strategy": "Successful strategies that worked",
        "failure": "Patterns that caused failures",
        "gotcha": "Tricky issues and edge cases"
    }

    def __init__(
        self,
        notes_dir: Optional[str] = None,
        summarization_model: str = "gemini-3-flash-preview"
    ):
        self.notes_dir = notes_dir or self.NOTES_DIR
        self.summarization_model = summarization_model
        self.notes: List[Note] = []

        # Initialize Gemini client for note generation
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
                print(f"[PersistentNotes] Gemini init error: {e}")

        # Ensure notes directory exists
        os.makedirs(self.notes_dir, exist_ok=True)

        # Load existing notes index
        self._load_index()

    def _load_index(self):
        """Load the notes index from disk."""
        index_path = os.path.join(self.notes_dir, self.INDEX_FILE)
        if os.path.exists(index_path):
            try:
                with open(index_path, "r") as f:
                    data = json.load(f)
                    self.notes = [
                        Note(
                            id=n["id"],
                            category=n["category"],
                            title=n["title"],
                            content=n["content"],
                            context=n["context"],
                            keywords=n["keywords"],
                            created_at=n.get("created_at", ""),
                            relevance_score=n.get("relevance_score", 1.0)
                        )
                        for n in data.get("notes", [])
                    ]
                    print(f"[Notes] Loaded {len(self.notes)} notes from index")
            except Exception as e:
                print(f"[Notes] Error loading index: {e}")

    def _save_index(self):
        """Save the notes index to disk."""
        index_path = os.path.join(self.notes_dir, self.INDEX_FILE)
        data = {
            "notes": [
                {
                    "id": n.id,
                    "category": n.category,
                    "title": n.title,
                    "content": n.content,
                    "context": n.context,
                    "keywords": n.keywords,
                    "created_at": n.created_at,
                    "relevance_score": n.relevance_score
                }
                for n in self.notes
            ]
        }
        with open(index_path, "w") as f:
            json.dump(data, f, indent=2)

    def write_note(
        self,
        category: str,
        title: str,
        content: str,
        context: str,
        keywords: Optional[List[str]] = None
    ) -> Note:
        """Write a new note to persistent storage."""
        note_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        note = Note(
            id=note_id,
            category=category,
            title=title,
            content=content,
            context=context,
            keywords=keywords or []
        )

        self.notes.append(note)

        # Write markdown file for human readability
        self._write_markdown(note)

        # Update index
        self._save_index()

        print(f"[Notes] Wrote note: {title}")
        return note

    def _write_markdown(self, note: Note):
        """Write a note as a markdown file."""
        category_dir = os.path.join(self.notes_dir, note.category)
        os.makedirs(category_dir, exist_ok=True)

        filepath = os.path.join(category_dir, f"{note.id}.md")

        md_content = f"""# {note.title}

**Category**: {note.category}
**Context**: {note.context}
**Created**: {note.created_at}
**Keywords**: {', '.join(note.keywords)}

---

{note.content}
"""

        with open(filepath, "w") as f:
            f.write(md_content)

    def get_notes_for_context(
        self,
        keywords: List[str],
        categories: Optional[List[str]] = None,
        max_notes: int = 5
    ) -> List[Note]:
        """Retrieve relevant notes based on keywords and categories."""
        relevant_notes = []

        for note in self.notes:
            # Filter by category if specified
            if categories and note.category not in categories:
                continue

            # Score by keyword match
            score = 0
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in note.title.lower():
                    score += 2
                if keyword_lower in note.content.lower():
                    score += 1
                if keyword_lower in [k.lower() for k in note.keywords]:
                    score += 3

            if score > 0:
                relevant_notes.append((note, score))

        # Sort by score and return top N
        relevant_notes.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in relevant_notes[:max_notes]]

    def format_notes_for_prompt(self, notes: List[Note]) -> str:
        """Format notes for inclusion in an LLM prompt."""
        if not notes:
            return ""

        parts = ["## Relevant Notes from Previous Sessions\n"]
        for note in notes:
            parts.append(f"### {note.title} ({note.category})")
            parts.append(f"{note.content[:500]}...")
            parts.append("")

        return "\n".join(parts)

    async def generate_notes_from_trace(
        self,
        trace: List[Dict[str, Any]],
        task_context: str
    ) -> List[Note]:
        """Auto-generate notes from an execution trace using Gemini."""
        if not self.client:
            return []

        # Format the trace for the LLM
        trace_text = "\n".join([
            f"Step {i+1}: {step.get('action', 'unknown')}\n"
            f"Result: {str(step.get('result', ''))[:300]}..."
            for i, step in enumerate(trace[-20:])  # Last 20 steps
        ])

        prompt = f"""Analyze this agent execution trace and extract reusable knowledge.

Task Context: {task_context}

Execution Trace:
{trace_text}

Generate 1-3 notes in the following JSON format:
[
  {{
    "category": "convention|strategy|failure|gotcha",
    "title": "Short descriptive title",
    "content": "Detailed explanation of the learning",
    "keywords": ["keyword1", "keyword2"]
  }}
]

Focus on:
- Patterns that worked or failed
- Repo-specific conventions discovered
- Tricky edge cases or gotchas

Return ONLY the JSON array, no other text."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.summarization_model,
                contents=prompt
            )

            # Parse the response
            import re
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                notes_data = json.loads(json_match.group())
                generated_notes = []
                for note_data in notes_data:
                    note = self.write_note(
                        category=note_data.get("category", "gotcha"),
                        title=note_data.get("title", "Untitled"),
                        content=note_data.get("content", ""),
                        context=task_context,
                        keywords=note_data.get("keywords", [])
                    )
                    generated_notes.append(note)
                return generated_notes
        except Exception as e:
            print(f"[Notes] Error generating notes: {e}")

        return []

    def get_all_notes(self) -> List[Note]:
        """Get all stored notes."""
        return self.notes

    def get_notes_by_category(self, category: str) -> List[Note]:
        """Get all notes in a specific category."""
        return [n for n in self.notes if n.category == category]
