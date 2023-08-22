import datetime
from typing import List, Optional, Literal, Any

from fastapi import HTTPException, status, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, Select, func
from sqlalchemy.orm import aliased

from app.posts import models
from app.users.models import User


class Author(BaseModel):
    id: int
    name: str = Field(alias="username")


class PostBase(BaseModel):
    id: int
    title: str
    text: str
    author: Author
    created: datetime.datetime
    update_date: datetime.datetime
    like: int = Field(description="count of likes")
    dislike: int = Field(description="count of dislikes")
    my_like: Optional[bool] = Field(
        default=None,
        description=
        """
        For authorized users:\n
        \tIf the "my_like" parameter is set to True, it means "like". \n
        \tIf the "my_like" parameter is set to False, it means "dislike". \n 
        \tIf "my_like" is Null, then "like" or "dislike" are not set. \n
        For not authorized users: \n
        \tmy_like will always be Null
        """,

    )


class PostCreateOrUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=4000)


class FilterPosts(BaseModel):
    skip: int = Field(default=0, le=20)
    limit: int = Field(default=10, ge=10, le=50)
    author: Optional[int] = Field(default=None, description="User ID")
    from_new_to_old: bool = True
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    my_like: Optional[bool] | Literal["all"] = Field(default=None)

    def select_posts(self, request: Request, count=None) -> Select:
        """
        Passes the FilterPosts parameters to the select(model.Post)
            * my_like True=like, False=dislike, all=like and dislike
            * author, date_from, date_to in .filter(*)
            * from_new_to_old in .order_by(*)
            * limit in .limit(*)
            * skip in .offset(*)
        """
        if isinstance(request.user, User):
            user: User = request.user
            sub_queries = [models.Likes.user_id == user.id, ]
            if self.my_like is not None:
                if self.my_like is True:
                    sub_queries.append(models.Likes.like == True)
                elif self.my_like is False:
                    sub_queries.append(models.Likes.like == False)
            subq = select(models.likes).where(
                *sub_queries
            ).subquery()
            my_like = aliased(models.Likes, subq)
        else:
            my_like = None

        queries = [models.Posts.is_deleted == False, ]
        if self.author:
            queries.append(models.Posts.author_id == self.author)
        if self.date_from and self.date_to:
            queries.append(models.Posts.created.between(
                self.date_from, self.date_to)
            )
        elif self.date_from:
            queries.append(models.Posts.created >= self.date_from)
        elif self.date_to:
            queries.append(models.Posts.created <= self.date_to)

        order_by = [
            models.Posts.created.desc() if self.from_new_to_old
            else models.Posts.created,
        ]

        if count and my_like and self.my_like is not None:
            return select(
                func.count(models.Posts.id)
            ).join(my_like).filter(*queries)
        elif count:
            return select(
                func.count(models.Posts.id)
            ).filter(*queries)

        if not my_like:
            return select(
                models.Posts
            ).filter(
                *queries
            ).order_by(*order_by).limit(self.limit).offset(self.skip)
        else:
            if self.my_like is not None:
                return select(
                    models.Posts,
                    my_like.like.label("my_like")
                ).join(
                    my_like
                ).filter(
                    *queries
                ).order_by(*order_by).limit(self.limit).offset(self.skip)
            else:
                return select(
                    models.Posts,
                    my_like.like.label("my_like")
                ).filter(
                    *queries
                ).join(
                    models.Posts,
                    full=True
                ).order_by(*order_by).limit(self.limit).offset(self.skip)


class AllPosts(FilterPosts):
    total: int
    posts: List[PostBase]


class LikeDislike(BaseModel):
    like: Literal["on", "off"] = Field(default=None)
    dislike: Literal["on", "off"] = Field(default=None)

    @model_validator(mode="before")
    def check_like_dislike(cls, data: Any) -> Any:
        if data.get("like") and data.get("dislike"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Pass one of the "like" or "dislike" parameters'
            )
        return data

