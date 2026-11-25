"""Construct asynchronous PostgreSQL persistence resources."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_database_engine(database_url: str) -> AsyncEngine:
    """Create the application-owned asynchronous database engine.

    Args:
        database_url:
            SQLAlchemy PostgreSQL URL using the psycopg driver.

    Returns:
        Asynchronous SQLAlchemy engine.

    Raises:
        ValueError:
            The URL does not select PostgreSQL with psycopg.
    """

    if not database_url.startswith("postgresql+psycopg://"):
        raise ValueError("Database URL must use PostgreSQL with psycopg.")
    return create_async_engine(database_url, pool_pre_ping=True)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create independent asynchronous sessions for repository operations.

    Args:
        engine:
            Application-owned asynchronous database engine.

    Returns:
        Typed asynchronous session factory.
    """

    return async_sessionmaker(engine, expire_on_commit=False)
