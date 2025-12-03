# deploy.py
"""
Unk Agent - Production Deployment Server
=========================================
FastAPI ASGI server with OIDC authentication,
CORS configuration, and cognitive routing.

Who Visions LLC - AI with Dav3
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Firebase Admin for token verification
try:
    import firebase_admin
    from firebase_admin import auth, credentials
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Import our agent system
from gemini_agent import (
    UnkAgent,
    AgentFactory,
    AgentResponse,
    GEMINI_MODELS,
    get_model,
    requires_subscription,
    estimate_cost,
    create_memory_search_tool,
    create_memory_store_tool,
    calculate_growth_metrics,
    get_current_timestamp
)

# Import price tracking
from gemini_agent.price_tracker import get_tracker

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Environment
ENV = os.environ.get("ENV", "development")
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "who-visions-llc")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
PORT = int(os.environ.get("PORT", 8080))

# CORS origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://aiwithdav3.com",
    "https://www.aiwithdav3.com",
    "https://whovisions.com",
    "https://www.whovisions.com",
    # Add your Vercel/Netlify domains here
]

# Logging
logging.basicConfig(
    level=logging.INFO if ENV == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("unk-agent")


# ═══════════════════════════════════════════════════════════════════════════
# LIFECYCLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("═" * 60)
    logger.info("UNK AGENT SYSTEM INITIALIZING")
    logger.info(f"Environment: {ENV}")
    logger.info(f"GCP Project: {GCP_PROJECT}")
    logger.info(f"GCP Location: {GCP_LOCATION}")
    logger.info("═" * 60)
    
    # Initialize Firebase if available
    if FIREBASE_AVAILABLE and not firebase_admin._apps:
        try:
            # Uses Application Default Credentials in GCP
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized")
        except Exception as e:
            logger.warning(f"Firebase initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("UNK AGENT SYSTEM SHUTTING DOWN")


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Unk Agent API",
    description="Multi-model cognitive agent with dynamic routing",
    version="1.0.0",
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ENV == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Processing-Time"]
)


# ═══════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class UserContext(BaseModel):
    """Authenticated user context."""
    uid: str
    email: Optional[str] = None
    plan: str = "free"  # free, pro, enterprise
    display_name: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat endpoint request payload."""
    message: str = Field(..., min_length=1, max_length=32000)
    mode: str = Field(default="default", description="Cognitive tier to use")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    enable_memory: bool = Field(default=True, description="Enable RAG memory")
    force_structured: bool = Field(default=False, description="Force JSON output")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Analyze the architecture for a multi-tenant SaaS platform",
                "mode": "unk_mode",
                "session_id": "sess_abc123",
                "enable_memory": True
            }
        }


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    success: bool
    data: Optional[AgentResponse] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    request_id: str
    processing_time_ms: float


class ModelInfo(BaseModel):
    """Public model information."""
    mode: str
    tier: str
    description: str
    capabilities: List[str]
    requires_subscription: bool


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str
    timestamp: str
    version: str


# ═══════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════

async def verify_token(authorization: Optional[str] = Header(None)) -> UserContext:
    """
    Verify Firebase/OIDC token and extract user context.
    
    In production, this verifies the JWT against Firebase Auth.
    In development, it accepts a dev token for testing.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
        
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
        
    token = authorization.split(" ")[1]
    
    # Development backdoor
    if ENV == "development" and token == "dev_token":
        return UserContext(
            uid="dev_user",
            email="dev@whovisions.com",
            plan="pro",
            display_name="Dev User"
        )
        
    # Production token verification
    if FIREBASE_AVAILABLE:
        try:
            decoded = auth.verify_id_token(token)
            
            # Extract custom claims for subscription tier
            plan = decoded.get("plan", "free")
            if "stripeRole" in decoded:
                plan = decoded["stripeRole"]
                
            return UserContext(
                uid=decoded["uid"],
                email=decoded.get("email"),
                plan=plan,
                display_name=decoded.get("name")
            )
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except auth.ExpiredIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[UserContext]:
    """Optional authentication - returns None if not authenticated."""
    if not authorization:
        return None
    try:
        return await verify_token(authorization)
    except HTTPException:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════

@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    """Add request ID and timing to all requests."""
    import uuid
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    response = await call_next(request)
    
    processing_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {processing_time:.2f}ms"
    )
    
    return response


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {"message": "Unk Agent API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for load balancers and Kubernetes."""
    return HealthResponse(
        status="healthy",
        environment=ENV,
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )


