from typing import List

import pytest
from httpx import AsyncClient

from tests.test_auth import HTTP_ERROR_401
from tests.test_data import FakeUser


@pytest.mark.order(6)
async def test_get_me(ac: AsyncClient, users: List[FakeUser]):
    after_get_me = {"id", "username", "email", "is_active"}
    response_result = {
        401: {
            "result": HTTP_ERROR_401
        },
    }
    for user in users:
        headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        response = await ac.get(
            "/user/",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json() == user.model_dump(include=after_get_me)

    for user in users:
        headers = {"Authorization": f"{user.token_type} {user.access_token}2"}
        response = await ac.get(
            "/user/",
            headers=headers
        )
        assert response.status_code == 401
        assert response.json() == response_result[401]["result"]


@pytest.mark.order(8)
async def test_change_name_user(ac: AsyncClient, users: List[FakeUser]):
    before_change = {"id", "username", "email", "is_active"}
    response_result = {
        401: {
            "result": HTTP_ERROR_401
        },
    }
    for user in users:
        user_fields = user.model_dump(include=before_change)
        new_name = "name"+user.username
        headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        response = await ac.put(
            "/user/",
            headers=headers,
            json={"username": new_name}
        )

        assert response.status_code == 200
        user_fields["username"] = new_name
        assert response.json() == user_fields
        user.update(response.json())

    for user in users:
        headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        response = await ac.put(
            "/user/",
            headers=headers,
            json={"email": "tt"+user.email}

        )
        assert response.status_code == 422, user

    for user in users:
        headers = {"Authorization": f"{user.token_type} {user.access_token}2"}
        response = await ac.put(
            "/user/",
            headers=headers,
            json={"username": "tt"+user.username}

        )
        assert response.status_code == 401
        assert response.json() == response_result[401]["result"]


@pytest.mark.order(10)
async def test_delete_me(ac: AsyncClient, users: List[FakeUser]):
    after_del_me = {"id", "username", "email", "is_active"}
    response_result = {
        401: {
            "result": HTTP_ERROR_401
        },
    }
    users_for_delete = [6, 7, 8, 9]
    list_user_deleted = []
    for user in users:
        if user.id in users_for_delete:
            user_fields = user.model_dump(include=after_del_me)
            headers = {"Authorization": f"{user.token_type} {user.access_token}"}
            response = await ac.delete(
                "/user/delete",
                headers=headers,
            )

            assert response.status_code == 200
            user_fields["is_active"] = False
            assert response.json() == user_fields
            user.update(response.json())
            list_user_deleted.append(user)

    for user in users:
        if user.id in users_for_delete:
            headers = {"Authorization": f"{user.token_type} {user.access_token}"}
            response = await ac.delete(
                "/user/delete",
                headers=headers
            )
            assert response.status_code == 401
            assert response.json() == response_result[401]["result"]

    for user in list_user_deleted:
        users.pop(users.index(user))
