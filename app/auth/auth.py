from typing import Optional

from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from starlette.authentication import (
    AuthCredentials, AuthenticationBackend, UnauthenticatedUser
)
from fastapi import Request

from app.auth import models
from app.database import async_session
from app.settings import SECRET_KEY, ALGORITHM, CONCURRENT_CONNECTIONS


class BasicAuthBackend(AuthenticationBackend):
    a_s = async_session

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
                            models.User.email == email,
                            models.User.is_active == True,
                        )
                    )

                    if CONCURRENT_CONNECTIONS:
                        stmt = select(models.AuthToken).filter(
                            models.AuthToken.user_id == user_id,
                            models.AuthToken.is_active == True,
                        ).order_by(
                            models.AuthToken.id.desc()
                        ).limit(CONCURRENT_CONNECTIONS).subquery()
                        a_auth = aliased(models.AuthToken, stmt)
                        auth = await session.scalars(
                            select(a_auth).filter(a_auth.access_token == token)
                        )
                    else:
                        auth = await session.scalars(
                            select(models.AuthToken).where(
                                models.AuthToken.user_id == user_id,
                                models.AuthToken.access_token == token,
                                models.AuthToken.is_active == True,
                            )
                        )
                    return auth.one_or_none(), user.one_or_none()

        return AuthCredentials([]), UnauthenticatedUser

    async def authenticate(self, request: Request):
        async with self.a_s() as session:
            return await self.main_auth(request, session)
