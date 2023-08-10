import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import User
from app.database import Base


class Posts(Base):

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column()
    author = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    update_date: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)


class Likes(Base):

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    post_id = mapped_column(ForeignKey(Posts.id, ondelete='CASCADE'))
    # True==like, False==Dislike
    like: Mapped[bool] = mapped_column()
    update_date: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    created: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    __table_args__ = (
        UniqueConstraint(
            'user_id', 'post_id',
            name='unique_likes',
        ),
    )
