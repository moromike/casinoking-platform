"""Guardia AST: la radice pytest non puo' caricare il plugin Mines."""

import ast
from pathlib import Path


CONFTEST_PATH = Path(__file__).resolve().parents[1] / "conftest.py"


def _is_mines_module(module: str) -> bool:
    return "mines" in module.split(".")


def _literal_strings(node: ast.expr) -> set[str] | None:
    """Restituisce le stringhe verificabili; None significa espressione opaca."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: set[str] = set()
        for item in node.elts:
            item_values = _literal_strings(item)
            if item_values is None:
                return None
            values.update(item_values)
        return values
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _literal_strings(node.left), _literal_strings(node.right)
        if left is None or right is None:
            return None
        return {a + b for a in left for b in right}
    return None


def test_conftest_no_mines() -> None:
    tree = ast.parse(CONFTEST_PATH.read_text(encoding="utf-8"), filename=str(CONFTEST_PATH))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offenders.extend(
                f"import {alias.name}" for alias in node.names if _is_mines_module(alias.name)
            )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_mines_module(module):
                offenders.append(f"from {module} import ...")
            offenders.extend(
                f"from {module} import {alias.name}"
                for alias in node.names
                if alias.name == "mines" or _is_mines_module(f"{module}.{alias.name}".strip("."))
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Name) and target.id == "pytest_plugins" for target in targets):
                continue
            values = _literal_strings(node.value)
            if values is None:
                offenders.append("pytest_plugins non staticamente verificabile")
            else:
                offenders.extend(
                    f"pytest_plugins = {plugin!r}"
                    for plugin in values
                    if _is_mines_module(plugin)
                )
    assert not offenders, "conftest.py carica Mines o un plugin non verificabile: " + "; ".join(offenders)
