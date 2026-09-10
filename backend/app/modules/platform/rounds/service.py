from decimal import Decimal
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    ensure_game_engine_is_available_in_transaction,
)
from app.modules.platform.ledger_metadata import build_forward_ledger_metadata
from app.modules.platform.table_sessions.service import (
    TABLE_SESSION_MAX_CHIPS,
    consume_reserved_loss,
    release_reserved_loss,
    validate_and_reserve_round_exposure,
)

HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
GAME_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS = frozenset(
    {
        "ledger_transactions_idempotency_key_key",
        "platform_rounds_user_idempotency_key_key",
        "platform_rounds_provider_idempotency_key_key",
    }
)
GAME_ROUND_SETTLEMENT_IDEMPOTENCY_CONSTRAINT = "ledger_transactions_idempotency_key_key"


class PlatformRoundValidationError(Exception):
    pass


class PlatformRoundInsufficientBalanceError(Exception):
    pass


class PlatformRoundIdempotencyConflictError(Exception):
    pass


class PlatformRoundNotFoundError(Exception):
    """Il chiamante ha indicato un round che non esiste per lui."""


class PlatformRoundReplayInvariantError(Exception):
    """Un replay ledger punta a un round che la piattaforma non possiede piu'."""

class PlatformRoundCurrencyMismatchError(Exception):
    pass


class PlatformRoundAmountBelowMinimumError(Exception):
    pass


class PlatformRoundAmountAboveMaximumError(Exception):
    pass


class PlatformRoundGameCodeInvalidError(PlatformRoundValidationError):
    pass


class PlatformRoundIdempotencyKeyTooLongError(PlatformRoundValidationError):
    pass


class PlatformRoundReserveTransactionMismatchError(Exception):
    pass


class PlatformRoundWalletUnavailableError(PlatformRoundValidationError):
    pass


class PlatformRoundPlayerSuspendedError(PlatformRoundValidationError):
    """A suspended player may settle an open round, but may not open another one."""

    pass


