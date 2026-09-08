"""Traduzioni esplicite degli errori di dominio del confine seamless.

Questo elenco e' intenzionalmente chiuso: un'eccezione non nominata qui deve
restare un guasto 500, non trasformarsi in un rifiuto del chiamante.
"""
from __future__ import annotations

from app.modules.platform.rounds.service import (
    PlatformRoundIdempotencyConflictError as _PlatformRoundIdempotencyConflictError,
    PlatformRoundInsufficientBalanceError as _PlatformRoundInsufficientBalanceError,
    PlatformRoundNotFoundError as _PlatformRoundNotFoundError,
    PlatformRoundCurrencyMismatchError as _PlatformRoundCurrencyMismatchError,
    PlatformRoundAmountBelowMinimumError as _PlatformRoundAmountBelowMinimumError,
    PlatformRoundAmountAboveMaximumError as _PlatformRoundAmountAboveMaximumError,
    PlatformRoundStateConflictError as _PlatformRoundStateConflictError,
    PlatformRoundGameCodeInvalidError as _PlatformRoundGameCodeInvalidError,
    PlatformRoundIdempotencyKeyTooLongError as _PlatformRoundIdempotencyKeyTooLongError,
    PlatformRoundReserveTransactionMismatchError as _PlatformRoundReserveTransactionMismatchError,
    PlatformRoundPlayerSuspendedError as _PlatformRoundPlayerSuspendedError,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError as _CatalogNotFoundError,
    CatalogProviderSuspendedError as _CatalogProviderSuspendedError,
)
from app.modules.platform.table_sessions.service import (
    TableSessionInsufficientBalanceError as _TableSessionInsufficientBalanceError,
    TableSessionLimitExceededError as _TableSessionLimitExceededError,
)

__all__ = ["SEAMLESS_ERROR_TRANSLATIONS", "translate_seamless_error"]


SEAMLESS_ERROR_TRANSLATIONS: dict[type[Exception], tuple[int, str]] = {
    _PlatformRoundInsufficientBalanceError: (422, "CK.WALLET.INSUFFICIENT_BALANCE"),
    _PlatformRoundNotFoundError: (422, "CK.SEAMLESS.ROUND_NOT_FOUND"),
    _PlatformRoundCurrencyMismatchError: (422, "CK.SEAMLESS.CURRENCY_MISMATCH"),
    _PlatformRoundAmountBelowMinimumError: (422, "CK.SEAMLESS.AMOUNT_BELOW_MINIMUM"),
    _PlatformRoundAmountAboveMaximumError: (422, "CK.SEAMLESS.AMOUNT_ABOVE_MAXIMUM"),
    _PlatformRoundIdempotencyConflictError: (409, "CK.LEDGER.IDEMPOTENCY_CONFLICT"),
    _PlatformRoundStateConflictError: (409, "CK.GAME.ROUND_CLOSED"),
    _PlatformRoundGameCodeInvalidError: (422, "CK.SEAMLESS.GAME_CODE_INVALID"),
    _PlatformRoundIdempotencyKeyTooLongError: (422, "CK.SEAMLESS.IDEMPOTENCY_KEY_TOO_LONG"),
    _PlatformRoundReserveTransactionMismatchError: (422, "CK.SEAMLESS.RESERVE_TRANSACTION_MISMATCH"),
    _PlatformRoundPlayerSuspendedError: (422, "CK.AUTH.PLAYER_SUSPENDED"),
    _CatalogNotFoundError: (404, "CK.SEAMLESS.GAME_NOT_FOUND"),
    _CatalogProviderSuspendedError: (422, "CK.SEAMLESS.PROVIDER_SUSPENDED"),
    _TableSessionInsufficientBalanceError: (422, "CK.WALLET.INSUFFICIENT_BALANCE"),
    _TableSessionLimitExceededError: (422, "CK.SEAMLESS.AMOUNT_ABOVE_MAXIMUM"),
}


def translate_seamless_error(exc: Exception) -> tuple[int, str] | None:
    """Restituisce la traduzione soltanto per una classe esplicitamente elencata."""
    return SEAMLESS_ERROR_TRANSLATIONS.get(type(exc))
