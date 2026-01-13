from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/.well-known/agent.json")
@router.get("/agent-card")
@router.get("/a2a/card")
@router.get("/a2a/discover")
@router.get("/a2a")
async def agent_identity_card():
    """
    A2A Identity Card - Agent-to-Agent Discovery.
    Exposes standardized agent capabilities for the Who Visions Fleet.
    """
    return JSONResponse({
        "name": "Unk Agent",
        "version": "1.0.0",
        "description": "Enterprise-grade multi-model cognitive agent with dynamic tier routing. Specialist in intelligent task complexity analysis, cost optimization, and scalable AI orchestration across Gemini 2.0/2.5 models.",
        "capabilities": [
            "text-generation",
            "code-generation",
            "code-analysis",
            "reasoning",
            "deep-research",
            "vector-memory",
            "rag-search",
            "cost-optimization",
            "cognitive-routing",
            "structured-output",
            "tool-execution"
        ],
        "endpoints": {
            "chat": "/chat",
            "chat_routed": "/chat/route",
            "health": "/health",
            "models": "/models",
            "usage": "/usage",
            "pricing_spikes": "/pricing/spikes",
            "pricing_history": "/pricing/history",
            "pricing_trends": "/pricing/trends"
        },
        "models": {
            "tiers": [
                "cost_saver",
                "default",
                "flash_thinking",
                "unk_mode",
                "ultrathink",
                "code_specialist"
            ],
            "primary": "gemini-2.5-pro",
            "routing": "automatic"
        },
        "extensions": {
            "color": "bold magenta",
            "role": "Cognitive Orchestrator",
            "tier_system": "6-tier cognitive routing",
            "memory_type": "Firestore Vector Store",
            "auth_method": "Firebase OIDC",
            "deployment": "Cloud Run",
            "project": "Who Visions LLC",
            "brand": "AI with Dav3",
            "social": {
                "instagram": "@aiwithdav3",
                "youtube": "youtube.com/aiwithdav3"
            },
            "reasoning_engine": {
                "enabled": True,
                "resource_name": "projects/574321322006/locations/us-central1/reasoningEngines/5608320741238898688",
                "location": "us-central1",
                "project_id": "unk-app-480102",
                "project_number": "574321322006",
                "display_name": "unk-agent",
                "description": "Unk Agent - Cognitive Orchestrator (Who Visions Fleet)"
            }
        }
    })
