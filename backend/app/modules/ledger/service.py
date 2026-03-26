from decimal import Decimal

from app.db.connection import db_connection


def list_transactions_for_viewer(
    *,
    viewer_user_id: str,
    viewer_role: str,
) -> list[dict[str, object]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            if viewer_role == "admin":
                cursor.execute(
                    """
                    SELECT
                        lt.id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.idempotency_key,
                        lt.created_at
                    FROM ledger_transactions lt
                    ORDER BY lt.created_at DESC
                    """,
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        lt.id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.idempotency_key,
                        lt.created_at
                    FROM ledger_transactions lt
                    WHERE lt.user_id = %s
                    ORDER BY lt.created_at DESC
                    """,
                    (viewer_user_id,),
                )
            rows = cursor.fetchall()

    return [_serialize_transaction_header(row) for row in rows]


def get_transaction_detail_for_viewer(
    *,
    viewer_user_id: str,
    viewer_role: str,
    transaction_id: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            if viewer_role == "admin":
                cursor.execute(
                    """
                    SELECT
                        lt.id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.idempotency_key,
                        lt.created_at
                    FROM ledger_transactions lt
                    WHERE lt.id = %s
                    """,
                    (transaction_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        lt.id,
                        lt.transaction_type,
                        lt.reference_type,
                        lt.reference_id,
                        lt.idempotency_key,
                        lt.created_at
                    FROM ledger_transactions lt
                    WHERE lt.id = %s
                      AND lt.user_id = %s
                    """,
                    (transaction_id, viewer_user_id),
                )
            transaction = cursor.fetchone()
            if transaction is None:
                return None

            cursor.execute(
                """
                SELECT
                    le.id,
                    la.account_code,
                    le.entry_side,
                    le.amount,
                    le.created_at
                FROM ledger_entries le
                JOIN ledger_accounts la ON la.id = le.ledger_account_id
                WHERE le.transaction_id = %s
                ORDER BY le.created_at, le.id
                """,
                (transaction_id,),
            )
            entries = cursor.fetchall()

    return {
        **_serialize_transaction_header(transaction),
        "entries": [
            {
                "id": str(entry["id"]),
                "ledger_account_code": entry["account_code"],
                "entry_side": entry["entry_side"],
                "amount": _format_amount(entry["amount"]),
                "created_at": entry["created_at"].isoformat(),
            }
            for entry in entries
        ],
    }


def transaction_exists(transaction_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM ledger_transactions
                WHERE id = %s
                """,
                (transaction_id,),
            )
            row = cursor.fetchone()
    return row is not None


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _serialize_transaction_header(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "transaction_type": row["transaction_type"],
        "reference_type": row["reference_type"],
        "reference_id": str(row["reference_id"])
        if row["reference_id"] is not None
        else None,
        "idempotency_key": row["idempotency_key"],
        "created_at": row["created_at"].isoformat(),
    }
