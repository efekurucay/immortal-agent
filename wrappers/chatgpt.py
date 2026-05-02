import httpx
import json
from .base import BaseWrapper
from loguru import logger


class ChatGPTWrapper(BaseWrapper):
    name = "chatgpt"

    # Unofficial endpoint used by the web UI
    API_URL = "https://chatgpt.com/backend-api/conversation"

    async def send(self, prompt: str) -> str | None:
        from config import COOKIES
        session_token = COOKIES.get("chatgpt", {}).get(
            "__Secure-next-auth.session-token", ""
        )
        if not session_token:
            logger.warning("[chatgpt] No cookie configured.")
            return None

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Cookie": f"__Secure-next-auth.session-token={session_token}",
            "Accept": "text/event-stream",
        }

        payload = {
            "action": "next",
            "messages": [
                {
                    "id": "msg-001",
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "model": "gpt-4o",
            "parent_message_id": "00000000-0000-0000-0000-000000000000",
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # First get access token via auth session
                auth_resp = await client.get(
                    "https://chatgpt.com/api/auth/session",
                    headers=headers,
                )
                if auth_resp.status_code != 200:
                    logger.error(f"[chatgpt] Auth failed: {auth_resp.status_code}")
                    return None

                access_token = auth_resp.json().get("accessToken", "")
                if not access_token:
                    logger.error("[chatgpt] No access token in session response.")
                    return None

                headers["Authorization"] = f"Bearer {access_token}"

                async with client.stream("POST", self.API_URL, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        logger.error(f"[chatgpt] API error: {resp.status_code}")
                        return None

                    result = ""
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                data = json.loads(line[6:])
                                parts = (
                                    data.get("message", {})
                                    .get("content", {})
                                    .get("parts", [])
                                )
                                if parts:
                                    result = parts[-1]
                            except Exception:
                                continue
                    return result if result else None

        except Exception as e:
            logger.error(f"[chatgpt] send() failed: {e}")
            return None
