"""
Unk Agent - FastAPI Deployment Entry Point
Who Visions LLC
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Unk Mode API", version="0.1.0")

# CORS for local dev and frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    prompt: str


# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "unk-agent"}


@app.get("/")
async def root():
    return {"message": "Unk Agent API is live.", "version": "0.1.0"}


@app.on_event("startup")
async def startup_event():
    """Lazy-load heavy dependencies after the server binds to the port."""
    from routers.unk_api import router as unk_router
    from services.llm.gemini_agent import GeminiAgent
    app.include_router(unk_router)
    app.state.base_agent = GeminiAgent()


@app.post("/agent/chat")
async def chat_endpoint(message: Message):
    if not hasattr(app.state, "base_agent"):
        return {"status": "error", "message": "Agent not initialized"}
    reply = app.state.base_agent.run(message.prompt)
    return {
        "status": "success",
        "agent_reply": reply,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting API server at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
