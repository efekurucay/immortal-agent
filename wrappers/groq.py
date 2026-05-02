import httpx
from .base import BaseWrapper
from loguru import logger


class GroqWrapper(BaseWrapper):
    name = "groq"

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama3-8b-8192"  # fast and free

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("groq", "")
        if not api_key:
            logger.warning("[groq] No API key configured.")
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
                    logger.error(f"[groq] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[groq] send() failed: {e}")
            return None
