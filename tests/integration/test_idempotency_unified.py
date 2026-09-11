"""PASSO 5B — collaudi per la tabella unica di idempotenza.

Nati ROSSI prima della migrazione 0063, VERDI dopo.
"""

from __future__ import annotations

pytest_plugins = ["tests.fixtures.mines"]

import json as _json
from pathlib import Path
from uuid import uuid4

from tests.concurrency._game_idempotency_helpers import auth_headers

import httpx

_MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[2] / "backend" / "migrations" / "sql"
)
_ROLLBACK_0063_PATH = (
    _MIGRATIONS_DIR / "rollback" / "0063__retromarcia_game_idempotency_keys.sql"
)
_FORWARD_0063_PATH = _MIGRATIONS_DIR / "0063__game_idempotency_keys.sql"

_GIOCHI = (
    ("boxe", "boxe_idempotency_keys"),
    ("hi_lo", "hi_lo_idempotency_keys"),
    ("mines", "mines_idempotency_keys"),
)


def _strip_txn(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


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
    """Conservazione con SENTINELLE note; il rollback e' verificato PRIMA del forward.

    In UNA transazione (ROLLBACK finale, nessun effetto sul DB):
    1. per ogni gioco: una sentinella pre-switch in *_pref4 con copia identica
       nella tabella unica (come una riga migrata), e una sentinella
       post-switch solo nella tabella unica (id nuovo);
    2. si esegue il SQL di rollback VERO: le tre tabelle tornano e devono
       contenere entrambe le sentinelle, con contatori NON nulli;
    3. si riesegue il forward 0063 VERO: ogni riga legacy deve essere nella
       tabella unica con valori identici, contatori NON nulli.

    Nessun dato esistente viene cancellato. Le sentinelle hanno round_id NULL:
    nessun orfano creato. Gli orfani nel riversamento seguono la politica
    dichiarata in testa al file di rollback (esclusi, con WARNING).
    """
    rollback_sql = _strip_txn(_ROLLBACK_0063_PATH.read_text(encoding="utf-8"))
    forward_sql = _strip_txn(_FORWARD_0063_PATH.read_text(encoding="utf-8"))

    sentinelle: dict[str, dict[str, dict[str, object]]] = {}

    with db_connection.cursor() as cursor:
        cursor.execute("BEGIN")
        try:
            for game_code, legacy in _GIOCHI:
                player = uuid4()
                pre = {
                    "id": uuid4(), "player": player,
                    "key": f"sent-pre-{game_code}-{uuid4().hex}",
                    "fp": f"fp-pre-{uuid4().hex}",
                    "resp": {"sentinella": f"pre-{game_code}"},
                }
                post = {
                    "id": uuid4(), "player": player,
                    "key": f"sent-post-{game_code}-{uuid4().hex}",
                    "fp": f"fp-post-{uuid4().hex}",
                    "resp": {"sentinella": f"post-{game_code}"},
                }
                sentinelle[game_code] = {"pre": pre, "post": post}
                # pre-switch: stessa riga nella tabella congelata e nella unica
                cursor.execute(
                    f"""
                    INSERT INTO {legacy}_pref4
                        (id, player_id, round_id, operation, idempotency_key,
                         request_fingerprint, response_json)
                    VALUES (%s, %s, NULL, 'start_round', %s, %s, %s::jsonb)
                    """,
                    (str(pre["id"]), str(player), pre["key"], pre["fp"],
                     _json.dumps(pre["resp"])),
                )
                for s in (pre, post):
                    cursor.execute(
                        """
                        INSERT INTO game_idempotency_keys
                            (id, game_code, player_id, round_id, operation,
                             idempotency_key, request_fingerprint, response_json)
                        VALUES (%s, %s, %s, NULL, 'start_round', %s, %s, %s::jsonb)
                        """,
                        (str(s["id"]), game_code, str(player), s["key"],
                         s["fp"], _json.dumps(s["resp"])),
                    )

            # contatori attesi dopo il rollback: pref4 (incl. sentinella pre)
            # piu' la sentinella post riversata dalla tabella unica
            attesi: dict[str, int] = {}
            for game_code, legacy in _GIOCHI:
                cursor.execute(f"SELECT count(*) AS n FROM {legacy}_pref4")
                attesi[game_code] = int(cursor.fetchone()["n"]) + 1

            # 2. ROLLBACK VERO
            cursor.execute(rollback_sql)
            for game_code, legacy in _GIOCHI:
                cursor.execute(f"SELECT count(*) AS n FROM {legacy}")
                n = int(cursor.fetchone()["n"])
                assert n == attesi[game_code], (
                    f"{game_code}: dopo il rollback {legacy} ha {n} righe, "
                    f"attese {attesi[game_code]}"
                )
                assert n > 0, f"{game_code}: contatore nullo, collaudo non probante"
                for kind in ("pre", "post"):
                    s = sentinelle[game_code][kind]
                    cursor.execute(
                        f"""
                        SELECT player_id, request_fingerprint, response_json
                        FROM {legacy} WHERE id = %s
                        """,
                        (str(s["id"]),),
                    )
                    row = cursor.fetchone()
                    assert row is not None, (
                        f"{game_code}: sentinella {kind} persa nel rollback"
                    )
                    assert str(row["player_id"]) == str(s["player"])
                    assert row["request_fingerprint"] == s["fp"]
                    assert row["response_json"] == s["resp"]

            # 3. FORWARD VERO (0063)
            cursor.execute(forward_sql)
            for game_code, legacy in _GIOCHI:
                cursor.execute(
                    "SELECT count(*) AS n FROM game_idempotency_keys WHERE game_code = %s",
                    (game_code,),
                )
                new_count = int(cursor.fetchone()["n"])
                cursor.execute(f"SELECT count(*) AS n FROM {legacy}_pref4")
                old_count = int(cursor.fetchone()["n"])
                assert new_count == old_count, (
                    f"{game_code}: nuova={new_count} != vecchia={old_count}"
                )
                assert new_count > 0, (
                    f"{game_code}: contatore nullo, collaudo non probante"
                )
                cursor.execute(
                    f"""
                    SELECT count(*) AS missing
                    FROM {legacy}_pref4 o
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
                missing = int(cursor.fetchone()["missing"])
                assert missing == 0, (
                    f"{game_code}: {missing} righe di {legacy}_pref4 non trovate "
                    "nella tabella unica"
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
    rollback_sql = _strip_txn(_ROLLBACK_0063_PATH.read_text(encoding="utf-8"))

    with db_connection.cursor() as cursor:
        cursor.execute("BEGIN")
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


def test_rollback_riga_viva_sostituisce_congelata(db_connection) -> None:
    """Conflitto logico nel rollback: vince la riga VIVA, non quella congelata.

    Sequenza (in UNA transazione, ROLLBACK finale):
    riga pre-0063 (in *_pref4 e nella tabella unica) → chiave cancellata dalla
    tabella unica → stessa chiave riusata (riga NUOVA, id diverso, stessa
    UNIQUE logica player/operation/key) → rollback VERO → la tabella vecchia
    deve contenere la riga NUOVA, non quella congelata.
    """
    rollback_sql = _strip_txn(_ROLLBACK_0063_PATH.read_text(encoding="utf-8"))

    player_id = uuid4()
    key = f"5bc-rollback-{uuid4().hex}"
    old_id, new_id = uuid4(), uuid4()

    with db_connection.cursor() as cursor:
        cursor.execute("BEGIN")
        try:
            # riga pre-0063: congelata in *_pref4 e copiata nella tabella unica
            cursor.execute(
                """
                INSERT INTO boxe_idempotency_keys_pref4
                    (id, player_id, round_id, operation, idempotency_key,
                     request_fingerprint, response_json)
                VALUES (%s, %s, NULL, 'start_round', %s, 'fp-vecchia', %s::jsonb)
                """,
                (str(old_id), str(player_id), key, _json.dumps({"v": "vecchia"})),
            )
            cursor.execute(
                """
                INSERT INTO game_idempotency_keys
                    (id, game_code, player_id, round_id, operation,
                     idempotency_key, request_fingerprint, response_json)
                VALUES (%s, 'boxe', %s, NULL, 'start_round', %s, 'fp-vecchia', %s::jsonb)
                """,
                (str(old_id), str(player_id), key, _json.dumps({"v": "vecchia"})),
            )
            # cancellazione della chiave (round_id NULL: nessun round toccato)
            cursor.execute(
                "DELETE FROM game_idempotency_keys WHERE id = %s", (str(old_id),)
            )
            # riuso della stessa chiave: riga NUOVA, stessa UNIQUE logica
            cursor.execute(
                """
                INSERT INTO game_idempotency_keys
                    (id, game_code, player_id, round_id, operation,
                     idempotency_key, request_fingerprint, response_json)
                VALUES (%s, 'boxe', %s, NULL, 'start_round', %s, 'fp-nuova', %s::jsonb)
                """,
                (str(new_id), str(player_id), key, _json.dumps({"v": "nuova"})),
            )

            cursor.execute(rollback_sql)

            cursor.execute(
                """
                SELECT id, request_fingerprint, response_json
                FROM boxe_idempotency_keys
                WHERE player_id = %s AND operation = 'start_round'
                  AND idempotency_key = %s
                """,
                (str(player_id), key),
            )
            rows = cursor.fetchall()
            assert len(rows) == 1, (
                f"attesa 1 riga per la chiave, trovate {len(rows)}: {rows}"
            )
            assert str(rows[0]["id"]) == str(new_id), (
                f"il rollback ha tenuto la riga congelata {rows[0]['id']} "
                f"invece di quella viva {new_id}"
            )
            assert rows[0]["request_fingerprint"] == "fp-nuova"
            assert rows[0]["response_json"] == {"v": "nuova"}
        finally:
            cursor.execute("ROLLBACK")


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
