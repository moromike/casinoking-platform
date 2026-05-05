from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import psycopg

from app.modules.games.mines.exceptions import (
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesValidationError,
)
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)
from app.modules.platform.rounds.service import (
    PlatformRoundIdempotencyConflictError,
    PlatformRoundInsufficientBalanceError,
    PlatformRoundValidationError,
    get_existing_round_win_by_key,
    get_mines_round_cashout_snapshot,
    is_mines_round_open_idempotency_violation,
    is_mines_round_settlement_idempotency_violation,
    namespace_mines_round_win_idempotency_key,
    open_mines_round,
    settle_mines_round_loss,
    settle_mines_round_win,
)
from app.modules.platform.table_sessions.service import (
    TableSessionLimitExceededError,
    TableSessionNotFoundError,
    TableSessionStateConflictError,
    TableSessionValidationError,
)


@dataclass(frozen=True)
class MinesPlatformRoundOpenResult:
    """Platform-owned facts produced while opening a Mines round."""

    platform_round_id: str
    wallet_account_id: str
    wallet_balance_after_start: Decimal
    ledger_transaction_id: str
    table_session_id: str
    table_session: dict[str, object]


@dataclass(frozen=True)
class MinesPlatformRoundWinResult:
    """Platform-owned facts produced while settling a Mines round as won."""

    platform_round_id: str
    wallet_balance_after: Decimal
    ledger_transaction_id: str
    already_exists: bool


@dataclass(frozen=True)
class MinesPlatformRoundLossResult:
    """Platform-owned facts produced while settling a Mines round as lost."""

    platform_round_id: str
    wallet_balance_after: Decimal
    bet_transaction_id: str
    safe_reveals_count: int


class PlatformGameClient(Protocol):
    """Boundary used by Mines to talk to platform-owned economic services."""

    def open_round(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        idempotency_key: str,
        grid_size: int,
        mine_count: int,
        bet_amount: Decimal,
        wallet_type: str,
        table_session_id: str | None = None,
        access_session_id: str | None = None,
        title_code: str | None = None,
        site_code: str | None = None,
    ) -> MinesPlatformRoundOpenResult:
        ...

    def get_existing_cashout_by_key(
        self,
        *,
        cursor: psycopg.Cursor,
        idempotency_key: str,
    ) -> dict[str, object] | None:
        ...

    def get_cashout_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
    ) -> dict[str, object] | None:
        ...

    def build_cashout_idempotency_key(self, *, user_id: str, idempotency_key: str) -> str:
        ...

    def is_open_round_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        ...

    def is_settlement_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        ...

    def get_round_start_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        platform_round_id: str,
    ) -> dict[str, object]:
        ...

    def settle_win(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        payout_amount: Decimal,
        safe_reveals_count: int,
        idempotency_key: str,
    ) -> MinesPlatformRoundWinResult:
        ...

    def settle_loss(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        safe_reveals_count: int,
    ) -> MinesPlatformRoundLossResult:
        ...


