from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import joinedload

from app.database import cache
from app.posts import models


async def get_post_in_db(
        post_id: int,
        request: Request,
        session: AsyncSession,

) -> models.Posts:
    post = await session.scalars(
        select(models.Posts).where(
            models.Posts.id == post_id,
            models.Posts.is_deleted == False,
        ).options(joinedload(models.Posts.author))
    )
    post = post.one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id={post_id} not found"
        )
    if post.author_id != request.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You can't edit a post with id={post_id}"
        )
    return post


async def setting_likes_dislikes(
        post_id: int,
        data: dict,
        request: Request,
        session: AsyncSession,
):
    text_result = "The reaction has not been changed"
    post = await session.scalars(
        select(models.Posts).where(
            models.Posts.id == post_id,
            models.Posts.author_id != request.user.id,
            models.Posts.is_deleted == False,
        )
    )

    like_info = await session.scalars(
        select(models.Likes).where(
            models.Likes.user_id == request.user.id,
            models.Likes.post_id == post_id,
        )
    )

    post = post.one_or_none()
    like_info = like_info.one_or_none()

    if not like_info and post and 'on' in data.values():
        like_info = models.Likes(
            user_id=request.user.id,
            post_id=post_id,
        )
        session.add(like_info)
    elif not like_info and post and 'off' in data.values():
        return text_result
    elif like_info and not post:
        # Deleting a self-like
        await session.delete(like_info)
        await session.commit()
        return text_result
    elif not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    data["current_status"] = like_info.like

    match data:

        case {"like": "on", "current_status": None} | \
             {"like": "on", "current_status": False}:
            like_info.like = True
            text_result = "The reaction is like delivered"

        case {"like": "off", "current_status": True} | \
             {"dislike": "off", "current_status": False}:
            await session.delete(like_info)
            text_result = "Reaction removed"

        case {"dislike": "on", "current_status": True} | \
             {"dislike": "on", "current_status": None}:
            like_info.like = False
            text_result = "The reaction is dislike delivered"

        case _:
            await session.rollback()
            return text_result

    await session.commit()
    await cache.incr(f"")
    return text_result
