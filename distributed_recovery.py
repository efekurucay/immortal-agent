"""
distributed_recovery.py — Distributed recovery beacon.

When the agent detects that ALL local wrappers are dead, it can
broadcast a recovery request to a remote peer (another immortal-agent
instance) and ask it to generate + return new wrapper code.

Protocol:
  POST /recover  {"service_hint": "..."}  →  {"code": "...", "name": "..."}

The peer must be running rest_api.py with the /recover endpoint enabled.
This module also exposes the /recover handler for inbound requests.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from loguru import logger

try:
    import httpx
except ImportError:
    raise ImportError("pip install httpx")

from codegen import generate_wrapper_code, install_wrapper
from wrapper_pool import WrapperPool


class DistributedRecovery:
    """Contacts peer agents to obtain new wrapper code."""

    def __init__(self, peers: list[str] | None = None):
        """
        peers: list of peer base URLs, e.g. ["http://peer1:8000", "http://peer2:8000"]
        """
        self.peers = peers or []

    async def request_wrapper_from_peer(
        self,
        pool: WrapperPool,
        service_hint: str = "any",
    ) -> bool:
        """Ask peers for a new wrapper. Returns True if one was installed."""
        if not self.peers:
            logger.debug("[dist-recovery] No peers configured.")
            return False

        for peer_url in self.peers:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.post(
                        f"{peer_url}/recover",
                        json={"service_hint": service_hint},
                    )
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    code = data.get("code", "")
                    name = data.get("name", "recovered")
                    if not code:
                        continue

                    wrapper_class = await install_wrapper(code, name)
                    if wrapper_class:
                        pool.add_wrapper(wrapper_class)
                        logger.success(
                            f"[dist-recovery] Installed wrapper '{name}' from peer {peer_url}"
                        )
                        return True
            except Exception as exc:
                logger.warning(f"[dist-recovery] Peer {peer_url} failed: {exc}")

        return False

    async def share_wrapper_code(
        self,
        working_wrapper,
        service_name: str,
        hints: str,
    ) -> Optional[str]:
        """Generate code locally and return it for sharing (used by /recover endpoint)."""
        return await generate_wrapper_code(working_wrapper, service_name, hints)
