from typing import Annotated

from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import reuseable_oauth
from app.auth.router_class import RouteAuth, RouteWithOutAuth
from app.database import get_session
from app.posts import models
from app.posts import schemas

router_posts = APIRouter(
    prefix="/posts",
    tags=["posts"],
    route_class=RouteAuth,
    dependencies=[Depends(reuseable_oauth)]
)

router_posts_wa = APIRouter(
    prefix="/posts",
    tags=["posts"],
    route_class=RouteWithOutAuth,
)


@router_posts.post(
    "/create",
    response_model=schemas.PostBase,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
        post_items: schemas.PostCreate,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> models.Posts:
    post = models.Posts(
        text=post_items.text,
        author=request.user.id,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post
