from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from decimal import Decimal
from typing import Annotated
import uuid

router = APIRouter(prefix="/seamless", tags=["Seamless Wallet"])

def verify_provider(authorization: Annotated[str, Header()]):
    if authorization != "Bearer PROVIDER_API_KEY_123":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

class ReserveRequest(BaseModel):
    player_id: str
    amount: Decimal
    currency: str
    game_session_id: str

class CommitRequest(BaseModel):
    player_id: str
    transaction_id: str
    win_amount: Decimal

class RollbackRequest(BaseModel):
    player_id: str
    transaction_id: str

@router.post("/wallet/reserve", dependencies=[Depends(verify_provider)])
def reserve_funds(req: ReserveRequest):
    # TODO: Call ledger to reserve
    return {"transaction_id": str(uuid.uuid4()), "balance_after": 100.0}

@router.post("/wallet/commit", dependencies=[Depends(verify_provider)])
def commit_funds(req: CommitRequest):
    # TODO: Call ledger to commit
    return {"balance_after": 100.0 + float(req.win_amount)}

@router.post("/wallet/rollback", dependencies=[Depends(verify_provider)])
def rollback_funds(req: RollbackRequest):
    return {"balance_after": 100.0}

@router.get("/auth/validate", dependencies=[Depends(verify_provider)])
def validate_token(token: str):
    return {"player_id": str(uuid.uuid4()), "currency": "EUR", "balance": 100.0}
