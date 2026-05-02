import aiosqlite
import json
from datetime import datetime
from loguru import logger

DB_PATH = "memory.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Base tables
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                wrapper_name TEXT,
                details TEXT,
                latency_ms INTEGER,
                success INTEGER,
                health_score REAL
            )
            """,
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS wrappers (
                name TEXT PRIMARY KEY,
                status TEXT,
                last_success TEXT,
                last_failure TEXT,
                fail_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                total_latency_ms INTEGER DEFAULT 0,
                health_score REAL DEFAULT 0.0,
                code TEXT
            )
            """,
        )

        await db.commit()


async def log_event(
    event_type: str,
    wrapper_name: str,
    details: dict | None = None,
    *,
    latency_ms: int | None = None,
    success: bool | None = None,
    health_score: float | None = None,
):
    """Insert a structured event into the events table."""

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO events (timestamp, event_type, wrapper_name, details, latency_ms, success, health_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                event_type,
                wrapper_name,
                json.dumps(details or {}),
                latency_ms,
                int(success) if success is not None else None,
                health_score,
            ),
        )
        await db.commit()


async def _compute_health(success_count: int, fail_count: int, total_latency_ms: int) -> float:
    """Compute a composite health score in [0,1] from success rate and avg latency."""

    calls = max(success_count + fail_count, 1)
    success_rate = success_count / calls

    avg_latency = total_latency_ms / calls if calls > 0 else 0
    if avg_latency <= 1000:
        latency_score = 1.0
    elif avg_latency >= 5000:
        latency_score = 0.1
    else:
        # Linearly decay from 1.0 → 0.1 between 1s and 5s
        latency_score = 1.0 - 0.9 * (avg_latency - 1000) / 4000

    # Weighted combination: success is slightly more important than latency
    health = 0.6 * success_rate + 0.4 * latency_score
    return max(0.0, min(1.0, health))


async def record_call(wrapper_name: str, success: bool, latency_ms: int) -> float:
    """Update wrapper stats after a call and return the new health score."""

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT success_count, fail_count, total_latency_ms, last_success, last_failure FROM wrappers WHERE name = ?",
            (wrapper_name,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            success_count = 1 if success else 0
            fail_count = 0 if success else 1
            total_latency_ms = max(latency_ms, 0)
            last_success = None
            last_failure = None
        else:
            success_count = (row["success_count"] or 0) + (1 if success else 0)
            fail_count = (row["fail_count"] or 0) + (0 if success else 1)
            total_latency_ms = (row["total_latency_ms"] or 0) + max(latency_ms, 0)
            last_success = row["last_success"]
            last_failure = row["last_failure"]

        health_score = await _compute_health(success_count, fail_count, total_latency_ms)
        now = datetime.utcnow().isoformat()

        status = "alive" if success else "dead"
        if success:
            last_success = now
        else:
            last_failure = now

        await db.execute(
            """
            INSERT INTO wrappers (name, status, last_success, last_failure, fail_count, success_count, total_latency_ms, health_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                status = excluded.status,
                last_success = COALESCE(excluded.last_success, wrappers.last_success),
                last_failure = COALESCE(excluded.last_failure, wrappers.last_failure),
                fail_count = excluded.fail_count,
                success_count = excluded.success_count,
                total_latency_ms = excluded.total_latency_ms,
                health_score = excluded.health_score
            """,
            (
                wrapper_name,
                status,
                last_success,
                last_failure,
                fail_count,
                success_count,
                total_latency_ms,
                health_score,
            ),
        )
        await db.commit()

    return health_score


async def mark_alive(wrapper_name: str):
    await record_call(wrapper_name, True, 0)


async def mark_dead(wrapper_name: str):
    await record_call(wrapper_name, False, 0)


async def get_wrapper_stats() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM wrappers ORDER BY health_score DESC, fail_count ASC",
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_recent_events(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
