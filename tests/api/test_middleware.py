"""Verify API request-body bounds and stream replay."""

from unittest.mock import AsyncMock

import pytest
from starlette.types import Message, Receive, Scope, Send

from support_desk.api.middleware import BodyLimitMiddleware

HTTP_SCOPE: Scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.4"},
    "http_version": "1.1",
    "method": "POST",
    "scheme": "http",
    "path": "/questions",
    "raw_path": b"/questions",
    "query_string": b"",
    "root_path": "",
    "headers": [],
    "server": ("testserver", 80),
    "client": ("testclient", 50000),
    "state": {},
}


class _ReceiveProbe:
    """Record messages delivered by an ASGI receive stream."""

    def __init__(self) -> None:
        """Initialize the recorded message list."""

        self.messages: list[Message] = []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Read the replayed request and following stream event.

        Args:
            scope:
                Synthetic HTTP connection metadata.
            receive:
                Middleware-provided incoming stream.
            send:
                Outgoing message stream.
        """

        del scope, send
        self.messages.append(await receive())
        self.messages.append(await receive())


@pytest.mark.asyncio
async def test_replays_chunked_body_once_then_resumes_stream() -> None:
    """Combine accepted chunks without repeating the buffered request."""

    incoming: list[Message] = [
        {"type": "http.request", "body": b"hello ", "more_body": True},
        {"type": "http.request", "body": b"world", "more_body": False},
        {"type": "http.disconnect"},
    ]
    receive = AsyncMock(side_effect=incoming)
    send = AsyncMock()
    probe = _ReceiveProbe()

    await BodyLimitMiddleware(probe, max_body_bytes=11)(HTTP_SCOPE, receive, send)

    assert probe.messages == [
        {"type": "http.request", "body": b"hello world", "more_body": False},
        {"type": "http.disconnect"},
    ]
