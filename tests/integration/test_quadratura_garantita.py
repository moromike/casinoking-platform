from __future__ import annotations
"""CON-02/CON-03: quadratura contabile garantita a livello di database.

Copre la migrazione ``0054__quadratura_garantita.sql``:

- CON-02: constraint trigger DEFERRABLE INITIALLY DEFERRED su ``ledger_entries``
  che al COMMIT verifica somma(dare) = somma(avere) per ogni transazione toccata;
- CON-03: ``ledger_transactions.idempotency_key`` NOT NULL.

Attenzione: con un vincolo differito l'errore arriva al COMMIT, non alla INSERT.
La fixture ``db_connection`` e' in autocommit, quindi i test aprono una
transazione esplicita con ``db_connection.transaction()`` e si aspettano
l'eccezione all'uscita del blocco (il COMMIT).
"""


from collections.abc import Generator
from uuid import UUID, uuid4

import psycopg
import pytest


def _insert_transaction(
    cursor: psycopg.Cursor,
    *,
    user_id: UUID,
    transaction_id: UUID,
    idempotency_key: str | None,
) -> None:
    cursor.execute(
        """
        INSERT INTO ledger_transactions (id, user_id, transaction_type, idempotency_key)
        VALUES (%s, %s, 'test_quadratura', %s)
        """,
        (transaction_id, user_id, idempotency_key),
    )


def _insert_entry(
    cursor: psycopg.Cursor,
    *,
    transaction_id: UUID,
    ledger_account_id: UUID,
    entry_side: str,
    amount: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO ledger_entries (id, transaction_id, ledger_account_id, entry_side, amount)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (uuid4(), transaction_id, ledger_account_id, entry_side, amount),
    )


@pytest.fixture
def ledger_lab(db_connection) -> Generator[dict[str, object], None, None]:
    """Un utente e due conti contabili di test, rimossi a fine test.

    ``transaction_ids`` va popolato dal test SOLO dopo un commit riuscito:
    il teardown cancella le scritture di quelle transazioni (in un'unica
    DELETE per transazione, cosi' la quadratura resta 0 = 0), poi le
    transazioni, i conti e l'utente creati qui.
    """
    user_id = uuid4()
    account_ids = (uuid4(), uuid4())
    with db_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id, email, role, status) VALUES (%s, %s, 'player', 'active')",
            (user_id, f"test-quadratura-{uuid4().hex[:12]}@example.com"),
        )
        for index, account_id in enumerate(account_ids):
            cursor.execute(
                """
                INSERT INTO ledger_accounts (id, account_code, account_type, currency_code, status)
                VALUES (%s, %s, 'test', 'EUR', 'active')
                """,
                (account_id, f"test_quadratura_{index}_{uuid4().hex[:8]}"),
            )

    lab = {
        "user_id": user_id,
        "account_ids": account_ids,
        "transaction_ids": [],
    }
    yield lab

    with db_connection.cursor() as cursor:
        for transaction_id in lab["transaction_ids"]:
            cursor.execute(
                "DELETE FROM ledger_entries WHERE transaction_id = %s",
                (transaction_id,),
            )
        if lab["transaction_ids"]:
            cursor.execute(
                "DELETE FROM ledger_transactions WHERE id = ANY(%s)",
                (lab["transaction_ids"],),
            )
        cursor.execute(
            "DELETE FROM ledger_accounts WHERE id = ANY(%s)",
            (list(account_ids),),
        )
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))


def _count_entries(db_connection, transaction_id: UUID) -> int:
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) AS n FROM ledger_entries WHERE transaction_id = %s",
            (transaction_id,),
        )
        row = cursor.fetchone()
    assert row is not None
    return int(row["n"])


def test_transazione_bilanciata_accettata(db_connection, ledger_lab) -> None:
    transaction_id = uuid4()
    with db_connection.transaction():
        with db_connection.cursor() as cursor:
            _insert_transaction(
                cursor,
                user_id=ledger_lab["user_id"],
                transaction_id=transaction_id,
                idempotency_key=f"quadratura-ok-{uuid4().hex}",
            )
            _insert_entry(
                cursor,
                transaction_id=transaction_id,
                ledger_account_id=ledger_lab["account_ids"][0],
                entry_side="debit",
                amount="100",
            )
            _insert_entry(
                cursor,
                transaction_id=transaction_id,
                ledger_account_id=ledger_lab["account_ids"][1],
                entry_side="credit",
                amount="100",
            )
    ledger_lab["transaction_ids"].append(transaction_id)

    assert _count_entries(db_connection, transaction_id) == 2


def test_transazione_con_solo_dare_rifiutata_al_commit(db_connection, ledger_lab) -> None:
    transaction_id = uuid4()
    with pytest.raises(psycopg.errors.RaiseException, match="Quadratura contabile violata"):
        with db_connection.transaction():
            with db_connection.cursor() as cursor:
                _insert_transaction(
                    cursor,
                    user_id=ledger_lab["user_id"],
                    transaction_id=transaction_id,
                    idempotency_key=f"quadratura-solo-dare-{uuid4().hex}",
                )
                _insert_entry(
                    cursor,
                    transaction_id=transaction_id,
                    ledger_account_id=ledger_lab["account_ids"][0],
                    entry_side="debit",
                    amount="100",
                )
            # l'errore arriva qui, al COMMIT (vincolo INITIALLY DEFERRED)

    assert _count_entries(db_connection, transaction_id) == 0


def test_transazione_con_importi_diversi_rifiutata(db_connection, ledger_lab) -> None:
    transaction_id = uuid4()
    with pytest.raises(psycopg.errors.RaiseException, match="Quadratura contabile violata"):
        with db_connection.transaction():
            with db_connection.cursor() as cursor:
                _insert_transaction(
                    cursor,
                    user_id=ledger_lab["user_id"],
                    transaction_id=transaction_id,
                    idempotency_key=f"quadratura-sbilanciata-{uuid4().hex}",
                )
                _insert_entry(
                    cursor,
                    transaction_id=transaction_id,
                    ledger_account_id=ledger_lab["account_ids"][0],
                    entry_side="debit",
                    amount="100",
                )
                _insert_entry(
                    cursor,
                    transaction_id=transaction_id,
                    ledger_account_id=ledger_lab["account_ids"][1],
                    entry_side="credit",
                    amount="60",
                )
            # l'errore arriva qui, al COMMIT (vincolo INITIALLY DEFERRED)

    assert _count_entries(db_connection, transaction_id) == 0


def test_transazione_senza_idempotency_key_rifiutata(db_connection, ledger_lab) -> None:
    transaction_id = uuid4()
    with pytest.raises(psycopg.errors.NotNullViolation):
        with db_connection.transaction():
            with db_connection.cursor() as cursor:
                _insert_transaction(
                    cursor,
                    user_id=ledger_lab["user_id"],
                    transaction_id=transaction_id,
                    idempotency_key=None,
                )

    assert _count_entries(db_connection, transaction_id) == 0
