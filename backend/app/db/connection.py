from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.db.config import database_config


@contextmanager
def db_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(
        database_config.database_url,
        row_factory=dict_row,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
