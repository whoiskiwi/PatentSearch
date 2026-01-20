"""FastAPI dependencies for authentication."""

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Header

from .database import db
from .jwt_handler import JWTHandler
from .models import User


async def get_token_from_request(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    """Extract token from Authorization header or cookie."""
    # Check Authorization header first
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]

    # Fall back to cookie
    return access_token


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request)
) -> User:
    """Get the current authenticated user. Raises 401 if not authenticated."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    payload = JWTHandler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check session is still valid
    session_id = payload.get("session_id")
    if session_id:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Get user
    user_id = int(payload["sub"])
    user_data = await db.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(**user_data)


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_request)
) -> Optional[User]:
    """Get the current user if authenticated, otherwise None.

    This dependency allows endpoints to work for both authenticated
    and unauthenticated users.
    """
    if not token:
        return None

    payload = JWTHandler.verify_token(token)
    if not payload:
        return None

    # Check session is still valid
    session_id = payload.get("session_id")
    if session_id:
        session = await db.get_session(session_id)
        if not session:
            return None

    user_id = int(payload["sub"])
    user_data = await db.get_user_by_id(user_id)
    if not user_data:
        return None

    return User(**user_data)
