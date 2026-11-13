"""Verify the public, non-billable deployment surface."""

import argparse
import sys
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

HEALTH_PATH = "/_stcore/health"
REQUEST_TIMEOUT_SECONDS = 15.0


class DeploymentSmokeFailure(Exception):
    """Report that the public deployment surface failed verification."""


def verify_deployment(base_url: str) -> None:
    """Verify HTTPS, Streamlit health, and the application entry point.

    Args:
        base_url:
            Public CloudFront application URL.

    Raises:
        DeploymentSmokeFailure:
            The URL is unsafe, unavailable, unhealthy, or does not serve the app.
    """

    parsed_url = urlparse(base_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise DeploymentSmokeFailure("Deployment URL must be an absolute HTTPS URL.")
    if parsed_url.username is not None or parsed_url.password is not None:
        raise DeploymentSmokeFailure("Deployment URL must not contain credentials.")

    health_body = _request_text(urljoin(base_url.rstrip("/") + "/", HEALTH_PATH[1:]))
    if health_body.strip() != "ok":
        raise DeploymentSmokeFailure("Streamlit health response was not healthy.")

    _request_text(base_url.rstrip("/") + "/")


def main() -> None:
    """Run the public deployment smoke from the command line."""

    parser = argparse.ArgumentParser(
        description="Verify the non-billable Support Desk deployment surface."
    )
    parser.add_argument("base_url", help="Public HTTPS CloudFront application URL.")
    arguments = parser.parse_args()

    try:
        verify_deployment(arguments.base_url)
    except DeploymentSmokeFailure as exc:
        print(f"Deployment smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Deployment smoke passed: HTTPS entry point and Streamlit are healthy.")


def _request_text(url: str) -> str:
    """Fetch one public URL with a bounded response size.

    Args:
        url:
            Absolute HTTPS URL to request.

    Returns:
        Decoded response body.

    Raises:
        DeploymentSmokeFailure:
            The endpoint is unavailable or returns an unsuccessful response.
    """

    request = Request(url, headers={"User-Agent": "support-desk-deployment-smoke/1"})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = cast(bytes, response.read(64 * 1024 + 1))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise DeploymentSmokeFailure(
            f"Request failed for {urlparse(url).path}."
        ) from exc

    if len(body) > 64 * 1024:
        raise DeploymentSmokeFailure("Deployment response exceeded 64 KiB.")
    return body.decode("utf-8", errors="replace")


if __name__ == "__main__":
    main()
