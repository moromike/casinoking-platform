from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from app.tools import apply_migrations


class FakeCursor:
    def __init__(
        self,
        *,
        fetchall_responses: list[list[dict[str, object]]] | None = None,
        fetchone_responses: list[dict[str, object] | None] | None = None,
    ) -> None:
        self.fetchall_responses = fetchall_responses or []
        self.fetchone_responses = fetchone_responses or []
        self.executed: list[str] = []
        self.executemany_calls: list[tuple[str, list[tuple[object, ...]]]] = []

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        del params
        self.executed.append(query.strip())

    def executemany(
        self,
        query: str,
        params_seq: list[tuple[object, ...]],
    ) -> None:
        self.executemany_calls.append((query.strip(), params_seq))

    def fetchall(self) -> list[dict[str, object]]:
        if not self.fetchall_responses:
            return []
        return self.fetchall_responses.pop(0)

    def fetchone(self) -> dict[str, object] | None:
        if not self.fetchone_responses:
            return None
        return self.fetchone_responses.pop(0)

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> FakeCursor:
        return self._cursor


def fake_db_connection(cursor: FakeCursor):
    @contextmanager
    def _factory():
        yield FakeConnection(cursor)

    return _factory


def test_looks_like_legacy_initialized_schema_detects_full_local_baseline() -> None:
    cursor = FakeCursor(
        fetchall_responses=[
            [
                {"table_name": "ledger_accounts"},
                {"table_name": "wallet_accounts"},
                {"table_name": "ledger_transactions"},
                {"table_name": "ledger_entries"},
                {"table_name": "users"},
                {"table_name": "user_credentials"},
                {"table_name": "password_reset_tokens"},
                {"table_name": "game_sessions"},
                {"table_name": "admin_actions"},
                {"table_name": "fairness_seed_rotations"},
            ]
        ],
        fetchone_responses=[{"system_account_count": 4}],
    )

    assert apply_migrations._looks_like_legacy_initialized_schema(cursor) is True


def test_apply_sql_migrations_backfills_legacy_state_without_replaying_sql(
    tmp_path: Path,
    monkeypatch,
) -> None:
    first = tmp_path / "0001__first.sql"
    second = tmp_path / "0002__second.sql"
    first.write_text("CREATE TABLE first_table (id int);", encoding="utf-8")
    second.write_text("CREATE TABLE second_table (id int);", encoding="utf-8")

    cursor = FakeCursor(
        fetchall_responses=[
            [],
            [
                {"table_name": "ledger_accounts"},
                {"table_name": "wallet_accounts"},
                {"table_name": "ledger_transactions"},
                {"table_name": "ledger_entries"},
                {"table_name": "users"},
                {"table_name": "user_credentials"},
                {"table_name": "password_reset_tokens"},
                {"table_name": "game_sessions"},
                {"table_name": "admin_actions"},
                {"table_name": "fairness_seed_rotations"},
            ],
        ],
        fetchone_responses=[{"system_account_count": 4}],
    )

    monkeypatch.setattr(apply_migrations, "MIGRATIONS_DIR", tmp_path)
    monkeypatch.setattr(
        apply_migrations,
        "db_connection",
        fake_db_connection(cursor),
    )

    result = apply_migrations.apply_sql_migrations()

    assert result["applied"] == []
    assert result["skipped"] == ["0001__first.sql", "0002__second.sql"]
    assert len(cursor.executemany_calls) == 1
    assert [row[0] for row in cursor.executemany_calls[0][1]] == [
        "0001__first.sql",
        "0002__second.sql",
    ]
    assert all("CREATE TABLE first_table" not in query for query in cursor.executed)
    assert all("CREATE TABLE second_table" not in query for query in cursor.executed)


def test_apply_sql_migrations_executes_missing_files_in_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    first = tmp_path / "0001__first.sql"
    second = tmp_path / "0002__second.sql"
    first.write_text("CREATE TABLE first_table (id int);", encoding="utf-8")
    second.write_text("CREATE TABLE second_table (id int);", encoding="utf-8")

    cursor = FakeCursor(
        fetchall_responses=[[]],
    )

    monkeypatch.setattr(apply_migrations, "MIGRATIONS_DIR", tmp_path)
    monkeypatch.setattr(
        apply_migrations,
        "db_connection",
        fake_db_connection(cursor),
    )
    monkeypatch.setattr(
        apply_migrations,
        "_looks_like_legacy_initialized_schema",
        lambda _cursor: False,
    )

    result = apply_migrations.apply_sql_migrations()

    assert result["applied"] == ["0001__first.sql", "0002__second.sql"]
    assert result["skipped"] == []
    assert any("CREATE TABLE first_table (id int);" in query for query in cursor.executed)
    assert any("CREATE TABLE second_table (id int);" in query for query in cursor.executed)
