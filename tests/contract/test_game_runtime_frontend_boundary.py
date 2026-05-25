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
HI_LO_UI_DIR = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "app" / "ui" / "hi-lo"
HI_LO_BACKOFFICE_UI_DIR = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend"
    / "app"
    / "ui"
    / "hi-lo-backoffice"
)

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
FORBIDDEN_HI_LO_IMPORTS = (
    "@/app/ui/hi-lo",
    "../hi-lo",
    "./hi-lo",
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


def test_game_runtime_does_not_import_hi_lo_frontend():
    offenders: list[str] = []
    for path in _game_runtime_sources():
        source = path.read_text(encoding="utf-8")
        for module_path in IMPORT_RE.findall(source):
            if module_path.startswith(FORBIDDEN_HI_LO_IMPORTS):
                offenders.append(f"{path.relative_to(GAME_RUNTIME_DIR.parents[3])}: {module_path}")

    assert offenders == []


def test_game_embed_bridge_is_shared_and_consumed_by_all_games():
    bridge_source = (GAME_RUNTIME_DIR / "use-game-embed-bridge.ts").read_text(
        encoding="utf-8"
    )
    mines_source = (MINES_UI_DIR / "mines-standalone.tsx").read_text(encoding="utf-8")
    boxe_source = (BOXE_UI_DIR / "boxe-standalone.tsx").read_text(encoding="utf-8")
    hi_lo_source = (HI_LO_UI_DIR / "hi-lo-standalone.tsx").read_text(encoding="utf-8")
    console_source = (
        pathlib.Path(__file__).resolve().parents[2]
        / "frontend"
        / "app"
        / "ui"
        / "casinoking-console.tsx"
    ).read_text(encoding="utf-8")

    assert "GAME_EMBED_CLOSE_MESSAGE" in bridge_source
    assert "GAME_EMBED_FULLSCREEN_STATE_MESSAGE" in bridge_source
    assert "casinoking:game-close" in bridge_source
    assert "casinoking:game-fullscreen-state" in bridge_source
    assert 'if (gameCode === "mines")' not in bridge_source
    assert 'if (gameCode === "boxe")' not in bridge_source
    assert 'if (gameCode === "hi_lo")' not in bridge_source

    for source in (mines_source, boxe_source, hi_lo_source):
        assert "useGameEmbedBridge" in source
        assert "requestEmbedClose" in source

    assert "GAME_EMBED_CLOSE_MESSAGE" in console_source
    assert "GAME_EMBED_FULLSCREEN_STATE_MESSAGE" in console_source
    assert "MINES_EMBED_CLOSE_MESSAGE" in console_source


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


def test_hi_lo_frontend_does_not_import_mines_or_boxe_frontend():
    if not HI_LO_UI_DIR.exists():
        return

    offenders: list[str] = []
    for path in sorted(HI_LO_UI_DIR.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        source = path.read_text(encoding="utf-8")
        for module_path in IMPORT_RE.findall(source):
            if module_path.startswith(FORBIDDEN_MINES_IMPORTS + FORBIDDEN_BOXE_IMPORTS):
                offenders.append(f"{path.relative_to(HI_LO_UI_DIR.parents[3])}: {module_path}")

    assert offenders == []


def test_game_info_rules_modal_is_shared_shell_only():
    shared_source = (GAME_RUNTIME_DIR / "game-info-rules-modal.tsx").read_text(encoding="utf-8")
    assert "@/app/ui/mines" not in shared_source
    assert "@/app/ui/boxe" not in shared_source
    assert "@/app/ui/hi-lo" not in shared_source
    assert "GameInfoRulesModal" in shared_source

    mines_source = (MINES_UI_DIR / "mines-rules-modal.tsx").read_text(encoding="utf-8")
    assert "@/app/ui/game-runtime/game-info-rules-modal" in mines_source
    hi_lo_source = (HI_LO_UI_DIR / "hi-lo-rules-modal.tsx").read_text(encoding="utf-8")
    assert "@/app/ui/game-runtime/game-info-rules-modal" in hi_lo_source


def test_game_boot_decision_flow_never_mounts_runtime_under_provider_intro():
    boot_flow_source = (GAME_RUNTIME_DIR / "game-boot-decision-flow.tsx").read_text(
        encoding="utf-8"
    )
    hi_lo_standalone_source = (HI_LO_UI_DIR / "hi-lo-standalone.tsx").read_text(
        encoding="utf-8"
    )

    assert "isRuntimeReady && !showProviderIntroGate ? children : null" in boot_flow_source
    show_provider_intro_block = re.search(
        r"const showProviderIntroGate =(?P<body>.*?);",
        hi_lo_standalone_source,
        re.DOTALL,
    )
    assert show_provider_intro_block is not None
    assert "!isCheckingActiveRound" not in show_provider_intro_block.group("body")


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


def test_boxe_rules_modal_renders_rich_manifest_sections():
    rules_modal_source = (BOXE_UI_DIR / "boxe-rules-modal.tsx").read_text(encoding="utf-8")
    copy_defaults_source = (
        BOXE_UI_DIR / "boxe-i18n" / "boxe-copy-defaults.ts"
    ).read_text(encoding="utf-8")

    expected_sections = [
        "bet_collect",
        "payout_display",
        "payout_rules",
        "fairness_explain",
        "board_mechanics",
        "difficulty_semantics",
        "max_win_cap",
    ]
    for section in expected_sections:
        assert section in copy_defaults_source

    assert "BOXE_DEFAULT_RULE_SECTIONS" in rules_modal_source
    assert "BOXE_RULE_SECTION_DEFINITIONS" in rules_modal_source
    assert ".map((section)" in rules_modal_source
    assert "server-authoritative" in copy_defaults_source
    assert "98%" in copy_defaults_source


def test_boxe_runtime_passes_title_asset_symbols_to_board():
    gameplay_source = (BOXE_UI_DIR / "boxe-gameplay.tsx").read_text(encoding="utf-8")
    board_source = (BOXE_UI_DIR / "boxe-pyramid-board.tsx").read_text(encoding="utf-8")

    assert "titleThemeAssets.symbol_safe" in gameplay_source
    assert "resolveBackendAssetUrl(titleThemeAssets.symbol_safe)" in gameplay_source
    assert "safeIconSrc={safeIconSrc}" in gameplay_source
    assert "titleThemeAssets.symbol_mine" in gameplay_source
    assert "resolveBackendAssetUrl(titleThemeAssets.symbol_mine)" in gameplay_source
    assert "mineIconSrc={mineIconSrc}" in gameplay_source

    assert "safeIconSrc = BOXE_SAFE_SYMBOL_URL" in board_source
    assert "mineIconSrc = BOXE_MINE_SYMBOL_URL" in board_source
    assert "src={safeIconSrc}" in board_source
    assert "src={mineIconSrc}" in board_source


def test_hi_lo_rules_modal_renders_rich_manifest_sections():
    rules_modal_source = (HI_LO_UI_DIR / "hi-lo-rules-modal.tsx").read_text(encoding="utf-8")
    copy_defaults_source = (
        HI_LO_UI_DIR / "hi-lo-i18n" / "hi-lo-copy-defaults.ts"
    ).read_text(encoding="utf-8")
    assets_source = (HI_LO_BACKOFFICE_UI_DIR / "hi-lo-assets-editor.tsx").read_text(
        encoding="utf-8"
    )
    theme_source = (HI_LO_BACKOFFICE_UI_DIR / "hi-lo-theme-editor.tsx").read_text(
        encoding="utf-8"
    )

    expected_sections = [
        "bet_predict_collect",
        "probability_display",
        "payout_rules",
        "fairness_explain",
        "card_deck_mechanics",
        "skip_semantics",
        "edge_rank_behavior",
    ]
    for section in expected_sections:
        assert section in copy_defaults_source

    assert "HI_LO_DEFAULT_RULE_SECTIONS" in rules_modal_source
    assert "HI_LO_RULE_SECTION_DEFINITIONS" in rules_modal_source
    assert ".map((section)" in rules_modal_source
    assert "server-authoritative" in copy_defaults_source
    assert "98%" in copy_defaults_source
    assert "title_logo" in assets_source
    assert "game_area_background" in assets_source
    assert "cell_face_down_background" not in assets_source
    assert "Card back texture" not in theme_source
