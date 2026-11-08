"""Protect executable dependency boundaries and packaged evidence."""

import ast
import sys
from pathlib import Path

import pytest

from support_desk.domain import SourceId
from support_desk.infrastructure.references import SOURCE_FILES

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_only_import_allowed_dependencies(layer: str) -> None:
    """Keep framework and outer-layer imports outside application policy.

    Args:
        layer:
            Inner package to inspect.
    """

    allowed = {"pydantic"}
    allowed.update(sys.stdlib_module_names)
    for path in (ROOT / "src/support_desk" / layer).glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0
                modules = [node.module or ""]
            for module in modules:
                assert module.split(".")[0] in allowed or module.startswith(
                    ("support_desk.domain", f"support_desk.{layer}")
                ), (path, module)


def test_packaged_sources_match_authored_reference_pack() -> None:
    """Keep wheel/container evidence identical to the reviewed product pack."""

    assert set(SOURCE_FILES) == set(SourceId)
    for filename in SOURCE_FILES.values():
        authored = ROOT / "docs/product/boardlight/v1" / filename
        packaged = ROOT / "src/support_desk/infrastructure/evidence" / filename
        assert packaged.read_bytes() == authored.read_bytes()
