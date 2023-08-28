import time
from typing import List

import pytest
from httpx import AsyncClient

from app.auth.schemas import Token, create_token
from app.users.schemas import UserToken
from tests.test_data import FakeUser


HTTP_ERROR_401 = {"detail": "Could not validate credentials"}


@pytest.mark.order(1)
async def test_register(ac: AsyncClient, users: List[FakeUser]):
    after_register = {"id", "username", "email", "is_active"}
    response_result = {
        201: {
            "key_params": after_register,
        },
        400: {
            "result":  {
                'detail': 'An account with this email '
                          'has already been registered'
            },
        },
    }
    for user in users:
        response = await ac.post(
            "/auth/register", json=user.model_dump(
                include={"username", "password", "email"}
            )
        )
        if user.fake:
            assert response.status_code == 422
        if not user.fake:
            assert response.status_code == 201
            assert set(response.json()) == response_result[201]["key_params"]
            user.update(response.json())

    for user in users:
        response = await ac.post(
            "/auth/register", json=user.model_dump(
                include={"username", "password", "email"}
            )
        )
        if user.fake:
            assert response.status_code == 422
        if not user.fake:
            assert response.status_code == 400
            assert response.json() == response_result[400]["result"]


@pytest.mark.order(2)
async def test_login(ac: AsyncClient, users: List[FakeUser]):
    after_login = {"refresh_token", "access_token", "token_type"}
    response_result = {
        201: {
            "key_params": after_login
        },
        404: {
            "result": {
                "detail": "Invalid username or password"
            }
        },
    }
    fake_users = []
    for user in users:
        response = await ac.post(
            "/auth/login", data={
                "username": user.email,
                "password": user.password,
            }
        )
        if user.fake:
            assert response.status_code == 404
            assert response.json() == response_result[404]["result"]
            fake_users.append(user)

        if not user.fake:
            assert response.status_code == 201
            assert set(response.json()) == response_result[201]["key_params"]
            user.update(response.json())

    # Delete bad users, we don't need them.
    for f in fake_users:
        users.pop(users.index(f))


@pytest.mark.order(3)
async def test_create_token(ac: AsyncClient, users: List[FakeUser]):
    after_create_token = {"refresh_token", "access_token", "token_type"}
    response_result = {
        201: {
            "key_params": after_create_token
        },
        401: {
            "result": {
                "detail": "Invalid refresh token"
            }
        },
    }

    for i, user in enumerate(users):
        assert user.fake == False
        refresh_token = user.refresh_token

        if i == 1:
            time.sleep(1)
            new_token: Token = create_token(
                user=UserToken.model_validate(user),
            )
            refresh_token = new_token.refresh_token
        if i == 3:
            refresh_token = refresh_token[:-3] + 'tYuO'

        response = await ac.post(
            "/auth/token", json={
                "refresh_token": refresh_token,
            }
        )

        if i in [1, 3]:
            assert response.status_code == 401
            assert response.json() == response_result[401]["result"]
        else:
            assert response.status_code == 201
            assert set(response.json()) == response_result[201]["key_params"]
            user.update(response.json())


@pytest.mark.order(4)
async def test_logout(ac: AsyncClient, users: List[FakeUser]):
    response_result = {
        401: {
            "result": HTTP_ERROR_401
        },
    }
    number_user = [2, 4]

    for i, user in enumerate(users):
        headers = {"Authorization": f"{user.token_type} {user.access_token}"}

        if i in number_user:
            time.sleep(1)
            new_token: Token = create_token(
                user=UserToken.model_validate(user),
                refresh_token=user.refresh_token
            )
            headers = {
                "Authorization": f"{user.token_type} {new_token.access_token}"
            }

        response = await ac.delete(
            "/auth/logout",
            headers=headers
        )

        if i in number_user:
            assert response.status_code == 401
            assert response.json() == response_result[401]["result"]
            assert response.headers['www-authenticate'].lower() == "bearer"
        else:
            assert response.status_code == 204
            assert response.text == ''

    await test_login(ac, users)


@pytest.mark.order(5)
async def test_change_password(ac: AsyncClient, users: List[FakeUser]):
    response_result = {
        200: {
            "result": "Password changed successfully"
        },
        400: {
            1: {
                "detail": "The new password does not match the repeated password"
            },
            2: {
                "detail": "The new password must not match the old password"
            },
            3: {
                "detail": "The current password was entered incorrectly"
            },
        },
        401: {
            "result": HTTP_ERROR_401
        },
    }

    for user in users:
        right_headers = {
            "Authorization": f"{user.token_type} {user.access_token}"
        }
        old_password = user.password
        new_password = f"test321{user.id}"
        repeat_new_password = new_password

        for number in range(1, 6):
            match number:
                case 1:
                    params = {
                        "old_password": old_password,
                        "new_password": new_password + "123",
                        "repeat_new_password": repeat_new_password,
                    }
                    headers = right_headers
                case 2:
                    params = {
                        "old_password": old_password,
                        "new_password": old_password,
                        "repeat_new_password": old_password,
                    }
                    headers = right_headers
                case 3:
                    params = {
                        "old_password": old_password + "123",
                        "new_password": new_password,
                        "repeat_new_password": repeat_new_password,
                    }
                    headers = right_headers
                case 4:
                    params = {
                        "old_password": old_password,
                        "new_password": new_password,
                        "repeat_new_password": repeat_new_password,
                    }
                    headers = {
                        "Authorization": f"{user.token_type} "
                                         f"{user.access_token}1"
                    }
                case _:
                    params = None
                    headers = right_headers

            response = await ac.post(
                "/auth/change-password",
                headers=headers,
                json=params,
            )
            if number == 4:
                assert response.status_code == 401, f"{user}"
                assert response.json() == response_result[401]["result"]
            elif not params:
                assert response.status_code == 422
            else:
                assert response.status_code == 400, f"{user}"
                assert response.json() == response_result[400][number]

        else:
            response = await ac.post(
                "/auth/change-password",
                headers=right_headers,
                json={
                    "old_password": old_password,
                    "new_password": new_password,
                    "repeat_new_password": repeat_new_password,
                }
            )
            assert response.status_code == 200, f"{user}"
            assert response.json() == response_result[200]["result"], f"{user}"
            user.password = new_password
