"""Guardia strutturale (4C-bis): nessun autouse nei plugin di tests/fixtures/.

pytest_plugins registra un plugin per TUTTA la sessione: una fixture
autouse=True in tests/fixtures/*.py si applica a ogni collaudo della suite,
anche ai file che non usano il plugin. E' il difetto D2 della revisione del
PASSO 4C. Il controllo e' sull'AST (non sul testo): la parola "autouse" nei
commenti non conta. Collaudo statico: niente database.
"""

import ast
from pathlib import Path


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def _is_fixture_call(decorator: ast.expr) -> ast.Call | None:
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    name = ""
    if isinstance(func, ast.Attribute):
        name = func.attr
    elif isinstance(func, ast.Name):
        name = func.id
    if name == "fixture":
        return decorator
    return None


def test_fixture_plugins_no_autouse() -> None:
    offenders: list[str] = []
    for path in sorted(FIXTURES_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                call = _is_fixture_call(decorator)
                if call is None:
                    continue
                for keyword in call.keywords:
                    if keyword.arg == "autouse" and not (
                        isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is False
                    ):
                        offenders.append(f"{path.relative_to(FIXTURES_DIR)}:{node.lineno} {node.name}")
    assert not offenders, (
        "Fixture con autouse diverso dal letterale False nei plugin di tests/fixtures/ "
        "(si applicano a TUTTA la suite): " + ", ".join(offenders)
    )
