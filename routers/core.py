from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from routers.dependencies import ENV, UserContext, get_optional_user

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    timestamp: str
    version: str


@router.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {"message": "Unk Agent API", "docs": "/docs"}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for load balancers and Kubernetes."""
    return HealthResponse(
        status="healthy",
        environment=ENV,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )


@router.get("/health/detailed", response_model=HealthResponse)
async def health_check_detailed():
    """Detailed health check."""
    # In future: add DB check, etc.
    return HealthResponse(
        status="healthy",
        environment=ENV,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )


@router.get("/config")
async def get_config(user: UserContext = Depends(get_optional_user)):
    """Get public configuration."""
    return {
        "environment": ENV,
        "features": {
            "web_search": True,
            "code_execution": True,
            "multimodal": True
        }
    }
