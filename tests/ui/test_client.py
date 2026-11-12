"""Verify the typed FastAPI question client."""

from collections.abc import Callable

import httpx
import pytest

from support_desk.domain import AnswerDraft
from support_desk.ui import (
    ApiQuestionFailure,
    HttpQuestionClient,
    InvalidApiResponse,
    QuestionApiUnavailable,
)


def test_returns_typed_draft(
    monkeypatch: pytest.MonkeyPatch, draft: AnswerDraft
) -> None:
    """Parse a successful API response into the domain value.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
        draft:
            Valid authored draft fixture.
    """

    post = _stub_post(
        monkeypatch,
        httpx.Response(200, json=draft.model_dump(mode="json")),
    )

    result = HttpQuestionClient("http://api:8000/").ask("How many boards?")

    assert result == draft
    assert post == [
        (
            "http://api:8000/questions",
            {"question": "How many boards?"},
            {},
            50.0,
        )
    ]


def test_sends_operator_access_token(
    monkeypatch: pytest.MonkeyPatch, draft: AnswerDraft
) -> None:
    """Send the configured operator token as bearer authorization.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
        draft:
            Valid authored draft fixture.
    """

    post = _stub_post(
        monkeypatch,
        httpx.Response(200, json=draft.model_dump(mode="json")),
    )

    HttpQuestionClient(
        "http://api:8000",
        access_token="synthetic-token",
    ).ask("How many boards?")

    assert post[0][2] == {"Authorization": "Bearer synthetic-token"}


def test_reports_safe_api_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose only the API's declared safe failure fields.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    _stub_post(
        monkeypatch,
        httpx.Response(
            503,
            json={
                "code": "generation_unavailable",
                "message": "Generation is not configured.",
            },
        ),
    )

    with pytest.raises(ApiQuestionFailure) as failure:
        HttpQuestionClient("http://api:8000").ask("How many boards?")

    assert failure.value.code == "generation_unavailable"
    assert failure.value.message == "Generation is not configured."


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, json={"answer": "missing fields"}),
        httpx.Response(502, text="provider detail"),
    ],
)
def test_rejects_invalid_api_response(
    monkeypatch: pytest.MonkeyPatch, response: httpx.Response
) -> None:
    """Reject success and failure payloads outside the API contract.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
        response:
            Malformed API response.
    """

    _stub_post(monkeypatch, response)

    with pytest.raises(InvalidApiResponse):
        HttpQuestionClient("http://api:8000").ask("How many boards?")


def test_reports_unavailable_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Map HTTP transport details to a stable UI failure.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    monkeypatch.setattr(httpx, "post", _fail_post)

    with pytest.raises(QuestionApiUnavailable):
        HttpQuestionClient("http://api:8000").ask("How many boards?")


def _stub_post(
    monkeypatch: pytest.MonkeyPatch, response: httpx.Response
) -> list[tuple[str, object, dict[str, str], float]]:
    """Replace the HTTP post call with a recorded response.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
        response:
            Response returned by the stub.

    Returns:
        Mutable record of calls made through the stub.
    """

    calls: list[tuple[str, object, dict[str, str], float]] = []

    def post(
        url: str,
        *,
        json: object,
        headers: dict[str, str],
        timeout: float,
    ) -> httpx.Response:
        """Record one HTTP request and return the configured response.

        Args:
            url:
                Target question URL.
            json:
                Serialized question request.
            headers:
                HTTP request headers.
            timeout:
                Overall HTTP deadline.

        Returns:
            Configured HTTP response.
        """

        calls.append((url, json, headers, timeout))
        return response

    typed_post: Callable[..., httpx.Response] = post
    monkeypatch.setattr(httpx, "post", typed_post)
    return calls


def _fail_post(
    url: str,
    *,
    json: object,
    headers: dict[str, str],
    timeout: float,
) -> httpx.Response:
    """Simulate a failed API connection.

    Args:
        url:
            Target question URL.
        json:
            Serialized question request.
        headers:
            HTTP request headers.
        timeout:
            Overall HTTP deadline.

    Raises:
        httpx.ConnectError:
            The API connection fails.
    """

    del url, json, headers, timeout
    raise httpx.ConnectError("private transport detail")
