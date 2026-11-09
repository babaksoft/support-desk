"""Apply transport-level request bounds."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from support_desk.api.schemas import ErrorResponse

MAX_REQUEST_BODY_BYTES = 16 * 1024


class BodyLimitMiddleware:
    """Reject HTTP request bodies above the configured byte limit."""

    def __init__(
        self, app: ASGIApp, max_body_bytes: int = MAX_REQUEST_BODY_BYTES
    ) -> None:
        """Wrap an ASGI application with a request-body limit.

        Args:
            app:
                Inner ASGI application.
            max_body_bytes:
                Maximum accepted request body size in bytes.

        Raises:
            ValueError:
                The configured limit is not positive.
        """

        if max_body_bytes <= 0:
            raise ValueError("Request body limit must be positive.")

        self._app = app
        self._max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Buffer and bound an HTTP request before dispatch.

        Args:
            scope:
                Connection metadata.
            receive:
                Incoming message stream.
            send:
                Outgoing message stream.
        """

        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return

            body.extend(message.get("body", b""))
            if len(body) > self._max_body_bytes:
                await self._reject(scope, receive, send)
                return

            if not message.get("more_body", False):
                break

        buffered_receive = BufferedReceive(bytes(body), receive)
        await self._app(scope, buffered_receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Return the request-too-large response.

        Args:
            scope:
                Connection metadata.
            receive:
                Incoming message stream.
            send:
                Outgoing message stream.
        """

        content = ErrorResponse(
            code="request_too_large",
            message=f"Request body exceeds {self._max_body_bytes} bytes.",
        )
        await JSONResponse(content=content.model_dump(mode="json"), status_code=413)(
            scope, receive, send
        )


class BufferedReceive:
    """Replay one buffered request and then resume the original stream."""

    def __init__(self, body: bytes, receive: Receive) -> None:
        """Store the buffered body and original receive callable.

        Args:
            body:
                Complete bounded request body.
            receive:
                Original incoming message stream.
        """

        self._body = body
        self._receive = receive
        self._delivered = False

    async def __call__(self) -> Message:
        """Deliver the buffered body once and then resume the original stream.

        Returns:
            Next ASGI request or disconnect message.
        """

        if not self._delivered:
            self._delivered = True
            return {"type": "http.request", "body": self._body, "more_body": False}

        return await self._receive()
