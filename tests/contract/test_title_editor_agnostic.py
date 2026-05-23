from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_engine_editor_registry_is_whitelist_based_and_lazy() -> None:
    source = _read("frontend/app/ui/title-editor/engine-editor-registry.ts")

    assert "REGISTERED_ENGINE_EDITORS" in source
    assert "REGISTERED_ENGINE_DIAGNOSTICS" in source
    assert "mines:" in source
    assert "boxe:" in source
    assert "hi_lo:" in source
    assert "dynamic<EngineEditorProps<unknown>>" in source
    assert "import { MinesEngineEditor" not in source
    assert "import { BoxeEngineEditor" not in source
    assert "import { MinesEngineDiagnostics" not in source
    assert "import { BoxeEngineDiagnostics" not in source
    assert "Unsupported" not in source


def test_hi_lo_player_route_uses_runtime_shell_and_keeps_admin_gameplay_free() -> None:
    registry_source = _read("frontend/app/ui/player-game-registry.ts")
    editor_source = _read("frontend/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx")
    route_source = _read("frontend/app/hi-lo/page.tsx")
    gameplay_source = _read("frontend/app/ui/hi-lo/hi-lo-gameplay.tsx")

    assert 'hi_lo: {' in registry_source
    assert 'launchRoute: "/hi-lo"' in registry_source
    assert "/admin/games/hi-lo/config" in editor_source
    assert "/games/hi-lo/start" not in editor_source
    assert "startHiLo" not in editor_source
    assert "cashoutHiLo" not in editor_source
    assert "HiLoStandalone" in route_source
    assert "startHiLoRound" in gameplay_source
    assert "cashoutHiLoRound" in gameplay_source


def test_hi_lo_backoffice_closes_full_surface_10_layers() -> None:
    editor_source = _read("frontend/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx")
    assets_source = _read("frontend/app/ui/hi-lo-backoffice/hi-lo-assets-editor.tsx")
    overview_source = _read("frontend/app/ui/hi-lo-backoffice/hi-lo-config-overview.tsx")
    theme_source = _read("frontend/app/ui/hi-lo-backoffice/hi-lo-theme-editor.tsx")
    service_source = _read("backend/app/modules/games/hi_lo/service.py")
    admin_routes_source = _read("backend/app/api/routes/admin.py")

    assert "TitleEditorCommandBar" in editor_source
    assert "TitleEditorTabFrame" in editor_source
    for label in [
        "Overview",
        "Copy i18n",
        "Rules HTML",
        "Gameplay config",
        "Assets",
        "Sounds",
        "Theme",
        "Validation",
    ]:
        assert label in editor_source
    assert "HiLoConfigOverview" in editor_source
    assert "HiLoAssetsEditor" in editor_source
    assert "HiLoThemeEditor" in editor_source
    assert "TitleSoundAssetsEditor" in editor_source
    assert "validateHiLoPayload" in editor_source

    assert "game_area_background" in assets_source
    assert "cell_face_down_background" in assets_source
    assert "title_logo" in theme_source
    assert "Advanced skin" in theme_source
    assert "Rules coverage" in overview_source

    assert "/games/hi-lo/config" in admin_routes_source
    assert "presentation_config" in service_source


def test_hi_lo_replay_and_account_history_are_registered() -> None:
    account_source = _read("frontend/app/ui/player-account-page.tsx")
    finance_source = _read("frontend/app/ui/admin-finance-panel.tsx")
    runtime_source = _read("frontend/app/ui/hi-lo/use-hi-lo-runtime.ts")
    route_source = _read("backend/app/api/routes/hi_lo.py")
    service_source = _read("backend/app/modules/games/hi_lo/service.py")

    assert "HiLoReplayViewer" in account_source
    assert "/games/hi-lo/sessions?limit=10" in account_source
    assert "/games/hi-lo/round/" in account_source
    assert "mapHiLoHistoryItem" in account_source
    assert "HiLoReplayViewer" in finance_source
    assert "/games/hi-lo/admin/round/" in finance_source
    assert "loadHiLoActiveRound" in runtime_source
    assert '@router.get("/active-round")' in route_source
    assert "def get_active_round" in service_source


