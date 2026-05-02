import httpx
from .base import BaseWrapper
from loguru import logger


class OllamaWrapper(BaseWrapper):
    """
    Local Ollama instance — no API key, no rate limits, no auth.
    The most reliable wrapper if you have Ollama running locally.
    Install: https://ollama.com
    Pull a model: ollama pull llama3.2
    """
    name = "ollama"

    async def send(self, prompt: str) -> str | None:
        from config import OLLAMA_BASE_URL, OLLAMA_MODEL
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[ollama] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["message"]["content"]
        except Exception as e:
            logger.error(f"[ollama] send() failed: {e}")
            return None
