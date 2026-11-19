"""Verify the reviewed PostgreSQL migration baseline."""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def test_upgrades_and_downgrades_persistence_baseline(database_url: str) -> None:
    """Apply, inspect, revert, and reapply the complete migration history.

    Args:
        database_url:
            Disposable PostgreSQL connection URL.
    """

    config = Config("alembic.ini")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        command.check(config)
        engine = create_engine(database_url)
        try:
            tables = set(inspect(engine).get_table_names())
            assert {
                "alembic_version",
                "support_interaction",
                "generation_attempt",
                "generation_attempt_evidence",
            } <= tables
        finally:
            engine.dispose()

        command.downgrade(config, "base")
        engine = create_engine(database_url)
        try:
            assert set(inspect(engine).get_table_names()) == {"alembic_version"}
        finally:
            engine.dispose()
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
