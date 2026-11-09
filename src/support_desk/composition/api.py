"""Configure the local API process from explicit provider settings."""

import os
from typing import Self

from fastapi import FastAPI
from openai import AsyncOpenAI
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from support_desk.api import create_app
from support_desk.application import AnswerService
from support_desk.infrastructure import AgentsAnswerGenerator


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

    settings = InferenceSettings.from_environment()
    if not settings.enabled:
        return create_app()

    client = AsyncOpenAI(
        api_key=settings.api_key.get_secret_value(), max_retries=0, timeout=40
    )
    service = AnswerService(AgentsAnswerGenerator(client, settings.model))

    return create_app(service, managed_resources=(client,))
