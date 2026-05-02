"""AI/ML API — free tier, OpenAI-compatible endpoint."""
from __future__ import annotations
import httpx
from wrappers.base import BaseWrapper
from config import WRAPPER_TIMEOUT

class AimlApiWrapper(BaseWrapper):
    name = "aimlapi"
    _url = "https://api.aimlapi.com/v1/chat/completions"
    _model = "mistralai/Mistral-7B-Instruct-v0.2"

    async def send(self, prompt: str) -> str | None:
        import os
        key = os.getenv("AIMLAPI_KEY", "")
        if not key:
            return None
        try:
            async with httpx.AsyncClient(timeout=WRAPPER_TIMEOUT) as client:
                r = await client.post(
                    self._url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": self._model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 256},
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
