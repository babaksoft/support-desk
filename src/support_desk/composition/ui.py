"""Configure the Streamlit process from explicit API settings."""

import os

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from support_desk.ui import HttpQuestionClient, render_app


class UiSettings(BaseModel):
    """Configure the operator interface.

    Attributes:
        api_url:
            Root URL of the Support Desk API.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    api_url: HttpUrl = Field(description="Root URL of the Support Desk API.")

    @classmethod
    def from_environment(cls) -> "UiSettings":
        """Read and validate UI settings from the environment.

        Returns:
            Validated operator-interface settings.
        """

        return cls.model_validate(
            {"api_url": os.environ.get("SUPPORT_DESK_API_URL", "http://127.0.0.1:8000")}
        )


def main() -> None:
    """Render the configured Streamlit operator interface."""

    settings = UiSettings.from_environment()
    render_app(HttpQuestionClient(str(settings.api_url)))


if __name__ == "__main__":
    main()
