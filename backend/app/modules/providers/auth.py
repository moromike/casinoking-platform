import hmac
import hashlib
from fastapi import Request, HTTPException, Header, Depends
from .registry import get_provider_secret

async def verify_provider_hmac(request: Request, x_provider_id: str = Header(default="m-and-m-games"), x_signature_hmac: str = Header(...)):
    secret = get_provider_secret(x_provider_id)
    if not secret:
        raise HTTPException(status_code=401, detail="Unknown provider")
        
    body = await request.body()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected, x_signature_hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")
        
    return x_provider_id
