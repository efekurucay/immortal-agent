"""Scaleway Generative APIs — free tier, OpenAI-compatible."""
from __future__ import annotations
import httpx
from wrappers.base import BaseWrapper
from config import WRAPPER_TIMEOUT

class ScalewayWrapper(BaseWrapper):
    name = "scaleway"
    _url = "https://api.scaleway.ai/v1/chat/completions"
    _model = "llama-3.1-8b-instruct"

    async def send(self, prompt: str) -> str | None:
        import os
        key = os.getenv("SCALEWAY_API_KEY", "")
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
