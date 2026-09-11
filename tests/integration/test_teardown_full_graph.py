from __future__ import annotations

# PERCHE' QUESTO COLLAUDO ESISTE (4C-bis, 11/09/2026): la versione precedente
# finiva con `assert True` e non poteva fallire. Questa costruisce davvero un
# utente con record collegati in tutte le tabelle del grafo di pulizia, esegue
# la pulizia del coordinatore ESPLICITAMENTE a meta' prova
# (UserCleanupCoordinator.execute_cleanup) e poi VERIFICA con query che non resti
# nessuna riga di quell'utente. Se un passo di cancellazione del coordinatore
# viene disattivato, questo collaudo diventa rosso (dimostrato nel rapporto del
# passo: missioni/2026-09-11-passo5/03-lavoro/R-fix-4C-kimi.md).

pytest_plugins = ["tests.fixtures.mines"]

from uuid import uuid4

from tests.integration.helpers import (
    apri_partita_cavia,
    chiudi_partita_cavia,
    create_game_access_session,
)


# tabella -> predicato che lega la riga all'utente (%s = user_id)
GRAPH_TABLES = [
    ("users", "id = %s"),
    ("user_credentials", "user_id = %s"),
    ("admin_profiles", "user_id = %s"),
    ("wallet_accounts", "user_id = %s"),
    ("ledger_accounts", "owner_user_id = %s"),
    ("ledger_transactions", "user_id = %s"),
    ("platform_rounds", "user_id = %s"),
    ("game_access_sessions", "user_id = %s"),
    ("game_table_sessions", "user_id = %s"),
    ("demo_play_sessions", "user_id = %s"),
    ("access_logs", "user_id = %s"),
    ("password_reset_tokens", "user_id = %s"),
    ("mines_game_rounds", "user_id = %s"),
    ("game_idempotency_keys", "player_id = %s"),
]

# tabelle in cui il collaudo DEVE aver creato almeno una riga prima della
# pulizia: senza questa verifica, un "dopo == 0" potrebbe essere un grafo mai
# costruito, cioe' di nuovo un collaudo che non puo' fallire.
MUST_HAVE_ROWS = {table for table, _ in GRAPH_TABLES}


def _count_for_user(db_connection, table: str, predicate: str, user_id: str) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE {predicate}", (user_id,))
        row = cursor.fetchone()
    assert row is not None
    return int(row["count"])


def test_teardown_full_graph_works(
    client,
    db_connection,
    create_authenticated_player,
    mines_auth_headers,
    user_cleanup_coordinator,
) -> None:
    player = create_authenticated_player(prefix="teardown-graph")
    user_id = str(player["user_id"])
    # Stampato apposta: se una prova di fallimento lascia righe nel database
    # condiviso, questo e' il dato che serve a rimuoverle a mano.
    print(f"TEARDOWN-GRAPH user_id={user_id} email={player['email']}")

    plain_headers = {"Authorization": f"Bearer {player['access_token']}"}

    # 1. Partita manichino completa con table session: game_access_sessions,
    #    game_table_sessions, platform_rounds, ledger_transactions/entries,
    #    movimenti su wallet_accounts.
    cavia = apri_partita_cavia(
        client,
        plain_headers,
        bet_amount="1.000000",
        table_budget_amount="10.000000",
        prefisso_idempotenza="teardown-graph-cavia",
    )
    chiudi_partita_cavia(
        client,
        plain_headers,
        game_launch_token=cavia["game_launch_token"],
        game_session_id=cavia["game_session_id"],
        esito="vincita",
        payout_amount="2.000000",
        prefisso_idempotenza="teardown-graph-cavia",
    )

    # 2. Round Mines reale lasciato aperto: mines_game_rounds,
    #    mines_idempotency_keys, platform_rounds, ledger.
    mines_headers = mines_auth_headers(player["access_token"])
    mines_title_code = mines_auth_headers.implicit_title_code() or "mines_auth_default"
    mines_access_session_id = create_game_access_session(
        client, mines_headers, game_code="mines", title_code=mines_title_code
    )
    mines_start = client.post(
        "/games/mines/start",
        headers={
            **mines_headers,
            "Idempotency-Key": f"teardown-graph-mines-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
            "access_session_id": mines_access_session_id,
        },
    )
    assert mines_start.status_code == 200, mines_start.text

    # 3. Sessione demo collegata all'utente (via db: la creazione via API
    #    richiederebbe un utente demo separato).
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO demo_play_sessions (anonymous_id, user_id, title_code, balance_chips)
            VALUES (%s, %s, 'mines_classic', 100)
            """,
            (str(uuid4()), user_id),
        )
        # La registrazione ha gia' creato credenziali, wallet e conto ledger;
        # questi tre rami non nascono invece dal normale flusso del giocatore.
        # Le righe qui sotto rispettano le rispettive chiavi esterne e vincoli.
        cursor.execute(
            """
            INSERT INTO admin_profiles (user_id, is_superadmin, areas)
            VALUES (%s, false, '{}')
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        cursor.execute(
            """
            INSERT INTO access_logs (user_id, user_email, user_role, ip_address, action)
            VALUES (%s, %s, 'player', '127.0.0.1', 'teardown_graph_probe')
            """,
            (user_id, player["email"]),
        )
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at)
            VALUES (%s, %s, %s, NOW() + INTERVAL '1 hour')
            """,
            (uuid4(), user_id, f"teardown-graph-reset-{uuid4().hex}"),
        )

    # Il grafo deve ESISTERE prima della pulizia, altrimenti il "dopo == 0"
    # non proverebbe niente.
    counts_before = {
        table: _count_for_user(db_connection, table, predicate, user_id)
        for table, predicate in GRAPH_TABLES
    }
    for table in sorted(MUST_HAVE_ROWS):
        assert counts_before[table] > 0, (
            f"Il grafo di collaudo non e' stato costruito: {table} non ha righe "
            f"per l'utente {user_id}"
        )

    # Esecuzione ESPLICITA della pulizia coordinata, a meta' prova: e' l'unico
    # modo per verificare il risultato dentro il collaudo invece di affidarsi
    # al teardown delle fixture (che pytest riporta come errore di teardown,
    # non come assert del collaudo).
    user_cleanup_coordinator.execute_cleanup(db_connection)

    counts_after = {
        table: _count_for_user(db_connection, table, predicate, user_id)
        for table, predicate in GRAPH_TABLES
    }
    leaked = {table: count for table, count in counts_after.items() if count > 0}
    assert not leaked, (
        f"La pulizia coordinata ha lasciato righe dell'utente {user_id}: {leaked}"
    )
