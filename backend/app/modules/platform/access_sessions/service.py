from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import psycopg

from app.core.structured_logging import log_event
from app.db.connection import db_connection
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_launchable_title_for_game_in_transaction,
)
from app.modules.platform.manichino_flag import ambiente_di_produzione

ACCESS_SESSION_TIMEOUT = timedelta(minutes=3)
ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT = 100
# Tetto di sicurezza: oltre questo numero di round attivi su una sola sessione non si
# tratta piu' di un caso legittimo ma di un guasto, e si ferma invece di ciclare.
_MAX_ROUND_DA_LIQUIDARE_PER_SESSIONE = 20
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_CLOSED = "closed"
SESSION_STATUS_TIMED_OUT = "timed_out"

CLOSE_REASON_PLAYER_LOGIN = "player_login_cleanup"
CLOSE_REASON_PLAYER_LOGOUT = "player_logout"
CLOSE_REASON_ACCESS_TIMEOUT = "access_session_timeout"
CLOSE_REASON_ACCESS_CLOSED = "access_session_closed"
CLOSE_REASON_ADMIN_VOIDED = "admin_voided"


class AccessSessionValidationError(Exception):
    pass


class AccessSessionNotFoundError(Exception):
    pass


class AccessSessionStateConflictError(Exception):
    pass


class AccessSessionVoidedByOperatorError(Exception):
    """Raised when a player operation hits an access_session that was
    closed by an admin force-close (closed_reason='admin_voided').
    The frontend uses this to show a neutral 'Sessione terminata' overlay.
    """
    pass


class AutoLiquidazioneNonDisponibileError(Exception):
    def __init__(self, *, game_code: str, round_id: str) -> None:
        self.game_code = game_code
        self.round_id = round_id
        super().__init__(
            f"Auto-liquidazione non disponibile per il gioco {game_code}, round {round_id}"
        )


