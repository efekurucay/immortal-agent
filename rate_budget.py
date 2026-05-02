"""
rate_budget.py — Global rate-limit budget to prevent self-DDoS.

Each call costs 1 token from the per-minute bucket.
If the bucket is empty, calls are queued with a small sleep.
Also enforces a per-minute token-estimate guard.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class RateBudget:
    max_rpm: int = 60          # max requests per minute
    max_tokens_pm: int = 50_000  # estimated token budget per minute
    avg_tokens_per_call: int = 600

    _call_times: list = field(default_factory=list)
    _token_times: list = field(default_factory=list)

    def _prune(self) -> None:
        cutoff = time.time() - 60
        self._call_times = [t for t in self._call_times if t > cutoff]
        self._token_times = [t for t in self._token_times if t > cutoff]

    def calls_this_minute(self) -> int:
        self._prune()
        return len(self._call_times)

    def tokens_this_minute(self) -> int:
        self._prune()
        return len(self._token_times) * self.avg_tokens_per_call

    async def acquire(self) -> None:
        """Block until a call slot is available."""
        while True:
            self._prune()
            if (
                len(self._call_times) < self.max_rpm
                and self.tokens_this_minute() < self.max_tokens_pm
            ):
                now = time.time()
                self._call_times.append(now)
                self._token_times.append(now)
                return
            wait = 0.5
            logger.debug(f"[budget] Rate budget full ({len(self._call_times)} rpm). Waiting {wait}s...")
            await asyncio.sleep(wait)

    def stats(self) -> dict:
        return {
            "calls_this_minute": self.calls_this_minute(),
            "tokens_this_minute_est": self.tokens_this_minute(),
            "max_rpm": self.max_rpm,
            "max_tokens_pm": self.max_tokens_pm,
        }


# Module-level singleton
BUDGET = RateBudget()
