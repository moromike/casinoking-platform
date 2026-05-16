import pathlib
import re


GAME_RUNTIME_DIR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend"
    / "app"
    / "ui"
    / "game-runtime"
)

IMPORT_RE = re.compile(r"(?:from|import)\s+['\"]([^'\"]+)['\"]")
FORBIDDEN_MINES_IMPORTS = (
    "@/app/ui/mines",
    "../mines",
    "./mines",
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
