"""Async Asterisk Manager Interface client using httpx."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from lxml import etree

from .config import Settings


class AsteriskManagerClient:
    """Async context manager for Asterisk Manager HTTP requests.

    Handles login/logoff lifecycle and provides methods for common AMI actions.
    """

    def __init__(self, settings: Settings):
        self.url = settings.manager_url
        self.username = settings.manager_username
        self.secret = settings.manager_secret
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsteriskManagerClient":
        self._client = httpx.AsyncClient(timeout=5.0)
        # Login to Asterisk Manager
        response = await self._client.get(
            self.url,
            params={
                "Action": "Login",
                "Username": self.username,
                "Secret": self.secret,
            },
        )
        response.raise_for_status()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            try:
                await self._client.get(self.url, params={"Action": "Logoff"})
            finally:
                await self._client.aclose()

    async def execute(self, action: str, **params) -> etree._Element:
        """Execute an Asterisk Manager action and return parsed XML."""
        if self._client is None:
            raise RuntimeError("Client not initialized - use async context manager")

        response = await self._client.get(
            self.url,
            params={"Action": action, **params},
        )
        response.raise_for_status()
        return etree.fromstring(response.content)

    async def get_parked_calls(self) -> list[tuple[str, str]]:
        """Get list of parked calls as (extension, name) tuples."""
        doc = await self.execute("ParkedCalls")
        calls = []
        for elem in doc.findall('response/generic[@event="ParkedCall"]'):
            extension = elem.get("exten", "")
            name = elem.get("calleridname") or elem.get("calleridnum") or ""
            calls.append((extension, name))
        return sorted(calls, key=lambda c: c[0])

    async def get_voicemail_users(self) -> list[tuple[str, str]]:
        """Get list of voicemail users as (mailbox, fullname) tuples."""
        doc = await self.execute("VoicemailUsersList")
        entries = []
        for elem in doc.findall('response/generic[@event="VoicemailUserEntry"]'):
            mailbox = elem.get("voicemailbox", "")
            name = elem.get("fullname", "")
            entries.append((mailbox, name))
        return sorted(entries, key=lambda e: e[1])

    async def get_sip_peer_by_device(self, device_name: str) -> dict | None:
        """Get SIP peer info for a device, including RTP statistics."""
        doc = await self.execute("SIPPeers")
        elem = doc.find(f'response/generic[@event="SIPPeer"][@devicename="{device_name}"]')

        if elem is None:
            return None

        peer_name = elem.get("name")
        if peer_name is None:
            return None

        peer_doc = await self.execute("SIPShowPeer", Peer=peer_name)
        peer_elem = peer_doc.find("response/generic[@name]")

        if peer_elem is None:
            return None

        return {
            "ip_address": peer_elem.get("ipaddress"),
            "status": peer_elem.get("status"),
            "rtp_rx_stat": peer_elem.get("rtprxstat"),
            "rtp_tx_stat": peer_elem.get("rtptxstat"),
        }


@asynccontextmanager
async def get_manager_client(settings: Settings) -> AsyncIterator[AsteriskManagerClient]:
    """Get an Asterisk Manager client as an async context manager."""
    client = AsteriskManagerClient(settings)
    async with client:
        yield client
