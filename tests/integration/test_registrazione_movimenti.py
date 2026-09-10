from __future__ import annotations
"""Test di integrazione per la funzione unica di partita doppia (CON-01).

Copre ``backend/app/modules/platform/ledger/registrazione.py``:
- quadratura: una scrittura valida produce transazione + entries + snapshot
  coerenti (drift zero contro la riconciliazione ledger);
- idempotenza: due chiamate con la stessa chiave producono un solo movimento;
- rifiuto dello sbilancio: una scrittura non quadrata viene respinta PRIMA
  di qualsiasi scrittura;
- il punto convertito (credito iniziale di registrazione in
  ``auth/service.py``) resta corretto end-to-end via API.
"""


from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.platform.ledger.registrazione import (
    RegistrazioneValidationError,
    RigaScrittura,
    registra_movimento,
)

HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
TEST_TRANSACTION_TYPE = "test_movement"


def _get_house_cash_account_id(db_connection) -> str:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM ledger_accounts WHERE account_code = %s",
            (HOUSE_CASH_ACCOUNT_CODE,),
        )
        row = cursor.fetchone()
    assert row is not None
    return str(row["id"])


def _get_player_cash_ledger_account_id(db_connection, user_id: str) -> str:
    with db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ledger_account_id
            FROM wallet_accounts
            WHERE user_id = %s
              AND wallet_type = 'cash'
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    assert row is not None
    return str(row["ledger_account_id"])


def _count_transactions_by_key(db_connection, idempotency_key: str) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) AS n FROM ledger_transactions WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        return int(cursor.fetchone()["n"])


def test_signup_credit_usa_la_funzione_unica(
    create_player,
    db_helpers,
) -> None:
    """Il punto convertito (auth/service.py) registra il credito iniziale."""
    player = create_player(prefix="integration-registrazione-signup")

    assert player["bootstrap_transaction_id"]
    entries = db_helpers.get_transaction_entries(player["bootstrap_transaction_id"])
    assert sorted((row["account_code"], row["entry_side"]) for row in entries) == [
        (HOUSE_CASH_ACCOUNT_CODE, "debit"),
        (f"PLAYER_CASH_{player['user_id']}", "credit"),
    ]
    assert all(Decimal(row["amount"]) == Decimal("1000.000000") for row in entries)
    assert db_helpers.get_wallet_balance(player["user_id"], "cash") == "1000.000000"
    assert db_helpers.get_wallet_reconciliation(player["user_id"], "cash")["drift"] == (
        "0.000000"
    )


