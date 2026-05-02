"""
rest_api.py — Lightweight FastAPI server exposing ImmortalAgent over HTTP.

Endpoints:
  GET  /health          — agent + wrapper health summary
  GET  /wrappers        — all wrapper stats
  GET  /events          — recent event log
  POST /ask             — send a prompt, get a response
  GET  /metrics         — prometheus-style text metrics
  GET  /budget          — current rate budget stats

Run with: uvicorn rest_api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import PlainTextResponse
    from pydantic import BaseModel
except ImportError:
    raise ImportError("pip install fastapi uvicorn")

from memory import init_db, get_wrapper_stats, get_recent_events
from wrapper_pool import WrapperPool
from rate_budget import BUDGET

_pool: Optional[WrapperPool] = None
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    await init_db()
    _pool = WrapperPool()
    yield


app = FastAPI(
    title="ImmortalAgent REST API",
    version="3.0",
    description="HTTP interface to the immortal-agent wrapper pool.",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    prompt: str
    timeout: float = 30.0


class AskResponse(BaseModel):
    response: str
    source: str
    latency_ms: int


@app.get("/health")
async def health():
    uptime = int(time.time() - _start_time)
    stats = await get_wrapper_stats()
    alive = [s for s in stats if s.get("status") == "alive"]
    return {
        "status": "ok" if alive else "degraded",
        "uptime_s": uptime,
        "alive_wrappers": len(alive),
        "total_wrappers": len(stats),
        "budget": BUDGET.stats(),
    }


@app.get("/wrappers")
async def wrappers():
    return await get_wrapper_stats()


@app.get("/events")
async def events(limit: int = 50):
    return await get_recent_events(limit)


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    if _pool is None:
        raise HTTPException(503, "Pool not initialised")
    await BUDGET.acquire()
    t0 = time.perf_counter()
    response, source = await _pool.send_with_fallback(req.prompt)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    if not response:
        raise HTTPException(503, "All wrappers failed")
    return AskResponse(response=response, source=source, latency_ms=latency_ms)


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    stats = await get_wrapper_stats()
    uptime = int(time.time() - _start_time)
    lines = [
        f"# HELP immortal_uptime_seconds Seconds since agent start",
        f"# TYPE immortal_uptime_seconds gauge",
        f"immortal_uptime_seconds {uptime}",
        f"# HELP immortal_wrapper_health Health score per wrapper",
        f"# TYPE immortal_wrapper_health gauge",
    ]
    for s in stats:
        name = s["name"].replace("-", "_")
        score = s.get("health_score", 0)
        lines.append(f'immortal_wrapper_health{{wrapper="{name}"}} {score}')
    lines.append(f"# HELP immortal_rpm Current requests per minute")
    lines.append(f"# TYPE immortal_rpm gauge")
    lines.append(f"immortal_rpm {BUDGET.calls_this_minute()}")
    return "\n".join(lines) + "\n"


@app.get("/budget")
async def budget():
    return BUDGET.stats()
