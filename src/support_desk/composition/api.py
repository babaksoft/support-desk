"""Configure the local API process from explicit provider settings."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from openai import AsyncOpenAI

from support_desk.api import create_app
from support_desk.application import AnswerQuestion
from support_desk.infrastructure import AgentsAnswerGenerator


def build_app() -> FastAPI:
    """Build an API with optional, explicitly enabled inference.

    Returns:
        Configured API or health-only API when inference is disabled.
    """

    model = os.environ.get("SUPPORT_DESK_MODEL", "").strip()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if os.environ.get("SUPPORT_DESK_ENABLE_INFERENCE") != "1" or not model or not key:
        return create_app()

    client = AsyncOpenAI(api_key=key, max_retries=0, timeout=40)
    app = create_app(AnswerQuestion(AgentsAnswerGenerator(client, model)))

    app.router.lifespan_context = partial(_lifespan, client)
    return app


@asynccontextmanager
async def _lifespan(client: AsyncOpenAI, app: FastAPI) -> AsyncIterator[None]:
    """Close provider connections when the API shuts down.

    Args:
        client:
            Provider client owned by this API instance.
        app:
            Running API instance.

    Yields:
        Control to the running API.
    """

    async with client:
        yield
