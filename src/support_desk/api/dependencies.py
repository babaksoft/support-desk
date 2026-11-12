"""Resolve configured application services for HTTP handlers."""

from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from support_desk.api.errors import ApiError
from support_desk.application import (
    AnswerService,
    OperatorAccessDenied,
    OperatorAuthorizer,
)
from support_desk.domain import (
    AccessTokenAuthenticator,
    AccessTokenRejected,
    AuthenticatedActor,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def require_generation(request: Request) -> AnswerService:
    """Resolve the configured answer generation service from the application.

    Args:
        request:
            Current HTTP request.

    Returns:
        Configured answer generation service.

    Raises:
        ApiError:
            Generation is unavailable in this process.
    """

    service = cast(AnswerService | None, request.app.state.generation_service)
    if service is None:
        raise ApiError(
            status_code=503,
            code="generation_unavailable",
            message="Generation is not configured.",
        )

    return service


def require_authentication(request: Request) -> AccessTokenAuthenticator:
    """Resolve the configured access-token authenticator.

    Args:
        request:
            Current HTTP request.

    Returns:
        Configured access-token authenticator.

    Raises:
        ApiError:
            Authentication is unavailable in this process.
    """

    authenticator = cast(
        AccessTokenAuthenticator | None,
        request.app.state.access_token_authenticator,
    )
    if authenticator is None:
        raise ApiError(
            status_code=503,
            code="authentication_unavailable",
            message="Authentication is not configured.",
        )

    return authenticator


async def require_operator(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
) -> AuthenticatedActor:
    """Authenticate and authorize an operator request.

    Args:
        request:
            Current HTTP request.
        credentials:
            Parsed bearer credentials, if supplied.

    Returns:
        Authenticated actor authorized as an operator.

    Raises:
        ApiError:
            Authentication is unavailable or the request lacks valid operator access.
    """

    authenticator = require_authentication(request)
    access_token = credentials.credentials if credentials is not None else None
    try:
        actor = await authenticator.authenticate(access_token)
    except AccessTokenRejected as exc:
        raise ApiError(
            status_code=401,
            code="invalid_access_token",
            message="A valid operator access token is required.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from exc

    authorizer = cast(OperatorAuthorizer, request.app.state.operator_authorizer)
    try:
        authorizer.authorize(actor)
    except OperatorAccessDenied as exc:
        raise ApiError(
            status_code=403,
            code="operator_access_required",
            message="Operator access is required.",
        ) from exc

    return actor