def test_movimento_quadrato_scrive_transazione_entries_e_snapshot(
    db_connection,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-registrazione-quadratura")
    player_account_id = _get_player_cash_ledger_account_id(
        db_connection, player["user_id"]
    )
    house_account_id = _get_house_cash_account_id(db_connection)
    idempotency_key = f"test-registrazione-{uuid4().hex}"

    with db_connection.cursor() as cursor:
        result = registra_movimento(
            cursor=cursor,
            user_id=str(player["user_id"]),
            transaction_type=TEST_TRANSACTION_TYPE,
            idempotency_key=idempotency_key,
            righe=(
                RigaScrittura(
                    ledger_account_id=player_account_id,
                    entry_side="debit",
                    amount=Decimal("10.000000"),
                ),
                RigaScrittura(
                    ledger_account_id=house_account_id,
                    entry_side="credit",
                    amount=Decimal("10.000000"),
                ),
            ),
        )

    assert result["already_exists"] is False
    assert len(result["wallet_updates"]) == 1
    assert (
        result["wallet_updates"][0]["balance_after"]
        == Decimal("990.000000")
    )

    entries = db_helpers.get_transaction_entries(result["transaction_id"])
    assert sorted((row["account_code"], row["entry_side"]) for row in entries) == [
        (HOUSE_CASH_ACCOUNT_CODE, "credit"),
        (f"PLAYER_CASH_{player['user_id']}", "debit"),
    ]
    assert db_helpers.get_wallet_balance(player["user_id"], "cash") == "990.000000"
    assert db_helpers.get_wallet_reconciliation(player["user_id"], "cash")["drift"] == (
        "0.000000"
    )


def test_stessa_chiave_produce_un_solo_movimento(
    db_connection,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-registrazione-idem")
    player_account_id = _get_player_cash_ledger_account_id(
        db_connection, player["user_id"]
    )
    house_account_id = _get_house_cash_account_id(db_connection)
    idempotency_key = f"test-registrazione-{uuid4().hex}"
    righe = (
        RigaScrittura(
            ledger_account_id=player_account_id,
            entry_side="debit",
            amount=Decimal("7.000000"),
        ),
        RigaScrittura(
            ledger_account_id=house_account_id,
            entry_side="credit",
            amount=Decimal("7.000000"),
        ),
    )

    with db_connection.cursor() as cursor:
        first = registra_movimento(
            cursor=cursor,
            user_id=str(player["user_id"]),
            transaction_type=TEST_TRANSACTION_TYPE,
            idempotency_key=idempotency_key,
            righe=righe,
        )
        second = registra_movimento(
            cursor=cursor,
            user_id=str(player["user_id"]),
            transaction_type=TEST_TRANSACTION_TYPE,
            idempotency_key=idempotency_key,
            righe=righe,
        )

    assert first["already_exists"] is False
    assert second["already_exists"] is True
    assert second["transaction_id"] == first["transaction_id"]
    assert second["wallet_updates"] == []
    assert _count_transactions_by_key(db_connection, idempotency_key) == 1
    assert db_helpers.get_wallet_balance(player["user_id"], "cash") == "993.000000"
    assert db_helpers.get_wallet_reconciliation(player["user_id"], "cash")["drift"] == (
        "0.000000"
    )


def test_sbilancio_rifiutato_senza_scrivere_nulla(
    db_connection,
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-registrazione-sbilancio")
    player_account_id = _get_player_cash_ledger_account_id(
        db_connection, player["user_id"]
    )
    house_account_id = _get_house_cash_account_id(db_connection)
    idempotency_key = f"test-registrazione-{uuid4().hex}"

    with db_connection.cursor() as cursor:
        with pytest.raises(RegistrazioneValidationError, match="Unbalanced"):
            registra_movimento(
                cursor=cursor,
                user_id=str(player["user_id"]),
                transaction_type=TEST_TRANSACTION_TYPE,
                idempotency_key=idempotency_key,
                righe=(
                    RigaScrittura(
                        ledger_account_id=player_account_id,
                        entry_side="debit",
                        amount=Decimal("10.000000"),
                    ),
                    RigaScrittura(
                        ledger_account_id=house_account_id,
                        entry_side="credit",
                        amount=Decimal("5.000000"),
                    ),
                ),
            )

    assert _count_transactions_by_key(db_connection, idempotency_key) == 0
    assert db_helpers.get_wallet_balance(player["user_id"], "cash") == "1000.000000"
    assert db_helpers.get_wallet_reconciliation(player["user_id"], "cash")["drift"] == (
        "0.000000"
    )


@pytest.mark.parametrize(
    ("righe", "idempotency_key", "match"),
    [
        (  # idempotency key vuota
            (
                RigaScrittura("a", "debit", Decimal("1")),
                RigaScrittura("b", "credit", Decimal("1")),
            ),
            "  ",
            "Idempotency key is required",
        ),
        (  # meno di due righe
            (RigaScrittura("a", "debit", Decimal("1")),),
            "k",
            "at least two rows",
        ),
        (  # importo nullo
            (
                RigaScrittura("a", "debit", Decimal("0")),
                RigaScrittura("b", "credit", Decimal("0")),
            ),
            "k",
            "must be positive",
        ),
        (  # piu' di 6 decimali
            (
                RigaScrittura("a", "debit", Decimal("0.0000001")),
                RigaScrittura("b", "credit", Decimal("0.0000001")),
            ),
            "k",
            "6 decimal places",
        ),
        (  # lato non valido
            (
                RigaScrittura("a", "addebito", Decimal("1")),
                RigaScrittura("b", "credit", Decimal("1")),
            ),
            "k",
            "Entry side is not valid",
        ),
    ],
)
def test_input_non_valido_rifiutato(
    db_connection,
    righe,
    idempotency_key,
    match,
) -> None:
    with db_connection.cursor() as cursor:
        with pytest.raises(RegistrazioneValidationError, match=match):
            registra_movimento(
                cursor=cursor,
                user_id=str(uuid4()),
                transaction_type=TEST_TRANSACTION_TYPE,
                idempotency_key=idempotency_key,
                righe=righe,
            )
