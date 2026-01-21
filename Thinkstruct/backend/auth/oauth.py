"""
Google OAuth Implementation

This module implements the Google OAuth 2.0 authentication flow.

OAuth Flow:
1. User clicks "Login with Google" -> redirected to Google
2. User authorizes app -> Google redirects back with auth code
3. Backend exchanges code for access token
4. Backend fetches user info using access token
5. Backend creates session and returns JWT to frontend

Endpoints used:
- Authorization: accounts.google.com/o/oauth2/v2/auth
- Token exchange: oauth2.googleapis.com/token
- User info: www.googleapis.com/oauth2/v2/userinfo

Usage:
    from .oauth import GoogleOAuth

    # Get login URL
    url = GoogleOAuth.get_authorization_url()

    # Handle callback
    user_info = await GoogleOAuth.authenticate(code)
"""

import httpx
from typing import Optional
from urllib.parse import urlencode

from .config import settings
from .models import GoogleUserInfo


class GoogleOAuth:
    """
    Handle Google OAuth 2.0 authentication flow.

    This class provides methods for each step of the OAuth flow:
    authorization URL generation, token exchange, and user info retrieval.
    """

    # Google OAuth endpoints
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    # OAuth scopes - what data we request access to
    SCOPES = ["openid", "email", "profile"]

    @classmethod
    def get_authorization_url(cls, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.

        Creates the URL that users should be redirected to for
        Google login. After authorization, Google redirects back
        to our callback URL with an authorization code.

        Args:
            state: Optional CSRF protection state parameter

        Returns:
            str: Full Google authorization URL with query parameters
        """
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",        # Request auth code
            "scope": " ".join(cls.SCOPES),  # Request profile access
            "access_type": "offline",       # Get refresh token
            "prompt": "consent",            # Always show consent screen
        }
        if state:
            params["state"] = state

        return f"{cls.AUTHORIZATION_URL}?{urlencode(params)}"

    @classmethod
    async def exchange_code_for_token(cls, code: str) -> Optional[dict]:
        """
        Exchange authorization code for access token.

        After user authorizes, Google redirects with a one-time code.
        This method exchanges that code for an access token.

        Args:
            code: Authorization code from Google callback

        Returns:
            dict: Token response containing access_token, refresh_token, etc.
            None: If exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                return None

            return response.json()

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[GoogleUserInfo]:
        """
        Get user info from Google using access token.

        Fetches the user's profile information from Google's
        userinfo endpoint using the access token.

        Args:
            access_token: Valid Google access token

        Returns:
            GoogleUserInfo: User's profile data
            None: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                cls.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return GoogleUserInfo(**data)

    @classmethod
    async def authenticate(cls, code: str) -> Optional[GoogleUserInfo]:
        """
        Complete OAuth flow: exchange code and get user info.

        Convenience method that performs both steps of the OAuth
        callback handling: token exchange and user info retrieval.

        Args:
            code: Authorization code from Google callback

        Returns:
            GoogleUserInfo: User's profile data if successful
            None: If any step fails
        """
        # Step 1: Exchange code for token
        token_data = await cls.exchange_code_for_token(code)
        if not token_data or "access_token" not in token_data:
            return None

        # Step 2: Get user info with token
        return await cls.get_user_info(token_data["access_token"])
