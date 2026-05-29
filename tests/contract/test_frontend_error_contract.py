from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_api_request_error_preserves_platform_diagnostics_and_nested_detail_envelope() -> None:
    source = _read("frontend-v3/app/lib/api.ts")
    types_source = _read("frontend-v3/app/lib/types.ts")

    assert "supportId?: string" in source
    assert "requestId?: string" in source
    assert "retryable?: boolean" in source
    assert "details?: unknown" in source
    assert "readPlatformError(payload)" in source
    assert "isNestedErrorEnvelope(payload.detail)" in source
    assert "extractValidationMessage(payload.detail)" in source
    assert "support_id?: string" in types_source
    assert "request_id?: string" in types_source
    assert "retryable?: boolean" in types_source


def test_shared_game_action_error_and_mines_render_compact_diagnostic_line() -> None:
    action_error_source = _read("frontend-v3/app/ui/game-runtime/game-action-error.tsx")
    runtime_css_source = _read("frontend-v3/app/ui/game-runtime/game-runtime.css")
    mines_source = _read("frontend-v3/app/ui/mines/mines-standalone.tsx")
    boxe_source = _read("frontend-v3/app/ui/boxe/boxe-gameplay.tsx")
    hi_lo_source = _read("frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx")

    assert "GameErrorDiagnosticLine" in action_error_source
    assert "game-error-diagnostic-line" in action_error_source
    assert "Codice:" in action_error_source
    assert "Supporto:" in action_error_source
    assert ".game-error-diagnostic-line" in runtime_css_source
    assert "GameErrorDiagnosticLine" in mines_source
    assert "statusDiagnostic" in mines_source
    assert "code={errorDiagnostic?.code}" in boxe_source
    assert "code={errorDiagnostic?.code}" in hi_lo_source
