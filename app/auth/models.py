import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.users.models import User


class AuthToken(Base):

    __tablename__ = "auth"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id = mapped_column(ForeignKey(User.id))
    access_token: Mapped[str] = mapped_column(
       unique=True, nullable=False
    )
    last_update: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    refresh_token: Mapped[str] = mapped_column(
        unique=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    __table_args__ = (Index('ix_user_id', user_id),)


class UsersActivity(Base):

    __tablename__ = "users_activity"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    url: Mapped[str] = mapped_column()
    addr: Mapped[str] = mapped_column()
    port: Mapped[int] = mapped_column()
    method: Mapped[str] = mapped_column()
    user_agent: Mapped[Optional[str]] = mapped_column()
    content_type: Mapped[Optional[str]] = mapped_column()
    content_length: Mapped[Optional[str]] = mapped_column()
    body: Mapped[Optional[str]] = mapped_column()
    query_string: Mapped[Optional[str]] = mapped_column()
    form_data: Mapped[Optional[str]] = mapped_column()

    user = mapped_column(ForeignKey(User.id))
    auth = mapped_column(ForeignKey(AuthToken.id))

    result_status: Mapped[Optional[int]] = mapped_column()
    result_len: Mapped[Optional[int]] = mapped_column()
    result_content: Mapped[Optional[str]] = mapped_column()
    millis: Mapped[Optional[float]] = mapped_column()

    traceback: Mapped[Optional[str]] = mapped_column()

    created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
