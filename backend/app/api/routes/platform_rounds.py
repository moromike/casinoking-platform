from fastapi import APIRouter, Header, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin, get_current_player, get_current_user
from app.api.responses import error_response
from app.modules.platform.game_launch.service import (
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    validate_game_launch_token,
)
from app.modules.platform.rounds.service import get_platform_round, platform_round_exists

router = APIRouter(prefix="/platform", tags=["platform-rounds"])


class GameLaunchValidateRequest(BaseModel):
    game_launch_token: str


@router.get("/rounds/{round_id}")
def get_platform_round_by_id(
    round_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, object] | object:
    # PERCHE' si replica la biforcazione di Mines: l'amministratore conserva la
    # lettura trasversale, il giocatore non puo' trasformare un id in una sonda
    # delle partite altrui.
    current_user = get_current_user(authorization)
    if current_user["role"] == "admin":
        current_admin = get_current_admin(authorization)
        result = get_platform_round(
            round_id=round_id,
            user_id=str(current_admin["id"]),
            viewer_role="admin",
        )
    else:
        current_player = get_current_player(authorization)
        result = get_platform_round(
            round_id=round_id,
            user_id=str(current_player["id"]),
            viewer_role="player",
        )

    if result is None:
        if platform_round_exists(round_id=round_id):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Game session ownership is not valid",
            )
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Game session not found",
        )
    return {"success": True, "data": result}


@router.post("/launch/validate")
def validate_platform_launch_token(
    payload: GameLaunchValidateRequest,
) -> dict[str, object] | object:
    try:
        # PERCHE' non si passa expected_game_code: il gettone e' della
        # piattaforma e la sua validita' non dipende dal runtime che lo usa.
        result = validate_game_launch_token(game_launch_token=payload.game_launch_token)
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except GameLaunchTokenScopeError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )
    return {"success": True, "data": result}
