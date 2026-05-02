import httpx
from .base import BaseWrapper
from loguru import logger


class OpenRouterWrapper(BaseWrapper):
    name = "openrouter"

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "mistralai/mistral-7b-instruct:free"  # always-free model

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("openrouter", "")
        if not api_key:
            logger.warning("[openrouter] No API key configured.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/efekurucay/immortal-agent",
            "X-Title": "Immortal Agent",
        }
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[openrouter] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[openrouter] send() failed: {e}")
            return None
