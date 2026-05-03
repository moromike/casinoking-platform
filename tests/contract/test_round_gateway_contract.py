"""P2-WP3-AT2 - Mines platform boundary contract tests.

Verifies that the Mines platform boundary translates platform exceptions
into Mines-domain exceptions, ensuring the game service never sees raw
platform errors.
"""

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
GATEWAY_PATH = (
    ROOT / "backend" / "app" / "modules" / "games" / "mines" / "round_gateway.py"
)
PLATFORM_CLIENT_PATH = (
    ROOT / "backend" / "app" / "modules" / "games" / "mines" / "platform_client.py"
)

MINES_EXCEPTIONS_MODULE = "app.modules.games.mines.exceptions"
PLATFORM_CLIENT_MODULE = "app.modules.games.mines.platform_client"
PLATFORM_ROUNDS_MODULE = "app.modules.platform.rounds.service"


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


def _extract_except_handler_names(source: str) -> list[str]:
    """Return all exception class names used in except clauses."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            if isinstance(node.type, ast.Name):
                names.append(node.type.id)
            elif isinstance(node.type, ast.Attribute):
                names.append(node.type.attr)
    return names


def _extract_raise_names(source: str) -> list[str]:
    """Return all exception class names used in raise statements."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            if isinstance(node.exc, ast.Call):
                func = node.exc.func
                if isinstance(func, ast.Name):
                    names.append(func.id)
                elif isinstance(func, ast.Attribute):
                    names.append(func.attr)
            elif isinstance(node.exc, ast.Name):
                names.append(node.exc.id)
    return names


def test_gateway_uses_platform_client_not_platform_module():
    """round_gateway.py must depend on the platform client boundary."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)
    assert PLATFORM_CLIENT_MODULE in modules, (
        f"round_gateway.py does not import from {PLATFORM_CLIENT_MODULE}"
    )
    assert PLATFORM_ROUNDS_MODULE not in modules, (
        "round_gateway.py must not import platform rounds directly after Fase 9a"
    )


def test_platform_client_imports_platform_module():
    """platform_client.py owns the in-process platform dependency."""
    source = PLATFORM_CLIENT_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)
    assert PLATFORM_ROUNDS_MODULE in modules, (
        f"platform_client.py does not import from {PLATFORM_ROUNDS_MODULE}"
    )


def test_platform_client_imports_mines_exceptions():
    """platform_client.py must import Mines-domain exceptions."""
    source = PLATFORM_CLIENT_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)
    assert MINES_EXCEPTIONS_MODULE in modules, (
        f"platform_client.py does not import from {MINES_EXCEPTIONS_MODULE}"
    )


def test_platform_client_catches_platform_exceptions():
    """platform_client.py must catch platform exceptions in try/except blocks."""
    source = PLATFORM_CLIENT_PATH.read_text(encoding="utf-8")
    caught = _extract_except_handler_names(source)

    platform_exceptions_caught = [
        name for name in caught if name.startswith("PlatformRound")
    ]
    assert len(platform_exceptions_caught) >= 1, (
        "platform_client.py does not catch any PlatformRound* exceptions. "
        "The client must translate platform exceptions into Mines exceptions."
    )


def test_platform_client_raises_mines_exceptions():
    """platform_client.py must raise Mines-domain exceptions."""
    source = PLATFORM_CLIENT_PATH.read_text(encoding="utf-8")
    raised = _extract_raise_names(source)

    mines_exceptions_raised = [
        name for name in raised if name.startswith("Mines")
    ]
    assert len(mines_exceptions_raised) >= 1, (
        "platform_client.py does not raise any Mines* exceptions. "
        "The client must translate platform exceptions into Mines exceptions."
    )


def test_platform_client_does_not_leak_platform_exceptions():
    """platform_client.py must not raise platform exceptions directly."""
    source = PLATFORM_CLIENT_PATH.read_text(encoding="utf-8")
    raised = _extract_raise_names(source)

    platform_exceptions_raised = [
        name for name in raised if name.startswith("PlatformRound")
    ]
    assert platform_exceptions_raised == [], (
        f"platform_client.py raises platform exceptions directly: {platform_exceptions_raised}. "
        "The client must only raise Mines-domain exceptions."
    )


def test_gateway_has_docstring_on_open_round():
    """open_round() must have a docstring documenting the return type."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "open_round":
            docstring = ast.get_docstring(node)
            assert docstring is not None, (
                "open_round() must have a docstring documenting the return shape"
            )
            assert "wallet_account_id" in docstring, (
                "open_round() docstring must document wallet_account_id in return type"
            )
            assert "wallet_balance_after_start" in docstring, (
                "open_round() docstring must document wallet_balance_after_start"
            )
            assert "ledger_transaction_id" in docstring, (
                "open_round() docstring must document ledger_transaction_id"
            )
            return

    assert False, "open_round() function not found in round_gateway.py"
