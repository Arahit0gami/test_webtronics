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
    fake: bool = False

    def update(self, params: dict):
        for k, v in params.items():
            if hasattr(self, k):
                setattr(self, k, v)
        return self