def test_title_editor_shell_uses_generic_runtime_config_and_diagnostics_slot() -> None:
    source = _read("frontend/app/ui/title-editor/title-editor-shell.tsx")

    assert "MinesRuntimeConfig" not in source
    assert "runtimeConfig: unknown | null" in source
    assert "setRuntimeConfig: Dispatch<SetStateAction<unknown | null>>" in source
    assert "resolveEngineDiagnostics" in source
    assert "<EngineDiagnostics" in source


def test_title_editor_command_bar_uses_engine_templated_busy_actions() -> None:
    source = _read("frontend/app/ui/title-editor/title-editor-command-bar.tsx")

    assert "admin-mines-backoffice" not in source
    assert "buildTitleEditorBusyAction" in source
    assert "admin-${engineCode}-backoffice-${action}" in source
    assert "engineCode: string" in source


def test_title_editor_shared_b1_tabs_exist_and_stay_engine_agnostic() -> None:
    tabs_dir = ROOT / "frontend/app/ui/title-editor/tabs"
    expected_files = {
        "title-editor-tab-frame.tsx",
        "title-editor-status-banner.tsx",
        "title-editor-validation-display.tsx",
        "title-editor-overview-tab.tsx",
        "title-editor-config-tab.tsx",
        "types.ts",
    }

    assert expected_files.issubset({path.name for path in tabs_dir.iterdir()})

    combined_source = "\n".join(
        (tabs_dir / filename).read_text(encoding="utf-8")
        for filename in expected_files
    )
    assert "engineCode ===" not in combined_source
    assert '"mines"' not in combined_source
    assert '"boxe"' not in combined_source
    assert "TitleEditorTabFrame" in combined_source
    assert "TitleEditorValidationDisplay" in combined_source


def test_admin_console_loads_title_editor_config_by_engine() -> None:
    source = _read("frontend/app/ui/casinoking-console.tsx")

    assert "/games/${encodeURIComponent(engineCode)}/config?" in source
    assert "selectedTitleEditorRuntimeConfig" in source
    assert "setSelectedTitleEditorRuntimeConfig" in source
    assert "Fairness diagnostics" not in source


def test_admin_engine_page_uses_generic_category_view_for_all_engines() -> None:
    overview_source = _read("frontend/app/ui/games/games-overview.tsx")
    category_source = _read("frontend/app/ui/games/game-category-view.tsx")
    variant_list_source = _read("frontend/app/ui/games/game-variant-list.tsx")
    console_source = _read("frontend/app/ui/casinoking-console.tsx")

    assert "showMines" not in overview_source
    assert "otherTitles" not in overview_source
    assert "title.engine_code === engineFilterCode" in overview_source
    assert "<GameCategoryView" in overview_source
    assert "engineCode={engineFilterCode}" in overview_source

    assert "handleDuplicateGameTitle" in console_source
    assert "handleDuplicateMinesTitle" not in console_source

    assert "Create ${engineDisplayName} variant from master" in category_source
    assert "GamePublicationBadges" in variant_list_source
    assert "onArchiveTitle" in variant_list_source
    assert "onRestoreTitle" in variant_list_source


def test_boxe_editor_is_registered_without_gameplay_logic() -> None:
    source = _read("frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx")

    assert "BoxeEngineEditor" in source
    assert "/admin/games/boxe/config" in source
    assert "startBoxeRound" not in source
    assert "revealPick" not in source
    assert "cashoutBoxeRound" not in source


def test_boxe_theme_and_title_presentation_follow_shared_contract() -> None:
    editor_source = _read("frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx")
    gameplay_source = _read("frontend/app/ui/boxe/boxe-gameplay.tsx")

    assert "body: JSON.stringify({ tokens: buildThemeDraftPayload() })" in editor_source
    assert "skin: themeDraftSkin ?? BOXE_ADVANCED_SKIN_DEFAULT" in editor_source
    assert "tokens: themeDraftTokens, skin:" not in editor_source

    assert 'const gameTitle = copy("game.title")' in gameplay_source
    assert "gameTitle={gameTitle}" in gameplay_source
    assert 'gameTitle="BOXE"' not in gameplay_source
