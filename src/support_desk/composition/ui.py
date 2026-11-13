"""Configure the Streamlit process from explicit API settings."""

import os
from typing import Literal

import streamlit as st
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from support_desk.ui import HttpQuestionClient, render_app


class UiSettings(BaseModel):
    """Configure the operator interface.

    Attributes:
        api_url:
            Root URL of the Support Desk API.
        authentication_mode:
            Operator authentication mode used by the interface.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    api_url: HttpUrl = Field(description="Root URL of the Support Desk API.")
    authentication_mode: Literal["local", "cognito"] = Field(
        description="Operator authentication mode used by the interface."
    )

    @classmethod
    def from_environment(cls) -> "UiSettings":
        """Read and validate UI settings from the environment.

        Returns:
            Validated operator-interface settings.
        """

        return cls.model_validate(
            {
                "api_url": os.environ.get(
                    "SUPPORT_DESK_API_URL", "http://127.0.0.1:8000"
                ),
                "authentication_mode": os.environ.get(
                    "SUPPORT_DESK_UI_AUTH_MODE", "local"
                ),
            }
        )


def main() -> None:
    """Render the configured Streamlit operator interface."""

    settings = UiSettings.from_environment()
    if settings.authentication_mode == "local":
        render_app(HttpQuestionClient(str(settings.api_url)))
        return

    if not st.user.is_logged_in:
        _render_login()
        return

    access_token = st.user.tokens.get("access")
    if not isinstance(access_token, str) or not access_token:
        _render_missing_access_token()
        return

    render_app(
        HttpQuestionClient(str(settings.api_url), access_token=access_token),
        operator_email=_operator_email(),
    )


def _render_login() -> None:
    """Prompt an unauthenticated operator to use the configured provider."""

    st.set_page_config(page_title="Support Desk", page_icon="💬")
    st.title("Support Desk")
    st.caption("Draft Boardlight product guidance from authored evidence.")
    st.info("Sign in with the approved Google account to continue.")
    if st.button("Sign in", type="primary"):
        st.login()


def _render_missing_access_token() -> None:
    """Fail closed when the authenticated session has no API access token."""

    st.set_page_config(page_title="Support Desk", page_icon="💬")
    st.title("Support Desk")
    st.error("The operator session is incomplete. Sign out and try again.")
    if st.button("Sign out"):
        st.logout()


def _operator_email() -> str | None:
    """Read the optional display email from trusted session claims.

    Returns:
        Operator email when Cognito supplied a nonempty string.
    """

    email = st.user.get("email")
    return email if isinstance(email, str) and email else None


if __name__ == "__main__":
    main()
