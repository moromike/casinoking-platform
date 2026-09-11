"""PASSO 5B — collaudi per la tabella unica di idempotenza.

Nati ROSSI prima della migrazione 0063, VERDI dopo.
"""

from __future__ import annotations

pytest_plugins = ["tests.fixtures.mines"]

from uuid import uuid4

from tests.concurrency._game_idempotency_helpers import auth_headers

import httpx


def _table_exists(cursor, name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s) AS t", (f"public.{name}",))
    return cursor.fetchone()["t"] is not None


def test_schema_una_sola_tabella(db_connection) -> None:
    """La tabella unica game_idempotency_keys esiste; le vecchie sono *_pref4."""
    with db_connection.cursor() as cursor:
        assert _table_exists(cursor, "game_idempotency_keys"), (
            "game_idempotency_keys non esiste"
        )
        assert not _table_exists(cursor, "boxe_idempotency_keys"), (
            "boxe_idempotency_keys dovrebbe essere rinominata in _pref4"
        )
        assert not _table_exists(cursor, "hi_lo_idempotency_keys"), (
            "hi_lo_idempotency_keys dovrebbe essere rinominata in _pref4"
        )
        assert not _table_exists(cursor, "mines_idempotency_keys"), (
            "mines_idempotency_keys dovrebbe essere rinominata in _pref4"
        )
        assert _table_exists(cursor, "boxe_idempotency_keys_pref4")
        assert _table_exists(cursor, "hi_lo_idempotency_keys_pref4")
        assert _table_exists(cursor, "mines_idempotency_keys_pref4")


def test_migrazione_preserva_tutte_le_righe(db_connection) -> None:
    """Rollback + forward in una transazione: ogni riga e' preservata.

    Indipendente dall'ordine di esecuzione degli altri test: opera su una
    transazione isolata con ROLLBACK finale.
    """
    from pathlib import Path

    migrations_dir = (
        Path(__file__).resolve().parents[2]
        / "backend" / "migrations" / "sql"
    )
    rollback_path = migrations_dir / "rollback" / "0063__retromarcia_game_idempotency_keys.sql"
    forward_path = migrations_dir / "0063__game_idempotency_keys.sql"

    def _strip_txn(sql: str) -> str:
        return "\n".join(
            line for line in sql.splitlines()
            if line.strip().upper() not in ("BEGIN;", "COMMIT;")
        )

    rollback_sql = _strip_txn(rollback_path.read_text(encoding="utf-8"))
    forward_sql = _strip_txn(forward_path.read_text(encoding="utf-8"))

    with db_connection.cursor() as cursor:
        cursor.execute("BEGIN")
        try:
            cursor.execute(
                """
                DELETE FROM game_idempotency_keys gik
                WHERE gik.round_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM boxe_rounds br
                      WHERE gik.game_code = 'boxe' AND br.id = gik.round_id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM hi_lo_rounds hr
                      WHERE gik.game_code = 'hi_lo' AND hr.id = gik.round_id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM mines_game_rounds mr
                      WHERE gik.game_code = 'mines' AND mr.id = gik.round_id
                  )
                """
            )
            cursor.execute(rollback_sql)
            cursor.execute(forward_sql)

            for old_table, game_code in [
                ("boxe_idempotency_keys_pref4", "boxe"),
                ("hi_lo_idempotency_keys_pref4", "hi_lo"),
                ("mines_idempotency_keys_pref4", "mines"),
            ]:
                cursor.execute(f"SELECT count(*) AS n FROM {old_table}")
                old_count = cursor.fetchone()["n"]
                cursor.execute(
                    "SELECT count(*) AS n FROM game_idempotency_keys WHERE game_code = %s",
                    (game_code,),
                )
                new_count = cursor.fetchone()["n"]
                assert new_count == old_count, (
                    f"{game_code}: nuova={new_count} != vecchia={old_count}"
                )

                cursor.execute(
                    f"""
                    SELECT count(*) AS missing
                    FROM {old_table} o
                    WHERE NOT EXISTS (
                        SELECT 1 FROM game_idempotency_keys n
                        WHERE n.game_code = %s
                          AND n.id = o.id
                          AND n.player_id = o.player_id
                          AND n.operation = o.operation
                          AND n.idempotency_key = o.idempotency_key
                          AND n.request_fingerprint = o.request_fingerprint
                          AND n.response_json = o.response_json
                    )
                    """,
                    (game_code,),
                )
                missing = cursor.fetchone()["missing"]
                assert missing == 0, (
                    f"{game_code}: {missing} righe di {old_table} non trovate nella nuova"
                )
        finally:
            cursor.execute("ROLLBACK")


