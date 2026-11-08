"""Verify the installed package is usable outside the repository directory."""

import subprocess
import sys
from pathlib import Path


def test_installed_package_is_importable_outside_repository(tmp_path: Path) -> None:
    """Import the package and resolve its distribution metadata in isolation.

    Args:
        tmp_path:
            Temporary working directory supplied by pytest.
    """

    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import support_desk; "
            "from importlib.metadata import version; "
            "version('support-desk')",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
