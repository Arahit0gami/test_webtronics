from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import joinedload

from app.posts import models


async def get_post_in_db(
        post_id: int,
        request: Request,
        session: AsyncSession,

):
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
