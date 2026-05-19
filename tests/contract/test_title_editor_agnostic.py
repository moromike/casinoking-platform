from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_engine_editor_registry_is_whitelist_based_and_lazy() -> None:
    source = _read("frontend/app/ui/title-editor/engine-editor-registry.ts")

    assert "REGISTERED_ENGINE_EDITORS" in source
    assert "mines:" in source
    assert "boxe:" in source
    assert "dynamic<EngineEditorProps<unknown>>" in source
    assert "import { MinesEngineEditor" not in source
    assert "import { BoxeEngineEditor" not in source
    assert "Unsupported" not in source


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


def test_boxe_editor_is_registered_without_gameplay_logic() -> None:
    source = _read("frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx")

    assert "BoxeEngineEditor" in source
    assert "/admin/games/boxe/config" in source
    assert "startBoxeRound" not in source
    assert "revealPick" not in source
    assert "cashoutBoxeRound" not in source
