import httpx
from .base import BaseWrapper
from loguru import logger


class LeptonWrapper(BaseWrapper):
    name = "lepton"

    API_URL = "https://llama3-1-8b.lepton.run/api/v1/chat/completions"
    MODEL = "llama3-1-8b"

    async def send(self, prompt: str) -> str | None:
        from config import API_KEYS
        api_key = API_KEYS.get("lepton", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {"model": self.MODEL, "messages": [{"role": "user", "content": prompt}]}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(self.API_URL, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error(f"[lepton] {resp.status_code}: {resp.text[:200]}")
                    return None
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[lepton] send() failed: {e}")
            return None
