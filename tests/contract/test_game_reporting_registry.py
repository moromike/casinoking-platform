from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_finance_replay_account_uses_reporting_registry() -> None:
    registry_source = _read("frontend/app/ui/game-reporting-registry.tsx")
    account_source = _read("frontend/app/ui/player-account-page.tsx")
    finance_source = _read("frontend/app/ui/admin-finance-panel.tsx")

    assert "GAME_REPORTING_REGISTRY" in registry_source
    for game_code in ["mines", "boxe", "hi_lo"]:
        assert f"{game_code}: {{" in registry_source

    assert "GAME_ACCOUNT_HISTORY_DESCRIPTORS.map" in account_source
    assert "readPlayerGameReplayEndpoint" in account_source
    assert "renderPlayerGameReplay" in account_source
    assert "readGameReportingDescriptor(session.game_code)" in account_source

    assert "hasAdminGameReplay(gameCode)" in finance_source
    assert "readAdminGameReplayEndpoint(gameCode, roundId)" in finance_source
    assert "renderAdminGameReplay(gameCode, replayState.replay)" in finance_source


def test_unknown_game_replay_is_unavailable_without_game_fallback() -> None:
    registry_source = _read("frontend/app/ui/game-reporting-registry.tsx")
    account_source = _read("frontend/app/ui/player-account-page.tsx")
    finance_source = _read("frontend/app/ui/admin-finance-panel.tsx")
    game_label_source = _read("frontend/app/ui/player-game-registry.ts")

    assert "return GAME_REPORTING_REGISTRY.mines" not in registry_source
    assert 'game_code: item.game_code ?? "mines"' not in account_source
    assert '"Unknown game"' in game_label_source
    assert "Replay unavailable for ${round.game_code}" in account_source
    assert "Replay unavailable for ${gameCode}" in finance_source
    assert "/games/mines/session/" not in account_source
    assert "/games/boxe/admin/round/" not in finance_source


def test_boxe_history_uses_wallet_source_without_cash_fallback() -> None:
    registry_source = _read("frontend/app/ui/game-reporting-registry.tsx")
    boxe_service_source = _read("backend/app/modules/games/boxe/service.py")

    assert 'wallet_type: "cash"' not in registry_source
    assert 'wallet_type: item.wallet_source ?? "legacy"' in registry_source
    assert "pr.wallet_type AS wallet_source" in boxe_service_source
    assert '"wallet_source": row.get("wallet_source") or "legacy"' in boxe_service_source


def test_no_frontend_finance_replay_fourth_branch_pattern() -> None:
    combined_source = "\n".join(
        [
            _read("frontend/app/ui/player-account-page.tsx"),
            _read("frontend/app/ui/admin-finance-panel.tsx"),
        ]
    )

    forbidden_fragments = [
        'gameCode === "boxe"',
        'gameCode === "hi_lo"',
        'round.game_code === "boxe"',
        'round.game_code === "hi_lo"',
        'session.game_code === "boxe"',
        'session.game_code === "hi_lo"',
        "readAdminReplayEndpoint",
        "renderAdminReplayViewer",
        "mapBoxeHistoryItem",
        "mapHiLoHistoryItem",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in combined_source


def test_backend_finance_account_dispatch_is_registry_based() -> None:
    admin_service_source = _read("backend/app/modules/admin/service.py")
    account_service_source = _read("backend/app/modules/account/service.py")
    access_session_source = _read("backend/app/modules/platform/access_sessions/service.py")

    assert "_GAME_ENRICHMENT_BUILDERS" in admin_service_source
    assert "_GAME_DETAIL_SUMMARY_BUILDERS" in account_service_source
    assert "_AUTO_SETTLE_ACTIVE_ROUND_HANDLERS" in access_session_source

    for source in [admin_service_source, account_service_source, access_session_source]:
        assert 'if game_code == "mines"' not in source
        assert 'if game_code == "boxe"' not in source
        assert 'if game_code == "hi_lo"' not in source
