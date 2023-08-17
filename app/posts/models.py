import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from sqlalchemy.sql.functions import func

from app.auth.models import User
from app.database import Base


class Likes(Base):

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    post_id = mapped_column(ForeignKey("posts.id", ondelete='CASCADE'))
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


class Posts(Base):

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column()
    author_id = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.now,
    )
    update_date: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False)
    author: Mapped["User"] = relationship(lazy="joined")
    like = column_property(
        select(func.count(Likes.id))
        .where(Likes.like == True, Likes.post_id == id)
        .correlate_except(Likes)
        .scalar_subquery()
    )
    dislike = column_property(
        select(func.count(Likes.id))
        .where(Likes.like == False, Likes.post_id == id)
        .correlate_except(Likes)
        .scalar_subquery()
    )
