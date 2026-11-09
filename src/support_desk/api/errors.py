"""Translate API failures into stable HTTP responses."""

from collections.abc import Mapping

from starlette.requests import Request
from starlette.responses import JSONResponse

from support_desk.api.schemas import ErrorResponse


class ApiError(Exception):
    """Describe a safe error returned by the HTTP adapter.

    Attributes:
        status_code:
            HTTP status associated with the failure.
        code:
            Stable machine-readable failure code.
        message:
            Safe operator-facing failure explanation.
        headers:
            Additional HTTP response headers.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Set the safe HTTP error details.

        Args:
            status_code:
                HTTP status associated with the failure.
            code:
                Stable machine-readable failure code.
            message:
                Safe operator-facing failure explanation.
            headers:
                Additional HTTP response headers.
        """

        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Serialize a safe API error.

    Args:
        request:
            Current HTTP request.
        exc:
            Error raised by an API route or dependency.

    Returns:
        JSON response containing the stable error contract.

    Raises:
        TypeError:
            The registered handler receives an unexpected exception type.
    """

    del request
    if not isinstance(exc, ApiError):
        raise TypeError("API error handler received an unexpected exception.")

    content = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=content.model_dump(mode="json"),
        headers=exc.headers,
    )
