from typing import Optional

from pydantic import BaseModel


class FakeUser(BaseModel):
    id: Optional[int] = None,
    email: Optional[str]
    username: Optional[str]
    password: Optional[str]
    is_active: Optional[bool] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_type: Optional[str] = None,
    count_like: int = 0
    count_dislike: int = 0
    fake: bool = False

    def update(self, params: dict):
        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)
        return self


class FakeAuthor(BaseModel):
    id: Optional[int] = None,
    username: Optional[str] = None


class FakePost(BaseModel):
    id: Optional[int] = None,
    title: Optional[str]
    text: Optional[str]
    author: Optional[FakeAuthor] = None
    created: Optional[str] = None
    update_date: Optional[str] = None
    like: Optional[int] = None
    dislike: Optional[int] = None
    my_like: Optional[bool] = None
    is_deleted: bool = False

    def update(self, params: dict):
        for k, v in params.items():
            if hasattr(self, k):
                if k == "author":
                    setattr(self, k, FakeAuthor(**v))
                    continue
                setattr(self, k, v)
        return self
