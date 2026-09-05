"""Servizio del manichino: due operazioni, nessuna regola di gioco.

PERCHE' ESISTE: i test della piattaforma hanno bisogno di una cavia che muova
denaro vero attraverso le tubature vere (round economico, ledger, sessioni
tavolo) con l'esito deciso da chi chiama. Il manichino e' quella cavia:
`apri_round` trattiene l'importo, `chiudi_round` accredita o consuma.

PERCHE' DETERMINISTICO: niente `random`, niente `secrets`. L'id del round e'
`uuid5` della chiave di idempotenza, cosi' una ripetizione della stessa
richiesta riapre lo STESSO round invece di crearne uno nuovo: un manichino
che tira i dadi renderebbe intermittenti proprio i test che deve stabilizzare.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import NAMESPACE_URL, uuid5

import psycopg

from app.modules.games.manichino import GAME_CODE_MANICHINO, TITLE_CODE_MANICHINO_TEST
from app.modules.games.manichino.exceptions import (
    ManichinoSessionVoidedByOperatorError,
    ManichinoGameStateConflictError,
    ManichinoIdempotencyConflictError,
    ManichinoValidationError,
)
from app.modules.games.manichino.round_gateway import (
    build_settle_idempotency_key,
    open_round,
    settle_round_loss,
    settle_round_win,
)
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)

GAME_CODE = GAME_CODE_MANICHINO
SITE_CODE_CASINOKING = "casinoking"
ESITO_VINCITA = "vincita"
ESITO_PERDITA = "perdita"


def apri_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    bet_amount: str,
    wallet_type: str,
    idempotency_key: str,
    title_code: str | None = None,
    site_code: str | None = None,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> dict[str, object]:
    """Trattiene l'importo aprendo il round economico.

    Restituisce il dettato della risposta con `game_session_id` e
    `wallet_balance_after_start`. Con la stessa `Idempotency-Key` la
    piattaforma solleva UniqueViolation e la rotta risponde con il round
    esistente: nessuna doppia scrittura contabile.
    """
    bet_amount_decimal = _parse_amount(bet_amount, field_name="bet_amount")
    normalized_wallet_type = wallet_type.strip().lower()
    if normalized_wallet_type not in {"cash", "demo"}:
        raise ManichinoValidationError("wallet_type must be cash or demo")
    normalized_title_code = _normalize_code(
        title_code or TITLE_CODE_MANICHINO_TEST,
        field_name="title_code",
    )
    normalized_site_code = _normalize_code(
        site_code or SITE_CODE_CASINOKING,
        field_name="site_code",
    )
    # PERCHE' uuid5 e non uuid4: l'id del round deriva dalla chiave di
    # idempotenza. Un retry con la stessa chiave punta allo stesso round e
    # urta il vincolo UNIQUE della piattaforma invece di creare un doppione.
    game_round_id = str(
        uuid5(NAMESPACE_URL, f"manichino:start:{user_id}:{idempotency_key}")
    )
    request_fingerprint = _build_request_fingerprint(
        user_id=user_id,
        bet_amount=bet_amount_decimal,
        wallet_type=normalized_wallet_type,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )

    if normalized_wallet_type == "demo":
        # Il demo non passa dal round economico reale: usa il portafoglio demo
        # della piattaforma, gia' idempotente per chiave.
        try:
            demo_session = open_demo_session(
                cursor=cursor,
                anonymous_id=user_id,
                title_code=normalized_title_code,
            )
            demo_session = debit_for_bet(
                cursor=cursor,
                session_id=str(demo_session["id"]),
                amount=bet_amount_decimal,
                idempotency_key=f"manichino:demo:bet:{game_round_id}",
                payload={
                    "game_round_id": game_round_id,
                    "title_code": normalized_title_code,
                },
            )
        except DemoWalletIdempotencyConflictError as exc:
            raise ManichinoIdempotencyConflictError(str(exc)) from exc
        return {
            "game_session_id": game_round_id,
            "status": "active",
            "mode": "demo",
            "bet_amount": _format_amount(bet_amount_decimal),
            "wallet_type": "demo",
            "title_code": normalized_title_code,
            "site_code": normalized_site_code,
            "wallet_balance_after_start": _format_amount(
                Decimal(demo_session["balance_chips"])
            ),
            "ledger_transaction_id": None,
            "table_session_id": None,
        }

    result = open_round(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
        idempotency_key=idempotency_key,
        bet_amount=bet_amount_decimal,
        wallet_type=normalized_wallet_type,
        table_session_id=table_session_id,
        access_session_id=access_session_id,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
        request_fingerprint=request_fingerprint,
    )
    return {
        "game_session_id": game_round_id,
        "status": "active",
        "bet_amount": _format_amount(bet_amount_decimal),
        "wallet_type": normalized_wallet_type,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "wallet_balance_after_start": _format_amount(result.wallet_balance_after_start),
        "ledger_transaction_id": result.ledger_transaction_id,
        "table_session_id": result.table_session_id,
        "table_session": result.table_session,
    }


def chiudi_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    esito: str,
    idempotency_key: str,
    payout_amount: str | None = None,
) -> dict[str, object]:
    """Chiude il round: con "vincita" accredita il payout, con "perdita" no.

    Idempotente: una vincita ripetuta con la stessa chiave urta il vincolo
    UNIQUE del ledger e la piattaforma restituisce la scrittura esistente
    (`already_exists`); una perdita ripetuta rilegge lo stato del round e non
    scrive di nuovo.
    """
    normalized_esito = esito.strip().lower()
    if normalized_esito not in {ESITO_VINCITA, ESITO_PERDITA}:
        raise ManichinoValidationError("esito must be vincita or perdita")
    if normalized_esito == ESITO_VINCITA:
        if payout_amount is None:
            raise ManichinoValidationError(
                "payout_amount is required when esito is vincita"
            )
        payout_decimal = _parse_amount(payout_amount, field_name="payout_amount")
    else:
        payout_decimal = None

    round_row = _get_platform_round(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
    )

    if round_row is None:
        return _chiudi_round_demo(
            cursor=cursor,
            user_id=user_id,
            game_round_id=game_round_id,
            esito=normalized_esito,
            payout_amount=payout_decimal,
        )

    _rifiuta_se_la_sessione_e_stata_chiusa_da_un_operatore(
        cursor=cursor,
        game_round_id=game_round_id,
    )

    status = str(round_row["status"])
    if status == "cancelled":
        raise ManichinoGameStateConflictError("Round was closed by an operator")
    if status == "lost":
        if normalized_esito != ESITO_PERDITA:
            raise ManichinoGameStateConflictError("Round is already settled as lost")
        # PERCHE' si risponde senza scrivere: la perdita non ha una chiave
        # contabile propria (la piattaforma aggiorna la transazione di bet),
        # quindi il replay rilegge lo stato e basta.
        return {
            "game_session_id": game_round_id,
            "status": "lost",
            "wallet_balance_after": _format_amount(
                Decimal(round_row["wallet_balance"])
            ),
            "ledger_transaction_id": str(round_row["start_ledger_transaction_id"]),
            "already_exists": True,
        }
    if status == "won" and normalized_esito != ESITO_VINCITA:
        raise ManichinoGameStateConflictError("Round is already settled as won")

    if normalized_esito == ESITO_PERDITA:
        result = settle_round_loss(
            cursor=cursor,
            user_id=user_id,
            game_round_id=game_round_id,
        )
        return {
            "game_session_id": game_round_id,
            "status": "lost",
            "wallet_balance_after": _format_amount(result.wallet_balance_after),
            "ledger_transaction_id": result.bet_transaction_id,
            "already_exists": False,
        }

    assert payout_decimal is not None
    result = settle_round_win(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
        payout_amount=payout_decimal,
        idempotency_key=build_settle_idempotency_key(
            user_id=user_id,
            idempotency_key=idempotency_key,
        ),
    )
    return {
        "game_session_id": game_round_id,
        "status": "won",
        "payout_amount": _format_amount(payout_decimal),
        "wallet_balance_after": _format_amount(result.wallet_balance_after),
        "ledger_transaction_id": result.ledger_transaction_id,
        "already_exists": result.already_exists,
    }


def _rifiuta_se_la_sessione_e_stata_chiusa_da_un_operatore(
    *,
    cursor: psycopg.Cursor,
    game_round_id: str,
) -> None:
    """La decisione dell'operatore deve arrivare al giocatore per quello che e'.

    Si guarda la sessione di accesso a cui il round e' appeso: e' un dato della
    PIATTAFORMA, e non serve sapere niente del gioco per leggerlo.
    """
    cursor.execute(
        """
        SELECT gas.status, gas.closed_reason
        FROM platform_rounds pr
        JOIN game_access_sessions gas ON gas.id = pr.access_session_id
        WHERE pr.id = %s
        """,
        (game_round_id,),
    )
    riga = cursor.fetchone()
    if riga is None:
        return
    if str(riga["status"]) != "active" and str(riga["closed_reason"]) == "admin_voided":
        raise ManichinoSessionVoidedByOperatorError(
            "Access session was closed by an operator"
        )


def get_open_round_by_idempotency_key(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    """Rilegge un round aperto dalla chiave di idempotenza (replay di start)."""
    cursor.execute(
        """
        SELECT
            pr.id,
            pr.wallet_type,
            pr.bet_amount,
            pr.title_code,
            pr.site_code,
            pr.wallet_balance_after_start,
            pr.start_ledger_transaction_id,
            pr.table_session_id,
            pr.request_fingerprint
        FROM platform_rounds pr
        WHERE pr.user_id = %s
          AND pr.idempotency_key = %s
          AND pr.game_code = %s
        """,
        (user_id, idempotency_key, GAME_CODE),
    )
    return cursor.fetchone()


def _chiudi_round_demo(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    esito: str,
    payout_amount: Decimal | None,
) -> dict[str, object]:
    # PERCHE' si cerca l'evento e non lo stato: il manichino non ha una
    # tabella dei round; la puntata demo e' registrata in demo_round_events
    # con chiave derivata dall'id del round, ed e' quella la prova che il
    # round demo esiste.
    cursor.execute(
        """
        SELECT demo_play_session_id
        FROM demo_round_events
        WHERE idempotency_key = %s
        """,
        (f"manichino:demo:bet:{game_round_id}",),
    )
    event_row = cursor.fetchone()
    if event_row is None:
        raise ManichinoValidationError("Round not found")
    demo_session_id = str(event_row["demo_play_session_id"])

    try:
        if esito == ESITO_VINCITA:
            assert payout_amount is not None
            settled = credit_for_win(
                cursor=cursor,
                session_id=demo_session_id,
                amount=payout_amount,
                idempotency_key=f"manichino:demo:win:{game_round_id}",
                payload={"game_round_id": game_round_id},
            )
            return {
                "game_session_id": game_round_id,
                "status": "won",
                "mode": "demo",
                "payout_amount": _format_amount(payout_amount),
                "wallet_balance_after": _format_amount(
                    Decimal(settled["balance_chips"])
                ),
                "ledger_transaction_id": None,
                "already_exists": False,
            }
        settled = record_loss(
            cursor=cursor,
            session_id=demo_session_id,
            idempotency_key=f"manichino:demo:loss:{game_round_id}",
            payload={"game_round_id": game_round_id},
        )
    except DemoWalletIdempotencyConflictError as exc:
        raise ManichinoIdempotencyConflictError(str(exc)) from exc
    return {
        "game_session_id": game_round_id,
        "status": "lost",
        "mode": "demo",
        "wallet_balance_after": _format_amount(Decimal(settled["balance_chips"])),
        "ledger_transaction_id": None,
        "already_exists": False,
    }


def _get_platform_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            pr.id,
            pr.status,
            pr.start_ledger_transaction_id,
            wa.balance_snapshot AS wallet_balance
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
          AND pr.game_code = %s
        """,
        (game_round_id, user_id, GAME_CODE),
    )
    return cursor.fetchone()


