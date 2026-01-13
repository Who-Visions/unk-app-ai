"""
Shared dependencies and context management.
"""
import logging
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status
from firebase_admin import auth

# Configuration
ENV = os.environ.get("ENV", "development")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """User context for the request."""
    user_id: str
    email: Optional[str] = None
    plan: str = "free"
    roles: list[str] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []


async def verify_token(authorization: Optional[str] = Header(None)) -> UserContext:
    """
    Verify Firebase ID token and return user context.
    Strict verification - raises 401 if invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split("Bearer ")[1]

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")

        # Get custom claims if any (e.g. plan, admin role)
        # Note: In a real app, you might look up the user in Firestore/SQL here
        # or rely on custom claims set on the token.
        plan = decoded_token.get("plan", "free")
        roles = decoded_token.get("roles", [])

        return UserContext(
            user_id=uid,
            email=email,
            plan=plan,
            roles=roles
        )

    except Exception as e:  # pylint: disable=W0718
        logger.warning("Auth failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        ) from e


async def get_optional_user(authorization: Optional[str] = Header(None)) -> UserContext:
    """
    Get user context if token is present, else return default free user.
    Does not raise 401.
    """
    if not authorization:
        return UserContext(user_id="anonymous", plan="free")

    try:
        return await verify_token(authorization)
    except HTTPException:
        # Ignore auth errors for optional user, just return anon
        return UserContext(user_id="anonymous", plan="free")
