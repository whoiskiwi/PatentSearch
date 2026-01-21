"""
Authentication Pydantic Models

This module defines all Pydantic models for authentication-related
request validation and response serialization.

Model categories:
- User models: User data and responses
- Session models: User session tracking
- OAuth models: Google OAuth flow
- History models: Search history storage
- Status models: Authentication status

Usage:
    from .models import User, TokenResponse, AuthStatus
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, EmailStr


# ============================================================================
# User Models
# ============================================================================

class User(BaseModel):
    """
    Complete user model with all database fields.

    Used internally for user data from database.
    Contains sensitive fields like google_id.

    Attributes:
        id: Database primary key
        google_id: Unique Google account ID
        email: User's email address
        name: User's display name
        picture_url: Profile picture URL from Google
        created_at: Account creation timestamp
        last_login_at: Most recent login timestamp
    """

    id: int
    google_id: str
    email: str
    name: str
    picture_url: Optional[str] = None
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True  # Allow ORM model conversion


class UserResponse(BaseModel):
    """
    Safe user model for API responses.

    Excludes sensitive fields like google_id for public responses.

    Attributes:
        id: User's unique ID
        email: User's email address
        name: User's display name
        picture_url: Profile picture URL
    """

    id: int
    email: str
    name: str
    picture_url: Optional[str] = None


# ============================================================================
# Session Models
# ============================================================================

class Session(BaseModel):
    """
    User session model.

    Represents an active user session stored in the database.
    Sessions can be revoked for logout functionality.

    Attributes:
        id: Unique session ID (UUID)
        user_id: Associated user's ID
        expires_at: Session expiration timestamp
        is_revoked: Whether session has been logged out
    """

    id: str
    user_id: int
    expires_at: str
    is_revoked: bool = False


# ============================================================================
# OAuth Models
# ============================================================================

class TokenResponse(BaseModel):
    """
    OAuth token response after successful authentication.

    Returned to frontend after successful Google OAuth flow.

    Attributes:
        access_token: JWT token for API authentication
        token_type: Token type (always "bearer")
        expires_in: Token validity in seconds
        user: Authenticated user information
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class GoogleUserInfo(BaseModel):
    """
    User information received from Google OAuth.

    Contains profile data returned by Google's userinfo endpoint.

    Attributes:
        id: Google's unique user ID
        email: User's Google email
        verified_email: Whether email is verified
        name: Full name from Google profile
        given_name: First name
        family_name: Last name
        picture: Profile picture URL
    """

    id: str
    email: str
    verified_email: bool = False
    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


# ============================================================================
# Search History Models
# ============================================================================

class SearchHistoryCreate(BaseModel):
    """
    Request model for saving search history.

    Used when frontend saves a search to user's history.

    Attributes:
        scenario: Search type (invalidity, infringement, patentability, patent_id)
        query_data: Search parameters as JSON object
        results_data: Optional search results for re-display
        result_count: Number of results returned
        search_time_ms: Search execution time
    """

    scenario: str
    query_data: Dict[str, Any]
    results_data: Optional[list] = None
    result_count: int = 0
    search_time_ms: float = 0


class SearchHistoryResponse(BaseModel):
    """
    Single search history entry response.

    Returned when fetching user's search history.

    Attributes:
        id: History entry ID
        scenario: Search type
        query_data: Original search parameters
        results_data: Stored search results
        result_count: Number of results
        search_time_ms: Search execution time
        created_at: When search was performed
    """

    id: int
    scenario: str
    query_data: Dict[str, Any]
    results_data: Optional[list] = None
    result_count: int
    search_time_ms: float
    created_at: str


class SearchHistoryListResponse(BaseModel):
    """
    Paginated list of search history entries.

    Attributes:
        items: List of history entries
        total: Total number of entries
    """

    items: list[SearchHistoryResponse]
    total: int


# ============================================================================
# Status Models
# ============================================================================

class AuthStatus(BaseModel):
    """
    Authentication status response.

    Used by frontend to check if user is logged in.

    Attributes:
        authenticated: Whether user is logged in
        user: User info if authenticated
        oauth_configured: Whether Google OAuth is set up
    """

    authenticated: bool
    user: Optional[UserResponse] = None
    oauth_configured: bool


class MessageResponse(BaseModel):
    """
    Generic message response for simple operations.

    Used for logout, delete, and other simple confirmations.

    Attributes:
        message: Human-readable message
        success: Whether operation succeeded
    """

    message: str
    success: bool = True
