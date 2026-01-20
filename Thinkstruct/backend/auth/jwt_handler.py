"""JWT token handling."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

from .config import settings


class JWTHandler:
    """Handle JWT token creation and verification."""

    @staticmethod
    def create_token(
        user_id: int,
        session_id: str,
        expires_hours: Optional[int] = None
    ) -> str:
        """Create a JWT token."""
        if expires_hours is None:
            expires_hours = settings.jwt_expiration_hours

        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        payload = {
            "sub": str(user_id),
            "session_id": session_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify a JWT token and return payload if valid."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """Extract user ID from token."""
        payload = JWTHandler.verify_token(token)
        if payload and "sub" in payload:
            return int(payload["sub"])
        return None

    @staticmethod
    def get_session_id_from_token(token: str) -> Optional[str]:
        """Extract session ID from token."""
        payload = JWTHandler.verify_token(token)
        if payload and "session_id" in payload:
            return payload["session_id"]
        return None
