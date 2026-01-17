from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal
from typing_extensions import TypedDict
from uuid import uuid4

import jwt

from config import get_settings

settings = get_settings()

class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"

class JWTRequest(TypedDict):
    sub: str
    role: str
    iat: int
    exp: int
    jti: str
    typ: Literal["access", "refresh"]

def _create_token(
        user_id: str, 
        role: str, 
        expires_delta: timedelta, 
        secret: str, 
        token_type: Literal["access", "refresh"], 
        extra_claims: Dict[str, Any] | None = None
    ) -> str:

    now = datetime.now(timezone.utc)
    payload: JWTRequest = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid4().hex,
        "typ": token_type
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, settings.JWT_HASHING_SCHEME)
        

def create_access_token(
        user_id: str,
        role: str,
        token_version: int,
        extra_claims: Dict[str, Any] | None = None
    ) -> str:

    expires = timedelta(settings.ACCESS_EXPIRE)
    claims = {"token_version": token_version}

    if extra_claims:
        claims.update(extra_claims)

    return _create_token(user_id, role, expires, settings.JWT_SECRET_KEY, TokenType.ACCESS, claims)

def create_refresh_token(
        user_id: str,
        role: str,
        token_version: int,
        extra_claims: Dict[str, Any] | None = None
    ) -> str:

    expires = timedelta(settings.REFRESH_EXPIRE)
    claims = {"token_version": token_version}

    if extra_claims:
        claims.update(extra_claims)

    return _create_token(user_id, role, expires, settings.JWT_REFRESH_KEY, TokenType.REFRESH, claims)

def decode_token(token: str, refresh: bool = False) -> Dict[str, Any]:
    secret = settings.JWT_REFRESH_KEY if refresh else settings.JWT_SECRET_KEY
    payload = jwt.decode(token, secret, algorithms=[settings.JWT_HASHING_SCHEME])

    return payload