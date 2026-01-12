"""
Unk Agent API Deployment
========================
Main entry point for the FastAPI application.
Configures middleware, routers, and lifecycle events.
"""
import os
import sys

# Add project root to sys.path to ensure 'routers', 'gemini_agent', etc. are importable
# even if running from services/ directory or as a module.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from contextlib import asynccontextmanager

import firebase_admin
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials


# Import Routers - Wrapped in try/except to catch import errors early
try:
    from routers import a2a, auth, chat, core, lore, models, orchestrator, tools
    from routers.config import ENV, PORT, logger
    from routers import threads  # Imported separately in original code, consolidating here if possible
except Exception as e:
    import logging
    logging.error(f"CRITICAL STARTUP ERROR: Failed to import routers. {e}")
    # We re-raise so the app still fails, but now we have a log entry that Cloud Run will definitely capture
    raise e


# Firebase Initialization
if not firebase_admin._apps: # pylint: disable=protected-access
    try:
        if ENV == "production":
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': os.environ.get("GOOGLE_CLOUD_PROJECT"),
            })
        else:
            # Local dev
            service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
            else:
                try:
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred)
                except Exception as e: # pylint: disable=broad-exception-caught
                    logger.warning("Could not init Firebase default credentials: %s", e)
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("Failed to initialize Firebase: %s", e)

@asynccontextmanager
async def lifespan(_fastapi_app: FastAPI): # renamed app to fastapi_app
    """Lifecycle events."""
    # Startup
    logger.info("Unk Agent API starting in %s mode...", ENV)
    yield
    # Shutdown
    logger.info("Unk Agent API shutting down...")

# FastAPI App
app = FastAPI(
    title="Unk Agent API",
    description="Multi-model cognitive agent with dynamic routing (Gemini 3 Powered)",
    version="2.0.0",
    docs_url="/docs" if ENV != "production" else None,
    redoc_url="/redoc" if ENV != "production" else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include Routers
app.include_router(core.router)
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(a2a.router)
app.include_router(tools.router, prefix="/tools")
app.include_router(lore.router, prefix="/lore")
app.include_router(orchestrator.router)
app.include_router(auth.router)

app.include_router(threads.router)

if __name__ == "__main__":
    # Run with uvicorn
    # Use 'services.deploy:app' if running from root, or just 'deploy:app' if inside services
    # We use path manipulation above so 'services.deploy:app' is safest if PYTHONPATH includes root
    uvicorn.run("services.deploy:app", host="0.0.0.0", port=PORT, reload=ENV == "development")
