"""Map durable support interactions to PostgreSQL."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from support_desk.infrastructure.db.base import DbBase

if TYPE_CHECKING:
    from support_desk.infrastructure.db.models.generation_attempt import (
        DbGenerationAttempt,
    )


class DbInteraction(DbBase):
    """Map one durable product-question interaction.

    Attributes:
        id:
            Stable interaction identity.
        operator_subject:
            Authenticated operator that owns the interaction.
        question:
            Original product question.
        created_at:
            Time the interaction was accepted.
        expires_at:
            Time the interaction becomes eligible for deletion.
        attempts:
            Generation attempts associated with the interaction.
    """

    __tablename__ = "support_interaction"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        doc="Stable support-interaction identity.",
    )
    operator_subject: Mapped[str] = mapped_column(
        String(256),
        index=True,
        doc="Authenticated operator identity that owns the interaction.",
    )
    question: Mapped[str] = mapped_column(
        String(2048),
        doc="Operator-authored product question.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        doc="Time the interaction was accepted.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        doc="Time the interaction becomes eligible for deletion.",
    )

    attempts: Mapped[list[DbGenerationAttempt]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
        doc="Generation attempts associated with the interaction.",
    )
