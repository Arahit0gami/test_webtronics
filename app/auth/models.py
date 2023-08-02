import datetime

from sqlalchemy import Boolean, Column, ForeignKey, \
    Integer, String, DateTime, Float
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)


class UsersActivity(Base):
    __tablename__ = "users_activity"

    id = Column(Integer, primary_key=True, index=True)

    url = Column(String)
    addr = Column(String)
    port = Column(Integer)
    method = Column(String)
    user_agent = Column(String)
    content_type = Column(String)
    content_length = Column(String)
    body = Column(String)
    query_string = Column(String)
    form_data = Column(String)

    user = Column(Integer, ForeignKey('users.id'))
    session = Column(String)
    action = Column(String)

    result_status = Column(Integer)
    result_len = Column(Integer)
    result_content = Column(String)
    millis = Column(Float)

    traceback = Column(String)

    created = Column(
        DateTime,
        default=datetime.datetime.now,
    )

