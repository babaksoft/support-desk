"""Verify deployed Streamlit OIDC server configuration."""

import stat
from pathlib import Path

import pytest

from support_desk.composition.ui_server import OidcServerSettings, _write_secrets


def test_writes_owner_only_cognito_oidc_settings(tmp_path: Path) -> None:
    """Create the exact deployed callback and expose only the API access token.

    Args:
        tmp_path:
            Isolated runtime secrets directory.
    """

    path = tmp_path / "secrets.toml"
    settings = OidcServerSettings.model_validate(
        {
            "client_id": "cognito-client",
            "client_secret": "cognito-secret",
            "cookie_secret": "a" * 64,
            "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool",
            "public_url": "https://example.cloudfront.net/",
        }
    )

    _write_secrets(settings, path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert path.read_text(encoding="utf-8") == (
        '[auth]\nredirect_uri = "https://example.cloudfront.net/oauth2callback"\n'
        'cookie_secret = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"\n'
        'client_id = "cognito-client"\n'
        'client_secret = "cognito-secret"\n'
        "server_metadata_url = "
        '"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_pool/'
        '.well-known/openid-configuration"\n'
        'expose_tokens = "access"\n'
    )


def test_requires_complete_oidc_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject a deployed server without its confidential settings.

    Args:
        monkeypatch:
            Pytest environment patching helper.
    """

    for name in (
        "SUPPORT_DESK_COGNITO_CLIENT_ID",
        "SUPPORT_DESK_COGNITO_CLIENT_SECRET",
        "SUPPORT_DESK_SESSION_COOKIE_SECRET",
        "SUPPORT_DESK_COGNITO_ISSUER",
        "SUPPORT_DESK_PUBLIC_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError):
        OidcServerSettings.from_environment()
