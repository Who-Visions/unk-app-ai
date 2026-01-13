"""
Thread Runner Models
====================
Defines the schema for the "Thread" - the unit of execution.
Stores state in Firestore or BigQuery.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThreadType(str, Enum):
    BASE = "base"
    PARALLEL = "parallel"
    CHAINED = "chained"
    FUSION = "fusion"
    BIG = "big"
    LONG = "long"
    REFACTOR = "refactor"


class ThreadStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_FOR_REVIEW = "waiting_for_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCallRecord(BaseModel):
    tool_name: str
    input: Dict[str, Any]
    output_ref: Optional[str] = None  # GCS URI or concise summary
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationRecord(BaseModel):
    check: str
    status: str  # pass|fail
    evidence_ref: Optional[str] = None


class Thread(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ThreadType = ThreadType.BASE
    goal: str = Field(..., description="What to ship")

    # Context
    context_refs: List[str] = Field(
        default_factory=list, description="Repo URLs, Ticket IDs, Doc IDs")

    # Planning
    plan: List[str] = Field(default_factory=list, description="High-level plan steps")

    # Execution History
    tool_trajectory: List[ToolCallRecord] = Field(default_factory=list)

    # Validation
    validations: List[ValidationRecord] = Field(default_factory=list)
    review_needed: bool = True

    # Outcome
    final_summary: Optional[str] = ""
    status: ThreadStatus = ThreadStatus.CREATED

    # Telemetry
    metrics: Dict[str, Any] = Field(default_factory=lambda: {
                                    "tool_calls": 0, "tokens": 0, "latency_ms": 0})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
