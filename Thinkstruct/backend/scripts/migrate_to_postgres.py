#!/usr/bin/env python3
"""
Migration script: SQLite to PostgreSQL

Usage:
    python -m backend.scripts.migrate_to_postgres

Before running:
    1. Install PostgreSQL and create database:
       createdb thinkstruct

    2. Set environment variables:
       export DATABASE_TYPE=postgresql
       export PG_HOST=localhost
       export PG_PORT=5432
       export PG_DATABASE=thinkstruct
       export PG_USER=postgres
       export PG_PASSWORD=your_password
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def parse_datetime(dt_str):
    """Parse datetime string to datetime object."""
    from datetime import datetime
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    # Try different formats
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


async def migrate():
    """Migrate data from SQLite to PostgreSQL."""
    import aiosqlite
    import asyncpg

    # SQLite path
    sqlite_path = os.path.join(
        os.path.dirname(__file__), "..", "thinkstruct.db"
    )

    if not os.path.exists(sqlite_path):
        print(f"SQLite database not found: {sqlite_path}")
        return

    # PostgreSQL connection info
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = int(os.getenv("PG_PORT", "5432"))
    pg_database = os.getenv("PG_DATABASE", "thinkstruct")
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "")

    print(f"Migrating from: {sqlite_path}")
    print(f"Migrating to: postgresql://{pg_user}@{pg_host}:{pg_port}/{pg_database}")

    # Connect to SQLite
    sqlite_conn = await aiosqlite.connect(sqlite_path)
    sqlite_conn.row_factory = aiosqlite.Row

    # Connect to PostgreSQL
    pg_conn = await asyncpg.connect(
        host=pg_host,
        port=pg_port,
        database=pg_database,
        user=pg_user,
        password=pg_password
    )

    try:
        # Create tables in PostgreSQL
        await pg_conn.execute("""
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
        """)
        print("PostgreSQL tables created")

        # Migrate users
        cursor = await sqlite_conn.execute("SELECT * FROM users")
        users = await cursor.fetchall()
        print(f"Found {len(users)} users to migrate")

        for user in users:
            user_dict = dict(user)
            try:
                await pg_conn.execute("""
                    INSERT INTO users (id, google_id, email, name, picture_url, created_at, last_login_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                """,
                    user_dict["id"],
                    user_dict["google_id"],
                    user_dict["email"],
                    user_dict["name"],
                    user_dict.get("picture_url"),
                    parse_datetime(user_dict.get("created_at")),
                    parse_datetime(user_dict.get("last_login_at"))
                )
            except Exception as e:
                print(f"  Error migrating user {user_dict['id']}: {e}")

        # Reset sequence for users
        await pg_conn.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
        print("Users migrated")

        # Migrate sessions
        cursor = await sqlite_conn.execute("SELECT * FROM sessions")
        sessions = await cursor.fetchall()
        print(f"Found {len(sessions)} sessions to migrate")

        for session in sessions:
            session_dict = dict(session)
            try:
                await pg_conn.execute("""
                    INSERT INTO sessions (id, user_id, expires_at, is_revoked)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO NOTHING
                """,
                    session_dict["id"],
                    session_dict["user_id"],
                    parse_datetime(session_dict["expires_at"]),
                    bool(session_dict.get("is_revoked", False))
                )
            except Exception as e:
                print(f"  Error migrating session {session_dict['id']}: {e}")

        print("Sessions migrated")

        # Migrate search history
        cursor = await sqlite_conn.execute("SELECT * FROM search_history")
        history_entries = await cursor.fetchall()
        print(f"Found {len(history_entries)} history entries to migrate")

        for entry in history_entries:
            entry_dict = dict(entry)
            try:
                query_data = entry_dict.get("query_data", "{}")
                results_data = entry_dict.get("results_data")

                await pg_conn.execute("""
                    INSERT INTO search_history (id, user_id, scenario, query_data, results_data, result_count, search_time_ms, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO NOTHING
                """,
                    entry_dict["id"],
                    entry_dict["user_id"],
                    entry_dict["scenario"],
                    query_data,
                    results_data,
                    entry_dict.get("result_count", 0),
                    entry_dict.get("search_time_ms", 0),
                    parse_datetime(entry_dict.get("created_at"))
                )
            except Exception as e:
                print(f"  Error migrating history entry {entry_dict['id']}: {e}")

        # Reset sequence for search_history
        await pg_conn.execute("SELECT setval('search_history_id_seq', (SELECT MAX(id) FROM search_history))")
        print("Search history migrated")

        print("\nMigration completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with DATABASE_TYPE=postgresql")
        print("2. Restart the backend server")

    finally:
        await sqlite_conn.close()
        await pg_conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
