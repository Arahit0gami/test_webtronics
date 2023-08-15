from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class UserLogin(UserBase):
    password: str


class UserCreate(UserBase):
    username: str
    password: str


class User(UserBase):
    id: int
    username: str
    is_active: bool


class UserToken(UserBase):
    id: int
    username: str
