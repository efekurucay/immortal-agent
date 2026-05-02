from abc import ABC, abstractmethod


class BaseWrapper(ABC):
    """
    Abstract base class for all LLM service wrappers.
    A wrapper is considered alive if send() returns a non-empty string.
    """

    name: str = "base"

    @abstractmethod
    async def send(self, prompt: str) -> str | None:
        """
        Send a prompt to the service and return the response text.
        Return None if the service is unreachable or returns an error.
        """
        ...

    async def is_alive(self, min_length: int = 10) -> bool:
        from config import SURVIVAL_PROMPT
        try:
            response = await self.send(SURVIVAL_PROMPT)
            return (
                response is not None
                and isinstance(response, str)
                and len(response.strip()) >= min_length
            )
        except Exception:
            return False
