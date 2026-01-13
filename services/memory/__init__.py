"""
Memory Services Package

Confucius-inspired memory management for the Unk Agent.
"""

from .notes_service import Note, PersistentNotes
from .working_memory import HierarchicalWorkingMemory, MemoryScope, MemoryStep

__all__ = [
    "HierarchicalWorkingMemory",
    "MemoryStep",
    "MemoryScope",
    "PersistentNotes",
    "Note"
]
