from app.db.connection import db_connection


def record_access_log(
    *,
    user_id: str,
    user_email: str,
    user_role: str,
    ip_address: str | None,
    action: str = "login",
) -> None:
    """Insert a row in access_logs. Silent no-op on any DB error to avoid breaking login flow."""
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO access_logs (user_id, user_email, user_role, ip_address, action)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, user_email, user_role, ip_address, action),
                )
    except Exception:
        pass
