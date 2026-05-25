from app.modules.platform.ledger_metadata import (
    METADATA_COMPLETENESS_COMPLETE,
    METADATA_COMPLETENESS_LEGACY,
    METADATA_COMPLETENESS_PARTIAL,
    build_forward_ledger_metadata,
    classify_metadata_completeness,
)


def test_forward_ledger_metadata_complete_for_terminal_settlement() -> None:
    metadata = build_forward_ledger_metadata(
        game_code="boxe",
        title_code="boxe001",
        site_code="casinoking",
        wallet_type="bonus",
        platform_round_id="round-1",
        game_round_id="round-1",
        access_session_id="access-1",
        settlement_kind="auto_cashout",
        idempotency_key="boxe:timeout:user:access:round",
        replay_ref={"game_code": "boxe", "round_id": "round-1"},
        game_config_payload={"rows": 8, "difficulty": "hard"},
        progress_payload={"safe_picks_count": 3},
    )

    assert metadata["metadata_schema_version"] == 2
    assert metadata["metadata_completeness"] == METADATA_COMPLETENESS_COMPLETE
    assert metadata["settlement_kind"] == "auto_cashout"
    assert metadata["wallet_type"] == "bonus"
    assert metadata["idempotency_key_hash"] != "boxe:timeout:user:access:round"
    assert metadata["game_config_payload"] == {"rows": 8, "difficulty": "hard"}


def test_forward_ledger_metadata_marks_open_bet_partial_and_old_rows_legacy() -> None:
    metadata = build_forward_ledger_metadata(
        game_code="mines",
        title_code="mines_classic",
        site_code="casinoking",
        wallet_type="cash",
        platform_round_id="round-1",
        game_round_id="round-1",
        access_session_id=None,
        settlement_kind=None,
        idempotency_key="mines:start:user:key",
        replay_ref=None,
    )

    assert metadata["metadata_completeness"] == METADATA_COMPLETENESS_PARTIAL
    assert classify_metadata_completeness({"game_code": "mines"}) == METADATA_COMPLETENESS_LEGACY
