"""
Thread Runner API
=================
Exposes endpoints to create, monitor, and retrieve Threads.
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from services.thread_runner.models import Thread
from services.thread_runner.persistence import store
from services.thread_runner.runner import ThreadRunner

router = APIRouter(prefix="/threads", tags=["threads"])
runner = None

# Lazy init helper


def get_runner():
    global runner
    if not runner:
        # Assumes Google Cloud Project is set
        import os
        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "unk-app-480102")
        runner = ThreadRunner(project_id=project)
    return runner


class CreateThreadRequest(BaseModel):
    goal: str
    context_refs: List[str] = []
    type: str = "base"


@router.post("/", response_model=Thread)
async def create_thread(req: CreateThreadRequest, background_tasks: BackgroundTasks):
    """Creates and starts a new thread."""
    thread = Thread(
        goal=req.goal,
        context_refs=req.context_refs,
        type=req.type
    )

    # Save initial state
    await store.save_thread(thread)

    # Run in background
    runner_instance = get_runner()
    background_tasks.add_task(runner_instance.run_thread, thread)

    return thread


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """Retrieves thread status."""
    thread = await store.load_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread
