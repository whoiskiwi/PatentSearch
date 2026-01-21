"""
Database Operations for Authentication

This module provides database abstraction for user authentication,
session management, and search history storage.

Supports two database backends:
- SQLite: Development/testing (file-based, no setup required)
- PostgreSQL: Production (connection pooling, better performance)

Database schema includes three tables:
- users: User profiles from Google OAuth
- sessions: Active user sessions for authentication
- search_history: User's search history records

Usage:
    from .database import db

    # Initialize on startup
    await db.init_db()

    # User operations
    user = await db.upsert_user(google_id, email, name, picture_url)

    # Session operations
    session_id = await db.create_session(user_id)
    session = await db.get_session(session_id)
    await db.revoke_session(session_id)

    # Search history
    await db.save_search_history(user_id, scenario, query_data)
    history = await db.get_search_history(user_id)
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, List
import uuid

from .config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Database Interface
# ============================================================================

class DatabaseInterface(ABC):
    """
    Abstract database interface.

    Defines the contract that all database implementations must follow.
    This allows switching between SQLite and PostgreSQL without
    changing the application code.
    """

    @abstractmethod
    async def init_db(self) -> None:
        """Initialize database schema (create tables if not exist)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connections gracefully."""
        pass

    # ==================== User Operations ====================

    @abstractmethod
    async def get_user_by_google_id(self, google_id: str) -> Optional[dict]:
        """Find user by their Google account ID."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Find user by database ID."""
        pass

    @abstractmethod
    async def create_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create a new user account."""
        pass

    @abstractmethod
    async def update_user_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        pass

    @abstractmethod
    async def upsert_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create user if not exists, or update login time if exists."""
        pass

    # ==================== Session Operations ====================

    @abstractmethod
    async def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Create a new session and return session ID."""
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session if valid (not expired, not revoked)."""
        pass

    @abstractmethod
    async def revoke_session(self, session_id: str) -> None:
        """Revoke a session (logout)."""
        pass

    @abstractmethod
    async def revoke_all_user_sessions(self, user_id: int) -> None:
        """Revoke all sessions for a user (logout from all devices)."""
        pass

    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions and return count deleted."""
        pass

    # ==================== Search History Operations ====================

    @abstractmethod
    async def save_search_history(self, user_id: int, scenario: str, query_data: dict,
                                   results_data: list = None, result_count: int = 0,
                                   search_time_ms: float = 0) -> int:
        """Save a search to user's history and return entry ID."""
        pass

    @abstractmethod
    async def get_search_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get user's search history (most recent first)."""
        pass

    @abstractmethod
    async def get_history_entry(self, history_id: int, user_id: int) -> Optional[dict]:
        """Get a specific history entry."""
        pass

    @abstractmethod
    async def delete_history_entry(self, history_id: int, user_id: int) -> bool:
        """Delete a history entry and return success status."""
        pass

    @abstractmethod
    async def clear_user_history(self, user_id: int) -> int:
        """Delete all history for a user and return count deleted."""
        pass


# ============================================================================
# SQLite Implementation
# ============================================================================

class SQLiteDatabase(DatabaseInterface):
    """
    SQLite database implementation.

    Uses aiosqlite for async operations. Connections are created
    per-operation to avoid threading issues.

    Best for: Development, testing, single-user scenarios.
    """

    # SQL schema for creating tables
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        picture_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        is_revoked BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scenario TEXT NOT NULL,
        query_data TEXT NOT NULL,
        results_data TEXT,
        result_count INTEGER DEFAULT 0,
        search_time_ms REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite database.

        Args:
            db_path: Path to database file (defaults to settings)
        """
        self.db_path = db_path or settings.database_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

    async def _get_connection(self):
        """Get a new database connection."""
        import aiosqlite
        return await aiosqlite.connect(self.db_path)

    async def init_db(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = await self._get_connection()
        try:
            await conn.executescript(self.SCHEMA)
            # Migration: add results_data column if missing (for old databases)
            try:
                await conn.execute("ALTER TABLE search_history ADD COLUMN results_data TEXT")
            except Exception:
                pass  # Column already exists
            await conn.commit()
        finally:
            await conn.close()

    async def close(self) -> None:
        """SQLite connections are closed per-operation."""
        pass

    async def get_user_by_google_id(self, google_id: str) -> Optional[dict]:
        """Find user by Google account ID."""
        import aiosqlite
        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Find user by database ID."""
        import aiosqlite
        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def create_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create a new user and return the user dict."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "INSERT INTO users (google_id, email, name, picture_url) VALUES (?, ?, ?, ?)",
                (google_id, email, name, picture_url)
            )
            await conn.commit()
            user_id = cursor.lastrowid
        finally:
            await conn.close()
        return await self.get_user_by_id(user_id)

    async def update_user_login(self, user_id: int) -> None:
        """Update last_login_at timestamp."""
        conn = await self._get_connection()
        try:
            await conn.execute(
                "UPDATE users SET last_login_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user_id)
            )
            await conn.commit()
        finally:
            await conn.close()

    async def upsert_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create or update user on login."""
        user = await self.get_user_by_google_id(google_id)
        if user:
            # Existing user - update login time
            await self.update_user_login(user["id"])
            return await self.get_user_by_id(user["id"])
        # New user - create account
        return await self.create_user(google_id, email, name, picture_url)

    async def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Create a new session with UUID and expiration."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        conn = await self._get_connection()
        try:
            await conn.execute(
                "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
                (session_id, user_id, expires_at.isoformat())
            )
            await conn.commit()
        finally:
            await conn.close()
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session if valid (not revoked and not expired)."""
        import aiosqlite
        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """SELECT * FROM sessions WHERE id = ? AND is_revoked = FALSE AND expires_at > ?""",
                (session_id, datetime.utcnow().isoformat())
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def revoke_session(self, session_id: str) -> None:
        """Mark session as revoked (logout)."""
        conn = await self._get_connection()
        try:
            await conn.execute("UPDATE sessions SET is_revoked = TRUE WHERE id = ?", (session_id,))
            await conn.commit()
        finally:
            await conn.close()

    async def revoke_all_user_sessions(self, user_id: int) -> None:
        """Revoke all sessions for a user."""
        conn = await self._get_connection()
        try:
            await conn.execute("UPDATE sessions SET is_revoked = TRUE WHERE user_id = ?", (user_id,))
            await conn.commit()
        finally:
            await conn.close()

    async def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions from database."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "DELETE FROM sessions WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),)
            )
            await conn.commit()
            return cursor.rowcount
        finally:
            await conn.close()

    async def save_search_history(self, user_id: int, scenario: str, query_data: dict,
                                   results_data: list = None, result_count: int = 0,
                                   search_time_ms: float = 0) -> int:
        """Save search to history and return entry ID."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """INSERT INTO search_history (user_id, scenario, query_data, results_data, result_count, search_time_ms)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, scenario, json.dumps(query_data),
                 json.dumps(results_data) if results_data else None,
                 result_count, search_time_ms)
            )
            await conn.commit()
            return cursor.lastrowid
        finally:
            await conn.close()

    async def get_search_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get user's search history, most recent first."""
        import aiosqlite
        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """SELECT * FROM search_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (user_id, limit, offset)
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                # Parse JSON fields
                item["query_data"] = json.loads(item["query_data"])
                item["results_data"] = json.loads(item["results_data"]) if item.get("results_data") else None
                results.append(item)
            return results
        finally:
            await conn.close()

    async def get_history_entry(self, history_id: int, user_id: int) -> Optional[dict]:
        """Get a specific history entry by ID."""
        import aiosqlite
        conn = await self._get_connection()
        try:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM search_history WHERE id = ? AND user_id = ?",
                (history_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                item = dict(row)
                item["query_data"] = json.loads(item["query_data"])
                item["results_data"] = json.loads(item["results_data"]) if item.get("results_data") else None
                return item
            return None
        finally:
            await conn.close()

    async def delete_history_entry(self, history_id: int, user_id: int) -> bool:
        """Delete a history entry. Returns True if deleted."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                "DELETE FROM search_history WHERE id = ? AND user_id = ?",
                (history_id, user_id)
            )
            await conn.commit()
            return cursor.rowcount > 0
        finally:
            await conn.close()

    async def clear_user_history(self, user_id: int) -> int:
        """Delete all history for a user. Returns count deleted."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
            await conn.commit()
            return cursor.rowcount
        finally:
            await conn.close()


# ============================================================================
# PostgreSQL Implementation
# ============================================================================

class PostgreSQLDatabase(DatabaseInterface):
    """
    PostgreSQL database implementation using asyncpg.

    Uses connection pooling for better performance under load.
    Pool size: 5-20 connections.

    Best for: Production, multi-user scenarios, high concurrency.
    """

    # PostgreSQL schema (uses SERIAL instead of AUTOINCREMENT, JSONB for JSON)
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        google_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        picture_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TIMESTAMP NOT NULL,
        is_revoked BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS search_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        scenario TEXT NOT NULL,
        query_data JSONB NOT NULL,
        results_data JSONB,
        result_count INTEGER DEFAULT 0,
        search_time_ms REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
    CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
    """

    def __init__(self):
        """Initialize with no connection pool (created on init_db)."""
        self.pool = None

    async def init_db(self) -> None:
        """Create connection pool and initialize schema."""
        import asyncpg
        # Create connection pool with 5-20 connections
        self.pool = await asyncpg.create_pool(
            host=settings.pg_host,
            port=settings.pg_port,
            database=settings.pg_database,
            user=settings.pg_user,
            password=settings.pg_password,
            min_size=5,
            max_size=20
        )
        # Create tables
        async with self.pool.acquire() as conn:
            await conn.execute(self.SCHEMA)
        logger.info("PostgreSQL database initialized")

    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()

    async def get_user_by_google_id(self, google_id: str) -> Optional[dict]:
        """Find user by Google account ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE google_id = $1", google_id)
            return self._convert_row(row) if row else None

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Find user by database ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return self._convert_row(row) if row else None

    async def create_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create new user and return with RETURNING clause."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (google_id, email, name, picture_url)
                   VALUES ($1, $2, $3, $4) RETURNING *""",
                google_id, email, name, picture_url
            )
            return self._convert_row(row)

    async def update_user_login(self, user_id: int) -> None:
        """Update last_login_at timestamp."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_login_at = $1 WHERE id = $2",
                datetime.utcnow(), user_id
            )

    async def upsert_user(self, google_id: str, email: str, name: str, picture_url: Optional[str] = None) -> dict:
        """Create or update user on login."""
        user = await self.get_user_by_google_id(google_id)
        if user:
            await self.update_user_login(user["id"])
            return await self.get_user_by_id(user["id"])
        return await self.create_user(google_id, email, name, picture_url)

    async def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Create new session with UUID."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO sessions (id, user_id, expires_at) VALUES ($1, $2, $3)",
                session_id, user_id, expires_at
            )
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session if valid."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT * FROM sessions WHERE id = $1 AND is_revoked = FALSE AND expires_at > $2""",
                session_id, datetime.utcnow()
            )
            return self._convert_row(row) if row else None

    async def revoke_session(self, session_id: str) -> None:
        """Mark session as revoked."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE sessions SET is_revoked = TRUE WHERE id = $1", session_id)

    async def revoke_all_user_sessions(self, user_id: int) -> None:
        """Revoke all sessions for a user."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE sessions SET is_revoked = TRUE WHERE user_id = $1", user_id)

    async def cleanup_expired_sessions(self) -> int:
        """Delete expired sessions."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM sessions WHERE expires_at < $1", datetime.utcnow())
            return int(result.split()[-1])

    async def save_search_history(self, user_id: int, scenario: str, query_data: dict,
                                   results_data: list = None, result_count: int = 0,
                                   search_time_ms: float = 0) -> int:
        """Save search to history with NOW() for accurate timestamps."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO search_history (user_id, scenario, query_data, results_data, result_count, search_time_ms, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, NOW()) RETURNING id, created_at""",
                user_id, scenario, json.dumps(query_data),
                json.dumps(results_data) if results_data else None,
                result_count, search_time_ms
            )
            logger.info(f"Saved search history with id={row['id']}, created_at={row['created_at']}")
            return row["id"]

    def _convert_row(self, row) -> dict:
        """
        Convert asyncpg row to dict with proper type handling.

        Converts datetime objects to ISO strings and handles JSONB fields.
        """
        item = dict(row)
        # Convert datetime to ISO string for JSON serialization
        for key in ["created_at", "last_login_at", "expires_at"]:
            if key in item and item[key] is not None:
                if hasattr(item[key], 'isoformat'):
                    item[key] = item[key].isoformat()
        # Handle JSONB fields (asyncpg may return them as strings or dicts)
        if "query_data" in item:
            if isinstance(item["query_data"], str):
                item["query_data"] = json.loads(item["query_data"])
        if "results_data" in item:
            if isinstance(item["results_data"], str):
                item["results_data"] = json.loads(item["results_data"])
        return item

    async def get_search_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        """Get user's search history, most recent first."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM search_history WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3""",
                user_id, limit, offset
            )
            return [self._convert_row(row) for row in rows]

    async def get_history_entry(self, history_id: int, user_id: int) -> Optional[dict]:
        """Get a specific history entry."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM search_history WHERE id = $1 AND user_id = $2",
                history_id, user_id
            )
            return self._convert_row(row) if row else None

    async def delete_history_entry(self, history_id: int, user_id: int) -> bool:
        """Delete a history entry."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM search_history WHERE id = $1 AND user_id = $2",
                history_id, user_id
            )
            return int(result.split()[-1]) > 0

    async def clear_user_history(self, user_id: int) -> int:
        """Delete all history for a user."""
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM search_history WHERE user_id = $1", user_id)
            return int(result.split()[-1])


# ============================================================================
# Database Factory
# ============================================================================

def create_database() -> DatabaseInterface:
    """
    Create database instance based on configuration.

    Reads DATABASE_TYPE from settings and returns the appropriate
    database implementation.

    Returns:
        DatabaseInterface: SQLiteDatabase or PostgreSQLDatabase
    """
    if settings.database_type == "postgresql":
        logger.info("Using PostgreSQL database")
        return PostgreSQLDatabase()
    else:
        logger.info("Using SQLite database")
        return SQLiteDatabase()


# Global database instance - init_db() called during app startup
db = create_database()
