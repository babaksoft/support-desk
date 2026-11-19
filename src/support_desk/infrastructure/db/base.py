"""Define shared SQLAlchemy mapping metadata."""

from sqlalchemy.orm import DeclarativeBase


class DbBase(DeclarativeBase):
    """Provide metadata for application-owned database mappings."""
