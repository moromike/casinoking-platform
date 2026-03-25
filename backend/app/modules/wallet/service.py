from decimal import Decimal

from app.db.connection import db_connection


def list_wallets_for_user(user_id: str) -> list[dict[str, object]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    wa.wallet_type,
                    wa.currency_code,
                    wa.balance_snapshot,
                    wa.status,
                    la.account_code
                FROM wallet_accounts wa
                JOIN ledger_accounts la ON la.id = wa.ledger_account_id
                WHERE wa.user_id = %s
                ORDER BY wa.wallet_type
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

    return [_wallet_response(row) for row in rows]


def get_wallet_for_user(
    *,
    user_id: str,
    wallet_type: str,
) -> dict[str, object] | None:
    normalized_wallet_type = wallet_type.strip().lower()
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    wa.wallet_type,
                    wa.currency_code,
                    wa.balance_snapshot,
                    wa.status,
                    la.account_code
                FROM wallet_accounts wa
                JOIN ledger_accounts la ON la.id = wa.ledger_account_id
                WHERE wa.user_id = %s
                  AND wa.wallet_type = %s
                """,
                (user_id, normalized_wallet_type),
            )
            row = cursor.fetchone()

    if row is None:
        return None
    return _wallet_response(row)


def _wallet_response(row: dict[str, object]) -> dict[str, object]:
    return {
        "wallet_type": row["wallet_type"],
        "currency_code": row["currency_code"],
        "balance_snapshot": _format_amount(row["balance_snapshot"]),
        "status": row["status"],
        "ledger_account_code": row["account_code"],
    }


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"
