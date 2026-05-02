"""
multi_agent.py — Multi-agent coordinator.

Runs N ImmortalAgent instances (shards) each with their own WrapperPool.
A Coordinator distributes prompts round-robin across healthy shards.
If a shard's pool goes fully dead, the coordinator reroutes to others.

Usage:
    python multi_agent.py --shards 3

Or import and embed:
    from multi_agent import Coordinator
    coord = Coordinator(n_shards=3)
    await coord.start()
    resp = await coord.ask("Are you alive?")
"""
from __future__ import annotations

import asyncio
import time
from typing import List, Optional, Tuple
from loguru import logger
from memory import init_db, log_event
from wrapper_pool import WrapperPool
from rate_budget import BUDGET
from config import SURVIVAL_PROMPT, PING_INTERVAL


class AgentShard:
    """Single agent shard with its own pool."""

    def __init__(self, shard_id: int):
        self.shard_id = shard_id
        self.name = f"shard-{shard_id}"
        self.pool = WrapperPool()
        self.alive = False
        self.last_ping = 0.0
        self.failures = 0

    async def ping(self) -> bool:
        await BUDGET.acquire()
        response, source = await self.pool.send_with_fallback(SURVIVAL_PROMPT)
        self.last_ping = time.time()
        if response:
            self.alive = True
            self.failures = 0
            logger.info(f"[{self.name}] ✅ alive via {source}")
            return True
        self.alive = False
        self.failures += 1
        logger.warning(f"[{self.name}] 💀 dead (failures={self.failures})")
        return False

    async def ask(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        await BUDGET.acquire()
        return await self.pool.send_with_fallback(prompt)

    def is_healthy(self) -> bool:
        return self.alive and self.failures < 5


class Coordinator:
    """Routes requests across multiple AgentShards."""

    def __init__(self, n_shards: int = 3):
        self.shards: List[AgentShard] = [
            AgentShard(i) for i in range(n_shards)
        ]
        self._rr_idx = 0
        self._running = False

    async def start(self) -> None:
        await init_db()
        self._running = True
        asyncio.ensure_future(self._heartbeat_loop())
        logger.success(f"[coordinator] Started with {len(self.shards)} shards.")

    async def stop(self) -> None:
        self._running = False

    async def _heartbeat_loop(self) -> None:
        while self._running:
            tasks = [s.ping() for s in self.shards]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            alive_count = sum(1 for r in results if r is True)
            await log_event(
                "coordinator_heartbeat",
                "coordinator",
                details={"alive_shards": alive_count, "total": len(self.shards)},
            )
            await asyncio.sleep(PING_INTERVAL)

    def _next_shard(self) -> Optional[AgentShard]:
        healthy = [s for s in self.shards if s.is_healthy()]
        if not healthy:
            return None
        shard = healthy[self._rr_idx % len(healthy)]
        self._rr_idx += 1
        return shard

    async def ask(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        shard = self._next_shard()
        if shard is None:
            logger.error("[coordinator] All shards unhealthy.")
            return None, None
        return await shard.ask(prompt)

    def status(self) -> list:
        return [
            {
                "shard": s.name,
                "alive": s.alive,
                "failures": s.failures,
                "last_ping": s.last_ping,
            }
            for s in self.shards
        ]


async def _main(n_shards: int = 3) -> None:
    coord = Coordinator(n_shards=n_shards)
    await coord.start()
    while True:
        await asyncio.sleep(10)
        status = coord.status()
        for s in status:
            logger.info(f"{s['shard']}: alive={s['alive']} fails={s['failures']}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--shards", type=int, default=3)
    args = p.parse_args()
    asyncio.run(_main(n_shards=args.shards))