def build_start_request_fingerprint(
    *,
    user_id: str,
    bet_amount: str,
    wallet_type: str,
    title_code: str | None,
    table_session_id: str | None,
    access_session_id: str | None,
) -> str | None:
    """Fingerprint della start per il replay idempotente (usato dalla rotta).

    Deve riprodurre ESATTAMENTE la normalizzazione di `apri_round`: se i due
    fingerprint divergono, una ripetizione legittima verrebbe scambiata per un
    riuso della chiave con payload diverso (409 al posto del replay).
    Restituisce None se l'importo non e' valido.
    """
    try:
        bet_amount_decimal = _parse_amount(bet_amount, field_name="bet_amount")
    except ManichinoValidationError:
        return None
    return _build_request_fingerprint(
        user_id=user_id,
        bet_amount=bet_amount_decimal,
        wallet_type=wallet_type.strip().lower(),
        title_code=_normalize_code(
            title_code or TITLE_CODE_MANICHINO_TEST,
            field_name="title_code",
        ),
        site_code=_normalize_code(SITE_CODE_CASINOKING, field_name="site_code"),
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )


def _parse_amount(raw_value: str, *, field_name: str) -> Decimal:
    try:
        amount = Decimal(raw_value)
    except (InvalidOperation, TypeError) as exc:
        raise ManichinoValidationError(f"{field_name} is not valid") from exc
    amount = amount.quantize(Decimal("0.000001"))
    if amount <= 0:
        raise ManichinoValidationError(f"{field_name} must be greater than zero")
    return amount


def _normalize_code(raw_value: str, *, field_name: str) -> str:
    normalized = raw_value.strip().lower()
    if not normalized:
        raise ManichinoValidationError(f"{field_name} is required")
    return normalized


def _build_request_fingerprint(
    *,
    user_id: str,
    bet_amount: Decimal,
    wallet_type: str,
    title_code: str,
    site_code: str,
    table_session_id: str | None,
    access_session_id: str | None,
) -> str:
    payload = json.dumps(
        {
            "user_id": user_id,
            "bet_amount": _format_amount(bet_amount),
            "wallet_type": wallet_type,
            "title_code": title_code,
            "site_code": site_code,
            "table_session_id": table_session_id,
            "access_session_id": access_session_id,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"
