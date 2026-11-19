"""Map generation attempts and their evidence to PostgreSQL."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from support_desk.infrastructure.db.base import DbBase
from support_desk.infrastructure.db.models.interaction import DbInteraction


class DbGenerationAttempt(DbBase):
    """Map one model generation attempt and its safe terminal outcome.

    Attributes:
        id:
            Stable generation-attempt identity.
        interaction_id:
            Interaction receiving this attempt.
        submission_id:
            Client idempotency key.
        retry_of_attempt_id:
            Failed attempt explicitly retried by this attempt.
        model_id:
            Configured model provenance.
        outcome:
            Current attempt outcome.
        answer_status:
            Evidence sufficiency result for a successful draft.
        answer:
            Successful unreviewed guidance.
        review_status:
            Review state for a successful draft.
        started_at:
            Time the attempt was durably admitted.
        finished_at:
            Time a terminal outcome was stored.
        interaction:
            Interaction receiving this attempt.
        evidence:
            Versioned evidence attached to a successful draft.
    """

    __tablename__ = "generation_attempt"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('started', 'succeeded', 'failed', 'timed_out', 'cancelled')",
            name="ck_generation_attempt_outcome",
        ),
        CheckConstraint(
            "(outcome = 'started' AND finished_at IS NULL) OR "
            "(outcome <> 'started' AND finished_at IS NOT NULL)",
            name="ck_generation_attempt_finished_at",
        ),
        CheckConstraint(
            "(outcome = 'succeeded' AND answer_status IS NOT NULL "
            "AND answer IS NOT NULL AND review_status = 'unreviewed') OR "
            "(outcome <> 'succeeded' AND answer_status IS NULL "
            "AND answer IS NULL AND review_status IS NULL)",
            name="ck_generation_attempt_result",
        ),
        CheckConstraint(
            "answer_status IS NULL OR "
            "answer_status IN ('answered', 'insufficient_evidence')",
            name="ck_generation_attempt_answer_status",
        ),
        UniqueConstraint("submission_id", name="uq_generation_attempt_submission_id"),
        UniqueConstraint(
            "retry_of_attempt_id", name="uq_generation_attempt_retry_of_attempt_id"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        comment="Stable generation-attempt identity.",
    )
    interaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_interaction.id", ondelete="CASCADE"),
        index=True,
        comment="Interaction receiving this generation attempt.",
    )
    submission_id: Mapped[UUID] = mapped_column(
        Uuid,
        comment="Client-provided attempt idempotency key.",
    )
    retry_of_attempt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("generation_attempt.id", ondelete="RESTRICT"),
        comment="Failed generation attempt explicitly retried by this attempt.",
    )
    model_id: Mapped[str] = mapped_column(
        String(256),
        comment="Configured model identifier used for generation.",
    )
    outcome: Mapped[str] = mapped_column(
        String(32),
        comment="Durable generation-attempt outcome.",
    )
    answer_status: Mapped[str | None] = mapped_column(
        String(32),
        comment="Evidence sufficiency result for a successful draft.",
    )
    answer: Mapped[str | None] = mapped_column(
        String(4096),
        comment="Successful unreviewed guidance or evidence-gap explanation.",
    )
    review_status: Mapped[str | None] = mapped_column(
        String(32),
        comment="Operator-review state for a successful draft.",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="Time the attempt was durably admitted.",
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="Time the terminal attempt outcome was stored.",
    )

    interaction: Mapped[DbInteraction] = relationship(
        back_populates="attempts",
        doc="Interaction receiving this generation attempt.",
    )
    evidence: Mapped[list["DbAttemptEvidence"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        doc="Versioned evidence attached to the successful draft.",
    )


class DbAttemptEvidence(DbBase):
    """Map one versioned evidence reference used by a successful attempt.

    Attributes:
        attempt_id:
            Successful generation attempt using the evidence.
        source_id:
            Stable authored source identity.
        source_version:
            Authored source revision.
        attempt:
            Successful attempt using the evidence.
    """

    __tablename__ = "generation_attempt_evidence"

    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("generation_attempt.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Successful generation attempt using the evidence.",
    )
    source_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        comment="Stable authored source identity.",
    )
    source_version: Mapped[str] = mapped_column(
        String(16),
        comment="Authored source revision.",
    )

    attempt: Mapped[DbGenerationAttempt] = relationship(
        back_populates="evidence",
        doc="Successful attempt using the evidence.",
    )
