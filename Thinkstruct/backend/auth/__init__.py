"""Auth module for Google OAuth and user sessions."""

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
    "settings",
    "DatabaseInterface",
    "db",
    "cache",
    "User",
    "Session",
    "TokenResponse",
    "SearchHistoryCreate",
    "SearchHistoryResponse",
    "SearchHistoryListResponse",
    "AuthStatus",
    "MessageResponse",
    "JWTHandler",
    "GoogleOAuth",
    "get_current_user",
    "get_optional_user",
]
