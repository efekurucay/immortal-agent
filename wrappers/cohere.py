import httpx
from .base import BaseWrapper
from loguru import logger


class CohereWrapper(BaseWrapper):
    name = "cohere"

    API_URL = "https://api.cohere.com/v2/chat"
    MODEL = "command-r"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("cohere", "")
        if not api_key:
            logger.warning("[cohere] No API key configured.")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[cohere] {resp.status_code}: {resp.text[:200]}")
                    return None
                data = resp.json()
                return data["message"]["content"][0]["text"]
        except Exception as e:
            logger.error(f"[cohere] send() failed: {e}")
            return None
