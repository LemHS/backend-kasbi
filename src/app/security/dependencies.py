from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import get_db
from app.models.user import User
from app.security.jwt import TokenType, decode_token, JWTRequest

bearer_scheme = HTTPBearer(auto_error=False)

class GetUser():
    def __init__(
            self
    ):
        pass

    def __call__(
            self,
            credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
            session: Session = Depends(get_db)
    ) -> User:
        
        self.session = session
        return self.get_current_user(credentials)

    def get_current_user(
            self,
            credentials: HTTPAuthorizationCredentials,
    ) -> User:
        if credentials is None:
            raise HTTPException(status_code=401, detail={"error_code": "auth_required", "message": "Authorization header missing"})
        
        payload = self.check_token(credentials)
        token_version = payload.get("token_version")
        user_id = payload.get("sub")
        user = self.check_user(user_id)

        if user.token_version != token_version:
            raise HTTPException(status_code=401, detail={"error_code": "token_revoked", "message": "Token revoked"})

        return user


    def check_token(
            self,
            credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    ) -> JWTRequest:
        try:
            payload = decode_token(credentials.credentials)
        except Exception as e:
            raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Invalid access token"}) from e
        
        return payload
    

    def check_user(
            self,
            user_id: int,
    ) -> User:
        if user_id is None:
            raise HTTPException(status_code=401, detail={"error_code": "invalid_token", "message": "Missing user id"})
        
        user = self.session.exec(
            select(User).options(selectinload(User.roles)).where(User.id == int(user_id))
        ).one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail={"error_code": "user_not_active", "message": "Missing or inactive user"})
        
        return user