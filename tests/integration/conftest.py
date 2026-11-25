"""Configure disposable PostgreSQL integration-test state."""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config


@pytest.fixture
def database_url() -> str:
    """Return the explicitly configured disposable PostgreSQL URL.

    Returns:
        SQLAlchemy PostgreSQL URL for integration tests.
    """

    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    return url


@pytest.fixture
def migrated_database(database_url: str) -> Iterator[str]:
    """Rebuild and migrate the disposable integration database.

    Args:
        database_url:
            Disposable PostgreSQL connection URL.

    Yields:
        Migrated database URL.
    """

    config = Config("alembic.ini")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        yield database_url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
