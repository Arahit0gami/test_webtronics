import datetime

from pydantic import BaseModel, Field


class PostBase(BaseModel):
    id: int
    text: str
    author: int
    created: datetime.datetime
    update_date: datetime.datetime


class PostCreate(BaseModel):
    text: str = Field(max_length=1000)
