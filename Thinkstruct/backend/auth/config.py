"""Auth configuration settings."""

import os
from dataclasses import dataclass
from pathlib import Path

# Load .env file
from dotenv import load_dotenv

# Find .env file in project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


@dataclass
class AuthSettings:
    """Authentication settings loaded from environment variables."""

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Database - SQLite (development) or PostgreSQL (production)
    database_type: str = "sqlite"  # "sqlite" or "postgresql"
    database_path: str = "thinkstruct.db"  # For SQLite

    # PostgreSQL settings
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_database: str = "thinkstruct"
    pg_user: str = "postgres"
    pg_password: str = ""

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_enabled: bool = False

    @classmethod
    def from_env(cls) -> "AuthSettings":
        """Load settings from environment variables."""
        return cls(
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            google_redirect_uri=os.getenv(
                "GOOGLE_REDIRECT_URI",
                "http://localhost:5000/api/auth/callback/google"
            ),
            jwt_secret=os.getenv("JWT_SECRET", "your-secret-key-change-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            # Database type
            database_type=os.getenv("DATABASE_TYPE", "sqlite"),
            database_path=os.getenv(
                "DATABASE_PATH",
                os.path.join(os.path.dirname(__file__), "..", "thinkstruct.db")
            ),
            # PostgreSQL
            pg_host=os.getenv("PG_HOST", "localhost"),
            pg_port=int(os.getenv("PG_PORT", "5432")),
            pg_database=os.getenv("PG_DATABASE", "thinkstruct"),
            pg_user=os.getenv("PG_USER", "postgres"),
            pg_password=os.getenv("PG_PASSWORD", ""),
            # Redis
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_enabled=os.getenv("REDIS_ENABLED", "false").lower() == "true",
        )

    def is_oauth_configured(self) -> bool:
        """Check if OAuth credentials are configured."""
        return bool(self.google_client_id and self.google_client_secret)

    def get_pg_dsn(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}"

    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = AuthSettings.from_env()
