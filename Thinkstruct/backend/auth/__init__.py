"""
Auth Module - Google OAuth and User Sessions

This module provides complete authentication functionality for the
Thinkstruct Patent Search System.

Features:
- Google OAuth 2.0 login
- JWT token authentication
- Session management with revocation support
- User profile storage
- Search history tracking
- Optional Redis caching

Components:
- config: Configuration settings from environment
- database: SQLite/PostgreSQL database operations
- cache: Optional Redis caching layer
- models: Pydantic models for requests/responses
- jwt_handler: JWT token creation and verification
- oauth: Google OAuth flow implementation
- dependencies: FastAPI dependency injection

Usage:
    from .auth import (
        settings,           # Configuration
        db,                 # Database operations
        cache,              # Redis cache
        JWTHandler,         # Token handling
        GoogleOAuth,        # OAuth flow
        get_current_user,   # Auth dependency
    )
"""

from .config import settings
from .database import DatabaseInterface, db
from .cache import cache
from .models import (
    User,
    Session,
    TokenResponse,
    SearchHistoryCreate,
    SearchHistoryResponse,
    SearchHistoryListResponse,
    AuthStatus,
    MessageResponse,
)
from .jwt_handler import JWTHandler
from .oauth import GoogleOAuth
from .dependencies import get_current_user, get_optional_user

__all__ = [
    # Configuration
    "settings",
    # Database
    "DatabaseInterface",
    "db",
    # Cache
    "cache",
    # Models
    "User",
    "Session",
    "TokenResponse",
    "SearchHistoryCreate",
    "SearchHistoryResponse",
    "SearchHistoryListResponse",
    "AuthStatus",
    "MessageResponse",
    # JWT
    "JWTHandler",
    # OAuth
    "GoogleOAuth",
    # Dependencies
    "get_current_user",
    "get_optional_user",
]
