from fastapi import Header, HTTPException
from typing import Optional
from .config import API_TOKEN

def verify_token(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    # expect 'Bearer <token>'
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True
