import aiosqlite
import json
from datetime import datetime
from loguru import logger

DB_PATH = "memory.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                wrapper_name TEXT,
                details TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wrappers (
                name TEXT PRIMARY KEY,
                status TEXT,
                last_success TEXT,
                last_failure TEXT,
                fail_count INTEGER DEFAULT 0,
                code TEXT
            )
        """)
        await db.commit()


async def log_event(event_type: str, wrapper_name: str, details: dict = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO events (timestamp, event_type, wrapper_name, details) VALUES (?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                event_type,
                wrapper_name,
                json.dumps(details or {}),
            ),
        )
        await db.commit()


async def mark_alive(wrapper_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO wrappers (name, status, last_success, fail_count)
            VALUES (?, 'alive', ?, 0)
            ON CONFLICT(name) DO UPDATE SET
                status = 'alive',
                last_success = excluded.last_success,
                fail_count = 0
        """, (wrapper_name, datetime.utcnow().isoformat()))
        await db.commit()


async def mark_dead(wrapper_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO wrappers (name, status, last_failure, fail_count)
            VALUES (?, 'dead', ?, 1)
            ON CONFLICT(name) DO UPDATE SET
                status = 'dead',
                last_failure = excluded.last_failure,
                fail_count = fail_count + 1
        """, (wrapper_name, datetime.utcnow().isoformat()))
        await db.commit()


async def get_wrapper_stats() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM wrappers ORDER BY fail_count ASC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_recent_events(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
