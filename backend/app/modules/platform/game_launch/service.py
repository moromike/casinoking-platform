from datetime import UTC, datetime, timedelta
import secrets
from uuid import uuid4

import jwt

from app.core.config import settings

GAME_CODE_MINES = "mines"
GAME_LAUNCH_TOKEN_KIND = "game_launch"
GAME_LAUNCH_ISSUER = "casinoking-platform"
GAME_LAUNCH_AUDIENCE = "casinoking-mines"


class GameLaunchTokenValidationError(Exception):
    pass


class GameLaunchTokenOwnershipError(Exception):
    pass


def issue_game_launch_token(*, player_id: str, role: str, game_code: str) -> dict[str, object]:
    if game_code != GAME_CODE_MINES:
        raise GameLaunchTokenValidationError("Game code is not supported")
    if role != "player":
        raise GameLaunchTokenValidationError("Only players can launch a game session")

    now = datetime.now(UTC)
    platform_session_id = str(uuid4())
    play_session_id = str(uuid4())
    game_play_session_id = str(uuid4())
    nonce = secrets.token_hex(16)
    expires_at = now + timedelta(minutes=settings.game_launch_token_ttl_minutes)

    payload = {
        "iss": GAME_LAUNCH_ISSUER,
        "aud": GAME_LAUNCH_AUDIENCE,
        "sub": player_id,
        "token_kind": GAME_LAUNCH_TOKEN_KIND,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "game_code": game_code,
        "nonce": nonce,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {
        "game_code": game_code,
        "game_launch_token": token,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "expires_at": expires_at.isoformat(),
    }


def validate_game_launch_token(*, game_launch_token: str) -> dict[str, object]:
    try:
        payload = jwt.decode(
            game_launch_token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=GAME_LAUNCH_AUDIENCE,
            issuer=GAME_LAUNCH_ISSUER,
        )
    except jwt.InvalidTokenError as exc:
        raise GameLaunchTokenValidationError("Game launch token is not valid") from exc

    if payload.get("token_kind") != GAME_LAUNCH_TOKEN_KIND:
        raise GameLaunchTokenValidationError("Game launch token is not valid")
    if payload.get("game_code") != GAME_CODE_MINES:
        raise GameLaunchTokenValidationError("Game launch token is not valid")

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

    return {
        "game_code": GAME_CODE_MINES,
        "player_id": player_id,
        "platform_session_id": platform_session_id,
        "play_session_id": play_session_id,
        "game_play_session_id": game_play_session_id,
        "expires_at": datetime.fromtimestamp(expires_at, tz=UTC).isoformat(),
    }


def validate_optional_game_launch_token_for_player(
    *,
    game_launch_token: str | None,
    player_id: str,
) -> dict[str, object] | None:
    if not game_launch_token:
        return None

    launch_context = validate_game_launch_token(game_launch_token=game_launch_token)
    if launch_context["player_id"] != player_id:
        raise GameLaunchTokenOwnershipError("Game launch token ownership is not valid")
    return launch_context
