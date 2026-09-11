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

_MIGRATION_0063_PATH = Path("backend/migrations/sql/0063__game_idempotency_keys.sql")
_ROLLBACK_0063_PATH = Path(
    "backend/migrations/sql/rollback/0063__retromarcia_game_idempotency_keys.sql"
)

_LEGACY_IDEMPOTENCY_TABLES = (
    "boxe_idempotency_keys",
    "hi_lo_idempotency_keys",
    "mines_idempotency_keys",
)

# Solo DROP: prima dei DROP gira il rollback VERO di 0063 (vedi
# drop_boxe_schema / drop_hi_lo_schema), che riversa le righe vive della
# tabella unica nelle tabelle legacy. Le chiavi del gioco quindi non restano
# MAI nella tabella condivisa quando i suoi round vengono droppati.
BOXE_SCHEMA_DROP_SQL = """
DROP TABLE IF EXISTS boxe_idempotency_keys_pref4;
DROP TABLE IF EXISTS boxe_idempotency_keys;
DROP TABLE IF EXISTS boxe_picks;
DROP TABLE IF EXISTS boxe_rounds;
"""

HI_LO_SCHEMA_DROP_SQL = """
DROP TABLE IF EXISTS hi_lo_idempotency_keys_pref4;
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


def _strip_txn(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


def _table_exists(cursor, name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s) AS t", (f"public.{name}",))
    return cursor.fetchone()["t"] is not None


def _esegui_rollback_0063_se_serve(cursor) -> None:
    """Se il mondo e' post-0063 esegue il file di rollback VERO: le righe vive
    della tabella unica tornano nelle tre tabelle legacy (politica orfani
    dichiarata in testa al file) prima di qualunque DROP di round."""
    if not _table_exists(cursor, "game_idempotency_keys"):
        return
    mancanti = [
        f"{t}_pref4" for t in _LEGACY_IDEMPOTENCY_TABLES
        if not _table_exists(cursor, f"{t}_pref4")
    ]
    if mancanti:
        raise RuntimeError(
            "Schema incoerente: game_idempotency_keys esiste ma mancano le "
            f"tabelle {mancanti}; il rollback vero di 0063 non puo' girare"
        )
    cursor.execute(_strip_txn(_ROLLBACK_0063_PATH.read_text(encoding="utf-8")))


def _applica_0063_vero(cursor) -> None:
    """Esegue il SQL VERO della migrazione 0063 (senza BEGIN/COMMIT: il
    chiamante sceglie la transazione). Richiede il mondo pre-0063: le tre
    tabelle legacy presenti e la tabella unica assente — niente DDL duplicato,
    lo stato finale e' quello del migratore vero."""
    mancanti = [
        t for t in _LEGACY_IDEMPOTENCY_TABLES if not _table_exists(cursor, t)
    ]
    if mancanti:
        raise RuntimeError(
            f"0063 non eseguibile: mancano le tabelle legacy {mancanti}"
        )
    if _table_exists(cursor, "game_idempotency_keys"):
        raise RuntimeError(
            "0063 non eseguibile: game_idempotency_keys esiste gia'"
        )
    cursor.execute(_strip_txn(_MIGRATION_0063_PATH.read_text(encoding="utf-8")))


def drop_boxe_schema(connection) -> None:
    with connection.cursor() as cursor:
        _esegui_rollback_0063_se_serve(cursor)
        cursor.execute(BOXE_SCHEMA_DROP_SQL)


def drop_hi_lo_schema(connection) -> None:
    with connection.cursor() as cursor:
        _esegui_rollback_0063_se_serve(cursor)
        cursor.execute(HI_LO_SCHEMA_DROP_SQL)


def apply_boxe_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        _esegui_rollback_0063_se_serve(cursor)
        cursor.execute("DROP TABLE IF EXISTS boxe_idempotency_keys_pref4 CASCADE")
        cursor.execute("DROP TABLE IF EXISTS boxe_idempotency_keys CASCADE")
        for migration_path in BOXE_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_BOXE_CANONICAL_CONSTRAINTS_SQL)
        _applica_0063_vero(cursor)


def apply_hi_lo_schema_migrations(connection) -> None:
    with connection.cursor() as cursor:
        _esegui_rollback_0063_se_serve(cursor)
        cursor.execute("DROP TABLE IF EXISTS hi_lo_idempotency_keys_pref4 CASCADE")
        cursor.execute("DROP TABLE IF EXISTS hi_lo_idempotency_keys CASCADE")
        for migration_path in HI_LO_SCHEMA_MIGRATION_PATHS:
            cursor.execute(migration_path.read_text(encoding="utf-8"))
        cursor.execute(_HI_LO_CANONICAL_CONSTRAINTS_SQL)
        _applica_0063_vero(cursor)


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
    table_budget_amount: str | None = None,
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

    table_session_id: str | None = None
    if table_budget_amount is not None:
        table_response = client.post(
            f"{prefisso}/table-sessions",
            headers=headers,
            json={
                "game_code": "manichino",
                "title_code": "manichino_test",
                "site_code": "casinoking",
                "wallet_type": "cash",
                "table_budget_amount": table_budget_amount,
                "access_session_id": access_session_id,
            },
        )
        assert table_response.status_code == 200, (
            "Creazione table session cavia fallita: "
            f"{table_response.status_code} {table_response.text}"
        )
        table_session_id = str(table_response.json()["data"]["id"])

    start_payload = {
        "bet_amount": bet_amount,
        "wallet_type": "cash",
        "access_session_id": access_session_id,
    }
    if table_session_id is not None:
        start_payload["table_session_id"] = table_session_id

    start_response = client.post(
        f"{prefisso}/games/manichino/start",
        headers={
            **headers,
            "X-Game-Launch-Token": game_launch_token,
            "Idempotency-Key": f"{prefisso_idempotenza}-start-{uuid4().hex}",
        },
        json=start_payload,
    )
    assert start_response.status_code == 200, (
        f"Apertura partita cavia fallita: {start_response.status_code} {start_response.text}"
    )
    game_session_id = str(start_response.json()["data"]["game_session_id"])

    dati_apertura = start_response.json()["data"]
    # PERCHE' SI RESTITUISCONO ANCHE QUESTI DUE. Senza, un collaudo che vuole verificare
    # che una lettura di piattaforma dica LA STESSA COSA dell'apertura non ha con cosa
    # confrontarla, e finisce per ripiegare su un controllo debole del tipo "e' una
    # stringa" — che passa il conteggio delle asserzioni ed e' un annacquamento.
    # Successo davvero, in test_admin_session_drilldown.py, e trovato dalla revisione
    # indipendente e non dal conteggio.
    return {
        "game_launch_token": game_launch_token,
        "access_session_id": access_session_id,
        "game_session_id": game_session_id,
        "table_session_id": str(dati_apertura["table_session_id"]),
        "ledger_transaction_id": str(dati_apertura["ledger_transaction_id"]),
        "wallet_balance_after_start": str(dati_apertura["wallet_balance_after_start"]),
        "idempotency_key": f"{prefisso_idempotenza}-start-",
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