def get_platform_round(
    *,
    round_id: str,
    user_id: str,
    viewer_role: str,
) -> dict[str, object] | None:
    """Restituisce la fotografia platform-owned di una partita reale."""
    with db_connection() as connection:
        with connection.cursor() as cursor:
            # PERCHE' la lettura non deve conoscere il gioco: questi campi sono
            # tutti proprieta' di platform_rounds e devono restare disponibili
            # quando un runtime viene portato fuori dal veicolo.
            query = """
                SELECT
                    id,
                    user_id,
                    game_code,
                    status,
                    wallet_type,
                    bet_amount,
                    payout_amount,
                    start_ledger_transaction_id,
                    wallet_balance_after_start,
                    created_at,
                    closed_at
                FROM platform_rounds
                WHERE id = %s
            """
            params: tuple[str, ...] = (round_id,)
            if viewer_role != "admin":
                query += " AND user_id = %s"
                params = (round_id, user_id)
            cursor.execute(query, params)
            row = cursor.fetchone()

    if row is None:
        return None
    return {
        "game_session_id": str(row["id"]),
        "game_code": row["game_code"],
        "status": row["status"],
        "wallet_type": row["wallet_type"],
        "bet_amount": f"{Decimal(row['bet_amount']):.6f}",
        "payout_amount": f"{Decimal(row['payout_amount']):.6f}",
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "wallet_balance_after_start": f"{Decimal(row['wallet_balance_after_start']):.6f}",
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def platform_round_exists(*, round_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM platform_rounds WHERE id = %s", (round_id,))
            return cursor.fetchone() is not None


class PlatformRoundStateConflictError(Exception):
    """Il round non e' piu' liquidabile: qualcun altro lo ha gia' chiuso."""


# Stati oltre i quali un round non si liquida piu': ha gia' avuto il suo esito.
_STATI_TERMINALI_DEL_ROUND = frozenset({"won", "lost", "cancelled"})


def namespace_game_round_win_idempotency_key(
    *,
    game_code: str,
    user_id: str,
    idempotency_key: str,
) -> str:
    normalized_game_code = _normalize_game_code(game_code)
    return f"{normalized_game_code}:cashout:{user_id}:{idempotency_key}"


def namespace_game_round_rollback_idempotency_key(
    *, game_code: str, user_id: str, idempotency_key: str
) -> str:
    return _namespace_idempotency_key(
        game_code=game_code,
        azione="rollback",
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def build_timeout_cashout_idempotency_key(
    *,
    game_code: str,
    user_id: str,
    access_session_id: str,
    round_id: str,
) -> str:
    digest = sha256(f"{access_session_id}:{round_id}".encode("utf-8")).hexdigest()[:32]
    return namespace_game_round_win_idempotency_key(
        game_code=game_code,
        user_id=user_id,
        idempotency_key=f"timeout:{digest}",
    )


def is_game_round_open_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return exc.diag.constraint_name in GAME_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS


def is_game_round_settlement_idempotency_violation(
    exc: psycopg.errors.UniqueViolation,
) -> bool:
    return exc.diag.constraint_name == GAME_ROUND_SETTLEMENT_IDEMPOTENCY_CONSTRAINT


# La colonna che ospita la chiave e' varchar(128). Una chiave piu' lunga faceva
# arrivare la richiesta fino alla INSERT e la banca dati rispondeva
# StringDataRightTruncation, che diventava un 500: un input del chiamante non deve mai
# produrre un errore di sistema, deve produrre un rifiuto che spiega cosa c'e' che non
# va. Trovato il 5/09/2026 con una chiave di 138 caratteri.
LUNGHEZZA_MASSIMA_CHIAVE_IDEMPOTENZA = 128


def _namespace_idempotency_key(
    *,
    game_code: str,
    azione: str,
    user_id: str,
    idempotency_key: str,
) -> str:
    chiave = f"{game_code}:{azione}:{user_id}:{idempotency_key}"
    if len(chiave) > LUNGHEZZA_MASSIMA_CHIAVE_IDEMPOTENZA:
        raise PlatformRoundIdempotencyKeyTooLongError(
            "Idempotency key is too long: "
            f"{len(chiave)} characters after namespacing, "
            f"maximum is {LUNGHEZZA_MASSIMA_CHIAVE_IDEMPOTENZA}"
        )
    return chiave


def open_game_round(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    user_id: str,
    game_session_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
    currency: str | None = None,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
    game_config_payload: dict[str, object] | None = None,
    request_fingerprint: str | None = None,
    seamless_request: bool = False,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    # La valuta e' un dato della richiesta seamless: va rifiutata prima di
    # riservare esposizione o acquisire lock che potrebbero toccare stato.
    if bet_amount <= 0:
        raise PlatformRoundAmountBelowMinimumError("Bet amount must be greater than zero")
    if bet_amount > TABLE_SESSION_MAX_CHIPS:
        raise PlatformRoundAmountAboveMaximumError("Bet amount exceeds the supported limit")
    _validate_wallet_currency(
        cursor=cursor,
        user_id=user_id,
        wallet_type=wallet_type,
        currency=currency,
    )
    if seamless_request:
        existing_reserve = _get_existing_seamless_reserve(
            cursor=cursor,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        if existing_reserve is not None:
            if (
                str(existing_reserve["id"]) != game_session_id
                or str(existing_reserve["game_code"]) != normalized_game_code
                or Decimal(existing_reserve["bet_amount"]) != bet_amount
                or str(existing_reserve["wallet_type"]) != wallet_type
            ):
                raise PlatformRoundIdempotencyConflictError(
                    "Idempotency key already used with a different reserve payload"
                )
            return {
                "platform_round_id": str(existing_reserve["id"]),
                "wallet_account_id": str(existing_reserve["wallet_account_id"]),
                "wallet_balance_after_start": existing_reserve["wallet_balance_after_start"],
                "ledger_transaction_id": str(existing_reserve["start_ledger_transaction_id"]),
                "table_session_id": str(existing_reserve["table_session_id"]),
                "already_exists": True,
            }
    cursor.execute("SELECT status FROM users WHERE id = %s FOR SHARE", (user_id,))
    player_row = cursor.fetchone()
    if player_row is None:
        raise PlatformRoundValidationError("Player not found")
    if player_row["status"] == "suspended":
        raise PlatformRoundPlayerSuspendedError("Suspended players cannot open a new round")
    _ensure_game_engine_is_available(
        cursor=cursor,
        game_code=normalized_game_code,
        preserve_catalog_errors=seamless_request,
    )
    
    cursor.execute("SELECT provider_code FROM game_engines WHERE engine_code = %s", (normalized_game_code,))
    provider_row = cursor.fetchone()
    if not provider_row:
        raise CatalogNotFoundError("Game engine not found")
    provider_code = provider_row["provider_code"]
    
    normalized_title_code = title_code or TITLE_CODE_MINES_CLASSIC

    normalized_site_code = site_code or SITE_CODE_CASINOKING
    platform_round_id = game_session_id
    cursor.execute(
        """
        SELECT status
        FROM platform_rounds
        WHERE id = %s
          AND user_id = %s
          AND game_code = %s
        FOR UPDATE
        """,
        (platform_round_id, user_id, normalized_game_code),
    )
    if cursor.fetchone() is not None:
        raise PlatformRoundStateConflictError("Round already exists")
    table_session = validate_and_reserve_round_exposure(
        cursor=cursor,
        user_id=user_id,
        table_session_id=table_session_id,
        game_code=normalized_game_code,
        wallet_type=wallet_type,
        bet_amount=bet_amount,
        access_session_id=access_session_id,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
    )
    cursor.execute(
        """
        SELECT
            wa.id,
            wa.wallet_type,
            wa.balance_snapshot,
            la.id AS ledger_account_id,
            la.currency_code
        FROM wallet_accounts wa
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE wa.user_id = %s
          AND wa.wallet_type = %s
          AND wa.status = 'active'
        FOR UPDATE
        """,
        (user_id, wallet_type),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundWalletUnavailableError("Selected wallet is not available")
    if wallet_row["balance_snapshot"] < bet_amount:
        raise PlatformRoundInsufficientBalanceError("Not enough available balance")

    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (HOUSE_CASH_ACCOUNT_CODE,),
    )
    house_cash_account = cursor.fetchone()
    if house_cash_account is None:
        raise PlatformRoundValidationError("Required system account is missing")

    transaction_id = str(uuid4())
    wallet_balance_after_start = wallet_row["balance_snapshot"] - bet_amount
    namespaced_idempotency_key = _namespace_idempotency_key(
        game_code=normalized_game_code,
        azione="start",
        user_id=user_id,
        idempotency_key=idempotency_key,
    )

    cursor.execute(
        """
        INSERT INTO ledger_transactions (
            id,
            user_id,
            transaction_type,
            reference_type,
            reference_id,
            idempotency_key,
            metadata_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            transaction_id,
            user_id,
            "bet",
            "game_session",
            game_session_id,
            namespaced_idempotency_key,
            json.dumps(
                build_forward_ledger_metadata(
                    game_code=normalized_game_code,
                    title_code=normalized_title_code,
                    site_code=normalized_site_code,
                    wallet_type=wallet_type,
                    platform_round_id=game_session_id,
                    game_round_id=game_session_id,
                    access_session_id=access_session_id,
                    settlement_kind=None,
                    idempotency_key=namespaced_idempotency_key,
                    replay_ref=None,
                    game_config_payload=game_config_payload
                    or {
                        "grid_size": grid_size,
                        "mine_count": mine_count,
                    },
                ),
                separators=(",", ":"),
                sort_keys=True,
            ),
        ),
    )
    cursor.execute(
        """
        INSERT INTO ledger_entries (
            id,
            transaction_id,
            ledger_account_id,
            entry_side,
            amount
        )
        VALUES
            (%s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s)
        """,
        (
            str(uuid4()),
            transaction_id,
            wallet_row["ledger_account_id"],
            "debit",
            bet_amount,
            str(uuid4()),
            transaction_id,
            house_cash_account["id"],
            "credit",
            bet_amount,
        ),
    )
    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot - %s
        WHERE id = %s
        """,
        (bet_amount, wallet_row["id"]),
    )
    cursor.execute(
        """
        INSERT INTO platform_rounds (
            id,
            user_id,
            game_code,
            provider_code,
            title_code,
            site_code,
            access_session_id,
            wallet_account_id,
            wallet_type,
            bet_amount,
            status,
            payout_amount,
            start_ledger_transaction_id,
            wallet_balance_after_start,
            table_session_id,
            idempotency_key,
            request_fingerprint
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            platform_round_id,
            user_id,
            normalized_game_code,
            provider_code,
            normalized_title_code,
            normalized_site_code,
            access_session_id,
            wallet_row["id"],
            wallet_type,
            bet_amount,
            Decimal("0.000000"),
            transaction_id,
            wallet_balance_after_start,
            table_session["id"],
            idempotency_key,
            request_fingerprint,
        ),
    )
    platform_round_row = cursor.fetchone()

    return {
        "platform_round_id": str(platform_round_row["id"]),
        "wallet_account_id": wallet_row["id"],
        "wallet_balance_after_start": wallet_balance_after_start,
        "ledger_transaction_id": transaction_id,
        "table_session_id": table_session["id"],
        "table_session": table_session,
    }


def _get_existing_seamless_reserve(
    *, cursor: psycopg.Cursor, user_id: str, idempotency_key: str
) -> dict[str, object] | None:
    """Restituisce la prima reserve seamless senza riapplicare la trattenuta."""
    cursor.execute(
        """
        SELECT
            id,
            game_code,
            wallet_account_id,
            wallet_type,
            bet_amount,
            wallet_balance_after_start,
            start_ledger_transaction_id,
            table_session_id
        FROM platform_rounds
        WHERE user_id = %s
          AND idempotency_key = %s
        FOR UPDATE
        """,
        (user_id, idempotency_key),
    )
    return cursor.fetchone()


def get_existing_round_win_by_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT id, reference_id, metadata_json
        FROM ledger_transactions
        WHERE idempotency_key = %s
          AND transaction_type = 'win'
          AND reference_type = 'game_session'
        """,
        (idempotency_key,),
    )
    return cursor.fetchone()


def get_game_round_cashout_snapshot(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            pr.game_code,
            pr.idempotency_key,
            pr.payout_amount AS payout_current,
            (pr.wallet_balance_after_start + pr.payout_amount) AS wallet_balance_after,
            la.currency_code
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
        """,
        (game_session_id, user_id),
    )
    return cursor.fetchone()


def _validate_wallet_currency(
    *, cursor: psycopg.Cursor, user_id: str, wallet_type: str, currency: str | None
) -> None:
    """Valida la valuta seamless prima di riservare esposizione o acquisire lock."""
    if currency is None:
        return
    cursor.execute(
        """
        SELECT la.currency_code
        FROM wallet_accounts wa
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE wa.user_id = %s
          AND wa.wallet_type = %s
          AND wa.status = 'active'
        """,
        (user_id, wallet_type),
    )
    row = cursor.fetchone()
    if row is None:
        raise PlatformRoundWalletUnavailableError("Selected wallet is not available")
    if currency != row["currency_code"]:
        raise PlatformRoundCurrencyMismatchError("Wallet currency does not match request currency")


def _validate_round_currency(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
    game_code: str,
    currency: str | None,
) -> None:
    """Confronta la valuta richiesta con il conto reale del round.

    Non usa una costante di protocollo: la moneta appartiene al ledger account
    collegato al round. E' una lettura prima di qualsiasi scrittura o lock di
    liquidazione; il lock successivo resta responsabile della concorrenza.
    """
    if currency is None:
        return
    cursor.execute(
        """
        SELECT la.currency_code
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
          AND pr.game_code = %s
        """,
        (game_session_id, user_id, game_code),
    )
    row = cursor.fetchone()
    if row is None:
        raise PlatformRoundNotFoundError("Platform round not found")
    if currency != row["currency_code"]:
        raise PlatformRoundCurrencyMismatchError("Wallet currency does not match request currency")


def _validate_reserve_transaction(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
    game_code: str,
    reserve_idempotency_key: str | None,
) -> None:
    """Lega commit e rollback alla stessa reserve che ha aperto il round."""
    if reserve_idempotency_key is None:
        return
    cursor.execute(
        """
        SELECT idempotency_key
        FROM platform_rounds
        WHERE id = %s
          AND user_id = %s
          AND game_code = %s
        """,
        (game_session_id, user_id, game_code),
    )
    row = cursor.fetchone()
    if row is None:
        raise PlatformRoundNotFoundError("Platform round not found")
    if row["idempotency_key"] != reserve_idempotency_key:
        raise PlatformRoundReserveTransactionMismatchError(
            "Reserve transaction does not belong to this round"
        )


def settle_game_round_loss(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    user_id: str,
    game_session_id: str,
    safe_reveals_count: int,
    settlement_kind: str = "loss",
    record_settlement_ledger_transaction: bool = False,
    seamless_request: bool = False,
    currency: str | None = None,
    reserve_idempotency_key: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    _ensure_game_engine_is_available(
        cursor=cursor,
        game_code=normalized_game_code,
        preserve_catalog_errors=seamless_request,
    )
    _validate_round_currency(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        currency=currency,
    )
    _validate_reserve_transaction(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        reserve_idempotency_key=reserve_idempotency_key,
    )
    cursor.execute(
        """
        SELECT
            wa.id,
            wa.balance_snapshot,
            wa.wallet_type,
            pr.table_session_id,
            pr.bet_amount,
            pr.title_code,
            pr.site_code,
            pr.access_session_id
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
          AND pr.game_code = %s
        FOR UPDATE OF wa, pr
        """,
        (game_session_id, user_id, normalized_game_code),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundWalletUnavailableError("Selected wallet is not available")

    cursor.execute(
        """
        SELECT id
        FROM ledger_transactions
        WHERE user_id = %s
          AND transaction_type = 'bet'
          AND reference_type = 'game_session'
          AND reference_id = %s
        """,
        (user_id, game_session_id),
    )
    bet_row = cursor.fetchone()
    if bet_row is None:
        raise PlatformRoundValidationError("Round bet transaction is not available")

    cursor.execute(
        """
        SELECT id
        FROM ledger_transactions
        WHERE user_id = %s
          AND transaction_type = 'win'
          AND reference_type = 'game_session'
          AND reference_id = %s
        """,
        (user_id, game_session_id),
    )
    win_row = cursor.fetchone()
    if win_row is not None:
        raise PlatformRoundStateConflictError("Round is already settled as win")

    table_session = consume_reserved_loss(
        cursor=cursor,
        table_session_id=(
            str(wallet_row["table_session_id"]) if wallet_row["table_session_id"] else None
        ),
        bet_amount=Decimal(wallet_row["bet_amount"]),
    )
    loss_metadata = build_forward_ledger_metadata(
        game_code=normalized_game_code,
        title_code=str(wallet_row["title_code"]),
        site_code=str(wallet_row["site_code"]),
        wallet_type=str(wallet_row["wallet_type"]),
        platform_round_id=game_session_id,
        game_round_id=game_session_id,
        access_session_id=(
            str(wallet_row["access_session_id"]) if wallet_row["access_session_id"] else None
        ),
        settlement_kind=settlement_kind,
        idempotency_key=None,
        replay_ref={"game_code": normalized_game_code, "round_id": game_session_id},
        progress_payload={"safe_reveals_count": safe_reveals_count},
    )
    cursor.execute(
        """
        UPDATE ledger_transactions
        SET metadata_json = metadata_json || %s::jsonb
        WHERE id = %s
        """,
        (
            json.dumps(loss_metadata, separators=(",", ":"), sort_keys=True),
            bet_row["id"],
        ),
    )
    cursor.execute(
        """
        UPDATE platform_rounds
        SET status = 'lost',
            payout_amount = %s,
            settlement_ledger_transaction_id = CASE
                WHEN %s THEN %s
                ELSE settlement_ledger_transaction_id
            END,
            closed_at = now()
        WHERE id = %s
          AND game_code = %s
        """,
        (
            Decimal("0.000000"),
            record_settlement_ledger_transaction,
            bet_row["id"],
            game_session_id,
            normalized_game_code,
        ),
    )

    return {
        "platform_round_id": game_session_id,
        "bet_transaction_id": str(bet_row["id"]),
        "wallet_balance_after": wallet_row["balance_snapshot"],
        "safe_reveals_count": safe_reveals_count,
        "table_session": table_session,
    }


def settle_game_round_win(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    user_id: str,
    game_session_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
    settlement_kind: str = "manual_cashout",
    seamless_request: bool = False,
    currency: str | None = None,
    reserve_idempotency_key: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    if payout_amount > TABLE_SESSION_MAX_CHIPS:
        raise PlatformRoundAmountAboveMaximumError("Settlement amount exceeds the supported limit")
    existing_cashout = get_existing_round_win_by_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )
    if existing_cashout is not None:
        if str(existing_cashout["reference_id"]) != game_session_id:
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different payload"
            )
        snapshot = get_game_round_cashout_snapshot(
            cursor=cursor, user_id=user_id, game_session_id=game_session_id
        )
        if snapshot is None:
            raise PlatformRoundReplayInvariantError("Platform round not found for replay")
        if Decimal(snapshot["payout_current"]) != payout_amount:
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different payload"
            )
        if (
            str(snapshot["game_code"]) != normalized_game_code
            or (
                reserve_idempotency_key is not None
                and snapshot["idempotency_key"] != reserve_idempotency_key
            )
            or (currency is not None and currency != snapshot["currency_code"])
        ):
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different payload"
            )
        metadata = existing_cashout["metadata_json"]
        persisted_balance = (
            metadata.get("wallet_balance_after")
            if isinstance(metadata, dict)
            else None
        )
        return {
            "platform_round_id": game_session_id,
            "ledger_transaction_id": str(existing_cashout["id"]),
            # I record anteriori a RIP-02 non hanno ancora la fotografia: per
            # loro resta il calcolo storico, mentre ogni nuovo commit conserva
            # esattamente la prima risposta sotto la sua stessa transazione.
            "wallet_balance_after": persisted_balance or snapshot["wallet_balance_after"],
            # La risposta seamless e' il replay della prima, non una risposta
            # diagnostica diversa: il chiamante deve poterla riutilizzare tale e quale.
            "already_exists": True,
        }

    _ensure_game_engine_is_available(
        cursor=cursor,
        game_code=normalized_game_code,
        preserve_catalog_errors=seamless_request,
    )
    _validate_round_currency(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        currency=currency,
    )
    _validate_reserve_transaction(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        reserve_idempotency_key=reserve_idempotency_key,
    )

    cursor.execute(
        """
        SELECT
            wa.id,
            wa.balance_snapshot,
            wa.wallet_type,
            la.id AS ledger_account_id,
            pr.status,
            pr.table_session_id,
            pr.bet_amount,
            pr.title_code,
            pr.site_code,
            pr.access_session_id
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
          AND pr.game_code = %s
        FOR UPDATE OF wa, pr
        """,
        (game_session_id, user_id, normalized_game_code),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundWalletUnavailableError("Selected wallet is not available")

    # PERCHE' SI RILEGGE LO STATO QUI, E NON PRIMA. Fra il controllo che il chiamante fa
    # sullo stato e questa riga c'e' il tempo di attesa del lock, e in quel tempo un'altra
    # transazione puo' aver gia' liquidato il round — per esempio la liquidazione
    # d'ufficio alla chiusura della sessione. Senza questo controllo si pagherebbe DUE
    # VOLTE: la chiave di idempotenza non protegge, perche' le due strade ne usano una
    # diversa. Il controllo del chiamante vale solo se fatto sotto lo stesso lock, e
    # pretenderlo da ogni gioco e' esattamente il genere di promessa che prima o poi
    # qualcuno non mantiene. Qui e' la piattaforma a rifiutare, per tutti.
    stato_del_round = str(wallet_row["status"])
    if stato_del_round in _STATI_TERMINALI_DEL_ROUND:
        raise PlatformRoundStateConflictError(
            f"Round {game_session_id} is already settled as {stato_del_round}"
        )

    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (HOUSE_CASH_ACCOUNT_CODE,),
    )
    house_cash_account = cursor.fetchone()
    if house_cash_account is None:
        raise PlatformRoundValidationError("Required system account is missing")

    wallet_balance_after = (
        wallet_row["balance_snapshot"] + payout_amount
    ).quantize(Decimal("0.000001"))
    transaction_id = str(uuid4())

    cursor.execute(
        """
        INSERT INTO ledger_transactions (
            id,
            user_id,
            transaction_type,
            reference_type,
            reference_id,
            idempotency_key,
            metadata_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            transaction_id,
            user_id,
            "win",
            "game_session",
            game_session_id,
            idempotency_key,
            json.dumps(
                build_forward_ledger_metadata(
                    game_code=normalized_game_code,
                    title_code=str(wallet_row["title_code"]),
                    site_code=str(wallet_row["site_code"]),
                    wallet_type=str(wallet_row["wallet_type"]),
                    platform_round_id=game_session_id,
                    game_round_id=game_session_id,
                    access_session_id=(
                        str(wallet_row["access_session_id"])
                        if wallet_row["access_session_id"]
                        else None
                    ),
                    settlement_kind=settlement_kind,
                    idempotency_key=idempotency_key,
                    replay_ref={"game_code": normalized_game_code, "round_id": game_session_id},
                    progress_payload={"safe_reveals_count": safe_reveals_count},
                )
                | {"wallet_balance_after": str(wallet_balance_after)},
                separators=(",", ":"),
                sort_keys=True,
            ),
        ),
    )
    cursor.execute(
        """
        INSERT INTO ledger_entries (
            id,
            transaction_id,
            ledger_account_id,
            entry_side,
            amount
        )
        VALUES
            (%s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s)
        """,
        (
            str(uuid4()),
            transaction_id,
            house_cash_account["id"],
            "debit",
            payout_amount,
            str(uuid4()),
            transaction_id,
            wallet_row["ledger_account_id"],
            "credit",
            payout_amount,
        ),
    )
    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot + %s
        WHERE id = %s
        """,
        (payout_amount, wallet_row["id"]),
    )
    table_session = release_reserved_loss(
        cursor=cursor,
        table_session_id=(
            str(wallet_row["table_session_id"]) if wallet_row["table_session_id"] else None
        ),
        bet_amount=Decimal(wallet_row["bet_amount"]),
        payout_amount=payout_amount,
    )
    # CON-05 (10/09/2026) — UN RIMBORSO NON E' UNA VINCITA, NEMMENO QUI.
    #
    # Fino a oggi questa riga scriveva 'won' SEMPRE, anche quando la liquidazione era un
    # rimborso senza progresso: il giocatore riprende la puntata perche' non e' successo
    # niente, e agli atti risultava una vincita.
    #
    # NON E' UNA DECISIONE NUOVA: e' la META' MANCANTE di una riparazione gia' fatta.
    # Il commit 0ec8fcf dell'8/09/2026 ("Le liquidazioni d'ufficio sono CANCELLED, non WON:
    # 278 vincite mai avvenute") ha corretto la tabella del GIOCO e non questa, che e' la
    # tabella della PIATTAFORMA. [GENERATO] Su 420 partite le due si contraddicevano — il
    # gioco diceva cancelled, la piattaforma won — e la piattaforma e' quella che il
    # giocatore legge: account/service.py la espone come `result` e il frontend la traduce
    # in "Vinto", sommandola al totale vinto.
    #
    # PERCHE' 'cancelled' E NON UNO STATO NUOVO: esiste gia' nel vincolo ed e' terminale,
    # il frontend lo mostra gia' come "Annullato" escludendolo dal totale vinto e dal
    # totale giocato (giusto: la puntata e' stata restituita), ed e' la stessa parola che
    # la riparazione dell'8/09 ha scelto per il lato gioco.
    #
    # NON SI DEDUCE DALL'IMPORTO. Si potrebbe pensare "payout == bet quindi e' un rimborso",
    # ma una vincita puo' legittimamente pagare quanto la puntata. L'informazione esatta
    # c'e' gia' ed e' il motivo della liquidazione, che arriva come parametro.
    stato_finale = "cancelled" if settlement_kind == "refund_no_progress" else "won"
    cursor.execute(
        """
        UPDATE platform_rounds
        SET status = %s,
            payout_amount = %s,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
          AND game_code = %s
        """,
        (stato_finale, payout_amount, transaction_id, game_session_id, normalized_game_code),
    )

    return {
        "platform_round_id": game_session_id,
        "ledger_transaction_id": transaction_id,
        "wallet_balance_after": wallet_balance_after,
        "already_exists": False,
        "table_session": table_session,
    }


def force_cancel_platform_round(
    cursor: psycopg.Cursor,
    *,
    round_id: str,
    settlement_ledger_transaction_id: str,
) -> None:
    """Mark a platform round as cancelled by admin force-close.

    Writes ONLY ``platform_rounds``; the caller is responsible for
    game-specific tables, ledger entries, and audit rows.
    """
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = 'cancelled',
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
          AND status = 'active'
        """,
        (settlement_ledger_transaction_id, round_id),
    )


def _normalize_game_code(game_code: str) -> str:
    normalized = game_code.strip().lower()
    if not normalized:
        raise PlatformRoundGameCodeInvalidError("Game code is required")
    return normalized


def _ensure_game_engine_is_available(
    *, cursor: psycopg.Cursor, game_code: str, preserve_catalog_errors: bool = False
) -> None:
    try:
        ensure_game_engine_is_available_in_transaction(cursor=cursor, game_code=game_code)
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        if preserve_catalog_errors:
            raise
        raise PlatformRoundValidationError(str(exc)) from exc






def rollback_game_round(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    user_id: str,
    game_session_id: str,
    idempotency_key: str,
    seamless_request: bool = False,
    currency: str | None = None,
    reserve_idempotency_key: str | None = None,
) -> dict[str, object]:
    from app.modules.platform.ledger.registrazione import registra_movimento, RigaScrittura
    import json
    from decimal import Decimal
    from uuid import uuid4
    
    normalized_game_code = _normalize_game_code(game_code)
    _ensure_game_engine_is_available(
        cursor=cursor,
        game_code=normalized_game_code,
        preserve_catalog_errors=seamless_request,
    )

    # Check if already rolled back
    cursor.execute(
        """
        SELECT id, reference_id
        FROM ledger_transactions
        WHERE idempotency_key = %s
          AND transaction_type = 'rollback'
          AND reference_type = 'game_session'
        """,
        (idempotency_key,)
    )
    existing = cursor.fetchone()
    if existing is not None:
        if str(existing["reference_id"]) != game_session_id:
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different rollback payload"
            )
        # Re-read snapshot
        cursor.execute(
            """
            SELECT
                pr.id,
                pr.game_code,
                pr.idempotency_key,
                wa.balance_snapshot,
                la.currency_code
            FROM platform_rounds pr
            JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
            JOIN ledger_accounts la ON la.id = wa.ledger_account_id
            WHERE pr.id = %s
              AND pr.user_id = %s
            """,
            (game_session_id, user_id)
        )
        pr_row = cursor.fetchone()
        if pr_row is None:
            raise PlatformRoundReplayInvariantError("Platform round not found for replay")
        if (
            str(pr_row["game_code"]) != normalized_game_code
            or (
                reserve_idempotency_key is not None
                and pr_row["idempotency_key"] != reserve_idempotency_key
            )
            or (currency is not None and currency != pr_row["currency_code"])
        ):
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different rollback payload"
            )
        return {
            "platform_round_id": game_session_id,
            "rollback_transaction_id": str(existing["id"]),
            "wallet_balance_after": pr_row["balance_snapshot"],
            "already_exists": True,
        }

    _validate_round_currency(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        currency=currency,
    )
    _validate_reserve_transaction(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_session_id,
        game_code=normalized_game_code,
        reserve_idempotency_key=reserve_idempotency_key,
    )

    # Lock round and wallet
    cursor.execute(
        """
        SELECT
            wa.id AS wallet_account_id,
            wa.balance_snapshot,
            wa.ledger_account_id,
            pr.status,
            pr.bet_amount,
            pr.title_code,
            pr.site_code,
            pr.wallet_type,
            pr.access_session_id
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
          AND pr.game_code = %s
        FOR UPDATE OF pr, wa
        """,
        (game_session_id, user_id, normalized_game_code)
    )
    row = cursor.fetchone()
    if row is None:
        raise PlatformRoundNotFoundError("Platform round not found")
        
    if str(row["status"]) != 'active':
        raise PlatformRoundIdempotencyConflictError("Round is not active")
        
    bet_amount = Decimal(row["bet_amount"])
    transaction_id = str(uuid4())
    
    # Get house account
    cursor.execute(
        "SELECT id FROM ledger_accounts WHERE account_code = %s",
        (HOUSE_CASH_ACCOUNT_CODE,)
    )
    house_account = cursor.fetchone()
    if house_account is None:
        raise PlatformRoundValidationError(f"Missing {HOUSE_CASH_ACCOUNT_CODE} account")
    
    metadata = {
        "game_code": normalized_game_code,
        "platform_round_id": game_session_id,
        "game_round_id": game_session_id,
        "settlement_kind": "rollback",
    }
    
    righe = [
        RigaScrittura(ledger_account_id=str(house_account["id"]), entry_side="debit", amount=bet_amount),
        RigaScrittura(ledger_account_id=str(row["ledger_account_id"]), entry_side="credit", amount=bet_amount),
    ]
    
    esito = registra_movimento(
        cursor=cursor,
        user_id=user_id,
        transaction_type="rollback",
        idempotency_key=idempotency_key,
        righe=righe,
        reference_type="game_session",
        reference_id=game_session_id,
        metadata=metadata,
        transaction_id=transaction_id,
    )
    
    # Update round
    cursor.execute(
        """
        UPDATE platform_rounds
        SET status = 'cancelled',
            payout_amount = 0,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (transaction_id, game_session_id)
    )
    
    # Rileggiamo il saldo per essere sicuri
    cursor.execute(
        """
        SELECT balance_snapshot
        FROM wallet_accounts
        WHERE id = %s
        """,
        (row["wallet_account_id"],)
    )
    wa_row = cursor.fetchone()
    
    return {
        "platform_round_id": game_session_id,
        "rollback_transaction_id": transaction_id,
        "wallet_balance_after": wa_row["balance_snapshot"],
        "already_exists": False,
    }
