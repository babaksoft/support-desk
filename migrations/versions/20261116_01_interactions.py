"""Create support interactions and generation attempts.

Revision ID: 20261116_01
Revises:
Create Date: 2026-11-16 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261116_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Slice 1.4 persistence baseline."""

    op.create_table(
        "support_interaction",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Stable support-interaction identity.",
        ),
        sa.Column(
            "operator_subject",
            sa.String(length=256),
            nullable=False,
            comment="Authenticated operator identity that owns the interaction.",
        ),
        sa.Column(
            "question",
            sa.String(length=2048),
            nullable=False,
            comment="Operator-authored product question.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Time the interaction was accepted.",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Time the interaction becomes eligible for deletion.",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_support_interaction_expires_at"),
        "support_interaction",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_interaction_operator_subject"),
        "support_interaction",
        ["operator_subject"],
        unique=False,
    )
    op.create_table(
        "generation_attempt",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Stable generation-attempt identity.",
        ),
        sa.Column(
            "interaction_id",
            sa.Uuid(),
            nullable=False,
            comment="Interaction receiving this generation attempt.",
        ),
        sa.Column(
            "submission_id",
            sa.Uuid(),
            nullable=False,
            comment="Client-provided attempt idempotency key.",
        ),
        sa.Column(
            "retry_of_attempt_id",
            sa.Uuid(),
            nullable=True,
            comment="Failed generation attempt explicitly retried by this attempt.",
        ),
        sa.Column(
            "model_id",
            sa.String(length=256),
            nullable=False,
            comment="Configured model identifier used for generation.",
        ),
        sa.Column(
            "outcome",
            sa.String(length=32),
            nullable=False,
            comment="Durable generation-attempt outcome.",
        ),
        sa.Column(
            "answer_status",
            sa.String(length=32),
            nullable=True,
            comment="Evidence sufficiency result for a successful draft.",
        ),
        sa.Column(
            "answer",
            sa.String(length=4096),
            nullable=True,
            comment="Successful unreviewed guidance or evidence-gap explanation.",
        ),
        sa.Column(
            "review_status",
            sa.String(length=32),
            nullable=True,
            comment="Operator-review state for a successful draft.",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Time the attempt was durably admitted.",
        ),
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Time the terminal attempt outcome was stored.",
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"], ["support_interaction.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "answer_status IS NULL OR "
            "answer_status IN ('answered', 'insufficient_evidence')",
            name="ck_generation_attempt_answer_status",
        ),
        sa.CheckConstraint(
            "(outcome = 'started' AND finished_at IS NULL) OR "
            "(outcome <> 'started' AND finished_at IS NOT NULL)",
            name="ck_generation_attempt_finished_at",
        ),
        sa.CheckConstraint(
            "outcome IN ('started', 'succeeded', 'failed', 'timed_out', 'cancelled')",
            name="ck_generation_attempt_outcome",
        ),
        sa.CheckConstraint(
            "(outcome = 'succeeded' AND answer_status IS NOT NULL "
            "AND answer IS NOT NULL AND review_status = 'unreviewed') OR "
            "(outcome <> 'succeeded' AND answer_status IS NULL "
            "AND answer IS NULL AND review_status IS NULL)",
            name="ck_generation_attempt_result",
        ),
        sa.ForeignKeyConstraint(
            ["retry_of_attempt_id"],
            ["generation_attempt.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "retry_of_attempt_id",
            name="uq_generation_attempt_retry_of_attempt_id",
        ),
        sa.UniqueConstraint(
            "submission_id", name="uq_generation_attempt_submission_id"
        ),
    )
    op.create_index(
        op.f("ix_generation_attempt_interaction_id"),
        "generation_attempt",
        ["interaction_id"],
        unique=False,
    )
    op.create_table(
        "generation_attempt_evidence",
        sa.Column(
            "attempt_id",
            sa.Uuid(),
            nullable=False,
            comment="Successful generation attempt using the evidence.",
        ),
        sa.Column(
            "source_id",
            sa.String(length=32),
            nullable=False,
            comment="Stable authored source identity.",
        ),
        sa.Column(
            "source_version",
            sa.String(length=16),
            nullable=False,
            comment="Authored source revision.",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["generation_attempt.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("attempt_id", "source_id"),
    )


def downgrade() -> None:
    """Remove the Slice 1.4 persistence baseline."""

    op.drop_table("generation_attempt_evidence")
    op.drop_index(
        op.f("ix_generation_attempt_interaction_id"),
        table_name="generation_attempt",
    )
    op.drop_table("generation_attempt")
    op.drop_index(
        op.f("ix_support_interaction_operator_subject"),
        table_name="support_interaction",
    )
    op.drop_index(
        op.f("ix_support_interaction_expires_at"),
        table_name="support_interaction",
    )
    op.drop_table("support_interaction")
