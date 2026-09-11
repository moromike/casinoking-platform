"""PASSO 3-bis (3bA) — introspezione del gettone di lancio per i fornitori.

PERCHE' ESISTE: M&M Games non riceve il segreto JWT della piattaforma. Per
fidarsi di un gettone di lancio lo ripresenta qui, server-to-server,
autenticandosi come fornitore con lo schema HMAC esistente
(`providers/auth.py`: 422 intestazione di firma assente, 401 fornitore ignoto
o firma falsa — codici conservati, non reinventati).

PERCHE' 403 E NON 401 SUL GETTONE: l'autenticazione (chi chiama) e' gia'
stata decisa dalla firma; un gettone scaduto, non valido o di un gioco che
non appartiene al chiamante e' un problema di SCOPE, non di identita'.

La risposta porta solo i sei campi del contratto: niente segreti, niente
gettone, niente dati di sessione oltre quelli che il fornitore deve
rimandare al confine seamless.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.db.connection import db_connection
from app.modules.platform.game_launch.service import (
    GameLaunchTokenScopeError,
    GameLaunchTokenValidationError,
    validate_game_launch_token,
)
from app.modules.providers.auth import verify_provider_hmac

router = APIRouter(prefix="/providers", tags=["providers"])


class LaunchIntrospectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    launch_token: str


@router.post("/launch/introspect")
def introspect_launch_token(
    payload: LaunchIntrospectRequest,
    provider_code: str = Depends(verify_provider_hmac),
) -> dict[str, object]:
    try:
        context = validate_game_launch_token(game_launch_token=payload.launch_token)
    except (GameLaunchTokenValidationError, GameLaunchTokenScopeError) as exc:
        raise HTTPException(
            status_code=403, detail="Launch token is not valid for introspection"
        ) from exc

    # Il gettone vale solo per il fornitore che possiede il gioco: Coins a
    # M&M, il manichino al fornitore di collaudo. Chi chiede con un gettone
    # altrui riceve lo stesso 403 di un gettone falso, senza imparare niente.
    game_code = str(context["game_code"])
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT provider_code FROM game_engines WHERE engine_code = %s",
                (game_code,),
            )
            row = cursor.fetchone()
    if row is None or row["provider_code"] != provider_code:
        raise HTTPException(
            status_code=403, detail="Launch token scope is not valid for this provider"
        )

    user_id = context.get("player_id") or context.get("anonymous_id")
    wallet_type = context.get("wallet_type")
    currency = context.get("currency")
    if not all(isinstance(value, str) and value for value in (user_id, wallet_type, currency)):
        raise HTTPException(
            status_code=403, detail="Launch token is not valid for introspection"
        )

    return {
        "user_id": str(user_id),
        "game_session_id": str(context["game_play_session_id"]),
        "game_code": game_code,
        "wallet_type": str(wallet_type),
        "currency": str(currency),
        "expires_at": str(context["expires_at"]),
    }
