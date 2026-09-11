from datetime import UTC, datetime, timedelta
import secrets
from uuid import uuid4

import jwt

from app.core.config import settings
from app.db.connection import db_connection
from app.modules.auth.service import CHIP_CURRENCY
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    ensure_game_engine_is_available,
    get_launchable_title_for_game,
    get_published_title_for_launch,
)
from app.modules.platform.demo_wallet.service import reset_demo_session_for_launch
from app.modules.platform.game_codes import GAME_CODE_MINES
from app.modules.platform.game_modules.descriptors import build_game_module_descriptor_payload
from app.modules.platform.manichino_flag import (
    GAME_CODE_MANICHINO,
    ambiente_di_produzione,
    manichino_attivo,
)

TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
LAUNCH_MODE_REAL = "real"
LAUNCH_MODE_DEMO = "demo"
GAME_LAUNCH_TOKEN_KIND = "game_launch"
GAME_ADMIN_PREVIEW_TOKEN_KIND = "game_admin_preview"
GAME_LAUNCH_ISSUER = "casinoking-platform"
GAME_LAUNCH_AUDIENCE = "casinoking-mines"
GAME_ADMIN_PREVIEW_AUDIENCE = "casinoking-admin-preview"
LAUNCH_REJECTED_MASTER = "LAUNCH_REJECTED_MASTER"
LAUNCH_VALIDATION_ERROR = "VALIDATION_ERROR"


class GameLaunchTokenValidationError(Exception):
    def __init__(self, message: str, *, code: str = LAUNCH_VALIDATION_ERROR) -> None:
        super().__init__(message)
        self.code = code


class GameLaunchTokenOwnershipError(Exception):
    pass


class GameLaunchTokenScopeError(Exception):
    pass


# PERCHE' PORTAFOLIO E VALUTA LI DECIDE LA PIATTAFORMA (PASSO 3-bis): il
# gioco esterno (Coins) deve rimandare al confine seamless esattamente il
# portafoglio e la valuta che la piattaforma conosce. Se arrivassero dalla
# richiesta del client, chi gioca potrebbe scegliersi un portafoglio diverso
# da quello addebitato. Il gettone li dichiara; il seamless li riverifica
# contro il conto vero (_validate_wallet_currency) prima di muovere denaro.
WALLET_TYPE_LANCIO_REAL = "cash"
WALLET_TYPE_LANCIO_DEMO = "demo"


