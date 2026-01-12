from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .config import NOTION_WHO_VISIONS_SECRET, NOTION_OBSERVATORY_SECRET

from .dependencies import get_optional_user, UserContext

router = APIRouter(tags=["lore"])

class NotionWebhookPayload(BaseModel):
    source: str
    data: Dict[str, Any]

class SyncRequest(BaseModel):
    world_id: str
    force: bool = False

async def trigger_sync(
    request: SyncRequest,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """Trigger manual sync for a world."""

    # Determine which integration to use based on world_id or request
    # For 'Observatory' related worlds, use Observatory Secret
    token = NOTION_WHO_VISIONS_SECRET
    if request.world_id.lower() in ["observatory", "agents", "w2"]:
        token = NOTION_OBSERVATORY_SECRET

    return {
        "status": "sync_started",
        "world": request.world_id,
        "used_token_preview": token[:10] + "..." if token else "None"
    }


@router.post("/webhook/notion")
async def notion_webhook(payload: NotionWebhookPayload):
    """Receive updates from Notion."""
    return {"status": "received", "processing": True}



@router.get("/sync/{world_id}")
async def sync_status(world_id: str):
    """Check sync status."""
    return {"world_id": world_id, "status": "idle", "last_sync": "2024-01-01T00:00:00Z"}

@router.get("/worlds")
async def list_worlds(user: Optional[UserContext] = Depends(get_optional_user)):
    """List available worlds in LoreDB."""
    return {
        "worlds": [
            {"id": "w1", "name": "Main Timeline", "description": "Primary reality"},
            {"id": "w2", "name": "Simulation B", "description": "Test environment"}
        ]
    }

@router.get("/lore/feed")
async def get_lore_feed(limit: int = 10):
    """Get recent lore updates."""
    return {"feed": []}

@router.get("/lore/bible")
async def get_world_bible(world_id: Optional[str] = None):
    """Get the 'Bible' (canonical facts) for a world."""
    return {"title": "World Bible", "entries": []}
