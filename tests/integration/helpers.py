from __future__ import annotations

from pathlib import Path
from uuid import uuid4

BOXE_SCHEMA_MIGRATION_PATHS = (
    Path("backend/migrations/sql/0039__boxe_session_tables.sql"),
    Path("backend/migrations/sql/0047__boxe_demo_session_id.sql"),
    Path("backend/migrations/sql/0048__boxe_drop_sessions.sql"),
)

HI_LO_SCHEMA_MIGRATION_PATHS = (
    Path("backend/migrations/sql/0043__hi_lo_round_tables.sql"),
)

BOXE_SCHEMA_DOWN_SQL = """
DROP TABLE IF EXISTS boxe_idempotency_keys;
DROP TABLE IF EXISTS boxe_picks;
DROP TABLE IF EXISTS boxe_rounds;
"""

HI_LO_SCHEMA_DOWN_SQL = """
DROP TABLE IF EXISTS hi_lo_idempotency_keys;
DROP TABLE IF EXISTS hi_lo_actions;
DROP TABLE IF EXISTS hi_lo_rounds;
"""

# Canonical BOXE constraints (equivalent to the BOXE sections of 0051 + 0052).
# Applied per-game so that each helper leaves the schema canonical without
# requiring the other game's tables to exist.
_BOXE_CANONICAL_CONSTRAINTS_SQL = """
ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_status_check;
ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'row_revealed',
            'cashout_pending',
            'completed_cashout',
            'completed_top_row',
            'failed_mine',
            'expired',
            'quarantined',
            'cancelled'
        ));

ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_closed_at_consistency_check;
ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'row_revealed', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'completed_top_row', 'failed_mine', 'expired', 'quarantined', 'cancelled') AND closed_at IS NOT NULL)
        );

ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_outcome_check;
ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'top_row', 'loss', 'expired', 'quarantined', 'admin_force_close')
        );

ALTER TABLE boxe_idempotency_keys
    DROP CONSTRAINT IF EXISTS boxe_idempotency_keys_player_id_fkey;
"""

# Canonical HI-LO constraints (equivalent to the HI-LO sections of 0051 + 0052).
_HI_LO_CANONICAL_CONSTRAINTS_SQL = """
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_status_check;
ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'cashout_pending',
            'completed_cashout',
            'failed_prediction',
            'expired',
            'quarantined',
            'cancelled'
        ));

ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_closed_at_consistency_check;
ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'failed_prediction', 'expired', 'quarantined', 'cancelled') AND closed_at IS NOT NULL)
        );

ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_outcome_check;
ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'loss', 'expired', 'quarantined', 'admin_force_close')
        );

ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_player_id_fkey;
ALTER TABLE hi_lo_idempotency_keys
    DROP CONSTRAINT IF EXISTS hi_lo_idempotency_keys_player_id_fkey;
"""


def apply_boxe_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in BOXE_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_BOXE_CANONICAL_CONSTRAINTS_SQL)


def apply_hi_lo_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        for migration_path in HI_LO_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_HI_LO_CANONICAL_CONSTRAINTS_SQL)


def create_game_access_session(
    client,
    headers,
    *,
    game_code: str,
    title_code: str,
    site_code: str = "casinoking",
) -> str:
    """Create a game access session and return its id."""
    resp = client.post(
        "/access-sessions",
        headers=headers,
        json={
            "game_code": game_code,
            "title_code": title_code,
            "site_code": site_code,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


def apri_partita_cavia(
    client,
    headers,
    *,
    bet_amount: str = "1.000000",
    prefisso_idempotenza: str,
    prefisso: str = "",
) -> dict[str, str]:
    """Emette il gettone e apre una partita reale del manichino di collaudo."""
    # PERCHE' il prefisso e' esplicito: il client HTTP live ha gia' `/api/v1` nella
    # base URL, mentre il TestClient in-processo parte dalla radice. Indovinarlo dal
    # client trasformerebbe un 404 di routing in un falso difetto di catalogo.
    token_response = client.post(
        f"{prefisso}/games/manichino/launch-token",
        headers=headers,
        json={},
    )
    assert token_response.status_code == 200, (
        f"Emissione gettone cavia fallita: {token_response.status_code} {token_response.text}"
    )
    game_launch_token = str(token_response.json()["data"]["game_launch_token"])

    access_response = client.post(
        f"{prefisso}/access-sessions",
        headers=headers,
        json={
            "game_code": "manichino",
            "title_code": "manichino_test",
            "site_code": "casinoking",
        },
    )
    assert access_response.status_code == 200, (
        f"Creazione access session cavia fallita: {access_response.status_code} {access_response.text}"
    )
    access_session_id = str(access_response.json()["data"]["id"])

    start_response = client.post(
        f"{prefisso}/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"{prefisso_idempotenza}-start-{uuid4().hex}",
        },
        json={
            "bet_amount": bet_amount,
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200, (
        f"Apertura partita cavia fallita: {start_response.status_code} {start_response.text}"
    )
    game_session_id = str(start_response.json()["data"]["game_session_id"])

    return {
        "game_launch_token": game_launch_token,
        "access_session_id": access_session_id,
        "game_session_id": game_session_id,
    }


def chiudi_partita_cavia(
    client,
    headers,
    *,
    game_launch_token: str,
    game_session_id: str,
    esito: str = "vincita",
    payout_amount: str | None = None,
    prefisso_idempotenza: str = "cavia",
    prefisso: str = "",
):
    """Chiude una partita del manichino, mantenendo il gettone della sua apertura."""
    payload = {
        "game_session_id": game_session_id,
        "esito": esito,
    }
    if payout_amount is not None:
        payload["payout_amount"] = payout_amount
    response = client.post(
        f"{prefisso}/games/manichino/settle",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"{prefisso_idempotenza}-settle-{uuid4().hex}",
        },
        json=payload,
    )
    assert response.status_code == 200, (
        f"Chiusura partita cavia fallita: {response.status_code} {response.text}"
    )
    return response
