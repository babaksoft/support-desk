"""Verify the public deployment smoke checks."""

from collections.abc import Iterator
from io import BytesIO
from urllib.error import URLError
from urllib.request import Request

import pytest

from support_desk.composition import deployment_smoke
from support_desk.composition.deployment_smoke import (
    DeploymentSmokeFailure,
    verify_deployment,
)


class _Response:
    """Provide a context-managed bounded HTTP response.

    Attributes:
        body:
            Response body returned by the fake endpoint.
    """

    def __init__(self, body: bytes) -> None:
        """Initialize the fake response.

        Args:
            body:
                Response body returned by reads.
        """

        self.body = body
        self._stream = BytesIO(body)

    def __enter__(self) -> "_Response":
        """Enter the fake response context.

        Returns:
            Current fake response.
        """

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> None:
        """Close the fake response stream.

        Args:
            exception_type:
                Exception type raised in the context.
            exception:
                Exception raised in the context.
            traceback:
                Traceback raised in the context.
        """

        del exception_type, exception, traceback
        self._stream.close()

    def read(self, size: int) -> bytes:
        """Read at most the requested response bytes.

        Args:
            size:
                Maximum number of bytes to return.

        Returns:
            Requested response bytes.
        """

        return self._stream.read(size)


def test_accepts_healthy_https_application(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accept a healthy Streamlit endpoint and application root.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    requested_urls: list[str] = []
    responses: Iterator[_Response] = iter([_Response(b"ok"), _Response(b"app")])

    def open_url(request: Request, timeout: float) -> _Response:
        """Return the next deterministic response.

        Args:
            request:
                Standard-library URL request.
            timeout:
                Configured request timeout.

        Returns:
            Next fake response.
        """

        requested_urls.append(request.full_url)
        assert timeout == deployment_smoke.REQUEST_TIMEOUT_SECONDS
        return next(responses)

    monkeypatch.setattr(deployment_smoke, "urlopen", open_url)

    verify_deployment("https://example.cloudfront.net")

    assert requested_urls == [
        "https://example.cloudfront.net/_stcore/health",
        "https://example.cloudfront.net/",
    ]


@pytest.mark.parametrize(
    "url",
    [
        "http://example.cloudfront.net",
        "example.cloudfront.net",
        "https://operator:secret@example.cloudfront.net",
    ],
)
def test_rejects_unsafe_deployment_url(url: str) -> None:
    """Reject deployment URLs that are not credential-free HTTPS.

    Args:
        url:
            Unsafe deployment URL.
    """

    with pytest.raises(DeploymentSmokeFailure):
        verify_deployment(url)


def test_rejects_unhealthy_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a reachable endpoint with an unhealthy body.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    monkeypatch.setattr(
        deployment_smoke,
        "urlopen",
        lambda request, timeout: _Response(b"not healthy"),
    )

    with pytest.raises(DeploymentSmokeFailure, match="not healthy"):
        verify_deployment("https://example.cloudfront.net")


def test_hides_transport_details(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace transport details with a bounded smoke failure.

    Args:
        monkeypatch:
            Pytest attribute patching helper.
    """

    def fail_open(request: Request, timeout: float) -> _Response:
        """Raise a private transport failure.

        Args:
            request:
                Standard-library URL request.
            timeout:
                Configured request timeout.

        Raises:
            URLError:
                The public endpoint is unreachable.
        """

        del request, timeout
        raise URLError("private transport detail")

    monkeypatch.setattr(deployment_smoke, "urlopen", fail_open)

    with pytest.raises(DeploymentSmokeFailure, match="Request failed") as failure:
        verify_deployment("https://example.cloudfront.net")

    assert "private transport detail" not in str(failure.value)
