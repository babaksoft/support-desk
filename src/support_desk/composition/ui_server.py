"""Start Streamlit with runtime-generated Cognito OIDC configuration."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, SecretStr

SECRETS_PATH = Path("/tmp/support-desk-streamlit-secrets.toml")


class OidcServerSettings(BaseModel):
    """Configure the deployed Streamlit OIDC server.

    Attributes:
        client_id:
            Confidential Cognito app-client identifier.
        client_secret:
            Confidential Cognito app-client secret.
        cookie_secret:
            Secret used to sign Streamlit identity cookies.
        issuer:
            Cognito user-pool OpenID Connect issuer.
        public_url:
            Public CloudFront URL of the Streamlit application.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    client_id: str = Field(
        min_length=1,
        max_length=128,
        description="Confidential Cognito app-client identifier.",
    )
    client_secret: SecretStr = Field(
        description="Confidential Cognito app-client secret."
    )
    cookie_secret: SecretStr = Field(
        min_length=32,
        description="Secret used to sign Streamlit identity cookies.",
    )
    issuer: HttpUrl = Field(description="Cognito user-pool OpenID Connect issuer.")
    public_url: HttpUrl = Field(
        description="Public CloudFront URL of the Streamlit application."
    )

    @classmethod
    def from_environment(cls) -> "OidcServerSettings":
        """Read and validate OIDC server settings from the environment.

        Returns:
            Validated deployed OIDC server settings.
        """

        return cls.model_validate(
            {
                "client_id": os.environ.get("SUPPORT_DESK_COGNITO_CLIENT_ID"),
                "client_secret": os.environ.get("SUPPORT_DESK_COGNITO_CLIENT_SECRET"),
                "cookie_secret": os.environ.get("SUPPORT_DESK_SESSION_COOKIE_SECRET"),
                "issuer": os.environ.get("SUPPORT_DESK_COGNITO_ISSUER"),
                "public_url": os.environ.get("SUPPORT_DESK_PUBLIC_URL"),
            }
        )


def main() -> None:
    """Write owner-only OIDC settings and replace this process with Streamlit."""

    settings = OidcServerSettings.from_environment()
    _write_secrets(settings, SECRETS_PATH)
    streamlit = "/app/.venv/bin/streamlit"
    os.execv(
        streamlit,
        _streamlit_arguments(streamlit, SECRETS_PATH),
    )


def _write_secrets(settings: OidcServerSettings, path: Path) -> None:
    """Write Streamlit authentication settings to an owner-only TOML file.

    Args:
        settings:
            Validated OIDC server settings.
        path:
            Runtime-only destination for the Streamlit secrets file.
    """

    redirect_uri = f"{str(settings.public_url).rstrip('/')}/oauth2callback"
    metadata_url = (
        f"{str(settings.issuer).rstrip('/')}/.well-known/openid-configuration"
    )
    values = {
        "redirect_uri": redirect_uri,
        "cookie_secret": settings.cookie_secret.get_secret_value(),
        "client_id": settings.client_id,
        "client_secret": settings.client_secret.get_secret_value(),
        "server_metadata_url": metadata_url,
        "expose_tokens": "access",
    }
    content = "[auth]\n" + "".join(
        f"{key} = {json.dumps(value)}\n" for key, value in values.items()
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as secrets_file:
        secrets_file.write(content)


def _streamlit_arguments(streamlit: str, secrets_path: Path) -> list[str]:
    """Build the deployed Streamlit command arguments.

    Args:
        streamlit:
            Absolute Streamlit executable path.
        secrets_path:
            Runtime OIDC settings file passed as one secrets location.

    Returns:
        Streamlit command arguments with the exact secrets file path.
    """

    return [
        streamlit,
        "run",
        "/app/src/support_desk/composition/ui.py",
        "--server.address=0.0.0.0",
        "--server.port=8501",
        "--server.headless=true",
        f"--secrets.files={secrets_path}",
    ]


if __name__ == "__main__":
    main()
