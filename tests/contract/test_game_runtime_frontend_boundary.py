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
MINES_UI_DIR = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "app" / "ui" / "mines"

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


def test_game_info_rules_modal_is_shared_shell_only():
    shared_source = (GAME_RUNTIME_DIR / "game-info-rules-modal.tsx").read_text(encoding="utf-8")
    assert "@/app/ui/mines" not in shared_source
    assert "@/app/ui/boxe" not in shared_source
    assert "GameInfoRulesModal" in shared_source

    mines_source = (MINES_UI_DIR / "mines-rules-modal.tsx").read_text(encoding="utf-8")
    assert "@/app/ui/game-runtime/game-info-rules-modal" in mines_source


def test_boxe_info_button_opens_rules_modal_not_how_to_play():
    standalone_source = (BOXE_UI_DIR / "boxe-standalone.tsx").read_text(encoding="utf-8")
    gameplay_source = (BOXE_UI_DIR / "boxe-gameplay.tsx").read_text(encoding="utf-8")
    rules_modal_source = (BOXE_UI_DIR / "boxe-rules-modal.tsx").read_text(encoding="utf-8")

    assert "onOpenGameInfo" not in standalone_source
    assert "onOpenGameInfo" not in gameplay_source
    assert "setShowRules(true)" in gameplay_source
    assert "BoxeRulesModal" in gameplay_source
    assert "boxe-info-modal" not in gameplay_source
    assert 'id: "replay"' in rules_modal_source
    assert "BoxeReplayViewer" in gameplay_source
