import datetime

from fastapi import HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import settings
from app.auth import models


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class UserLogin(UserBase):
    password: str


class UserCreate(UserBase):
    username: str
    password: str


class User(UserBase):
    id: int
    username: str
    is_active: bool


class UserToken(UserBase):
    id: int
    username: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str
    repeat_new_password: str


class TokenBase(BaseModel):
    token: str
    token_type: str = Field(default='Bearer')


class RefreshTokenBase(BaseModel):

    refresh_token: str


class RespToken(TokenBase, RefreshTokenBase):
    pass


class Token(TokenBase, RefreshTokenBase):
    user_id: int

    class Config:
        from_attributes = True


def create_token(
        user: UserToken,
        refresh_token: str = None
):
    if ACCESS_TOKEN_EXPIRE_MINUTES:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

    if refresh_token:
        return Token(
            user_id=user.id,
            token=jwt.encode(
                {**user.model_dump(), 'exp': expire},
                SECRET_KEY,
                algorithm=ALGORITHM
            ),
            refresh_token=refresh_token,
        )

    ref_expire = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    return Token(
        user_id=user.id,
        token=jwt.encode(
            {**user.model_dump(), 'exp': expire},
            SECRET_KEY,
            algorithm=ALGORITHM
        ),
        refresh_token=jwt.encode(
            {**user.model_dump(), 'exp': ref_expire},
            SECRET_KEY,
            algorithm=ALGORITHM
        ),
    )


async def new_token(
        refresh_token: str,
        session: AsyncSession,
):
    invalid_refresh_token = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid refresh token"
        )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise invalid_refresh_token

    match payload:
        case {
            'id': int() as id,
            'username': str() as username,
            'email': str() as email,
            'exp': int()
        }:
            user = await session.execute(
                select(models.User).where(
                    models.User.id == id,
                    models.User.username == username,
                    models.User.email == email,
                    models.User.is_active == True,
                )
            )
            user = user.scalars().one_or_none()
            if not user:
                raise invalid_refresh_token
            auth = await session.execute(
                select(models.AuthToken).where(
                    models.AuthToken.user_id == user.id,
                    models.AuthToken.refresh_token == refresh_token,
                    models.AuthToken.is_active == True,
                )
            )
            auth = auth.scalars().one_or_none()
            if not auth:
                raise invalid_refresh_token
            new_token: Token = create_token(
                user=UserToken.model_validate(user),
                refresh_token=refresh_token,
            )
            auth.token = new_token.token
            auth.last_update = datetime.datetime.now()
            await session.commit()
            return new_token
        case _:
            raise invalid_refresh_token


