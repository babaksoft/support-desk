"""Bound question generation with immediate admission and a deadline."""

import asyncio

from pydantic import BaseModel, ConfigDict, Field

from support_desk.domain import AnswerDraft, AnswerGenerator


class QuestionRequest(BaseModel):
    """Request a product answer.

    Attributes:
        question:
            Operator-authored product question.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    question: str = Field(
        min_length=1,
        max_length=2048,
        description="Product question to draft an answer for.",
    )


class GenerationBusy(Exception):
    """Signal that the single generation slot is occupied."""


class GenerationFailed(Exception):
    """Signal an unavailable or invalid generation result."""


class GenerationTimedOut(Exception):
    """Signal that generation exceeded its deadline."""


class AnswerQuestion:
    """Generate one answer at a time within a deadline."""

    def __init__(self, generator: AnswerGenerator, timeout_seconds: float = 45) -> None:
        """Set generation dependencies and deadline.

        Args:
            generator:
                Evidence-based generation capability.
            timeout_seconds:
                Maximum elapsed generation time.
        """

        self._generator = generator
        self._timeout_seconds = timeout_seconds
        self._busy = False

    async def execute(self, request: QuestionRequest) -> AnswerDraft:
        """Admit and execute a bounded generation request.

        Args:
            request:
                Validated product question.

        Returns:
            Unreviewed answer draft.

        Raises:
            GenerationBusy:
                Another request occupies the generation slot.
            GenerationTimedOut:
                Generation exceeds the deadline.
            GenerationFailed:
                Generation fails or produces invalid output.
        """

        if self._busy:
            raise GenerationBusy

        self._busy = True
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await self._generator.generate(request.question)
        except TimeoutError as exc:
            raise GenerationTimedOut from exc
        except Exception as exc:
            raise GenerationFailed from exc
        finally:
            self._busy = False
