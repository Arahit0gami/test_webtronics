from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr


class UserLogin(UserBase):
    password: str


class UserName(BaseModel):
    username: str = Field(min_length=1, max_length=40)


class UserCreate(UserBase, UserName):
    password: str = Field(min_length=4, max_length=20)


class User(UserBase):
    id: int
    username: str
    is_active: bool


class UserToken(UserBase):
    id: int
    username: str
