"""Google OAuth implementation."""

import httpx
from typing import Optional
from urllib.parse import urlencode

from .config import settings
from .models import GoogleUserInfo


class GoogleOAuth:
    """Handle Google OAuth flow."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    SCOPES = ["openid", "email", "profile"]

    @classmethod
    def get_authorization_url(cls, state: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL."""
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(cls.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state

        return f"{cls.AUTHORIZATION_URL}?{urlencode(params)}"

    @classmethod
    async def exchange_code_for_token(cls, code: str) -> Optional[dict]:
        """Exchange authorization code for access token."""
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
        """Get user info from Google using access token."""
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
        """Complete OAuth flow: exchange code and get user info."""
        token_data = await cls.exchange_code_for_token(code)
        if not token_data or "access_token" not in token_data:
            return None

        return await cls.get_user_info(token_data["access_token"])
