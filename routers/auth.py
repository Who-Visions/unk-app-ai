import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# --- Models ---

class AuthStartResponse(BaseModel):
    auth_url: str
    state: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str

class ConnectedAccount(BaseModel):
    provider: str # cleaning, branding, etc.
    account_id: str
    email: Optional[str] = None
    status: str

# --- Endpoints ---

@router.get("/start/{provider}", response_model=AuthStartResponse)
async def start_auth(provider: str, redirect_uri: str):
    """
    Initiate an OAuth flow for a specific provider (e.g., 'google', 'twitter').
    Returns the authorization URL to redirect the user to.
    """
    if provider not in ["google", "notion", "twitter"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # In a real app, generate a secure state and construct the provider's auth URL
    base_url = f"https://accounts.{provider}.com/o/oauth2/auth"
    params = f"?client_id=xyz&redirect_uri={redirect_uri}"
    fake_url = base_url + params

    return AuthStartResponse(
        auth_url=fake_url,
        state="random_secure_state_string"
    )

@router.get("/callback/{provider}")
async def auth_callback(provider: str, code: str):
    """
    Handle the OAuth callback. Exchange code for tokens.
    """
    logger.info("Received callback for %s with code %s...", provider, code[:5])

    # Mock token exchange
    return {
        "message": f"Successfully authenticated with {provider}",
        "access_token": f"mock_token_for_{provider}",
        "user_data": {"name": "Test User", "email": "test@example.com"}
    }

@router.get("/accounts", response_model=List[ConnectedAccount])
async def list_accounts():
    """List all connected 3rd party accounts."""
    # In a real app, query the DB for the current user's linked accounts
    return [
        ConnectedAccount(
            provider="google",
            account_id="acc_123",
            email="user@gmail.com",
            status="active"
        ),
        ConnectedAccount(
            provider="notion",
            account_id="acc_456",
            status="expired"
        ),
    ]

@router.post("/logout")
async def logout():
    """Invalidate session."""
    return {"message": "Logged out successfully"}
