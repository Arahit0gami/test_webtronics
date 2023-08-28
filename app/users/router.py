from typing import Annotated

from fastapi import APIRouter, Depends, status, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router_class import RouteAuth
from app.database import get_session
from app.users import models
from app.users.schemas import User, UserName

router_users = APIRouter(
    prefix="/user",
    tags=["Users"],
    route_class=RouteAuth,
)


@router_users.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=User,
)
async def get_me(request: Request):
    return request.user


@router_users.put(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=User,
)
async def change_name_user(
        request: Request,
        form_data: UserName,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await session.get(
        models.User, request.user.id,
    )
    user.username = form_data.username
    await session.commit()
    return user


@router_users.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
    response_model=User,
)
async def get_me(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await session.get(
        models.User, request.user.id,
    )
    user.is_active = False
    await session.commit()
    return user
