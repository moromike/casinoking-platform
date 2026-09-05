import pytest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_finance_replay_account_uses_reporting_registry() -> None:
    registry_source = _read("frontend-v3/app/ui/game-reporting-registry.tsx")
    account_source = _read("frontend-v3/app/ui/player-account-page.tsx")
    finance_source = _read("frontend-v3/app/ui/admin-finance-panel.tsx")

    assert "GAME_REPORTING_REGISTRY" in registry_source
    for game_code in ["mines", "boxe", "hi_lo"]:
        assert f"{game_code}: {{" in registry_source
    for runtime_descriptor_field in [
        "payoutRuntimeSource",
        "mathSource",
        "rtpSource",
        "replayVerificationSource",
        "specPaths",
    ]:
        assert runtime_descriptor_field in registry_source

    assert "GAME_ACCOUNT_HISTORY_DESCRIPTORS.map" in account_source
    assert "readPlayerGameReplayEndpoint" in account_source
    assert "renderPlayerGameReplay" in account_source
    assert "readGameReportingDescriptor(session.game_code)" in account_source

    assert "hasAdminGameReplay(gameCode)" in finance_source
    assert "readAdminGameReplayEndpoint(gameCode, roundId)" in finance_source
    assert "renderAdminGameReplay(gameCode, replayState.replay)" in finance_source


def test_unknown_game_replay_is_unavailable_without_game_fallback() -> None:
    registry_source = _read("frontend-v3/app/ui/game-reporting-registry.tsx")
    account_source = _read("frontend-v3/app/ui/player-account-page.tsx")
    finance_source = _read("frontend-v3/app/ui/admin-finance-panel.tsx")
    game_label_source = _read("frontend-v3/app/ui/player-game-registry.ts")

    assert "return GAME_REPORTING_REGISTRY.mines" not in registry_source
    assert 'game_code: item.game_code ?? "mines"' not in account_source
    assert '"Unknown game"' in game_label_source
    assert "Replay unavailable for ${round.game_code}" in account_source
    assert "Replay unavailable for ${gameCode}" in finance_source
    assert "/games/mines/session/" not in account_source
    assert "/games/boxe/admin/round/" not in finance_source


def test_boxe_history_uses_wallet_source_without_cash_fallback() -> None:
    registry_source = _read("frontend-v3/app/ui/game-reporting-registry.tsx")
    boxe_service_source = _read("backend/app/modules/games/boxe/service.py")
    boxe_repository_source = _read("backend/app/modules/games/boxe/repository.py")

    assert 'wallet_type: "cash"' not in registry_source
    assert 'wallet_type: item.wallet_source ?? "legacy"' in registry_source
    assert "pr.wallet_type" in boxe_repository_source
    assert "AS wallet_source" in boxe_repository_source
    assert '"wallet_source": row.get("wallet_source") or "legacy"' in boxe_service_source


def test_no_frontend_finance_replay_fourth_branch_pattern() -> None:
    combined_source = "\n".join(
        [
            _read("frontend-v3/app/ui/player-account-page.tsx"),
            _read("frontend-v3/app/ui/admin-finance-panel.tsx"),
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
    liquidation_registry_source = _read(
        "backend/app/modules/platform/access_sessions/registro_liquidazione.py"
    )

    assert "_GAME_ENRICHMENT_BUILDERS" in admin_service_source
    assert "_GAME_DETAIL_SUMMARY_BUILDERS" in account_service_source
    assert "cerca_liquidazione" in access_session_source
    assert "def registra_liquidazione" in liquidation_registry_source
    assert "def cerca_liquidazione" in liquidation_registry_source

    for source in [admin_service_source, account_service_source]:
        assert 'if game_code == "mines"' not in source
        assert 'if game_code == "boxe"' not in source
        assert 'if game_code == "hi_lo"' not in source

    # PERCHE' L'ELENCO SI RICAVA DAI GIOCHI INSTALLATI e non si scrive a mano: una
    # lista fissa protegge solo i giochi che c'erano il giorno in cui e' stata scritta.
    # Domani un `if game_code == "manichino"` dentro il servizio di piattaforma
    # passerebbe indisturbato, ed e' esattamente il difetto che questa fase sta curando.
    giochi_installati = sorted(
        percorso.name
        for percorso in (ROOT / "backend" / "app" / "modules" / "games").iterdir()
        if percorso.is_dir() and not percorso.name.startswith("__")
    )
    assert giochi_installati, "nessun gioco trovato: il controllo non varrebbe niente"

    for game_code in giochi_installati:
        for forbidden_game_name in (
            f'"{game_code}"',
            f"GAME_CODE_{game_code.upper()}",
        ):
            assert forbidden_game_name not in access_session_source, (
                f"{forbidden_game_name} compare in access_sessions/service.py: la "
                "piattaforma e' tornata a conoscere un gioco per nome."
            )