@app.get("/models", response_model=List[ModelInfo])
async def list_models(user: Optional[UserContext] = Depends(get_optional_user)):
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
            mode=mode,
            tier=spec["tier"],
            description=spec["description"],
            capabilities=spec.get("capabilities", []),
            requires_subscription=requires_subscription(mode)
        ))
        
    return models


@app.get("/models/{mode}")
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


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Primary chat endpoint.
    Routes to appropriate cognitive tier based on mode.
    """
    import uuid
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    # Validate mode
    if request.mode not in GEMINI_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{request.mode}'. Available: {list(GEMINI_MODELS.keys())}"
        )
        
    # Check subscription requirements
    if requires_subscription(request.mode):
        if user.plan not in ["pro", "enterprise"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Mode '{request.mode}' requires a Pro subscription. Current plan: {user.plan}"
            )
            
    # Build tool list
    tools = [
        calculate_growth_metrics,
        get_current_timestamp
    ]
    
    # Add memory tools if enabled
    if request.enable_memory:
        try:
            tools.append(create_memory_search_tool(GCP_PROJECT))
            tools.append(create_memory_store_tool(GCP_PROJECT))
        except Exception as e:
            logger.warning(f"Memory tools unavailable: {e}")
            
    try:
        # Create agent for this request
        agent = UnkAgent(
            mode=request.mode,
            tools=tools,
            gcp_project=GCP_PROJECT,
            gcp_location=GCP_LOCATION,
            user_context={
                "uid": user.uid if user else "anonymous",
                "email": user.email if user else None,
                "plan": user.plan if user else "free"
            }
        )
        
        # Execute the turn
        result = await agent.execute_turn(
            request.message,
            force_structured=request.force_structured
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        if isinstance(result, AgentResponse):
            return ChatResponse(
                success=True,
                data=result,
                request_id=request_id,
                processing_time_ms=processing_time
            )
        else:
            return ChatResponse(
                success=True,
                raw_response=str(result),
                request_id=request_id,
                processing_time_ms=processing_time
            )
            
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            success=False,
            error=str(e) if ENV == "development" else "Processing failed",
            request_id=request_id,
            processing_time_ms=processing_time
        )


@app.post("/chat/route")
async def routed_chat(
    request: ChatRequest,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Auto-routed chat endpoint.
    Classifies intent and routes to optimal cognitive tier.
    """
    import uuid
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Create routed agent
        agent = await AgentFactory.create_routed(
            user_input=request.message,
            tools=[calculate_growth_metrics, get_current_timestamp],
            user_tier=user.plan,
            gcp_project=GCP_PROJECT,
            gcp_location=GCP_LOCATION
        )
        
        # Execute
        result = await agent.execute_turn(
            request.message,
            force_structured=True
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            success=True,
            data=result if isinstance(result, AgentResponse) else None,
            raw_response=str(result) if not isinstance(result, AgentResponse) else None,
            request_id=request_id,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Routed chat error: {e}", exc_info=True)
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            success=False,
            error=str(e) if ENV == "development" else "Processing failed",
            request_id=request_id,
            processing_time_ms=processing_time
        )