class InProcessPlatformGameClient:
    """Current monolith implementation of the Mines/platform boundary."""

    def open_round(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        idempotency_key: str,
        grid_size: int,
        mine_count: int,
        bet_amount: Decimal,
        wallet_type: str,
        table_session_id: str | None = None,
        access_session_id: str | None = None,
        title_code: str | None = None,
        site_code: str | None = None,
    ) -> MinesPlatformRoundOpenResult:
        try:
            result = open_mines_round(
                cursor=cursor,
                user_id=user_id,
                game_session_id=game_round_id,
                idempotency_key=idempotency_key,
                grid_size=grid_size,
                mine_count=mine_count,
                bet_amount=bet_amount,
                wallet_type=wallet_type,
                table_session_id=table_session_id,
                access_session_id=access_session_id,
                title_code=title_code,
                site_code=site_code,
            )
            return MinesPlatformRoundOpenResult(
                platform_round_id=game_round_id,
                wallet_account_id=str(result["wallet_account_id"]),
                wallet_balance_after_start=Decimal(result["wallet_balance_after_start"]),
                ledger_transaction_id=str(result["ledger_transaction_id"]),
                table_session_id=str(result["table_session_id"]),
                table_session=dict(result["table_session"]),
            )
        except PlatformRoundValidationError as exc:
            raise MinesValidationError(str(exc)) from exc
        except PlatformRoundInsufficientBalanceError as exc:
            raise MinesInsufficientBalanceError(str(exc)) from exc
        except TableSessionLimitExceededError as exc:
            raise MinesValidationError(str(exc)) from exc
        except (
            TableSessionNotFoundError,
            TableSessionStateConflictError,
            TableSessionValidationError,
        ) as exc:
            raise MinesValidationError(str(exc)) from exc

    def get_existing_cashout_by_key(
        self,
        *,
        cursor: psycopg.Cursor,
        idempotency_key: str,
    ) -> dict[str, object] | None:
        return get_existing_round_win_by_key(
            cursor=cursor,
            idempotency_key=idempotency_key,
        )

    def get_cashout_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
    ) -> dict[str, object] | None:
        return get_mines_round_cashout_snapshot(
            cursor=cursor,
            user_id=user_id,
            game_session_id=game_round_id,
        )

    def build_cashout_idempotency_key(self, *, user_id: str, idempotency_key: str) -> str:
        return namespace_mines_round_win_idempotency_key(
            user_id=user_id,
            idempotency_key=idempotency_key,
        )

    def is_open_round_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        return is_mines_round_open_idempotency_violation(exc)

    def is_settlement_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        return is_mines_round_settlement_idempotency_violation(exc)

    def get_round_start_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        platform_round_id: str,
    ) -> dict[str, object]:
        cursor.execute(
            """
            SELECT
                pr.wallet_balance_after_start,
                pr.start_ledger_transaction_id
            FROM platform_rounds pr
            WHERE pr.id = %s
            """,
            (platform_round_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise MinesValidationError(f"Platform round {platform_round_id} not found")
        return {
            "wallet_balance_after_start": row["wallet_balance_after_start"],
            "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        }

    def settle_win(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        payout_amount: Decimal,
        safe_reveals_count: int,
        idempotency_key: str,
    ) -> MinesPlatformRoundWinResult:
        try:
            result = settle_mines_round_win(
                cursor=cursor,
                user_id=user_id,
                game_session_id=game_round_id,
                payout_amount=payout_amount,
                safe_reveals_count=safe_reveals_count,
                idempotency_key=idempotency_key,
            )
            wallet_balance_after = result.get("wallet_balance_after")
            if wallet_balance_after is None:
                snapshot = get_mines_round_cashout_snapshot(
                    cursor=cursor,
                    user_id=user_id,
                    game_session_id=game_round_id,
                )
                if snapshot is None:
                    raise MinesValidationError("Cashout snapshot is not available")
                wallet_balance_after = snapshot["wallet_balance_after"]
            return MinesPlatformRoundWinResult(
                platform_round_id=game_round_id,
                wallet_balance_after=Decimal(wallet_balance_after),
                ledger_transaction_id=str(result["ledger_transaction_id"]),
                already_exists=bool(result["already_exists"]),
            )
        except PlatformRoundValidationError as exc:
            raise MinesValidationError(str(exc)) from exc
        except PlatformRoundIdempotencyConflictError as exc:
            raise MinesIdempotencyConflictError(str(exc)) from exc

    def settle_loss(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        safe_reveals_count: int,
    ) -> MinesPlatformRoundLossResult:
        try:
            result = settle_mines_round_loss(
                cursor=cursor,
                user_id=user_id,
                game_session_id=game_round_id,
                safe_reveals_count=safe_reveals_count,
            )
            return MinesPlatformRoundLossResult(
                platform_round_id=game_round_id,
                wallet_balance_after=Decimal(result["wallet_balance_after"]),
                bet_transaction_id=str(result["bet_transaction_id"]),
                safe_reveals_count=int(result["safe_reveals_count"]),
            )
        except PlatformRoundValidationError as exc:
            raise MinesValidationError(str(exc)) from exc


class DemoPlatformGameClient:
    """Demo implementation of the Mines/platform boundary."""

    def __init__(self, *, anonymous_id: str) -> None:
        self.anonymous_id = anonymous_id

    def open_round(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        idempotency_key: str,
        grid_size: int,
        mine_count: int,
        bet_amount: Decimal,
        wallet_type: str,
        table_session_id: str | None = None,
        access_session_id: str | None = None,
        title_code: str | None = None,
        site_code: str | None = None,
    ) -> MinesPlatformRoundOpenResult:
        del user_id, wallet_type, table_session_id, access_session_id, site_code
        normalized_title_code = title_code or "mines_classic"
        try:
            session = open_demo_session(
                cursor=cursor,
                anonymous_id=self.anonymous_id,
                title_code=normalized_title_code,
            )
            debited = debit_for_bet(
                cursor=cursor,
                session_id=str(session["id"]),
                amount=bet_amount,
                idempotency_key=idempotency_key,
                payload={
                    "game_round_id": game_round_id,
                    "grid_size": grid_size,
                    "mine_count": mine_count,
                    "title_code": normalized_title_code,
                },
            )
        except DemoWalletInsufficientBalanceError as exc:
            raise MinesInsufficientBalanceError(str(exc)) from exc
        except DemoWalletIdempotencyConflictError as exc:
            raise MinesIdempotencyConflictError(str(exc)) from exc
        except DemoWalletValidationError as exc:
            raise MinesValidationError(str(exc)) from exc

        return MinesPlatformRoundOpenResult(
            platform_round_id=str(session["id"]),
            wallet_account_id=str(session["id"]),
            wallet_balance_after_start=Decimal(debited["balance_chips"]),
            ledger_transaction_id=str(debited["event_id"]),
            table_session_id=str(session["id"]),
            table_session={
                "id": str(session["id"]),
                "mode": "demo",
                "balance_chips": f"{Decimal(debited['balance_chips']):.6f}",
                "status": debited["status"],
            },
        )

    def get_existing_cashout_by_key(
        self,
        *,
        cursor: psycopg.Cursor,
        idempotency_key: str,
    ) -> dict[str, object] | None:
        cursor.execute(
            """
            SELECT
                dre.id,
                dmgr.id AS reference_id
            FROM demo_round_events dre
            JOIN demo_mines_game_rounds dmgr
              ON dmgr.demo_play_session_id = dre.demo_play_session_id
             AND dmgr.id::text = dre.payload_json->>'game_round_id'
            WHERE dre.idempotency_key = %s
              AND dre.kind = 'win'
              AND dmgr.anonymous_id = %s
            LIMIT 1
            """,
            (idempotency_key, self.anonymous_id),
        )
        return cursor.fetchone()

    def get_cashout_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
    ) -> dict[str, object] | None:
        del user_id
        cursor.execute(
            """
            SELECT
                dmgr.payout_current,
                dps.balance_chips AS wallet_balance_after
            FROM demo_mines_game_rounds dmgr
            JOIN demo_play_sessions dps ON dps.id = dmgr.demo_play_session_id
            WHERE dmgr.id = %s
              AND dmgr.anonymous_id = %s
            """,
            (game_round_id, self.anonymous_id),
        )
        return cursor.fetchone()

    def build_cashout_idempotency_key(self, *, user_id: str, idempotency_key: str) -> str:
        del user_id
        return f"mines:demo:cashout:{self.anonymous_id}:{idempotency_key}"

    def is_open_round_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        # Demo wallet handles idempotency proactively in debit_for_bet
        # (see _get_event_by_key under FOR UPDATE lock); any UniqueViolation
        # reaching this layer is NOT an idempotency replay.
        del exc
        return False

    def is_settlement_idempotency_violation(
        self,
        exc: psycopg.errors.UniqueViolation,
    ) -> bool:
        # Demo wallet handles idempotency proactively in credit_for_win and
        # record_loss (see _get_event_by_key under FOR UPDATE lock); any
        # UniqueViolation reaching this layer is NOT an idempotency replay.
        del exc
        return False

    def get_round_start_snapshot(
        self,
        *,
        cursor: psycopg.Cursor,
        platform_round_id: str,
    ) -> dict[str, object]:
        cursor.execute(
            """
            SELECT
                dps.balance_chips AS wallet_balance_after_start,
                dre.id AS start_ledger_transaction_id
            FROM demo_play_sessions dps
            LEFT JOIN demo_round_events dre
              ON dre.demo_play_session_id = dps.id
             AND dre.kind = 'bet'
            WHERE dps.id = %s
            ORDER BY dre.created_at DESC
            LIMIT 1
            """,
            (platform_round_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise MinesValidationError(f"Demo session {platform_round_id} not found")
        return {
            "wallet_balance_after_start": row["wallet_balance_after_start"],
            "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        }

    def settle_win(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        payout_amount: Decimal,
        safe_reveals_count: int,
        idempotency_key: str,
    ) -> MinesPlatformRoundWinResult:
        del user_id
        try:
            demo_session_id = self._get_demo_session_id(
                cursor=cursor,
                game_round_id=game_round_id,
            )
            credited = credit_for_win(
                cursor=cursor,
                session_id=demo_session_id,
                amount=payout_amount,
                idempotency_key=idempotency_key,
                payload={
                    "game_round_id": game_round_id,
                    "safe_reveals_count": safe_reveals_count,
                },
            )
        except DemoWalletIdempotencyConflictError as exc:
            raise MinesIdempotencyConflictError(str(exc)) from exc
        except DemoWalletValidationError as exc:
            raise MinesValidationError(str(exc)) from exc

        return MinesPlatformRoundWinResult(
            platform_round_id=game_round_id,
            wallet_balance_after=Decimal(credited["balance_chips"]),
            ledger_transaction_id=str(credited["event_id"]),
            already_exists=False,
        )

    def settle_loss(
        self,
        *,
        cursor: psycopg.Cursor,
        user_id: str,
        game_round_id: str,
        safe_reveals_count: int,
    ) -> MinesPlatformRoundLossResult:
        del user_id
        try:
            demo_session_id = self._get_demo_session_id(
                cursor=cursor,
                game_round_id=game_round_id,
            )
            recorded = record_loss(
                cursor=cursor,
                session_id=demo_session_id,
                idempotency_key=f"mines:demo:loss:{game_round_id}",
                payload={
                    "game_round_id": game_round_id,
                    "safe_reveals_count": safe_reveals_count,
                },
            )
        except DemoWalletIdempotencyConflictError as exc:
            raise MinesIdempotencyConflictError(str(exc)) from exc
        except DemoWalletValidationError as exc:
            raise MinesValidationError(str(exc)) from exc

        return MinesPlatformRoundLossResult(
            platform_round_id=game_round_id,
            wallet_balance_after=Decimal(recorded["balance_chips"]),
            bet_transaction_id=str(recorded["event_id"]),
            safe_reveals_count=safe_reveals_count,
        )

    def _get_demo_session_id(
        self,
        *,
        cursor: psycopg.Cursor,
        game_round_id: str,
    ) -> str:
        cursor.execute(
            """
            SELECT demo_play_session_id
            FROM demo_mines_game_rounds
            WHERE id = %s
              AND anonymous_id = %s
            """,
            (game_round_id, self.anonymous_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise MinesValidationError("Demo game round not found")
        return str(row["demo_play_session_id"])
