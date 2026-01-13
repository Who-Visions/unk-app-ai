import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.llm.gemini_agent import GeminiAgent
from routers.unk_api import router as unk_router

app = FastAPI(title="Unk Mode API", version="0.1.0")

# CORS for local dev and frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared agent instance for base chat if needed
base_agent = GeminiAgent()

# Mount the dedicated Unk API router
app.include_router(unk_router)


class Message(BaseModel):
    prompt: str


@app.post("/agent/chat")
async def chat_endpoint(message: Message):
    # Fallback/General chat endpoint
    reply = base_agent.run(message.prompt)
    return {
        "status": "success",
        "agent_reply": reply,
    }


if __name__ == "__main__":
    print("Starting API server at http://127.0.0.1:8000")
    uvicorn.run("deploy:app", host="0.0.0.0", port=8000, reload=True)
