"""Manage resources owned by the running API process."""

from collections.abc import AsyncGenerator, Iterable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

ManagedResource = AbstractAsyncContextManager[object]


class ApiLifespan:
    """Enter and release configured asynchronous resources."""

    def __init__(self, resources: Iterable[ManagedResource] = ()) -> None:
        """Store resources in their startup order.

        Args:
            resources:
                Asynchronous resources owned by the API process.
        """

        self._resources = tuple(resources)

    @asynccontextmanager
    async def __call__(self, app: FastAPI) -> AsyncGenerator[None]:
        """Enter resources and release them in reverse order.

        Args:
            app:
                Running FastAPI application.

        Yields:
            Control to the running application.
        """

        del app
        async with AsyncExitStack() as stack:
            for resource in self._resources:
                await stack.enter_async_context(resource)
            yield
