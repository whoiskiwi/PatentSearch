"""Auth router for Google OAuth."""

from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse

from ..auth.config import settings
from ..auth.database import db
from ..auth.models import (
    User,
    UserResponse,
    TokenResponse,
    AuthStatus,
    MessageResponse,
)
from ..auth.jwt_handler import JWTHandler
from ..auth.oauth import GoogleOAuth
from ..auth.dependencies import get_current_user, get_token_from_request

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    token: str = Depends(get_token_from_request)
):
    """Get current authentication status."""
    user = None
    authenticated = False

    if token:
        payload = JWTHandler.verify_token(token)
        if payload:
            session_id = payload.get("session_id")
            if session_id:
                session = await db.get_session(session_id)
                if session:
                    user_data = await db.get_user_by_id(int(payload["sub"]))
                    if user_data:
                        user = UserResponse(
                            id=user_data["id"],
                            email=user_data["email"],
                            name=user_data["name"],
                            picture_url=user_data.get("picture_url"),
                        )
                        authenticated = True

    return AuthStatus(
        authenticated=authenticated,
        user=user,
        oauth_configured=settings.is_oauth_configured(),
    )


@router.get("/login/google")
async def login_google():
    """Redirect to Google OAuth login."""
    if not settings.is_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.",
        )

    auth_url = GoogleOAuth.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback/google")
async def callback_google(code: str, response: Response):
    """Handle Google OAuth callback."""
    if not settings.is_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured.",
        )

    # Exchange code for user info
    user_info = await GoogleOAuth.authenticate(code)
    if not user_info:
        return RedirectResponse(
            url=f"{settings.frontend_url}?error=auth_failed",
            status_code=302,
        )

    # Create or update user
    user_data = await db.upsert_user(
        google_id=user_info.id,
        email=user_info.email,
        name=user_info.name,
        picture_url=user_info.picture,
    )

    # Create session
    session_id = await db.create_session(
        user_id=user_data["id"],
        expires_hours=settings.jwt_expiration_hours,
    )

    # Create JWT
    token = JWTHandler.create_token(
        user_id=user_data["id"],
        session_id=session_id,
    )

    # Redirect to frontend with token in URL (frontend will store it)
    redirect_url = f"{settings.frontend_url}?token={token}"
    redirect_response = RedirectResponse(url=redirect_url, status_code=302)

    # Also set as httpOnly cookie for additional security
    redirect_response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.jwt_expiration_hours * 3600,
    )

    return redirect_response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture_url=user.picture_url,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    token: str = Depends(get_token_from_request),
):
    """Logout current user."""
    # Revoke the session
    if token:
        session_id = JWTHandler.get_session_id_from_token(token)
        if session_id:
            await db.revoke_session(session_id)

    # Clear the cookie
    response.delete_cookie("access_token")

    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_sessions(
    response: Response,
    user: User = Depends(get_current_user),
):
    """Logout from all sessions."""
    await db.revoke_all_user_sessions(user.id)
    response.delete_cookie("access_token")
    return MessageResponse(message="Logged out from all sessions")
