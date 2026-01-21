"""
JWT Token Handler

This module handles JSON Web Token (JWT) creation and verification
for user authentication.

JWT tokens are used to authenticate API requests without
requiring the user to send credentials with every request.

Token structure:
- sub: User ID (subject)
- session_id: Database session ID for revocation
- exp: Expiration timestamp
- iat: Issued at timestamp

Usage:
    from .jwt_handler import JWTHandler

    # Create token after login
    token = JWTHandler.create_token(user_id=1, session_id="uuid-string")

    # Verify token from request
    payload = JWTHandler.verify_token(token)
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

from .config import settings


class JWTHandler:
    """
    Handle JWT token creation and verification.

    This class provides static methods for working with JWT tokens.
    All methods use the secret key and algorithm from settings.
    """

    @staticmethod
    def create_token(
        user_id: int,
        session_id: str,
        expires_hours: Optional[int] = None
    ) -> str:
        """
        Create a JWT token for authenticated user.

        Generates a signed JWT containing user identification and
        session tracking information.

        Args:
            user_id: Database user ID to embed in token
            session_id: Session ID for logout/revocation support
            expires_hours: Custom expiration time (defaults to settings)

        Returns:
            str: Encoded JWT token string
        """
        if expires_hours is None:
            expires_hours = settings.jwt_expiration_hours

        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        # Build token payload
        payload = {
            "sub": str(user_id),      # Subject: user identifier
            "session_id": session_id,  # For session revocation
            "exp": expires_at,         # Expiration time
            "iat": datetime.utcnow(),  # Issued at time
        }

        # Sign and encode the token
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify a JWT token and return payload if valid.

        Decodes and validates the token signature and expiration.
        Returns None if token is invalid or expired.

        Args:
            token: JWT token string to verify

        Returns:
            dict: Token payload if valid
            None: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            # Token is invalid, expired, or has wrong signature
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        Extract user ID from a valid token.

        Convenience method for getting user ID from token
        without handling the full payload.

        Args:
            token: JWT token string

        Returns:
            int: User ID if token is valid
            None: If token is invalid or doesn't contain user ID
        """
        payload = JWTHandler.verify_token(token)
        if payload and "sub" in payload:
            return int(payload["sub"])
        return None

    @staticmethod
    def get_session_id_from_token(token: str) -> Optional[str]:
        """
        Extract session ID from a valid token.

        Used for checking if session has been revoked.

        Args:
            token: JWT token string

        Returns:
            str: Session ID if token is valid
            None: If token is invalid or doesn't contain session ID
        """
        payload = JWTHandler.verify_token(token)
        if payload and "session_id" in payload:
            return payload["session_id"]
        return None
