"""Configure the local API process from explicit provider settings."""

import os
from typing import Literal, Self

from fastapi import FastAPI
from openai import AsyncOpenAI
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
    model_validator,
)

from support_desk.api import create_app
from support_desk.application import AnswerService, OperatorAuthorizer
from support_desk.domain import AccessTokenAuthenticator
from support_desk.infrastructure import (
    AgentsAnswerGenerator,
    CognitoAccessTokenAuthenticator,
    LocalOperatorAuthenticator,
)


class AuthenticationSettings(BaseModel):
    """Configure local or Cognito operator authentication.

    Attributes:
        mode:
            Authentication adapter selected for this process.
        issuer:
            Cognito user-pool issuer for deployed authentication.
        client_id:
            Cognito app client allowed to authenticate operators.
        operator_group:
            Cognito group authorized for operator use cases.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    mode: Literal["local", "cognito"] = Field(
        description="Authentication adapter selected for this process."
    )
    issuer: HttpUrl | None = Field(
        description="Cognito user-pool issuer for deployed authentication."
    )
    client_id: str = Field(
        max_length=128,
        description="Cognito app client allowed to authenticate operators.",
    )
    operator_group: str = Field(
        min_length=1,
        max_length=128,
        description="Cognito group authorized for operator use cases.",
    )

    @model_validator(mode="after")
    def validate_mode_configuration(self) -> Self:
        """Require complete and mode-appropriate authentication settings.

        Returns:
            Validated authentication settings.

        Raises:
            ValueError:
                Cognito settings are incomplete or supplied in local mode.
        """

        if self.mode == "cognito":
            if self.issuer is None or not self.client_id:
                raise ValueError(
                    "Cognito authentication requires issuer and client ID."
                )
            if self.issuer.scheme != "https":
                raise ValueError("Cognito issuer must use HTTPS.")
        elif self.issuer is not None or self.client_id:
            raise ValueError("Local authentication does not accept Cognito settings.")

        return self

    @classmethod
    def from_environment(cls) -> Self:
        """Read and validate authentication settings from the environment.

        Returns:
            Validated authentication settings.

        Raises:
            ValueError:
                Authentication settings are invalid or incomplete.
        """

        return cls.model_validate(
            {
                "mode": os.environ.get("SUPPORT_DESK_AUTH_MODE", "local"),
                "issuer": os.environ.get("SUPPORT_DESK_COGNITO_ISSUER") or None,
                "client_id": os.environ.get("SUPPORT_DESK_COGNITO_CLIENT_ID", ""),
                "operator_group": os.environ.get(
                    "SUPPORT_DESK_OPERATOR_GROUP", "operators"
                ),
            }
        )


class InferenceSettings(BaseModel):
    """Configure optional model inference.

    Attributes:
        enabled:
            Whether model inference is explicitly enabled.
        model:
            OpenAI Responses model identifier.
        api_key:
            OpenAI provider credential.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    enabled: bool = Field(description="Whether model inference is explicitly enabled.")
    model: str = Field(description="OpenAI Responses model identifier.")
    api_key: SecretStr = Field(description="OpenAI provider credential.", repr=False)

    @field_validator("enabled", mode="before")
    @classmethod
    def validate_enabled(cls, value: object) -> bool:
        """Accept only explicit boolean or zero/one enablement values.

        Args:
            value:
                Raw enablement value.

        Returns:
            Validated enablement state.

        Raises:
            ValueError:
                The enablement value is ambiguous.
        """

        if value in (None, "", "0", False):
            return False
        if value in ("1", True):
            return True

        raise ValueError("SUPPORT_DESK_ENABLE_INFERENCE must be 0 or 1.")

    @model_validator(mode="after")
    def validate_enabled_configuration(self) -> Self:
        """Require provider settings when inference is enabled.

        Returns:
            Validated inference settings.

        Raises:
            ValueError:
                Enabled inference lacks a model or API key.
        """

        if self.enabled and (
            not self.model or not self.api_key.get_secret_value().strip()
        ):
            raise ValueError("Enabled inference requires a model and API key.")

        return self

    @classmethod
    def from_environment(cls) -> Self:
        """Read and validate inference settings from the environment.

        Returns:
            Validated inference settings.

        Raises:
            ValueError:
                The enable flag is invalid or enabled settings are incomplete.
        """

        return cls.model_validate(
            {
                "enabled": os.environ.get("SUPPORT_DESK_ENABLE_INFERENCE", ""),
                "model": os.environ.get("SUPPORT_DESK_MODEL", "").strip(),
                "api_key": os.environ.get("OPENAI_API_KEY", "").strip(),
            }
        )


def build_app() -> FastAPI:
    """Build an API with optional, explicitly enabled inference.

    Returns:
        Configured API or health-only API when inference is disabled.
    """

    authentication = AuthenticationSettings.from_environment()
    authenticator = _build_authenticator(authentication)
    authorizer = OperatorAuthorizer(required_group=authentication.operator_group)

    inference = InferenceSettings.from_environment()
    if not inference.enabled:
        return create_app(
            authenticator=authenticator,
            operator_authorizer=authorizer,
        )

    client = AsyncOpenAI(
        api_key=inference.api_key.get_secret_value(), max_retries=0, timeout=40
    )
    service = AnswerService(AgentsAnswerGenerator(client, inference.model))

    return create_app(
        service,
        managed_resources=(client,),
        authenticator=authenticator,
        operator_authorizer=authorizer,
    )


def _build_authenticator(
    settings: AuthenticationSettings,
) -> AccessTokenAuthenticator:
    """Construct the configured authentication adapter.

    Args:
        settings:
            Validated authentication settings.

    Returns:
        Local or Cognito access-token authenticator.
    """

    if settings.mode == "local":
        return LocalOperatorAuthenticator(settings.operator_group)
    if settings.issuer is None:
        raise RuntimeError("Validated Cognito settings lost their issuer.")

    return CognitoAccessTokenAuthenticator(
        issuer=str(settings.issuer),
        client_id=settings.client_id,
    )
