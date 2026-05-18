import pathlib
import re


GAME_RUNTIME_DIR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend"
    / "app"
    / "ui"
    / "game-runtime"
)
BOXE_UI_DIR = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "app" / "ui" / "boxe"

IMPORT_RE = re.compile(r"(?:from|import)\s+['\"]([^'\"]+)['\"]")
FORBIDDEN_MINES_IMPORTS = (
    "@/app/ui/mines",
    "../mines",
    "./mines",
)
FORBIDDEN_BOXE_IMPORTS = (
    "@/app/ui/boxe",
    "../boxe",
    "./boxe",
)


def _game_runtime_sources() -> list[pathlib.Path]:
    return sorted(
        path
        for path in GAME_RUNTIME_DIR.iterdir()
        if path.suffix in {".ts", ".tsx"}
    )


def test_game_runtime_does_not_import_mines_frontend():
    offenders: list[str] = []
    for path in _game_runtime_sources():
        source = path.read_text(encoding="utf-8")
        for module_path in IMPORT_RE.findall(source):
            if module_path.startswith(FORBIDDEN_MINES_IMPORTS):
                offenders.append(f"{path.relative_to(GAME_RUNTIME_DIR.parents[3])}: {module_path}")

    assert offenders == []


def test_game_runtime_does_not_import_boxe_frontend():
    offenders: list[str] = []
    for path in _game_runtime_sources():
        source = path.read_text(encoding="utf-8")
        for module_path in IMPORT_RE.findall(source):
            if module_path.startswith(FORBIDDEN_BOXE_IMPORTS):
                offenders.append(f"{path.relative_to(GAME_RUNTIME_DIR.parents[3])}: {module_path}")

    assert offenders == []


def test_boxe_frontend_does_not_import_mines_frontend():
    if not BOXE_UI_DIR.exists():
        return

    offenders: list[str] = []
    for path in sorted(BOXE_UI_DIR.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        source = path.read_text(encoding="utf-8")
        for module_path in IMPORT_RE.findall(source):
            if module_path.startswith(FORBIDDEN_MINES_IMPORTS):
                offenders.append(f"{path.relative_to(BOXE_UI_DIR.parents[3])}: {module_path}")

    assert offenders == []
