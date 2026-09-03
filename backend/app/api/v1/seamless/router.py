from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from decimal import Decimal
from typing import Annotated
import uuid

# Import the new provider hmac validation
from app.modules.providers.auth import verify_provider_hmac

router = APIRouter(prefix="/seamless", tags=["Seamless Wallet"])

class ReserveRequest(BaseModel):
    tx_id: str
    amount: Decimal

class CommitRequest(BaseModel):
    tx_id: str
    amount: Decimal
    is_win: bool

class RollbackRequest(BaseModel):
    tx_id: str

@router.post("/wallet/reserve", dependencies=[Depends(verify_provider_hmac)])
def reserve_funds(req: ReserveRequest):
    # TODO: Call ledger to reserve
    return {"status": "success", "balance_after": 100.0}

@router.post("/wallet/commit", dependencies=[Depends(verify_provider_hmac)])
def commit_funds(req: CommitRequest):
    # TODO: Call ledger to commit
    return {"status": "success", "balance_after": 100.0 + float(req.amount)}

@router.post("/wallet/rollback", dependencies=[Depends(verify_provider_hmac)])
def rollback_funds(req: RollbackRequest):
    return {"status": "success", "balance_after": 100.0}