def test_isolamento_tra_giochi_stessa_chiave(
    api_base_url, create_authenticated_player, db_connection,
) -> None:
    """Stessa (player, operation, key) su due giochi diversi: entrambe esistono."""
    player = create_authenticated_player(prefix="5b-iso")
    key = f"5b-iso-{uuid4().hex}"

    boxe_headers = auth_headers(str(player["access_token"]), idempotency_key=key)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        boxe_start = client.post(
            "/games/boxe/start",
            headers=boxe_headers,
            json={
                "title_code": "boxe001", "rows": 4, "difficulty": "easy",
                "bet_amount": "2", "wallet_source": "demo", "client_seed": key,
            },
        )
    assert boxe_start.status_code == 200, boxe_start.text

    hilo_headers = auth_headers(str(player["access_token"]), idempotency_key=key)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        hilo_start = client.post(
            "/games/hi-lo/start",
            headers=hilo_headers,
            json={
                "title_code": "hilo001", "bet_amount": "2",
                "wallet_source": "demo", "client_seed": key,
            },
        )
    assert hilo_start.status_code == 200, hilo_start.text

    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT game_code, count(*) AS n
            FROM game_idempotency_keys
            WHERE player_id = %s AND operation = 'start_round' AND idempotency_key = %s
            GROUP BY game_code
            """,
            (player["user_id"], key),
        )
        rows = cursor.fetchall()
        games = {row["game_code"] for row in rows}
        assert "boxe" in games, f"boxe missing: {rows}"
        assert "hi_lo" in games, f"hi_lo missing: {rows}"


def test_conflitto_fingerprint_per_gioco(
    api_base_url, create_authenticated_player,
) -> None:
    """Stessa chiave, payload diverso → 409 per ciascun gioco."""
    player = create_authenticated_player(prefix="5b-conflict")
    key = f"5b-conflict-{uuid4().hex}"
    headers = auth_headers(str(player["access_token"]), idempotency_key=key)

    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        first = client.post(
            "/games/boxe/start",
            headers=headers,
            json={
                "title_code": "boxe001", "rows": 4, "difficulty": "easy",
                "bet_amount": "2", "wallet_source": "demo", "client_seed": "seed-A",
            },
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/games/boxe/start",
            headers=headers,
            json={
                "title_code": "boxe001", "rows": 4, "difficulty": "easy",
                "bet_amount": "3", "wallet_source": "demo", "client_seed": "seed-B",
            },
        )
        assert second.status_code == 409, (
            f"Expected 409 for fingerprint conflict, got {second.status_code}: {second.text}"
        )


def test_rollback_in_transazione(db_connection) -> None:
    """Il SQL di rollback eseguito in una transazione che si annulla ripristina le 3 tabelle."""
    from pathlib import Path

    rollback_path = (
        Path(__file__).resolve().parents[2]
        / "backend" / "migrations" / "sql" / "rollback"
        / "0063__retromarcia_game_idempotency_keys.sql"
    )
    raw_sql = rollback_path.read_text(encoding="utf-8")
    rollback_sql = "\n".join(
        line for line in raw_sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )

    with db_connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(
            """
            DELETE FROM game_idempotency_keys gik
            WHERE gik.round_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM boxe_rounds br
                  WHERE gik.game_code = 'boxe' AND br.id = gik.round_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM hi_lo_rounds hr
                  WHERE gik.game_code = 'hi_lo' AND hr.id = gik.round_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM mines_game_rounds mr
                  WHERE gik.game_code = 'mines' AND mr.id = gik.round_id
              )
            """
        )
        cursor.execute(rollback_sql)
        assert _table_exists(cursor, "boxe_idempotency_keys"), (
            "boxe_idempotency_keys should be restored"
        )
        assert _table_exists(cursor, "hi_lo_idempotency_keys"), (
            "hi_lo_idempotency_keys should be restored"
        )
        assert _table_exists(cursor, "mines_idempotency_keys"), (
            "mines_idempotency_keys should be restored"
        )
        cursor.execute("ROLLBACK")

    with db_connection.cursor() as cursor:
        assert _table_exists(cursor, "game_idempotency_keys"), (
            "game_idempotency_keys should still exist after rollback"
        )
        assert not _table_exists(cursor, "boxe_idempotency_keys"), (
            "boxe_idempotency_keys should NOT exist after rollback"
        )


def test_cancella_round_poi_riprova_stessa_chiave(
    api_base_url, create_authenticated_player, db_connection,
) -> None:
    """Cancella un round, riprova con la stessa chiave: non riproduce un round fantasma."""
    player = create_authenticated_player(prefix="5b-delete-retry")
    key = f"5b-delete-retry-{uuid4().hex}"
    headers = auth_headers(str(player["access_token"]), idempotency_key=key)

    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        start = client.post(
            "/games/boxe/start",
            headers=headers,
            json={
                "title_code": "boxe001", "rows": 4, "difficulty": "easy",
                "bet_amount": "2", "wallet_source": "demo", "client_seed": key,
            },
        )
        assert start.status_code == 200, start.text
        round_id = start.json()["data"]["round_id"]

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.game_idempotency_keys') AS t")
        if cursor.fetchone()["t"] is not None:
            cursor.execute(
                "DELETE FROM game_idempotency_keys WHERE game_code = 'boxe' AND round_id = %s",
                (round_id,),
            )
        cursor.execute("DELETE FROM boxe_picks WHERE round_id = %s", (round_id,))
        cursor.execute("DELETE FROM boxe_rounds WHERE id = %s", (round_id,))

    headers2 = auth_headers(str(player["access_token"]), idempotency_key=key)
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        retry = client.post(
            "/games/boxe/start",
            headers=headers2,
            json={
                "title_code": "boxe001", "rows": 4, "difficulty": "easy",
                "bet_amount": "2", "wallet_source": "demo", "client_seed": key,
            },
        )
    assert retry.status_code == 200, retry.text
    new_round_id = retry.json()["data"]["round_id"]
    assert new_round_id != round_id, (
        "Retry with the same key must NOT return the deleted round"
    )

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT id FROM boxe_rounds WHERE id = %s", (round_id,))
        assert cursor.fetchone() is None, "Old round should still be deleted"


def test_mines_demo_replay_identico(
    api_base_url, create_authenticated_player,
) -> None:
    """Mines demo: prima risposta e replay sono IDENTICI campo per campo."""
    player = create_authenticated_player(prefix="5c-mines-demo")
    key = f"5c-mines-demo-{uuid4().hex}"
    headers = auth_headers(str(player["access_token"]), idempotency_key=key)
    payload = {
        "grid_size": 25,
        "mine_count": 3,
        "bet_amount": "2.000000",
        "wallet_type": "demo",
    }

    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        first = client.post("/games/mines/start", headers=headers, json=payload)
        assert first.status_code == 200, first.text
        first_data = first.json()

        replay = client.post("/games/mines/start", headers=headers, json=payload)
        assert replay.status_code == 200, replay.text
        replay_data = replay.json()

    assert first_data == replay_data, (
        f"Mines demo replay differs:\n"
        f"  first:  {first_data}\n"
        f"  replay: {replay_data}"
    )
    inner = first_data.get("data", first_data)
    for field in ("wallet_balance_after", "demo_event_id", "demo_play_session_id"):
        assert inner.get(field) is not None, (
            f"first response has {field}=None"
        )


def test_audit_orfani_zero(db_connection) -> None:
    """Nessun round_id orfano nella tabella unica (round che non esiste nel suo gioco)."""
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT count(*) AS orphans
            FROM game_idempotency_keys gik
            WHERE gik.round_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM boxe_rounds br
                  WHERE gik.game_code = 'boxe' AND br.id = gik.round_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM hi_lo_rounds hr
                  WHERE gik.game_code = 'hi_lo' AND hr.id = gik.round_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM mines_game_rounds mr
                  WHERE gik.game_code = 'mines' AND mr.id = gik.round_id
              )
            """
        )
        orphans = cursor.fetchone()["orphans"]
        assert orphans == 0, f"Found {orphans} orphan idempotency rows"
