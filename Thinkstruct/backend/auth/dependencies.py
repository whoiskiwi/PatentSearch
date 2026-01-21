"""
FastAPI Authentication Dependencies

This module provides dependency injection functions for authentication.
Dependencies are used in route handlers to get the current user.

Dependencies:
- get_token_from_request: Extract JWT from header or cookie
- get_current_user: Get authenticated user (raises 401 if not logged in)
- get_optional_user: Get user if authenticated (returns None otherwise)

Usage in routes:
    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user": user.name}

    @router.get("/optional")
    async def optional_auth(user: Optional[User] = Depends(get_optional_user)):
        if user:
            return {"logged_in": True}
        return {"logged_in": False}
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Header

from .database import db
from .jwt_handler import JWTHandler
from .models import User


async def get_token_from_request(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    """
    Extract JWT token from request.

    Checks two sources for the token:
    1. Authorization header: "Bearer <token>"
    2. Cookie: "access_token=<token>"

    Authorization header takes priority over cookie.

    Args:
        authorization: Authorization header value (injected by FastAPI)
        access_token: Cookie value (injected by FastAPI)

    Returns:
        str: JWT token if found
        None: If no token in request
    """
    # Check Authorization header first (standard OAuth approach)
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]  # Remove "Bearer " prefix

    # Fall back to cookie (for browser-based requests)
    return access_token


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request)
) -> User:
    """
    Get the current authenticated user.

    Validates the JWT token and returns the associated user.
    Raises HTTP 401 if not authenticated or token is invalid.

    This dependency should be used for protected routes that
    require authentication.

    Args:
        token: JWT token from request (injected by FastAPI)

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException 401: If not authenticated, token invalid,
                          session expired, or user not found
    """
    # Check if token exists
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token signature and expiration
    payload = JWTHandler.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if session is still valid (not revoked)
    session_id = payload.get("session_id")
    if session_id:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Get user from database
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
    """
    Get the current user if authenticated, otherwise None.

    This dependency allows endpoints to work for both authenticated
    and unauthenticated users. It performs the same validation as
    get_current_user but returns None instead of raising errors.

    Use this for routes that have optional authentication, such as
    search endpoints that show different UI for logged-in users.

    Args:
        token: JWT token from request (injected by FastAPI)

    Returns:
        User: The authenticated user if valid token
        None: If not authenticated or any validation fails
    """
    # No token means not authenticated
    if not token:
        return None

    # Verify token - return None if invalid
    payload = JWTHandler.verify_token(token)
    if not payload:
        return None

    # Check session validity - return None if revoked
    session_id = payload.get("session_id")
    if session_id:
        session = await db.get_session(session_id)
        if not session:
            return None

    # Get user - return None if not found
    user_id = int(payload["sub"])
    user_data = await db.get_user_by_id(user_id)
    if not user_data:
        return None

    return User(**user_data)
