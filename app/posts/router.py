import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import reuseable_oauth
from app.auth.router_class import RouteAuth, RouteWithOutAuth
from app.database import get_session
from app.posts import models
from app.posts import schemas
from app.posts.utils import get_post_in_db, setting_likes_dislikes
from app.posts.schemas import FilterPosts, LikeDislike


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


@router_posts_wa.get(
    "/",
    response_model=schemas.AllPosts,
    status_code=status.HTTP_200_OK
)
async def get_posts(
    session: Annotated[AsyncSession, Depends(get_session)],
    q: Annotated[FilterPosts, Depends()]
):
    """
    Viewing all posts.\n
    Filter: author, date_from, date_to \n
    Sorting: from_new_to_old \n
    Skip and Limit
    """
    count = await session.scalars(q.select_posts(count=True))
    posts = await session.scalars(
        q.select_posts()
    )

    return {**q.model_dump(), "posts": posts, "total": count.one()}


@router_posts.post(
    "/create",
    response_model=schemas.PostBase,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
        post_items: schemas.PostCreateOrUpdate,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> models.Posts:
    post = models.Posts(
        text=post_items.text,
        author=request.user,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@router_posts_wa.get(
    "/{post_id}",
    response_model=schemas.PostBase,
    status_code=status.HTTP_200_OK
)
async def get_post(
        post_id: int,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    post = await session.scalars(
        select(models.Posts).where(
            models.Posts.id == post_id,
            models.Posts.is_deleted == False,
        )
    )
    post = post.one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"post with id={post_id} not found"
        )

    return post


@router_posts.put(
    "/{post_id}",
    response_model=schemas.PostBase,
    status_code=status.HTTP_200_OK
)
async def update_post(
        post_id: int,
        post_items: schemas.PostCreateOrUpdate,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> models.Posts:
    post = await get_post_in_db(post_id, request, session)
    post.text = post_items.text
    post.update_date = datetime.datetime.now()
    await session.commit()

    return post


@router_posts.delete(
    "/{post_id}",
    status_code=status.HTTP_200_OK
)
async def delete_post(
        post_id: int,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    post = await get_post_in_db(post_id, request, session)
    post.is_deleted = True
    post.update_date = datetime.datetime.now()
    await session.commit()

    return f"Post with id={post_id} successfully deleted"


@router_posts.post(
    "/like/{post_id}",
    status_code=status.HTTP_200_OK
)
async def like_post(
        post_id: int,
        request: Request,
        form_data: LikeDislike,
        session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await setting_likes_dislikes(
        post_id=post_id,
        data=form_data.model_dump(),
        request=request,
        session=session,
    )

    return result
