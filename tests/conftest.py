import asyncio
import random
import string
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, \
    async_sessionmaker

from app.auth.auth import BasicAuthBackend
from app.auth.router_class import BaseUserLogs
from app.database import get_session, Base
from app.settings import (DB_HOST_TEST, DB_NAME_TEST, DB_PASS_TEST,
                          DB_PORT_TEST,
                          DB_USER_TEST)
from main import app
from tests.test_data import FakeUser, FakePost

# DATABASE
DATABASE_URL_TEST = f"postgresql+asyncpg://{DB_USER_TEST}:{DB_PASS_TEST}@{DB_HOST_TEST}:{DB_PORT_TEST}/{DB_NAME_TEST}"


engine_test = create_async_engine(DATABASE_URL_TEST, echo=False)
async_session = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)
Base.metadata.bind = engine_test


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

app.dependency_overrides[get_session] = override_get_async_session
BaseUserLogs.a_s = async_session
BasicAuthBackend.a_s = async_session


@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# SETUP
@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app=app, base_url="http://test")


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def db() -> AsyncGenerator[AsyncClient, None]:
    async with async_session() as session:
        yield session


@pytest.fixture(scope="session")
def users() -> list:
    users = [
        FakeUser(
            id=None,
            email=f"user{i}@example.com",
            username=f"user{i}",
            password=f"test123{i}",
            is_active=None,
            access_token=None,
            refresh_token=None,
            token_type=None,
            fake=False,
        )
        for i in range(1, 10)
    ]
    users.append(
        FakeUser(
            id=None,
            email=f"fake@example.com",
            username=f"fake"*11,
            password="tes",
            is_active=None,
            access_token=None,
            refresh_token=None,
            token_type=None,
            fake=True,
        )
    )
    users.append(
        FakeUser(
            id=None,
            email=f"fake1@example.com",
            username=f"fake1",
            password="tes"*7,
            is_active=None,
            access_token=None,
            refresh_token=None,
            token_type=None,
            fake=True,
        )
    )
    yield users


@pytest.fixture(scope="session")
def posts() -> list:
    letters = string.printable
    posts = [
        FakePost(
            title=''.join(
                random.choice(letters) for i in range(
                    random.randint(1, 200)
                )
            ),
            text=''.join(
                random.choice(letters) for i in range(
                    random.randint(1, 4000)
                )
            )
        )
        for i in range(100)
    ]
    yield posts
