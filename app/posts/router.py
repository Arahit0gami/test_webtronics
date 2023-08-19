import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import reuseable_oauth
from app.auth.router_class import RouteAuth, RouteWithOutAuth
from app.database import get_session
from app.posts import models
from app.posts import schemas
from app.posts.utils import get_post_in_db, setting_likes_dislikes, \
    get_post_in_db_and_like
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
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    q: Annotated[FilterPosts, Depends()]
):
    """
    Viewing all posts.\n
    Filter: author, date_from, date_to, my_like \n
    Sorting: from_new_to_old \n
    Skip and Limit \n
    my_like: like=True, dislike=False, nothing=None
    """
    count = await session.scalars(q.select_posts(
        request=request, count=True)
    )
    posts = await session.execute(
        q.select_posts(request=request)
    )
    result = [
        {
            **p._mapping.get("Posts", {}).__dict__,
            "my_like": p._mapping.get("my_like")
        } for p in posts
    ]

    return {**q.model_dump(), "posts": result, "total": count.one()}


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
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
):

    post = await get_post_in_db_and_like(post_id, request, session)

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
