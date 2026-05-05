from __future__ import annotations

from decimal import Decimal
from uuid import uuid4
from threading import Barrier, Thread

import pytest
import psycopg
from psycopg.rows import dict_row

from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)


def test_demo_wallet_open_gives_100_chips(db_connection) -> None:
    cursor = db_connection.cursor()
    session = open_demo_session(
        cursor=cursor,
        anonymous_id=str(uuid4()),
        title_code="mines_classic",
    )

    assert session["balance_chips"] == Decimal("100.000000")
    assert session["status"] == "active"


def test_demo_wallet_debit_credit_loss_and_idempotency(db_connection) -> None:
    cursor = db_connection.cursor()
    session = open_demo_session(
        cursor=cursor,
        anonymous_id=str(uuid4()),
        title_code="mines_classic",
    )

    debited = debit_for_bet(
        cursor=cursor,
        session_id=str(session["id"]),
        amount=Decimal("5.000000"),
        idempotency_key="demo-wallet-debit-once",
        payload={"round": "a"},
    )
    duplicate = debit_for_bet(
        cursor=cursor,
        session_id=str(session["id"]),
        amount=Decimal("5.000000"),
        idempotency_key="demo-wallet-debit-once",
        payload={"round": "a"},
    )
    credited = credit_for_win(
        cursor=cursor,
        session_id=str(session["id"]),
        amount=Decimal("8.000000"),
        idempotency_key="demo-wallet-credit-once",
        payload={"round": "a"},
    )
    loss = record_loss(
        cursor=cursor,
        session_id=str(session["id"]),
        idempotency_key="demo-wallet-loss-once",
        payload={"round": "b"},
    )

    assert debited["balance_chips"] == Decimal("95.000000")
    assert duplicate["balance_chips"] == Decimal("95.000000")
    assert credited["balance_chips"] == Decimal("103.000000")
    assert loss["balance_chips"] == Decimal("103.000000")


def test_demo_wallet_idempotency_conflict(db_connection) -> None:
    cursor = db_connection.cursor()
    session = open_demo_session(
        cursor=cursor,
        anonymous_id=str(uuid4()),
        title_code="mines_classic",
    )

    debit_for_bet(
        cursor=cursor,
        session_id=str(session["id"]),
        amount=Decimal("5.000000"),
        idempotency_key="demo-wallet-conflict",
        payload={"round": "a"},
    )

    with pytest.raises(DemoWalletIdempotencyConflictError):
        debit_for_bet(
            cursor=cursor,
            session_id=str(session["id"]),
            amount=Decimal("6.000000"),
            idempotency_key="demo-wallet-conflict",
            payload={"round": "a"},
        )


def test_demo_wallet_exhausted_rejects_bet(db_connection) -> None:
    cursor = db_connection.cursor()
    session = open_demo_session(
        cursor=cursor,
        anonymous_id=str(uuid4()),
        title_code="mines_classic",
    )
    debited = debit_for_bet(
        cursor=cursor,
        session_id=str(session["id"]),
        amount=Decimal("100.000000"),
        idempotency_key="demo-wallet-empty",
    )
    exhausted = record_loss(
        cursor=cursor,
        session_id=str(session["id"]),
        idempotency_key="demo-wallet-empty-loss",
    )

    assert debited["balance_chips"] == Decimal("0.000000")
    assert exhausted["status"] == "exhausted"

    with pytest.raises((DemoWalletInsufficientBalanceError, DemoWalletValidationError)):
        debit_for_bet(
            cursor=cursor,
            session_id=str(session["id"]),
            amount=Decimal("1.000000"),
            idempotency_key="demo-wallet-after-empty",
        )


def test_demo_wallet_debit_atomicity(database_url, db_connection) -> None:
    cursor = db_connection.cursor()
    session = open_demo_session(
        cursor=cursor,
        anonymous_id=str(uuid4()),
        title_code="mines_classic",
    )
    session_id = str(session["id"])
    barrier = Barrier(2)
    results: list[str] = []

    def _debit(idempotency_key: str) -> None:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as worker_cursor:
                barrier.wait(timeout=10)
                try:
                    debit_for_bet(
                        cursor=worker_cursor,
                        session_id=session_id,
                        amount=Decimal("60.000000"),
                        idempotency_key=idempotency_key,
                    )
                    results.append("ok")
                except DemoWalletInsufficientBalanceError:
                    results.append("insufficient")

    threads = [
        Thread(target=_debit, args=(f"demo-wallet-atomic-{index}",))
        for index in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    row = db_connection.execute(
        """
        SELECT balance_chips
        FROM demo_play_sessions
        WHERE id = %s
        """,
        (session_id,),
    ).fetchone()

    assert sorted(results) == ["insufficient", "ok"]
    assert row["balance_chips"] == Decimal("40.000000")
