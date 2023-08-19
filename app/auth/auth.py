from typing import Optional

from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, UnauthenticatedUser
)
from fastapi import Request

from app.auth import models
from app.database import async_session
from app.settings import SECRET_KEY, ALGORITHM


class BasicAuthBackend(AuthenticationBackend):

    @staticmethod
    def get_user_token(request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        return None if not authorization or scheme.lower() != "bearer" else token

    async def main_auth(self, request: Request, session: AsyncSession):
        token = self.get_user_token(request)
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            except JWTError:
                return AuthCredentials([]), UnauthenticatedUser

            match payload:
                case {
                    "id": int() as user_id,
                    "username": str() as username,
                    "email": str() as email,
                    "exp": int()
                }:
                    user = await session.scalars(
                        select(models.User).where(
                            models.User.id == user_id,
                            models.User.username == username,
                            models.User.email == email,
                            models.User.is_active == True,
                        )
                    )
                    auth = await session.scalars(
                        select(models.AuthToken).where(
                            models.AuthToken.user_id == user_id,
                            models.AuthToken.token == token,
                            models.AuthToken.is_active == True,
                        )
                    )
                    return auth.one_or_none(), user.one_or_none()

        return AuthCredentials([]), UnauthenticatedUser

    async def authenticate(self, request: Request):
        async with async_session() as session:
            return await self.main_auth(request, session)
