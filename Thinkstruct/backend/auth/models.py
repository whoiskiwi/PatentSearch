"""Pydantic models for authentication."""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model."""

    id: int
    google_id: str
    email: str
    name: str
    picture_url: Optional[str] = None
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response for API."""

    id: int
    email: str
    name: str
    picture_url: Optional[str] = None


class Session(BaseModel):
    """Session model."""

    id: str
    user_id: int
    expires_at: str
    is_revoked: bool = False


class TokenResponse(BaseModel):
    """OAuth token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class GoogleUserInfo(BaseModel):
    """Google user info from OAuth."""

    id: str
    email: str
    verified_email: bool = False
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


class SearchHistoryCreate(BaseModel):
    """Request to save search history."""

    scenario: str
    query_data: Dict[str, Any]
    results_data: Optional[list] = None
    result_count: int = 0
    search_time_ms: float = 0


class SearchHistoryResponse(BaseModel):
    """Search history entry response."""

    id: int
    scenario: str
    query_data: Dict[str, Any]
    results_data: Optional[list] = None
    result_count: int
    search_time_ms: float
    created_at: str


class SearchHistoryListResponse(BaseModel):
    """List of search history entries."""

    items: list[SearchHistoryResponse]
    total: int


class AuthStatus(BaseModel):
    """Auth status response."""

    authenticated: bool
    user: Optional[UserResponse] = None
    oauth_configured: bool


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True
