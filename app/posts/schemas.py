import datetime
from typing import List, Optional, Literal, Any

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, Select, func

from app.posts import models


class Author(BaseModel):
    id: int
    name: str = Field(alias='username')


class PostBase(BaseModel):
    id: int
    text: str
    author: Author
    created: datetime.datetime
    update_date: datetime.datetime


class PostCreateOrUpdate(BaseModel):
    text: str = Field(max_length=4000)


class FilterPosts(BaseModel):
    skip: int = Field(default=0, le=20)
    limit: int = Field(default=10, ge=10, le=50)
    author: Optional[int] = Field(default=None, description="author.id")
    from_new_to_old: bool = True
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None

    def select_posts(self, count=False) -> Select:
        """
        Passes the FilterPosts parameters to the select(model.Post)
            * author, date_from, date_to in .filter(*)
            * from_new_to_old in .order_by(*)
            * limit in .limit(*)
            * skip in .offset(*)

        :returns: select(model.Post).filter(*).order_by(**).limit(self.limit).offset(self.skip)
        """
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

        if count:
            return select(func.count(models.Posts.id)).filter(*queries)

        return select(
            models.Posts
        ).filter(
            *queries
        ).order_by(*order_by).limit(self.limit).offset(self.skip)


class AllPosts(FilterPosts):
    total: int
    posts: List[PostBase]


class LikeDislike(BaseModel):
    like: Literal['on', 'off'] = Field(default=None)
    dislike: Literal['on', 'off'] = Field(default=None)

    @model_validator(mode='before')
    def check_like_dislike(cls, data: Any) -> Any:
        if data.get("like") and data.get("dislike"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Pass one of the "like" or "dislike" parameters'
            )
        return data

