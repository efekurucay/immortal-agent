import asyncio
from loguru import logger
from wrappers import ALL_WRAPPERS
from memory import mark_alive, mark_dead, log_event
from config import MIN_ALIVE_LENGTH


class WrapperPool:
    def __init__(self):
        # Instantiate all built-in wrappers
        self.wrappers = [W() for W in ALL_WRAPPERS]
        self.dead: set[str] = set()

    def add_wrapper(self, wrapper_class):
        """Dynamically add a new wrapper class to the pool."""
        instance = wrapper_class()
        self.wrappers.append(instance)
        logger.info(f"[pool] Added new wrapper: {instance.name}")

    async def get_live_wrapper(self):
        """Return the first wrapper that is currently alive."""
        for wrapper in self.wrappers:
            if wrapper.name in self.dead:
                continue
            alive = await wrapper.is_alive(min_length=MIN_ALIVE_LENGTH)
            if alive:
                await mark_alive(wrapper.name)
                await log_event("ping_success", wrapper.name)
                return wrapper
            else:
                self.dead.add(wrapper.name)
                await mark_dead(wrapper.name)
                await log_event("ping_failed", wrapper.name)
                logger.warning(f"[pool] {wrapper.name} is dead.")
        return None

    async def send_with_fallback(self, prompt: str) -> tuple[str | None, str | None]:
        """
        Try each wrapper until one responds.
        Returns (response_text, wrapper_name) or (None, None).
        """
        for wrapper in self.wrappers:
            try:
                response = await wrapper.send(prompt)
                if response and len(response.strip()) >= MIN_ALIVE_LENGTH:
                    self.dead.discard(wrapper.name)
                    await mark_alive(wrapper.name)
                    return response, wrapper.name
                else:
                    self.dead.add(wrapper.name)
                    await mark_dead(wrapper.name)
            except Exception as e:
                logger.error(f"[pool] {wrapper.name} threw: {e}")
                self.dead.add(wrapper.name)
                await mark_dead(wrapper.name)
        return None, None

    def reset_dead(self):
        """Clear the dead set to retry all wrappers."""
        self.dead.clear()

    def all_dead(self) -> bool:
        return all(w.name in self.dead for w in self.wrappers)
