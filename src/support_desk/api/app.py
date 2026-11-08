"""Expose the bounded product-question use case over HTTP."""

from functools import partial

from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from support_desk.application import (
    AnswerQuestion,
    GenerationBusy,
    GenerationFailed,
    GenerationTimedOut,
    QuestionRequest,
)
from support_desk.domain import AnswerDraft


def create_app(service: AnswerQuestion | None = None) -> FastAPI:
    """Construct HTTP routes around a configured application service.

    Args:
        service:
            Configured question-answer use case, if available.

    Returns:
        FastAPI application with health and question routes.
    """

    app = FastAPI(title="Support Desk", version="0.1.0")
    app.add_middleware(_BodyLimit)

    routes = _QuestionRoutes(service)
    app.add_api_route("/health/live", _live, methods=["GET"], name="live")
    app.add_api_route("/health/ready", routes._ready, methods=["GET"], name="ready")
    app.add_api_route(
        "/questions",
        routes._answer,
        methods=["POST"],
        response_model=AnswerDraft,
        name="answer",
    )
    return app


async def _live() -> dict[str, str]:
    """Report that the HTTP process is alive.

    Returns:
        Process liveness status.
    """

    return {"status": "alive"}


class _QuestionRoutes:
    """Bind HTTP handlers to one application service."""

    def __init__(self, service: AnswerQuestion | None) -> None:
        """Set the question-answer dependency for these routes.

        Args:
            service:
                Configured question-answer use case, if available.
        """

        self._service = service

    async def _ready(self) -> dict[str, str]:
        """Report local configuration readiness.

        Returns:
            Local readiness status.

        Raises:
            HTTPException:
                Generation dependencies are unconfigured.
        """

        if self._service is None:
            raise HTTPException(503, "Generation is not configured.")

        return {"status": "ready"}

    async def _answer(self, request: QuestionRequest) -> AnswerDraft:
        """Draft a product answer for operator review.

        Args:
            request:
                Validated operator question.

        Returns:
            Unreviewed answer and source references.

        Raises:
            HTTPException:
                Generation is unconfigured, busy, timed out, or failed.
        """

        if self._service is None:
            raise HTTPException(503, "Generation is not configured.")

        try:
            return await self._service.execute(request)
        except GenerationBusy as exc:
            raise HTTPException(
                429,
                "Generation is busy; please try again later.",
                headers={"Retry-After": "5"},
            ) from exc
        except GenerationTimedOut as exc:
            raise HTTPException(
                504, "Generation timed out; please retry explicitly."
            ) from exc
        except GenerationFailed as exc:
            raise HTTPException(
                502, "Generation failed; please retry explicitly."
            ) from exc


class _BodyLimit:
    """Bound HTTP request bodies before JSON parsing."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the HTTP application.

        Args:
            app:
                Inner ASGI application.
        """

        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Buffer at most 16 KiB before dispatching an HTTP request.

        Args:
            scope:
                Connection metadata.
            receive:
                Incoming message stream.
            send:
                Outgoing response stream.
        """

        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > 16384:
                await JSONResponse(
                    {"detail": "Request body exceeds 16 KiB."}, status_code=413
                )(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        await self._app(scope, partial(_buffered_receive, bytes(body)), send)


async def _buffered_receive(body: bytes) -> Message:
    """Return the bounded request body.

    Args:
        body:
            Buffered HTTP request bytes.

    Returns:
        Complete HTTP request message.
    """

    return {"type": "http.request", "body": body, "more_body": False}