def create_access_session(
    *,
    user_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _lock_launchable_title_for_access_session(
                cursor=cursor,
                game_code=normalized_game_code,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
            )
            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                FROM game_access_sessions
                WHERE user_id = %s
                  AND game_code = %s
                  AND title_code = %s
                  AND site_code = %s
                  AND status = %s
                ORDER BY started_at DESC
                LIMIT 1
                FOR UPDATE
                """,
                (
                    user_id,
                    normalized_game_code,
                    normalized_title_code,
                    normalized_site_code,
                    SESSION_STATUS_ACTIVE,
                ),
            )
            existing = cursor.fetchone()
            if existing is not None:
                if _is_access_session_expired(existing):
                    _timeout_access_session(cursor=cursor, session=existing)
                else:
                    return _serialize_access_session(existing)

            access_session_id = str(uuid4())
            cursor.execute(
                """
                INSERT INTO game_access_sessions (
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, now(), now(), %s)
                RETURNING
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                """,
                (
                    access_session_id,
                    user_id,
                    normalized_game_code,
                    normalized_title_code,
                    normalized_site_code,
                    SESSION_STATUS_ACTIVE,
                ),
            )
            row = cursor.fetchone()

    assert row is not None
    return _serialize_access_session(row)


def _lock_launchable_title_for_access_session(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    title_code: str,
    site_code: str,
) -> None:
    try:
        title = get_launchable_title_for_game_in_transaction(
            cursor=cursor,
            site_code=site_code,
            title_code=title_code,
            game_code=game_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise AccessSessionValidationError(str(exc)) from exc

    if ambiente_di_produzione() and title["is_test"] is True:
        raise AccessSessionValidationError("Test titles cannot be launched in production")
    if title["is_master"] is True:
        raise AccessSessionValidationError("Master titles cannot be launched publicly")
    publication = title["publication"]
    assert isinstance(publication, dict)
    if (
        publication["site_title_status"] != "active"
        or publication["lobby_visibility"] != "visible"
    ):
        raise AccessSessionValidationError("Title is not visible in the player library")
    if publication["real_enabled"] is not True:
        raise AccessSessionValidationError("Real launch mode is not enabled for this title")


def force_close_user_sessions(
    *,
    user_id: str,
    game_code: str | None = None,
    reason: str,
) -> dict[str, object]:
    """Close all active access_sessions and table_sessions for a user.

    If game_code is None, applies to all games.
    Cascades through close_access_session, which auto-settles active rounds
    and closes linked table_sessions.
    """
    normalized_game_code = _normalize_game_code(game_code) if game_code else None
    closed_count = 0
    with db_connection() as connection:
        with connection.cursor() as cursor:
            closed_count = _force_close_user_sessions_in_transaction(
                cursor=cursor,
                user_id=user_id,
                game_code=normalized_game_code,
                reason=reason,
            )

    return {"closed_sessions": closed_count, "reason": reason}


def _chiudi_una_sessione_isolata(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    reason: str,
    job_id: str | None = None,
) -> tuple[dict[str, object] | None, bool]:
    """Chiude UNA sessione dentro un punto di ripristino tutto suo.

    PERCHE' ESISTE. Il fail-closed e' giusto: se i soldi trattenuti non si possono
    restituire, la sessione non deve chiudersi. Ma applicato a un LOTTO di sessioni
    dentro un'unica transazione produce due danni che con la protezione dei soldi non
    c'entrano niente:

    - lo spazzino delle sessioni scadute lavora in ordine dalla piu' vecchia, quindi una
      sola sessione non liquidabile fa fallire l'intero lotto e, restando sempre la
      prima, blocca la liquidazione di TUTTE le altre per sempre;
    - il login chiama la chiusura forzata, quindi la stessa sessione impedirebbe al
      giocatore di entrare.

    Con un punto di ripristino per sessione, quella che non si puo' liquidare **resta
    aperta** — coi soldi al loro posto e un allarme nel registro — e le altre proseguono.
    L'errore NON viene ingoiato: viene contato e registrato come critico.

    Restituisce (sessione_chiusa_o_None, e' _stata_saltata).
    """
    punto = f"sessione_{uuid4().hex}"
    cursor.execute(f"SAVEPOINT {punto}")
    try:
        closed_session, _ = _close_access_session_in_transaction(
            cursor=cursor,
            access_session_id=access_session_id,
            user_id=user_id,
            reason=reason,
        )
    except AutoLiquidazioneNonDisponibileError as exc:
        cursor.execute(f"ROLLBACK TO SAVEPOINT {punto}")
        log_event(
            "critical",
            "access_session.close_skipped_money_still_held",
            {
                "access_session_id": access_session_id,
                "game_code": exc.game_code,
                "round_id": exc.round_id,
                "reason": reason,
                "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
            },
            job_id=job_id,
        )
        return None, True
    cursor.execute(f"RELEASE SAVEPOINT {punto}")
    return closed_session, False


def _force_close_user_sessions_in_transaction(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_code: str | None,
    reason: str,
) -> int:
    query = """
        SELECT id, game_code
        FROM game_access_sessions
        WHERE user_id = %s
          AND status = %s
    """
    params: list[object] = [user_id, SESSION_STATUS_ACTIVE]
    if game_code is not None:
        query += " AND game_code = %s"
        params.append(game_code)
    query += " FOR UPDATE"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall() or []

    closed_count = 0
    for row in rows:
        closed_session, saltata = _chiudi_una_sessione_isolata(
            cursor=cursor,
            access_session_id=str(row["id"]),
            user_id=user_id,
            reason=reason,
        )
        if saltata:
            # La sessione resta aperta apposta: i soldi non si potevano restituire.
            # Non si alza l'eccezione, o un solo round guasto impedirebbe il LOGIN.
            continue
        if closed_session is not None and closed_session["status"] == SESSION_STATUS_CLOSED:
            closed_count += 1

    # Sweep any orphan active table_sessions not linked to an access_session.
    sweep_query = """
        UPDATE game_table_sessions
        SET
            status = %s,
            closed_reason = %s,
            closed_at = now()
        WHERE status = %s
          AND user_id = %s
    """
    sweep_params: list[object] = [
        SESSION_STATUS_CLOSED,
        reason,
        SESSION_STATUS_ACTIVE,
        user_id,
    ]
    if game_code is not None:
        sweep_query += " AND game_code = %s"
        sweep_params.append(game_code)
    cursor.execute(sweep_query, tuple(sweep_params))

    return closed_count


def timeout_expired_access_sessions(
    *,
    limit: int = ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
    job_id: str | None = None,
) -> int:
    cutoff = datetime.now(UTC) - ACCESS_SESSION_TIMEOUT
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status,
                    closed_reason
                FROM game_access_sessions
                WHERE status = %s
                  AND last_activity_at < %s
                ORDER BY last_activity_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT %s
                """,
                (SESSION_STATUS_ACTIVE, cutoff, limit),
            )
            rows = cursor.fetchall() or []
            scadute = 0
            for session in rows:
                # PERCHE' UN PUNTO DI RIPRISTINO PER SESSIONE. Le righe arrivano in
                # ordine dalla piu' vecchia: senza isolamento, UNA sessione i cui soldi
                # non si possono restituire farebbe fallire l'intero lotto e, restando
                # sempre la prima della lista, bloccherebbe la liquidazione di tutte le
                # altre a ogni giro, per sempre. Il fail-closed deve fermare QUELLA
                # sessione, non lo spazzino.
                punto = f"scadenza_{uuid4().hex}"
                cursor.execute(f"SAVEPOINT {punto}")
                try:
                    _timeout_access_session(
                        cursor=cursor, session=session, job_id=job_id
                    )
                except AutoLiquidazioneNonDisponibileError as exc:
                    cursor.execute(f"ROLLBACK TO SAVEPOINT {punto}")
                    log_event(
                        "critical",
                        "access_session.timeout_skipped_money_still_held",
                        {
                            "access_session_id": str(session["id"]),
                            "game_code": exc.game_code,
                            "round_id": exc.round_id,
                            "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
                        },
                        job_id=job_id,
                    )
                    continue
                cursor.execute(f"RELEASE SAVEPOINT {punto}")
                scadute += 1
            return scadute


def ping_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    conflict_message: str | None = None
    voided_by_operator = False

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if session["status"] == SESSION_STATUS_ACTIVE and _is_access_session_expired(session):
                _timeout_access_session(cursor=cursor, session=session)
                conflict_message = "Access session timed out"

            if session["status"] == SESSION_STATUS_TIMED_OUT:
                conflict_message = "Access session timed out"

            if (
                conflict_message is None
                and session["status"] != SESSION_STATUS_ACTIVE
                and session.get("closed_reason") == CLOSE_REASON_ADMIN_VOIDED
            ):
                voided_by_operator = True

            if conflict_message is None and session["status"] != SESSION_STATUS_ACTIVE:
                conflict_message = "Access session is not active"

            if conflict_message is not None:
                updated_session = None
            else:
                cursor.execute(
                    """
                    UPDATE game_access_sessions
                    SET last_activity_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        user_id,
                        game_code,
                        title_code,
                        site_code,
                        started_at,
                        last_activity_at,
                        ended_at,
                        status
                    """,
                    (normalized_session_id,),
                )
                updated_session = cursor.fetchone()

    if voided_by_operator:
        raise AccessSessionVoidedByOperatorError(
            "Access session was closed by an operator"
        )

    if conflict_message is not None:
        raise AccessSessionStateConflictError(conflict_message)

    assert updated_session is not None
    return _serialize_access_session(updated_session)


def close_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            closed_session, auto_cashout = _close_access_session_in_transaction(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                reason=CLOSE_REASON_ACCESS_CLOSED,
            )

    if closed_session is None:
        raise AccessSessionNotFoundError("Access session not found")
    return _serialize_access_session(closed_session, auto_cashout=auto_cashout)


def _close_access_session_in_transaction(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    reason: str,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    session = _get_access_session_for_update(
        cursor=cursor,
        access_session_id=access_session_id,
        user_id=user_id,
    )
    if session is None:
        return None, None

    if session["status"] != SESSION_STATUS_ACTIVE:
        return session, None

    auto_cashout = _auto_settle_active_round_for_access_session(
        cursor=cursor,
        session=session,
    )

    cursor.execute(
        """
        UPDATE game_access_sessions
        SET
            last_activity_at = now(),
            ended_at = now(),
            status = %s,
            closed_reason = %s
        WHERE id = %s
        RETURNING
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        """,
        (SESSION_STATUS_CLOSED, reason, access_session_id),
    )
    closed_session = cursor.fetchone()

    _close_table_sessions_for_access_session(
        cursor=cursor,
        access_session_id=access_session_id,
        user_id=str(session["user_id"]),
        game_code=str(session["game_code"]),
        title_code=str(session["title_code"]),
        site_code=str(session["site_code"]),
        reason=reason,
    )

    return closed_session, auto_cashout


def ensure_access_session_active_for_round_start(
    *,
    user_id: str,
    access_session_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    normalized_game_code = _normalize_game_code(game_code)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    timed_out = False

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                game_code=normalized_game_code,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if (
                session["status"] != SESSION_STATUS_ACTIVE
                and session.get("closed_reason") == CLOSE_REASON_ADMIN_VOIDED
            ):
                raise AccessSessionVoidedByOperatorError(
                    "Access session was closed by an operator"
                )

            if session["status"] != SESSION_STATUS_ACTIVE:
                raise AccessSessionStateConflictError("Access session is not active")

            if _is_access_session_expired(session):
                _timeout_access_session(cursor=cursor, session=session)
                timed_out = True
            else:
                cursor.execute(
                    """
                    UPDATE game_access_sessions
                    SET last_activity_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        user_id,
                        game_code,
                        title_code,
                        site_code,
                        started_at,
                        last_activity_at,
                        ended_at,
                        status
                    """,
                    (normalized_session_id,),
                )
                active_session = cursor.fetchone()

    if timed_out:
        raise AccessSessionStateConflictError("Access session timed out")

    assert active_session is not None
    return _serialize_access_session(active_session)


def _timeout_access_session(
    *,
    cursor: psycopg.Cursor,
    session: dict[str, object],
    job_id: str | None = None,
) -> tuple[dict[str, object], dict[str, object] | None]:
    try:
        auto_cashout = _auto_settle_active_round_for_access_session(
            cursor=cursor,
            session=session,
        )
    except Exception as exc:
        log_event(
            "critical",
            "access_session.auto_settlement_failed",
            {
                "access_session_id": str(session["id"]),
                "game_code": str(session["game_code"]),
                "title_code": str(session["title_code"]),
                "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
                "exception_type": type(exc).__name__,
            },
            job_id=job_id,
        )
        raise

    cursor.execute(
        """
        UPDATE game_access_sessions
        SET
            ended_at = now(),
            status = %s,
            closed_reason = %s
        WHERE id = %s
        RETURNING
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        """,
        (SESSION_STATUS_TIMED_OUT, CLOSE_REASON_ACCESS_TIMEOUT, str(session["id"])),
    )
    timed_out_session = cursor.fetchone()
    assert timed_out_session is not None

    _close_table_sessions_for_access_session(
        cursor=cursor,
        access_session_id=str(session["id"]),
        user_id=str(session["user_id"]),
        game_code=str(session["game_code"]),
        title_code=str(session["title_code"]),
        site_code=str(session["site_code"]),
        reason=CLOSE_REASON_ACCESS_TIMEOUT,
    )

    return timed_out_session, auto_cashout


def _auto_settle_active_round_for_access_session(
    *,
    cursor: psycopg.Cursor,
    session: dict[str, object],
) -> dict[str, object] | None:
    from app.modules.platform.access_sessions.bootstrap_liquidazione import (
        assicura_iscrizioni,
    )
    from app.modules.platform.access_sessions.registro_liquidazione import (
        cerca_liquidazione,
    )

    assicura_iscrizioni()
    access_session_id = str(session["id"])
    user_id = str(session["user_id"])

    # PERCHE' UN CICLO E NON UNA SOLA LETTURA. Niente in banca dati impedisce a una
    # sessione di avere piu' di un round attivo: non esiste un indice unico parziale su
    # (access_session_id, status='active'). Prendendone uno solo, il piu' recente, gli
    # altri resterebbero aperti PER SEMPRE — con la loro puntata trattenuta — e la
    # sessione si chiuderebbe lo stesso, senza che nessuno se ne accorga. Si liquida
    # finche' ce n'e', e si esce solo quando non ne resta nessuno.
    primo_esito: dict[str, object] | None = None
    for _ in range(_MAX_ROUND_DA_LIQUIDARE_PER_SESSIONE):
        active_round = _leggi_round_attivo(
            cursor=cursor,
            access_session_id=access_session_id,
            user_id=user_id,
        )
        if active_round is None:
            return primo_esito

        game_code = str(active_round["game_code"])
        round_id = str(active_round["id"])
        handler = cerca_liquidazione(game_code)
        if handler is None:
            log_event(
                "critical",
                "access_session.auto_settlement_unavailable",
                {
                    "access_session_id": access_session_id,
                    "game_code": game_code,
                    "round_id": round_id,
                    "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
                },
            )
            raise AutoLiquidazioneNonDisponibileError(
                game_code=game_code,
                round_id=round_id,
            )

        esito = handler(
            cursor=cursor,
            access_session_id=access_session_id,
            user_id=user_id,
        )
        if primo_esito is None:
            primo_esito = esito

        # PERCHE' SI RICONTROLLA. Che il gestore non sollevi eccezioni non dimostra che
        # abbia chiuso il round: potrebbe restituire un resoconto e lasciarlo aperto. La
        # piattaforma verifica da sola, guardando platform_rounds, che e' roba sua e non
        # richiede di sapere niente del gioco.
        ancora_attivo = _leggi_round_attivo(
            cursor=cursor,
            access_session_id=access_session_id,
            user_id=user_id,
        )
        if ancora_attivo is not None and str(ancora_attivo["id"]) == round_id:
            log_event(
                "critical",
                "access_session.auto_settlement_did_not_close_round",
                {
                    "access_session_id": access_session_id,
                    "game_code": game_code,
                    "round_id": round_id,
                    "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
                },
            )
            raise AutoLiquidazioneNonDisponibileError(
                game_code=game_code,
                round_id=round_id,
            )

    # Piu' round attivi del tetto: e' un guasto, non una sessione movimentata. Non si
    # chiude niente.
    log_event(
        "critical",
        "access_session.auto_settlement_too_many_rounds",
        {
            "access_session_id": access_session_id,
            "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
        },
    )
    raise AutoLiquidazioneNonDisponibileError(
        game_code="",
        round_id="",
    )


def _leggi_round_attivo(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT id, game_code
        FROM platform_rounds
        WHERE access_session_id = %s
          AND user_id = %s
          AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    return cursor.fetchone()


def _close_table_sessions_for_access_session(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    game_code: str,
    title_code: str,
    site_code: str,
    reason: str,
) -> None:
    """Close all active table_sessions linked to this access_session,
    plus any orphan active table_sessions for the same user/game.
    Auto-cashout has already happened upstream, so loss_reserved should be 0.
    """
    cursor.execute(
        """
        UPDATE game_table_sessions
        SET
            status = %s,
            closed_reason = %s,
            closed_at = now()
        WHERE status = %s
          AND user_id = %s
          AND game_code = %s
          AND title_code = %s
          AND site_code = %s
          AND (access_session_id = %s OR access_session_id IS NULL)
        """,
        (
            SESSION_STATUS_CLOSED,
            reason,
            SESSION_STATUS_ACTIVE,
            user_id,
            game_code,
            title_code,
            site_code,
            access_session_id,
        ),
    )


def _get_access_session_for_update(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    game_code: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object] | None:
    query = """
        SELECT
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status,
            closed_reason
        FROM game_access_sessions
        WHERE id = %s
          AND user_id = %s
    """
    params: list[object] = [access_session_id, user_id]
    if game_code is not None:
        query += " AND game_code = %s"
        params.append(game_code)
    if title_code is not None:
        query += " AND title_code = %s"
        params.append(title_code)
    if site_code is not None:
        query += " AND site_code = %s"
        params.append(site_code)
    query += " FOR UPDATE"
    cursor.execute(query, tuple(params))
    return cursor.fetchone()


def _is_access_session_expired(session: dict[str, object]) -> bool:
    last_activity_at = session["last_activity_at"]
    assert isinstance(last_activity_at, datetime)
    return datetime.now(UTC) - last_activity_at > ACCESS_SESSION_TIMEOUT


def _normalize_access_session_id(access_session_id: str) -> str:
    try:
        return str(UUID(access_session_id))
    except (TypeError, ValueError) as exc:
        raise AccessSessionValidationError("Access session id is not valid") from exc


def _normalize_game_code(game_code: str) -> str:
    normalized_game_code = game_code.strip().lower()
    if not normalized_game_code:
        raise AccessSessionValidationError("Game code is required")
    return normalized_game_code


def _normalize_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise AccessSessionValidationError("Title code is required")
    return normalized_title_code


def _normalize_site_code(site_code: str) -> str:
    normalized_site_code = site_code.strip().lower()
    if not normalized_site_code:
        raise AccessSessionValidationError("Site code is required")
    return normalized_site_code


def _serialize_access_session(
    row: dict[str, object],
    *,
    auto_cashout: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "game_code": row["game_code"],
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "status": row["status"],
        "started_at": row["started_at"].isoformat(),
        "last_activity_at": row["last_activity_at"].isoformat(),
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "auto_cashout": auto_cashout,
    }
