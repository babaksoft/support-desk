"""Bound question generation with immediate admission and a deadline."""

import asyncio
import math

from support_desk.application.errors import (
    GenerationBusy,
    GenerationFailed,
    GenerationTimedOut,
)
from support_desk.domain import AnswerDraft, AnswerGenerator

MAX_QUESTION_LENGTH = 2048


class AnswerService:
    """Generate one answer at a time within a deadline."""

    def __init__(self, generator: AnswerGenerator, timeout_seconds: float = 45) -> None:
        """Set generation dependencies and deadline.

        Args:
            generator:
                Evidence-based generation capability.
            timeout_seconds:
                Maximum elapsed generation time.

        Raises:
            ValueError:
                The generation deadline is not positive and finite.
        """

        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Generation timeout must be positive and finite.")

        self._generator = generator
        self._timeout_seconds = timeout_seconds
        self._busy = False

    async def execute(self, question: str) -> AnswerDraft:
        """Admit and execute a bounded generation request.

        Args:
            question:
                Product question that needs validation.

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
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(
                f"Question cannot be longer than {MAX_QUESTION_LENGTH} characters."
            )

        self._busy = True
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await self._generator.generate(question)
        except TimeoutError as exc:
            raise GenerationTimedOut from exc
        except Exception as exc:
            raise GenerationFailed from exc
        finally:
            self._busy = False
