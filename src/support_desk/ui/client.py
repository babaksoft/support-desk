"""Call the question API through typed request and response values."""

from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from support_desk.api.schemas import AnswerRequest
from support_desk.domain import AnswerDraft


class QuestionApi(Protocol):
    """Request an answer draft from the application API."""

    def ask(self, question: str) -> AnswerDraft:
        """Submit an operator question.

        Args:
            question:
                Valid operator-authored product question.

        Returns:
            Unreviewed answer draft from the API.

        Raises:
            ApiQuestionFailure:
                The API rejected or could not generate the draft.
            QuestionApiUnavailable:
                The API could not be reached before the client deadline.
            InvalidApiResponse:
                The API response violated its declared contract.
        """

        ...


class ApiQuestionFailure(Exception):
    """Report an operator-safe failure returned by the question API.

    Attributes:
        code:
            Stable API failure code.
        message:
            Safe operator-facing explanation.
    """

    def __init__(self, code: str, message: str) -> None:
        """Initialize an API failure.

        Args:
            code:
                Stable API failure code.
            message:
                Safe operator-facing explanation.
        """

        super().__init__(message)
        self.code = code
        self.message = message


class QuestionApiUnavailable(Exception):
    """Report that the question API could not be reached."""


class InvalidApiResponse(Exception):
    """Report that the question API broke its response contract."""


class HttpQuestionClient:
    """Submit questions to FastAPI over bounded HTTP.

    Attributes:
        base_url:
            Root URL of the Support Desk API.
        timeout_seconds:
            Overall HTTP request timeout in seconds.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 50.0) -> None:
        """Initialize the HTTP question client.

        Args:
            base_url:
                Root URL of the Support Desk API.
            timeout_seconds:
                Overall HTTP request timeout in seconds.
        """

        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def ask(self, question: str) -> AnswerDraft:
        """Submit an operator question.

        Args:
            question:
                Valid operator-authored product question.

        Returns:
            Unreviewed answer draft from the API.

        Raises:
            ApiQuestionFailure:
                The API returned a declared safe failure.
            QuestionApiUnavailable:
                The API could not be reached before the client deadline.
            InvalidApiResponse:
                The API response violated its declared contract.
        """

        request = AnswerRequest(question=question)
        try:
            response = httpx.post(
                f"{self.base_url}/questions",
                json=request.model_dump(mode="json"),
                timeout=self.timeout_seconds,
            )
        except httpx.RequestError as exc:
            raise QuestionApiUnavailable from exc

        if response.is_error:
            self._raise_api_failure(response)

        try:
            return AnswerDraft.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise InvalidApiResponse from exc

    @staticmethod
    def _raise_api_failure(response: httpx.Response) -> None:
        """Raise a typed failure from an unsuccessful response.

        Args:
            response:
                Unsuccessful API response.

        Raises:
            ApiQuestionFailure:
                The response contains a declared safe failure.
            InvalidApiResponse:
                The response does not contain a declared safe failure.
        """

        try:
            failure = _ErrorPayload.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise InvalidApiResponse from exc

        raise ApiQuestionFailure(failure.code, failure.message)


class _ErrorPayload(BaseModel):
    """Validate a safe API error response.

    Attributes:
        code:
            Stable machine-readable failure code.
        message:
            Safe operator-facing failure explanation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1, max_length=64, description="Stable failure code.")
    message: str = Field(
        min_length=1,
        max_length=256,
        description="Safe operator-facing failure explanation.",
    )
