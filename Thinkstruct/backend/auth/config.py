"""
Authentication Configuration Settings

This module manages all configuration settings for the authentication system,
including Google OAuth credentials, JWT tokens, database connections, and cache.

Settings are loaded from environment variables via .env file.

Configuration categories:
- Google OAuth: Client ID, secret, redirect URI
- JWT: Secret key, algorithm, expiration time
- Database: SQLite (development) or PostgreSQL (production)
- Redis: Optional caching layer for sessions

Usage:
    from .config import settings

    # Check if OAuth is configured
    if settings.is_oauth_configured():
        # Use Google OAuth
        pass
"""

import os
from dataclasses import dataclass
from pathlib import Path

# Load .env file
from dotenv import load_dotenv

# Find .env file in project root (Thinkstruct/.env)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class AuthSettings:
    """
    Authentication settings loaded from environment variables.

    This dataclass holds all configuration needed for authentication,
    database connections, and caching. Values are loaded from environment
    variables with sensible defaults for development.

    Attributes:
        google_client_id: Google OAuth 2.0 client ID
        google_client_secret: Google OAuth 2.0 client secret
        google_redirect_uri: Callback URL after Google login
        jwt_secret: Secret key for JWT token signing
        jwt_algorithm: JWT signing algorithm (default: HS256)
        jwt_expiration_hours: Token validity period (default: 24 hours)
        frontend_url: Frontend application URL for redirects
        database_type: "sqlite" or "postgresql"
        database_path: SQLite database file path
        pg_*: PostgreSQL connection settings
        redis_*: Redis cache settings
    """

    # Google OAuth credentials
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # JWT token configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Frontend URL for OAuth redirects
    frontend_url: str = "http://localhost:3000"

    # Database configuration - SQLite (development) or PostgreSQL (production)
    database_type: str = "sqlite"  # "sqlite" or "postgresql"
    database_path: str = "thinkstruct.db"  # For SQLite

    # PostgreSQL connection settings
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "thinkstruct"
    pg_user: str = "postgres"
    pg_password: str = ""

    # Redis cache settings (optional)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_enabled: bool = False

    @classmethod
    def from_env(cls) -> "AuthSettings":
        """
        Load settings from environment variables.

        Reads all configuration from environment variables with default values
        for development. In production, these should be set in the environment
        or in a .env file.

        Returns:
            AuthSettings: Configured settings instance
        """
        return cls(
            # Google OAuth
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            google_redirect_uri=os.getenv(
                "GOOGLE_REDIRECT_URI",
                "http://localhost:5000/api/auth/callback/google"
            ),
            # JWT configuration
            jwt_secret=os.getenv("JWT_SECRET", "your-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            # Frontend
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            # Database type selection
            database_type=os.getenv("DATABASE_TYPE", "sqlite"),
            database_path=os.getenv(
                "DATABASE_PATH",
                os.path.join(os.path.dirname(__file__), "..", "thinkstruct.db")
            ),
            # PostgreSQL settings
            pg_host=os.getenv("PG_HOST", "localhost"),
            pg_port=int(os.getenv("PG_PORT", "5432")),
            pg_database=os.getenv("PG_DATABASE", "thinkstruct"),
            pg_user=os.getenv("PG_USER", "postgres"),
            pg_password=os.getenv("PG_PASSWORD", ""),
            # Redis settings
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_enabled=os.getenv("REDIS_ENABLED", "false").lower() == "true",
        )

    def is_oauth_configured(self) -> bool:
        """
        Check if Google OAuth credentials are configured.

        Returns:
            bool: True if both client_id and client_secret are set
        """
        return bool(self.google_client_id and self.google_client_secret)

    def get_pg_dsn(self) -> str:
        """
        Get PostgreSQL connection string (DSN).

        Returns:
            str: PostgreSQL connection URL in format:
                 postgresql://user:password@host:port/database
        """
        return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"

    def get_redis_url(self) -> str:
        """
        Get Redis connection URL.

        Returns:
            str: Redis connection URL in format:
                 redis://[:password@]host:port/db
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance - loaded once at module import
settings = AuthSettings.from_env()
