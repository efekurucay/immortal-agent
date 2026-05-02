import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from loguru import logger

from wrappers import ALL_WRAPPERS
from memory import record_call, log_event, get_wrapper_stats
from config import MIN_ALIVE_LENGTH


CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"

# Canary settings
CANARY_CALLS = 5          # How many calls to observe before full promotion
CANARY_MIN_SUCCESS = 0.6  # Min success rate to promote (60%)
CANARY_MAX_FAILS = 3      # If consecutive fails exceed this, quarantine immediately


@dataclass
class CircuitState:
    failures: int = 0
    last_failure_ts: float = 0.0
    state: str = CLOSED
    opened_until: float = 0.0


@dataclass
class CanaryState:
    """Tracks probationary period for newly generated wrappers."""
    total: int = 0
    successes: int = 0
    consecutive_fails: int = 0
    promoted: bool = False
    quarantined: bool = False


class WrapperPool:
    """Manages all wrappers, health, circuit breaker, and canary state.

    Static wrappers (ALL_WRAPPERS) are trusted from the start.
    Generated wrappers enter canary mode and must earn promotion.
    """

    def __init__(self):
        self.wrappers = [W() for W in ALL_WRAPPERS]
        self.circuits: Dict[str, CircuitState] = {
            w.name: CircuitState() for w in self.wrappers
        }
        self._static_priority = {w.name: i for i, w in enumerate(self.wrappers)}
        # canary tracking — only populated for dynamically added wrappers
        self._canary: Dict[str, CanaryState] = {}

    # ------------------------------------------------------------------
    # Circuit breaker helpers
    # ------------------------------------------------------------------

    def _state_for(self, name: str) -> CircuitState:
        if name not in self.circuits:
            self.circuits[name] = CircuitState()
        return self.circuits[name]

    def _should_skip(self, name: str, now: float) -> bool:
        state = self._state_for(name)
        if state.state == OPEN:
            if now < state.opened_until:
                return True
            state.state = HALF_OPEN
        return False

    def _on_success(self, name: str):
        state = self._state_for(name)
        state.failures = 0
        state.state = CLOSED
        state.opened_until = 0.0

    def _on_failure(
        self,
        name: str,
        now: float,
        *,
        max_failures: int = 3,
        open_seconds: float = 60.0,
    ):
        state = self._state_for(name)
        state.failures += 1
        state.last_failure_ts = now
        if state.failures >= max_failures:
            state.state = OPEN
            state.opened_until = now + open_seconds
            logger.warning(
                f"[pool] Circuit opened for {name} after {state.failures} failures."
            )

    # ------------------------------------------------------------------
    # Canary helpers
    # ------------------------------------------------------------------

    def add_wrapper(self, wrapper_class) -> None:
        """Add a dynamically generated wrapper in canary mode."""
        instance = wrapper_class()
        self.wrappers.append(instance)
        self.circuits[instance.name] = CircuitState()
        self._canary[instance.name] = CanaryState()
        # Give canary a low static priority so it's tried last
        self._static_priority[instance.name] = len(self.wrappers) + 1000
        logger.info(f"[pool] Canary wrapper added: {instance.name}")

    def _is_quarantined(self, name: str) -> bool:
        cs = self._canary.get(name)
        return cs is not None and cs.quarantined

    def _record_canary(self, name: str, success: bool) -> None:
        """Update canary stats and decide promotion or quarantine."""
        cs = self._canary.get(name)
        if cs is None or cs.promoted or cs.quarantined:
            return

        cs.total += 1
        if success:
            cs.successes += 1
            cs.consecutive_fails = 0
        else:
            cs.consecutive_fails += 1

        # Immediate quarantine on too many consecutive fails
        if cs.consecutive_fails >= CANARY_MAX_FAILS:
            cs.quarantined = True
            logger.error(
                f"[pool][canary] {name} quarantined after "
                f"{cs.consecutive_fails} consecutive failures."
            )
            asyncio.ensure_future(
                log_event("wrapper_quarantined", name, details={"reason": "consecutive_fails"})
            )
            return

        if cs.total >= CANARY_CALLS:
            rate = cs.successes / cs.total
            if rate >= CANARY_MIN_SUCCESS:
                cs.promoted = True
                # Boost priority to normal range
                self._static_priority[name] = len(ALL_WRAPPERS) + 1
                logger.success(
                    f"[pool][canary] {name} promoted! success_rate={rate:.0%}"
                )
                asyncio.ensure_future(
                    log_event("wrapper_promoted", name, details={"success_rate": rate})
                )
            else:
                cs.quarantined = True
                logger.error(
                    f"[pool][canary] {name} quarantined after canary period. "
                    f"success_rate={rate:.0%} < {CANARY_MIN_SUCCESS:.0%}"
                )
                asyncio.ensure_future(
                    log_event(
                        "wrapper_quarantined",
                        name,
                        details={"reason": "low_success_rate", "rate": rate},
                    )
                )

    def canary_status(self, name: str) -> Optional[str]:
        """Return human-readable canary status for dashboard."""
        cs = self._canary.get(name)
        if cs is None:
            return None  # trusted static wrapper
        if cs.quarantined:
            return "quarantined"
        if cs.promoted:
            return "promoted"
        return f"canary {cs.total}/{CANARY_CALLS}"

    # ------------------------------------------------------------------
    # Core send logic
    # ------------------------------------------------------------------

    async def _call_with_retry(
        self,
        wrapper,
        prompt: str,
        *,
        max_retries: int = 2,
        base_delay: float = 0.1,
        budget_s: float = 3.0,
    ) -> Tuple[Optional[str], Optional[int]]:
        """Call wrapper.send with bounded retries and jitter."""

        attempt = 0
        start_overall = time.perf_counter()
        last_exc: Optional[Exception] = None

        while attempt <= max_retries:
            attempt += 1
            single_start = time.perf_counter()
            try:
                response = await wrapper.send(prompt)
                latency_ms = int((time.perf_counter() - single_start) * 1000)
                return response, latency_ms
            except Exception as e:  # noqa: BLE001
                last_exc = e
                logger.error(f"[pool] {wrapper.name} send() threw on attempt {attempt}: {e}")

            if time.perf_counter() - start_overall > budget_s:
                break

            delay = base_delay * (2 ** (attempt - 1))
            delay += random.uniform(0, delay)
            await asyncio.sleep(delay)

        if last_exc is not None:
            logger.error(f"[pool] {wrapper.name} failed after retries: {last_exc}")
        return None, None

    async def _ordered_wrappers(self):
        """Return wrappers ordered by dynamic health and static priority.

        Quarantined wrappers are excluded entirely.
        Canary wrappers appear last (high static priority index).
        """

        try:
            stats = await get_wrapper_stats()
            health_by_name = {
                s["name"]: float(s.get("health_score") or 0.0) for s in stats
            }
        except Exception:  # noqa: BLE001
            health_by_name = {}

        def sort_key(w):
            return (
                -health_by_name.get(w.name, 0.0),
                self._static_priority.get(w.name, 0),
            )

        return [
            w for w in sorted(self.wrappers, key=sort_key)
            if not self._is_quarantined(w.name)
        ]

    async def send_with_fallback(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """Try each wrapper (respecting circuit + quarantine) until one responds."""

        wrappers = await self._ordered_wrappers()

        for wrapper in wrappers:
            name = wrapper.name
            now = time.time()

            if self._should_skip(name, now):
                logger.debug(f"[pool] Skipping {name} due to open circuit.")
                continue

            response, latency_ms = await self._call_with_retry(wrapper, prompt)
            success = bool(
                response is not None
                and isinstance(response, str)
                and len(response.strip()) >= MIN_ALIVE_LENGTH
            )

            # Update canary stats if applicable
            self._record_canary(name, success)

            if success:
                self._on_success(name)
                health = await record_call(name, True, latency_ms or 0)
                await log_event(
                    "ping_success",
                    name,
                    latency_ms=latency_ms,
                    success=True,
                    health_score=health,
                )
                return response, name

            self._on_failure(name, now)
            health = await record_call(name, False, latency_ms or 0)
            await log_event(
                "ping_failed",
                name,
                latency_ms=latency_ms,
                success=False,
                health_score=health,
            )

        return None, None

    # ------------------------------------------------------------------
    # Backwards-compatible helpers
    # ------------------------------------------------------------------

    async def get_live_wrapper(self):
        """Return first wrapper that passes is_alive. Used for self-repair codegen."""

        for wrapper in self.wrappers:
            if self._is_quarantined(wrapper.name):
                continue
            try:
                alive = await wrapper.is_alive(min_length=MIN_ALIVE_LENGTH)
            except Exception:  # noqa: BLE001
                alive = False

            if alive:
                await log_event("ping_success", wrapper.name, details={"probe": True})
                return wrapper

        return None

    def reset_dead(self):
        """No-op placeholder, retained for backwards compatibility."""
        return None

    def all_dead(self) -> bool:
        """Return True if all non-quarantined circuits are currently open."""
        now = time.time()
        return all(
            self._should_skip(w.name, now)
            for w in self.wrappers
            if not self._is_quarantined(w.name)
        )
