import asyncio
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from loguru import logger

from wrappers import ALL_WRAPPERS
from memory import record_call, log_event
from config import MIN_ALIVE_LENGTH, SURVIVAL_PROMPT


CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


@dataclass
class CircuitState:
    failures: int = 0
    last_failure_ts: float = 0.0
    state: str = CLOSED
    opened_until: float = 0.0


class WrapperPool:
    """Manages all wrappers, health, and circuit breaker state.

    Wrapper priority is primarily determined by the static order in ALL_WRAPPERS,
    but dynamic health and circuit state decide whether a wrapper is eligible
    at any given moment.
    """

    def __init__(self):
        self.wrappers = [W() for W in ALL_WRAPPERS]
        self.circuits: Dict[str, CircuitState] = {
            w.name: CircuitState() for w in self.wrappers
        }

    # ---------------------------------------------------------------------
    # Circuit breaker helpers
    # ---------------------------------------------------------------------

    def _state_for(self, name: str) -> CircuitState:
        if name not in self.circuits:
            self.circuits[name] = CircuitState()
        return self.circuits[name]

    def _should_skip(self, name: str, now: float) -> bool:
        state = self._state_for(name)
        if state.state == OPEN:
            if now < state.opened_until:
                # Still in open window, skip this wrapper
                return True
            # Open window expired → half-open
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

    # ---------------------------------------------------------------------
    # Core send logic
    # ---------------------------------------------------------------------

    async def _call_with_retry(
        self,
        wrapper,
        prompt: str,
        *,
        max_retries: int = 2,
        base_delay: float = 0.1,
        budget_s: float = 3.0,
    ) -> Tuple[Optional[str], Optional[int]]:
        """Call wrapper.send with bounded retries and jitter.

        Returns (response_text or None, latency_ms or None).
        """

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

    async def send_with_fallback(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """Try each wrapper (respecting circuit state) until one responds.

        Returns (response_text, wrapper_name) or (None, None) if all fail.
        """

        # TODO: in the future, order by dynamic health_score from DB.
        for wrapper in self.wrappers:
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

            # Failure path
            self._on_failure(name, now)
            health = await record_call(name, False, latency_ms or 0)
            await log_event(
                "ping_failed",
                name,
                latency_ms=latency_ms,
                success=False,
                health_score=health,
            )

        # All wrappers failed
        return None, None

    # ---------------------------------------------------------------------
    # Backwards-compatible helpers used by agent.self_repair
    # ---------------------------------------------------------------------

    async def get_live_wrapper(self):
        """Return the first wrapper that passes a basic is_alive check.

        This is only used for self-repair code generation. It ignores
        circuit state on purpose to maximize chances of finding *any*
        working model.
        """

        for wrapper in self.wrappers:
            try:
                alive = await wrapper.is_alive(min_length=MIN_ALIVE_LENGTH)
            except Exception:  # noqa: BLE001
                alive = False

            if alive:
                await log_event("ping_success", wrapper.name, details={"probe": True})
                return wrapper

        return None

    def reset_dead(self):  # kept for backwards compatibility
        """No-op placeholder, retained to avoid breaking existing code.

        Circuit state is time-based and will naturally heal.
        """

        return None

    def all_dead(self) -> bool:
        """Return True if all circuits are currently open.

        Not used by the main loop today, but can be helpful for diagnostics.
        """

        now = time.time()
        return all(
            self._should_skip(w.name, now) for w in self.wrappers
        )
