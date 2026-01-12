from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from google import genai
from pydantic import BaseModel

from gemini_agent.models_spec import (GEMINI_MODELS, requires_subscription)
from routers.dependencies import UserContext, get_optional_user

router = APIRouter()

class ModelInfo(BaseModel):
    """Public model information."""
    id: str
    mode: str
    tier: str
    description: str
    capabilities: List[str]
    requires_subscription: bool

# pylint: disable=too-few-public-methods, duplicate-code

class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""
    input: str | List[str]
    model: str = "text-embedding-004"

@router.get("/models", response_model=List[ModelInfo])
@router.get("/v1/models", response_model=List[ModelInfo])
async def list_models(_user: Optional[UserContext] = Depends(get_optional_user)):
    """
    List available cognitive modes.
    Returns public information about each mode.
    """
    models = []
    for mode, spec in GEMINI_MODELS.items():
        # Skip utility models like embedder
        if spec.get("tier") == "utility":
            continue

        models.append(ModelInfo(
            id=spec["model_id"],
            mode=mode,
            tier=spec["tier"],
            description=spec["description"],
            capabilities=spec.get("capabilities", []),
            requires_subscription=requires_subscription(mode)
        ))

    return models

@router.get("/models/{mode}")
async def get_model_info(
    mode: str,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """Get detailed information about a specific mode."""
    if mode not in GEMINI_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mode '{mode}' not found"
        )

    spec = GEMINI_MODELS[mode]

    # Include pricing only for authenticated users
    return {
        "mode": mode,
        "model_id": spec["model_id"],
        "tier": spec["tier"],
        "description": spec["description"],
        "capabilities": spec.get("capabilities", []),
        "context_window": spec.get("context_window"),
        "pricing": spec.get("pricing"),
        "requires_subscription": requires_subscription(mode),
        "user_has_access": (
            user.plan in ["pro", "enterprise"]
            if requires_subscription(mode)
            else True
        )
    }

@router.post("/embeddings")
@router.post("/v1/embeddings")
async def create_embeddings(
    request: EmbeddingRequest,
    _user: Optional[UserContext] = Depends(get_optional_user)
):
    """Generate vector embeddings."""
    # Simple passthrough to Gemini Embeddings
    # In production, cache this client or better yet move to a service
    client = genai.Client(vertexai=True, location="us-central1")

    try:
        result = client.models.embed_content(
            model=request.model,
            contents=request.input
        )

        # Format response to look somewhat standard
        data = []
        if hasattr(result, 'embeddings'):
            for i, emb in enumerate(result.embeddings):
                data.append({
                    "object": "embedding",
                    "index": i,
                    "embedding": emb.values
                })

        return {
            "object": "list",
            "data": data,
            "model": request.model
        }
    except Exception as e:  # pylint: disable=W0718
        raise HTTPException(status_code=500, detail=str(e)) from e
