"""
memory.py — Persistent memory with time-series stats and health history.

Schema:
  events   — structured event log (all agent events)
  wrappers — per-wrapper stats (running totals + health_score)
  hourly   — hourly aggregated snapshots for trend analysis
"""
from __future__ import annotations

import aiosqlite
import json
from datetime import datetime, timezone
from loguru import logger

DB_PATH = "memory.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT,
                event_type    TEXT,
                wrapper_name  TEXT,
                details       TEXT,
                latency_ms    INTEGER,
                success       INTEGER,
                health_score  REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wrappers (
                name              TEXT PRIMARY KEY,
                status            TEXT,
                last_success      TEXT,
                last_failure      TEXT,
                fail_count        INTEGER DEFAULT 0,
                success_count     INTEGER DEFAULT 0,
                total_latency_ms  INTEGER DEFAULT 0,
                health_score      REAL    DEFAULT 0.5,
                code              TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hourly (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                hour          TEXT,
                wrapper_name  TEXT,
                success_count INTEGER DEFAULT 0,
                fail_count    INTEGER DEFAULT 0,
                avg_latency   REAL    DEFAULT 0,
                health_score  REAL    DEFAULT 0.5,
                UNIQUE(hour, wrapper_name)
            )
        """)
        # Indexes for fast time-series queries
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_wrapper ON events(wrapper_name)"
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
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO events
              (timestamp, event_type, wrapper_name, details, latency_ms, success, health_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).isoformat(),
            event_type,
            wrapper_name,
            json.dumps(details or {}),
            latency_ms,
            int(success) if success is not None else None,
            health_score,
        ))
        await db.commit()


async def _compute_health(
    success_count: int, fail_count: int, total_latency_ms: int
) -> float:
    calls = max(success_count + fail_count, 1)
    success_rate = success_count / calls
    avg_latency = total_latency_ms / calls if calls > 0 else 0
    if avg_latency <= 500:
        lat_score = 1.0
    elif avg_latency >= 8000:
        lat_score = 0.0
    else:
        lat_score = 1.0 - (avg_latency - 500) / 7500
    health = 0.60 * success_rate + 0.40 * lat_score
    return round(max(0.0, min(1.0, health)), 4)


async def record_call(
    wrapper_name: str, success: bool, latency_ms: int
) -> float:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT success_count, fail_count, total_latency_ms FROM wrappers WHERE name = ?",
            (wrapper_name,),
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            sc = 1 if success else 0
            fc = 0 if success else 1
            tl = max(latency_ms, 0)
        else:
            sc = (row["success_count"] or 0) + (1 if success else 0)
            fc = (row["fail_count"] or 0) + (0 if success else 1)
            tl = (row["total_latency_ms"] or 0) + max(latency_ms, 0)

        health = await _compute_health(sc, fc, tl)
        now = datetime.now(timezone.utc).isoformat()
        status = "alive" if success else "dead"
        ls = now if success else None
        lf = now if not success else None

        await db.execute("""
            INSERT INTO wrappers
              (name, status, last_success, last_failure, fail_count, success_count,
               total_latency_ms, health_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                status           = excluded.status,
                last_success     = COALESCE(excluded.last_success, wrappers.last_success),
                last_failure     = COALESCE(excluded.last_failure, wrappers.last_failure),
                fail_count       = excluded.fail_count,
                success_count    = excluded.success_count,
                total_latency_ms = excluded.total_latency_ms,
                health_score     = excluded.health_score
        """, (wrapper_name, status, ls, lf, fc, sc, tl, health))

        # Hourly snapshot upsert
        hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        await db.execute("""
            INSERT INTO hourly (hour, wrapper_name, success_count, fail_count, avg_latency, health_score)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hour, wrapper_name) DO UPDATE SET
                success_count = hourly.success_count + ?,
                fail_count    = hourly.fail_count + ?,
                avg_latency   = (hourly.avg_latency * (hourly.success_count + hourly.fail_count)
                                  + ?) / (hourly.success_count + hourly.fail_count + 1),
                health_score  = excluded.health_score
        """, (
            hour, wrapper_name,
            1 if success else 0,
            0 if success else 1,
            latency_ms, health,
            1 if success else 0,
            0 if success else 1,
            latency_ms,
        ))

        await db.commit()
    return health


async def mark_alive(wrapper_name: str):
    await record_call(wrapper_name, True, 0)


async def mark_dead(wrapper_name: str):
    await record_call(wrapper_name, False, 0)


async def get_wrapper_stats() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM wrappers ORDER BY health_score DESC, fail_count ASC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_recent_events(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_hourly_trend(wrapper_name: str, hours: int = 24) -> list[dict]:
    """Return hourly health_score trend for a wrapper (last N hours)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT hour, success_count, fail_count, avg_latency, health_score
            FROM hourly
            WHERE wrapper_name = ?
            ORDER BY hour DESC
            LIMIT ?
        """, (wrapper_name, hours)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_best_wrapper_by_hour(target_hour: str) -> str | None:
    """Return wrapper with highest health_score for a given hour string (YYYY-MM-DDTHH:00)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT wrapper_name FROM hourly
            WHERE hour = ?
            ORDER BY health_score DESC
            LIMIT 1
        """, (target_hour,)) as cur:
            row = await cur.fetchone()
            return row["wrapper_name"] if row else None
