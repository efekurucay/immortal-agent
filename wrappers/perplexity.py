import httpx
import json
from .base import BaseWrapper
from loguru import logger


class PerplexityWrapper(BaseWrapper):
    name = "perplexity"

    BASE_URL = "https://www.perplexity.ai/socket.io/"
    REST_URL = "https://www.perplexity.ai/api/auth/session"

    async def send(self, prompt: str) -> str | None:
        from config import COOKIES
        cookies = COOKIES.get("perplexity", {})
        session_token = cookies.get("__Secure-next-auth.session-token", "")
        pplx_auth = cookies.get("pplx_auth", "")

        if not session_token and not pplx_auth:
            logger.warning("[perplexity] No cookie configured.")
            return None

        cookie_str = "; ".join(
            f"{k}={v}" for k, v in cookies.items() if v
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Cookie": cookie_str,
            "Content-Type": "application/json",
            "Referer": "https://www.perplexity.ai/",
        }

        # Perplexity uses a REST endpoint for quick queries
        payload = {
            "query": prompt,
            "search_focus": "writing",
            "language": "en-US",
        }

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.post(
                    "https://www.perplexity.ai/rest/sse/perplexity_ask",
                    headers=headers,
                    json=payload,
                )

                if resp.status_code != 200:
                    logger.error(f"[perplexity] API error: {resp.status_code}")
                    return None

                result = ""
                for line in resp.text.splitlines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            answer = data.get("answer") or data.get("text") or ""
                            if answer:
                                result = answer
                        except Exception:
                            continue
                return result.strip() if result else None

        except Exception as e:
            logger.error(f"[perplexity] send() failed: {e}")
            return None
