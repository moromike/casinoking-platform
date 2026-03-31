"""P2-WP3-AT2 — Round gateway contract tests.

Verifies that round_gateway functions translate platform exceptions
into Mines-domain exceptions, ensuring the game service never sees
raw platform errors.
"""

import ast
import pathlib

GATEWAY_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "backend"
    / "app"
    / "modules"
    / "games"
    / "mines"
    / "round_gateway.py"
)

MINES_EXCEPTIONS_MODULE = "app.modules.games.mines.exceptions"
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


def test_gateway_imports_platform_module():
    """round_gateway.py must import from the platform rounds service."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)
    assert PLATFORM_ROUNDS_MODULE in modules, (
        f"round_gateway.py does not import from {PLATFORM_ROUNDS_MODULE}"
    )


def test_gateway_imports_mines_exceptions():
    """round_gateway.py must import Mines-domain exceptions."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    modules = _extract_import_modules(source)
    assert MINES_EXCEPTIONS_MODULE in modules, (
        f"round_gateway.py does not import from {MINES_EXCEPTIONS_MODULE}"
    )


def test_gateway_catches_platform_exceptions():
    """round_gateway.py must catch platform exceptions in try/except blocks."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    caught = _extract_except_handler_names(source)

    platform_exceptions_caught = [
        name for name in caught if name.startswith("PlatformRound")
    ]
    assert len(platform_exceptions_caught) >= 1, (
        "round_gateway.py does not catch any PlatformRound* exceptions. "
        "The gateway must translate platform exceptions into Mines exceptions."
    )


def test_gateway_raises_mines_exceptions():
    """round_gateway.py must raise Mines-domain exceptions (not platform ones)."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    raised = _extract_raise_names(source)

    mines_exceptions_raised = [
        name for name in raised if name.startswith("Mines")
    ]
    assert len(mines_exceptions_raised) >= 1, (
        "round_gateway.py does not raise any Mines* exceptions. "
        "The gateway must translate platform exceptions into Mines exceptions."
    )


def test_gateway_does_not_leak_platform_exceptions():
    """round_gateway.py must not raise platform exceptions directly."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    raised = _extract_raise_names(source)

    platform_exceptions_raised = [
        name for name in raised if name.startswith("PlatformRound")
    ]
    assert platform_exceptions_raised == [], (
        f"round_gateway.py raises platform exceptions directly: {platform_exceptions_raised}. "
        "The gateway must only raise Mines-domain exceptions."
    )


def test_gateway_has_docstring_on_open_round():
    """open_round() must have a docstring documenting the return type."""
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "open_round":
            docstring = ast.get_docstring(node)
            assert docstring is not None, (
                "open_round() must have a docstring documenting the return dict shape"
            )
            assert "wallet_account_id" in docstring, (
                "open_round() docstring must document wallet_account_id in return type"
            )
            assert "wallet_balance_after_start" in docstring, (
                "open_round() docstring must document wallet_balance_after_start in return type"
            )
            assert "ledger_transaction_id" in docstring, (
                "open_round() docstring must document ledger_transaction_id in return type"
            )
            return

    assert False, "open_round() function not found in round_gateway.py"