@app.get("/usage")
async def get_usage(user: Optional[UserContext] = Depends(get_optional_user)):
    """Get usage statistics for the current user."""
    # In production, this would query Firestore or BigQuery
    return {
        "user_id": user.uid,
        "plan": user.plan if user else "free",
        "period": "current_month",
        "usage": {
            "requests": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "estimated_cost": 0.0
        },
        "limits": {
            "requests_per_month": 10000 if user.plan == "pro" else 1000,
            "unk_mode_enabled": user.plan in ["pro", "enterprise"],
            "ultrathink_enabled": user.plan == "enterprise"
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# PRICE TRACKING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/pricing/spikes")
async def get_price_spikes(
    threshold: float = 10.0,
    service: Optional[str] = None,
    days: int = 30,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Get detected price spikes.
    
    Args:
        threshold: Minimum percentage increase to consider a spike (default: 10%)
        service: Filter by service name (e.g., 'GCP')
        days: Days to look back for comparison (default: 30)
    """
    tracker = get_tracker()
    spikes = tracker.detect_spikes(
        service=service,
        threshold_percentage=threshold,
        days_lookback=days
    )
    
    return {
        "success": True,
        "count": len(spikes),
        "threshold": threshold,
        "lookback_days": days,
        "spikes": [
            {
                "timestamp": spike.timestamp,
                "service": spike.service,
                "sku_id": spike.sku_id,
                "sku_description": spike.sku_description,
                "price_type": spike.price_type,
                "previous_price": spike.previous_price,
                "current_price": spike.current_price,
                "percentage_increase": spike.percentage_increase,
                "absolute_increase": spike.absolute_increase,
                "severity": spike.severity,
                "days_since_last_check": spike.days_since_last_check
            }
            for spike in spikes
        ]
    }


@app.get("/pricing/history")
async def get_price_history(
    service: Optional[str] = None,
    sku_id: Optional[str] = None,
    price_type: Optional[str] = None,
    days: Optional[int] = None,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Get price history for tracked SKUs.
    
    Args:
        service: Filter by service name
        sku_id: Filter by SKU ID
        price_type: Filter by price type (input, output, storage, etc.)
        days: Limit to last N days
    """
    tracker = get_tracker()
    history = tracker.get_price_history(
        service=service,
        sku_id=sku_id,
        price_type=price_type,
        days=days
    )
    
    return {
        "success": True,
        "count": len(history),
        "history": [
            {
                "timestamp": snapshot.timestamp,
                "service": snapshot.service,
                "sku_id": snapshot.sku_id,
                "sku_description": snapshot.sku_description,
                "price_type": snapshot.price_type,
                "price_per_unit": snapshot.price_per_unit,
                "unit": snapshot.unit,
                "tier_start": snapshot.tier_start,
                "metadata": snapshot.metadata
            }
            for snapshot in history
        ]
    }


@app.get("/pricing/trends")
async def get_price_trends(
    service: Optional[str] = None,
    sku_id: Optional[str] = None,
    price_type: Optional[str] = None,
    days: int = 30,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Get price trend analysis for tracked SKUs.
    
    Args:
        service: Filter by service name
        sku_id: Filter by SKU ID
        price_type: Filter by price type
        days: Number of days to analyze (default: 30)
    """
    tracker = get_tracker()
    
    # Get unique combinations
    seen = set()
    trends = []
    
    for snapshot in tracker.history:
        if service and snapshot.service != service:
            continue
        if sku_id and snapshot.sku_id != sku_id:
            continue
        if price_type and snapshot.price_type != price_type:
            continue
        
        key = (snapshot.service, snapshot.sku_id, snapshot.price_type)
        if key not in seen:
            seen.add(key)
            trend = tracker.get_price_trend(
                service=snapshot.service,
                sku_id=snapshot.sku_id,
                price_type=snapshot.price_type,
                days=days
            )
            if trend["data_points"] >= 2:
                trends.append(trend)
    
    return {
        "success": True,
        "count": len(trends),
        "trends": trends
    }


@app.post("/pricing/record")
async def record_price(
    service: str,
    sku_id: str,
    sku_description: str,
    price_type: str,
    price_per_unit: float,
    unit: str,
    tier_start: Optional[float] = None,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Record a price snapshot manually.
    
    Note: In production, this should be restricted to admin users.
    """
    tracker = get_tracker()
    tracker.record_price(
        service=service,
        sku_id=sku_id,
        sku_description=sku_description,
        price_type=price_type,
        price_per_unit=price_per_unit,
        unit=unit,
        tier_start=tier_start
    )
    
    return {
        "success": True,
        "message": "Price recorded successfully"
    }


# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error" if ENV == "production" else str(exc),
            "status_code": 500
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "deploy:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info" if ENV == "production" else "debug",
        reload=ENV == "development",
        workers=1  # Cloud Run handles scaling
    )