def _portafoglio_di_lancio(player_id: str) -> tuple[str, str]:
    """(wallet_type, currency) del lancio reale, letti dal conto del giocatore.

    GIRO 1 (revisione agy): lo schema NON garantisce un solo portafoglio cash
    per giocatore — l'unicita' e' su (user_id, wallet_type, currency_code)
    (migrazione 0002, backend/migrations/sql/0002__financial_core_foundations.sql:40-41),
    quindi due cash in valute diverse sono leciti. Con zero righe o piu' di una
    il lancio si RIFIUTA con un errore di dominio: pescarne una con fetchone()
    sarebbe una scelta arbitraria su quale denaro muovere."""
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT currency_code
                FROM wallet_accounts
                WHERE user_id = %s AND wallet_type = %s
                """,
                (player_id, WALLET_TYPE_LANCIO_REAL),
            )
            rows = cursor.fetchall()
    if not rows:
        raise GameLaunchTokenValidationError("Player wallet is not available")
    if len(rows) > 1:
        raise GameLaunchTokenValidationError("Player cash wallet is not unique")
    return WALLET_TYPE_LANCIO_REAL, str(rows[0]["currency_code"])


def issue_game_launch_token(
    *,
    player_id: str,
    role: str,
    game_code: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
    mode: str | None = None,
    host_code: str | None = None,
    brand_code: str | None = None,
    return_url: str | None = None,
    locale: str | None = None,
    embed_origin: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code or GAME_CODE_MINES)
    normalized_title_code = _normalize_title_code(title_code)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    normalized_mode = _normalize_mode(mode or LAUNCH_MODE_REAL)
    normalized_host_code = _normalize_optional_code(host_code) or normalized_site_code
    normalized_brand_code = _normalize_optional_code(brand_code) or normalized_site_code
    normalized_locale = _normalize_locale(locale)
    normalized_correlation_id = _normalize_optional_text(correlation_id)

    if role != "player":
        raise GameLaunchTokenValidationError("Only players can launch a game session")
    if normalized_game_code == GAME_CODE_MANICHINO and not manichino_attivo():
        raise GameLaunchTokenValidationError("Manichino is not active")

    try:
        title = get_published_title_for_launch(
            site_code=normalized_site_code,
            title_code=normalized_title_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise GameLaunchTokenValidationError(str(exc)) from exc
    if title["engine_code"] != normalized_game_code:
        raise GameLaunchTokenValidationError("Title engine is not valid for this launch")
    _ensure_title_launch_mode_allowed(title=title, mode=normalized_mode)

    now = datetime.now(UTC)
    platform_session_id = str(uuid4())
    play_session_id = str(uuid4())
    game_play_session_id = str(uuid4())
    nonce = secrets.token_hex(16)
    expires_at = now + timedelta(minutes=settings.game_launch_token_ttl_minutes)
    if normalized_mode == LAUNCH_MODE_REAL:
        wallet_type, currency = _portafoglio_di_lancio(player_id)
    else:
        wallet_type, currency = WALLET_TYPE_LANCIO_DEMO, CHIP_CURRENCY

    payload = {
        "iss": GAME_LAUNCH_ISSUER,
        "aud": GAME_LAUNCH_AUDIENCE,
        "sub": player_id,
        "token_kind": GAME_LAUNCH_TOKEN_KIND,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "host_code": normalized_host_code,
        "brand_code": normalized_brand_code,
        "mode": normalized_mode,
        "locale": normalized_locale,
        "wallet_type": wallet_type,
        "currency": currency,
        "nonce": nonce,
        "iat": now,
        "exp": expires_at,
    }
    if return_url:
        payload["return_url"] = return_url
    if embed_origin:
        payload["embed_origin"] = embed_origin
    if normalized_correlation_id:
        payload["correlation_id"] = normalized_correlation_id

    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "host_code": normalized_host_code,
        "brand_code": normalized_brand_code,
        "mode": normalized_mode,
        "game_launch_token": token,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "expires_at": expires_at.isoformat(),
        **build_game_module_descriptor_payload(
            game_code=normalized_game_code,
            title_code=normalized_title_code,
            site_code=normalized_site_code,
            mode=normalized_mode,
            player_ref=player_id,
            wallet_source=wallet_type,
            launch_ref=platform_session_id,
            host_code=normalized_host_code,
            brand_code=normalized_brand_code,
            return_url=return_url,
            locale=normalized_locale,
            embed_origin=embed_origin,
            correlation_id=normalized_correlation_id,
        ),
    }


def issue_demo_game_launch_token(
    *,
    anonymous_id: str,
    game_code: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
    host_code: str | None = None,
    brand_code: str | None = None,
    return_url: str | None = None,
    locale: str | None = None,
    embed_origin: str | None = None,
    correlation_id: str | None = None,
    allow_unpublished_preview: bool = False,
    preview_admin_user_id: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code or GAME_CODE_MINES)
    normalized_title_code = _normalize_title_code(title_code)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    normalized_host_code = _normalize_optional_code(host_code) or normalized_site_code
    normalized_brand_code = _normalize_optional_code(brand_code) or normalized_site_code
    normalized_locale = _normalize_locale(locale)
    normalized_correlation_id = _normalize_optional_text(correlation_id)

    if normalized_game_code == GAME_CODE_MANICHINO and not manichino_attivo():
        raise GameLaunchTokenValidationError("Manichino is not active")

    try:
        title = get_published_title_for_launch(
            site_code=normalized_site_code,
            title_code=normalized_title_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise GameLaunchTokenValidationError(str(exc)) from exc
    if title["engine_code"] != normalized_game_code:
        raise GameLaunchTokenValidationError("Title engine is not valid for this launch")
    if not allow_unpublished_preview:
        _ensure_title_launch_mode_allowed(title=title, mode=LAUNCH_MODE_DEMO)

    now = datetime.now(UTC)
    platform_session_id = str(uuid4())
    play_session_id = str(uuid4())
    game_play_session_id = str(uuid4())
    nonce = secrets.token_hex(16)
    expires_at = now + timedelta(minutes=settings.game_launch_token_ttl_minutes)

    payload = {
        "iss": GAME_LAUNCH_ISSUER,
        "aud": GAME_LAUNCH_AUDIENCE,
        "sub": anonymous_id,
        "anonymous_id": anonymous_id,
        "token_kind": GAME_LAUNCH_TOKEN_KIND,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "host_code": normalized_host_code,
        "brand_code": normalized_brand_code,
        "mode": LAUNCH_MODE_DEMO,
        "locale": normalized_locale,
        "wallet_type": WALLET_TYPE_LANCIO_DEMO,
        "currency": CHIP_CURRENCY,
        "nonce": nonce,
        "iat": now,
        "exp": expires_at,
    }
    if return_url:
        payload["return_url"] = return_url
    if embed_origin:
        payload["embed_origin"] = embed_origin
    if normalized_correlation_id:
        payload["correlation_id"] = normalized_correlation_id
    if allow_unpublished_preview:
        payload["admin_preview"] = True
        if preview_admin_user_id:
            payload["preview_admin_user_id"] = preview_admin_user_id

    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    fresh_session = reset_demo_session_for_launch(
        anonymous_id=anonymous_id,
        title_code=normalized_title_code,
    )
    balance_chips = str(fresh_session["balance_chips"])
    return {
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "host_code": normalized_host_code,
        "brand_code": normalized_brand_code,
        "mode": LAUNCH_MODE_DEMO,
        "anonymous_id": anonymous_id,
        "game_launch_token": token,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "expires_at": expires_at.isoformat(),
        "balance_chips": balance_chips,
        **build_game_module_descriptor_payload(
            game_code=normalized_game_code,
            title_code=normalized_title_code,
            site_code=normalized_site_code,
            mode=LAUNCH_MODE_DEMO,
            player_ref=anonymous_id,
            wallet_source="demo",
            launch_ref=platform_session_id,
            host_code=normalized_host_code,
            brand_code=normalized_brand_code,
            return_url=return_url,
            locale=normalized_locale,
            embed_origin=embed_origin,
            correlation_id=normalized_correlation_id,
        ),
    }


def issue_admin_game_preview_token(
    *,
    admin_user_id: str,
    game_code: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code or GAME_CODE_MINES)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)

    try:
        title = get_published_title_for_launch(
            site_code=normalized_site_code,
            title_code=normalized_title_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise GameLaunchTokenValidationError(str(exc)) from exc
    if title["engine_code"] != normalized_game_code:
        raise GameLaunchTokenValidationError("Title engine is not valid for this preview")

    now = datetime.now(UTC)
    nonce = secrets.token_hex(16)
    expires_at = now + timedelta(minutes=settings.game_launch_token_ttl_minutes)
    payload = {
        "iss": GAME_LAUNCH_ISSUER,
        "aud": GAME_ADMIN_PREVIEW_AUDIENCE,
        "sub": admin_user_id,
        "token_kind": GAME_ADMIN_PREVIEW_TOKEN_KIND,
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "mode": LAUNCH_MODE_DEMO,
        "nonce": nonce,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {
        "game_code": normalized_game_code,
        "title_code": normalized_title_code,
        "site_code": normalized_site_code,
        "mode": LAUNCH_MODE_DEMO,
        "preview_token": token,
        "expires_at": expires_at.isoformat(),
    }


def validate_admin_game_preview_token(*, preview_token: str) -> dict[str, object]:
    try:
        payload = jwt.decode(
            preview_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=GAME_ADMIN_PREVIEW_AUDIENCE,
            issuer=GAME_LAUNCH_ISSUER,
        )
    except jwt.InvalidTokenError as exc:
        raise GameLaunchTokenValidationError("Admin preview token is not valid") from exc

    if payload.get("token_kind") != GAME_ADMIN_PREVIEW_TOKEN_KIND:
        raise GameLaunchTokenValidationError("Admin preview token is not valid")

    admin_user_id = payload.get("sub")
    game_code = payload.get("game_code")
    title_code = payload.get("title_code")
    site_code = payload.get("site_code")
    mode = payload.get("mode")
    nonce = payload.get("nonce")
    expires_at = payload.get("exp")

    if mode != LAUNCH_MODE_DEMO or not isinstance(game_code, str):
        raise GameLaunchTokenValidationError("Admin preview token scope is not valid")
    if not all(
        isinstance(value, str) and value
        for value in [admin_user_id, title_code, site_code, nonce]
    ):
        raise GameLaunchTokenValidationError("Admin preview token is not valid")
    if not isinstance(expires_at, (int, float)):
        raise GameLaunchTokenValidationError("Admin preview token is not valid")
    try:
        ensure_game_engine_is_available(game_code=game_code)
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise GameLaunchTokenValidationError("Admin preview token scope is not valid") from exc

    return {
        "admin_user_id": admin_user_id,
        "game_code": game_code,
        "title_code": title_code,
        "site_code": site_code,
        "mode": LAUNCH_MODE_DEMO,
        "expires_at": datetime.fromtimestamp(expires_at, tz=UTC).isoformat(),
    }


def validate_game_launch_token(
    *,
    game_launch_token: str,
    expected_game_code: str | None = None,
) -> dict[str, object]:
    try:
        payload = jwt.decode(
            game_launch_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=GAME_LAUNCH_AUDIENCE,
            issuer=GAME_LAUNCH_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        # PERCHE' la scadenza e' una causa operativa diversa dalla firma: chi
        # integra la piattaforma deve poter rinnovare il gettone, non inseguire
        # un generico errore di autenticazione.
        raise GameLaunchTokenValidationError("Game launch token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise GameLaunchTokenValidationError("Game launch token is not valid") from exc

    if payload.get("token_kind") != GAME_LAUNCH_TOKEN_KIND:
        raise GameLaunchTokenValidationError("Game launch token is not valid")
    game_code = payload.get("game_code")
    title_code = payload.get("title_code")
    site_code = payload.get("site_code")
    mode = payload.get("mode")

    if not isinstance(game_code, str):
        raise GameLaunchTokenScopeError("Game launch token game code is not valid")
    if expected_game_code is not None and game_code != expected_game_code:
        raise GameLaunchTokenScopeError("Game launch token game code is not valid")
    if not all(isinstance(value, str) and value for value in [title_code, site_code, mode]):
        raise GameLaunchTokenValidationError("Game launch token is not valid")
    if mode not in {LAUNCH_MODE_REAL, LAUNCH_MODE_DEMO}:
        raise GameLaunchTokenValidationError("Game launch token is not valid")
    try:
        get_launchable_title_for_game(
            site_code=site_code,
            title_code=title_code,
            game_code=game_code,
        )
    except (CatalogNotFoundError, CatalogValidationError) as exc:
        raise GameLaunchTokenScopeError("Game launch token game code is not valid") from exc

    player_id = payload.get("sub")
    platform_session_id = payload.get("platform_session_id")
    play_session_id = payload.get("play_session_id")
    game_play_session_id = payload.get("game_play_session_id")
    nonce = payload.get("nonce")
    expires_at = payload.get("exp")

    if not all(
        isinstance(value, str) and value
        for value in [player_id, platform_session_id, play_session_id, game_play_session_id, nonce]
    ):
        raise GameLaunchTokenValidationError("Game launch token is not valid")

    if not isinstance(expires_at, (int, float)):
        raise GameLaunchTokenValidationError("Game launch token is not valid")

    result = {
        "game_code": game_code,
        "title_code": title_code,
        "site_code": site_code,
        "host_code": payload.get("host_code"),
        "brand_code": payload.get("brand_code"),
        "mode": mode,
        "locale": payload.get("locale"),
        "return_url": payload.get("return_url"),
        "embed_origin": payload.get("embed_origin"),
        "correlation_id": payload.get("correlation_id"),
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "wallet_type": payload.get("wallet_type"),
        "currency": payload.get("currency"),
        "expires_at": datetime.fromtimestamp(expires_at, tz=UTC).isoformat(),
    }
    if mode == LAUNCH_MODE_DEMO:
        anonymous_id = payload.get("anonymous_id", player_id)
        if not isinstance(anonymous_id, str) or not anonymous_id:
            raise GameLaunchTokenValidationError("Game launch token is not valid")
        result["anonymous_id"] = anonymous_id
    else:
        result["player_id"] = player_id
    return result


def validate_optional_game_launch_token_for_player(
    *,
    game_launch_token: str | None,
    player_id: str,
) -> dict[str, object] | None:
    if not game_launch_token:
        return None

    launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
    _ensure_launch_context_belongs_to_player(
        launch_context=launch_context,
        player_id=player_id,
    )
    return launch_context


def _normalize_game_code(raw_value: str | None) -> str:
    if raw_value is None:
        raise GameLaunchTokenValidationError("Game code is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise GameLaunchTokenValidationError("Game code is required")
    return normalized


def _normalize_title_code(raw_value: str | None) -> str:
    if raw_value is None:
        raise GameLaunchTokenValidationError("Title code is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise GameLaunchTokenValidationError("Title code is required")
    return normalized


def _normalize_site_code(raw_value: str | None) -> str:
    if raw_value is None:
        raise GameLaunchTokenValidationError("Site code is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise GameLaunchTokenValidationError("Site code is required")
    return normalized


def _normalize_mode(raw_value: str | None) -> str:
    if raw_value is None:
        raise GameLaunchTokenValidationError("Launch mode is required")
    normalized = raw_value.strip().lower()
    if not normalized:
        raise GameLaunchTokenValidationError("Launch mode is required")
    if normalized not in {LAUNCH_MODE_REAL, LAUNCH_MODE_DEMO}:
        raise GameLaunchTokenValidationError("Launch mode is not supported")
    return normalized


def _normalize_optional_code(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip().lower()
    return normalized or None


def _normalize_optional_text(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    return normalized or None


def _normalize_locale(raw_value: str | None) -> str:
    normalized = (raw_value or "it").strip().lower()
    return normalized or "it"


def _ensure_title_launch_mode_allowed(
    *,
    title: dict[str, object],
    mode: str,
) -> None:
    if ambiente_di_produzione() and title.get("is_test") is True:
        raise GameLaunchTokenValidationError("Test titles cannot be launched in production")
    if title.get("is_master") is True:
        raise GameLaunchTokenValidationError(
            "Master titles cannot be launched publicly",
            code=LAUNCH_REJECTED_MASTER,
        )

    publication = title.get("publication")
    if not isinstance(publication, dict):
        raise GameLaunchTokenValidationError("Title publication state is not valid")
    if publication.get("lobby_visibility") != "visible":
        raise GameLaunchTokenValidationError("Title is not visible in the player library")
    if mode == LAUNCH_MODE_DEMO and publication.get("demo_enabled") is not True:
        raise GameLaunchTokenValidationError("Demo launch mode is not enabled for this title")
    if mode == LAUNCH_MODE_REAL and publication.get("real_enabled") is not True:
        raise GameLaunchTokenValidationError("Real launch mode is not enabled for this title")


def validate_required_game_launch_token_for_player(
    *,
    game_launch_token: str | None,
    player_id: str,
) -> dict[str, object]:
    if not game_launch_token:
        raise GameLaunchTokenValidationError("X-Game-Launch-Token header is required")

    launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
    _ensure_launch_context_belongs_to_player(
        launch_context=launch_context,
        player_id=player_id,
    )
    return launch_context


def _ensure_launch_context_belongs_to_player(
    *,
    launch_context: dict[str, object],
    player_id: str,
) -> None:
    if launch_context.get("mode") != LAUNCH_MODE_REAL:
        raise GameLaunchTokenOwnershipError("Game launch token ownership is not valid")
    if launch_context.get("player_id") != player_id:
        raise GameLaunchTokenOwnershipError("Game launch token ownership is not valid")
