"""Typed evidence and unreviewed answer values."""

from enum import StrEnum
from typing import Literal, Protocol, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceId(StrEnum):
    """Identify an authored Boardlight source."""

    PLANS = "BL-PLANS"
    UPGRADES = "BL-UPGRADES"
    ACCESS = "BL-ACCESS"
    TROUBLESHOOTING = "BL-TROUBLESHOOTING"


class Evidence(BaseModel):
    """Identify a versioned source used by an answer.

    Attributes:
        source_id:
            Stable product source identifier.
        version:
            Source revision.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: SourceId = Field(description="Stable product source identifier.")
    version: Literal["1"] = Field(description="Source revision.")


class AnswerDraft(BaseModel):
    """Represent a generated response awaiting operator review.

    Attributes:
        status:
            Whether available evidence supports an answer.
        answer:
            Draft guidance or explanation of the evidence gap.
        evidence:
            Sources supporting the guidance.
        review_status:
            Required operator-review state.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["answered", "insufficient_evidence"] = Field(
        description="Whether available evidence supports an answer."
    )
    answer: str = Field(
        min_length=1,
        max_length=4096,
        description="Unreviewed guidance or evidence gap.",
    )
    evidence: tuple[Evidence, ...] = Field(
        max_length=4, description="Supporting source revisions."
    )
    review_status: Literal["unreviewed"] = Field(
        description="Required operator-review state."
    )

    @model_validator(mode="after")
    def _validate_evidence(self) -> Self:
        """Require supporting sources for answered questions.

        Returns:
            The validated draft.

        Raises:
            ValueError:
                An answered question has no evidence or repeats a source.
        """

        if self.status == "answered" and not self.evidence:
            raise ValueError("An answer requires evidence.")
        if len(set(self.evidence)) != len(self.evidence):
            raise ValueError("Evidence must be unique.")

        return self


class AnswerGenerator(Protocol):
    """Generate product guidance from bounded evidence."""

    async def generate(self, question: str) -> AnswerDraft:
        """Draft an answer to a product question.

        Args:
            question:
                Operator-authored product question.

        Returns:
            Unreviewed guidance with supporting evidence or an evidence gap.
        """

        ...
