"""
health.py — Composite health scoring with time-series awareness.

Scores are computed from:
  - 1h / 24h success rate  (40% weight)
  - P95 latency             (30% weight)
  - error rate              (20% weight)
  - rate-limit signal       (10% weight)

All scores normalised to [0.0, 1.0].
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Deque, List, Optional
from collections import deque


@dataclass
class CallRecord:
    ts: float          # unix timestamp
    success: bool
    latency_ms: int
    rate_limited: bool = False


@dataclass
class HealthWindow:
    """Rolling window of call records for a single wrapper."""
    records: Deque[CallRecord] = field(default_factory=lambda: deque(maxlen=500))

    def push(self, success: bool, latency_ms: int, rate_limited: bool = False) -> None:
        self.records.append(CallRecord(
            ts=time.time(),
            success=success,
            latency_ms=latency_ms,
            rate_limited=rate_limited,
        ))

    def _window(self, seconds: int) -> List[CallRecord]:
        cutoff = time.time() - seconds
        return [r for r in self.records if r.ts >= cutoff]

    def success_rate(self, window_s: int = 3600) -> float:
        recs = self._window(window_s)
        if not recs:
            return 0.5  # neutral prior
        return sum(1 for r in recs if r.success) / len(recs)

    def p95_latency_ms(self, window_s: int = 3600) -> float:
        recs = self._window(window_s)
        if not recs:
            return 1000.0
        lats = sorted(r.latency_ms for r in recs)
        idx = max(0, int(len(lats) * 0.95) - 1)
        return float(lats[idx])

    def error_rate(self, window_s: int = 3600) -> float:
        return 1.0 - self.success_rate(window_s)

    def rate_limit_signal(self, window_s: int = 300) -> float:
        """Fraction of recent calls that were rate-limited."""
        recs = self._window(window_s)
        if not recs:
            return 0.0
        return sum(1 for r in recs if r.rate_limited) / len(recs)

    def score(self) -> float:
        sr = self.success_rate(3600)
        lat = self.p95_latency_ms(3600)
        rl = self.rate_limit_signal(300)

        # Latency score: 1.0 at <=500ms, 0.0 at >=8000ms
        if lat <= 500:
            lat_score = 1.0
        elif lat >= 8000:
            lat_score = 0.0
        else:
            lat_score = 1.0 - (lat - 500) / 7500

        err_score = 1.0 - self.error_rate(3600)
        rl_score = 1.0 - rl

        composite = (
            0.40 * sr
            + 0.30 * lat_score
            + 0.20 * err_score
            + 0.10 * rl_score
        )
        return round(max(0.0, min(1.0, composite)), 4)

    def hourly_stats(self) -> dict:
        recs = self._window(3600)
        return {
            "calls_1h": len(recs),
            "success_rate_1h": round(self.success_rate(3600), 3),
            "p95_latency_ms_1h": round(self.p95_latency_ms(3600), 1),
            "error_rate_1h": round(self.error_rate(3600), 3),
            "health_score": self.score(),
        }
