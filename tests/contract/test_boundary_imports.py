"""P2-WP3-AT1 — Boundary import test.

Verifies that the Mines game service (service.py) does NOT import directly
from app.modules.platform. All platform interaction must go through
app.modules.games.mines.round_gateway.
"""

import ast
import pathlib


SERVICE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "backend"
    / "app"
    / "modules"
    / "games"
    / "mines"
    / "service.py"
)

ALLOWED_GATEWAY_MODULE = "app.modules.games.mines.round_gateway"
FORBIDDEN_PREFIX = "app.modules.platform"


def _extract_import_modules(source: str) -> list[str]:
    """Return all imported module paths from a Python source string."""
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def test_service_does_not_import_platform_directly():
    """service.py must not import from app.modules.platform directly."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)

    platform_imports = [
        m for m in modules if m.startswith(FORBIDDEN_PREFIX)
    ]
    assert platform_imports == [], (
        f"service.py imports directly from platform modules: {platform_imports}. "
        f"All platform access must go through {ALLOWED_GATEWAY_MODULE}."
    )


def test_service_imports_round_gateway():
    """service.py must import from round_gateway (the boundary gateway)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)

    gateway_imports = [
        m for m in modules if m == ALLOWED_GATEWAY_MODULE
    ]
    assert len(gateway_imports) >= 1, (
        f"service.py does not import from {ALLOWED_GATEWAY_MODULE}. "
        "The game service must use the gateway for all platform interactions."
    )
