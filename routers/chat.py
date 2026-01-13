"""
Chat Router
===========
Handles chat interactions, including direct chat, routed chat,
and OpenAI-compatible completions.
"""
import time
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from gemini_agent import (GEMINI_MODELS, AgentFactory, AgentResponse, UnkAgent,
                          calculate_growth_metrics, create_memory_search_tool,
                          create_memory_store_tool, get_current_timestamp,
                          requires_subscription)
from routers.config import ENV, GCP_LOCATION, GCP_PROJECT, logger
from routers.dependencies import UserContext, get_optional_user

router = APIRouter()

# --- Request/Response Models ---


class ChatRequest(BaseModel):
    """Chat endpoint request payload."""
    message: str = Field(..., min_length=1, max_length=32000)
    mode: str = Field(default="default", description="Cognitive tier to use")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    enable_memory: bool = Field(default=True, description="Enable RAG memory")
    force_structured: bool = Field(default=False, description="Force JSON output")


class ChatResponse(BaseModel):
    """Chat endpoint response."""
    success: bool
    data: Optional[AgentResponse] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    request_id: str
    processing_time_ms: float


class OpenAIChatCompletionRequest(BaseModel):
    """OpenAI-compatible request."""
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    stream: bool = False


class GenerateRequest(BaseModel):
    """Generation request model."""
    prompt: str
    model: Optional[str] = "default"


class ImageRequest(BaseModel):
    """Image generation request model."""
    prompt: str
    n: int = 1
    size: str = "1024x1024"

# --- Endpoints ---


@router.post("/chat", response_model=ChatResponse)
@router.post("/v1/chat")
async def chat(
    request: ChatRequest,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Primary chat endpoint.
    Routes to appropriate cognitive tier based on mode.
    """
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
        if not user or user.plan not in ["pro", "enterprise"]:
            # If no user in dev, allow if accessing dev_token
            if not (ENV == "development" and user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Mode '{request.mode}' requires a Pro subscription."
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
        except Exception as e:  # pylint: disable=W0718
            logger.warning("Memory tools unavailable: %s", e)

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

        return ChatResponse(
            success=True,
            raw_response=str(result),
            request_id=request_id,
            processing_time_ms=processing_time
        )

    except Exception as e:  # pylint: disable=W0718
        logger.error("Chat error: %s", e, exc_info=True)
        processing_time = (time.time() - start_time) * 1000

        return ChatResponse(
            success=False,
            error=str(e) if ENV == "development" else "Processing failed",
            request_id=request_id,
            processing_time_ms=processing_time
        )


@router.post("/chat/route", response_model=ChatResponse)
async def routed_chat(
    request: ChatRequest,
    user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    Auto-routed chat endpoint.
    Classifies intent and routes to optimal cognitive tier.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    try:
        # Create routed agent
        agent = await AgentFactory.create_routed(
            user_input=request.message,
            tools=[calculate_growth_metrics, get_current_timestamp],
            user_tier=user.plan if user else "free",
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

    except Exception as e:  # pylint: disable=W0718
        logger.error("Routed chat error: %s", e, exc_info=True)
        processing_time = (time.time() - start_time) * 1000

        return ChatResponse(
            success=False,
            error=str(e) if ENV == "development" else "Processing failed",
            request_id=request_id,
            processing_time_ms=processing_time
        )


@router.post("/v1/chat/completions")
async def openai_chat_completions(
    request: OpenAIChatCompletionRequest,
    _user: Optional[UserContext] = Depends(get_optional_user)
):
    """
    OpenAI-compatible chat completion endpoint.
    Allows generic clients to use Unk Agent.
    """
    # Simply mapping last user message to our logic for now
    last_msg = next(
        (m["content"] for m in reversed(request.messages) if m["role"] == "user"),
        None
    )
    if not last_msg:
        raise HTTPException(status_code=400, detail="No user message found")

    # Map 'model' to our modes if possible, else default
    mode = "default"
    for m in GEMINI_MODELS:
        if m in request.model:
            mode = m
            break

    # Reuse standard chat logic (simplified)
    # in production this should handle history properly
    agent = UnkAgent(mode=mode, gcp_project=GCP_PROJECT, gcp_location=GCP_LOCATION)
    response_text = await agent.execute_turn(last_msg, force_structured=False)

    if isinstance(response_text, AgentResponse):
        response_text = response_text.final_answer

    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": str(response_text)
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,  # Placeholder
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


@router.post("/generate")
async def generate(
    request: GenerateRequest,
    _user: Optional[UserContext] = Depends(get_optional_user)
):
    """Simple generation endpoint."""
    agent = UnkAgent(mode=request.model, gcp_project=GCP_PROJECT, gcp_location=GCP_LOCATION)
    response = await agent.execute_turn(request.prompt, force_structured=False)
    # Try different fields or cast to str
    final_text = (
        response.final_answer
        if isinstance(response, AgentResponse)
        else str(response)
    )

    return {
        "generated_text": final_text,
        "model": request.model
    }


@router.post("/generate-image")
async def generate_image(
    _request: ImageRequest,
    _user: Optional[UserContext] = Depends(get_optional_user)
):
    """Stub for image generation."""
    return {
        "created": int(time.time()),
        "data": [
            {"url": "https://placeholder.com/image.png"}
        ]
    }


@router.post("/generate/video")
async def generate_video(
    _request: GenerateRequest,
    _user: Optional[UserContext] = Depends(get_optional_user)
):
    """Stub for video generation."""
    return {"status": "queued", "job_id": str(uuid.uuid4())}
