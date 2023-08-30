import datetime
import random
from typing import List

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.models import Posts
from tests.test_auth import HTTP_ERROR_401
from tests.test_data import FakeUser, FakePost


@pytest.mark.order(7)
async def test_create_post(
        ac: AsyncClient, users: List[FakeUser], posts: List[FakePost]
):
    after_create = {
        "id", "title", "text", "author",
        "created", "update_date", "like", "dislike", "my_like"
    }
    response_result = {
        201: {
            "key_params": after_create
        },
        401: {
            "result": HTTP_ERROR_401
        },
    }
    for post in posts:
        user: FakeUser = random.choice(users)
        headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        response = await ac.post(
            "/posts/create",
            headers=headers,
            json={
                "title": post.title,
                "text": post.text,
            }
        )
        assert response.status_code == 201, user
        assert set(response.json()) == response_result[201]["key_params"], user
        post.update(response.json())

    else:
        user: FakeUser = random.choice(users)
        post: FakePost = random.choice(posts)
        headers = {"Authorization": f"{user.token_type} {user.access_token}2"}
        response = await ac.post(
            "/posts/create",
            headers=headers,
            json={
                "title": post.title,
                "text": post.text,
            }
        )
        assert response.status_code == 401
        assert response.json() == response_result[401]["result"]

        headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        response = await ac.post(
            "/posts/create",
            headers=headers,
            json={
                "title": post.title*200,
                "text": post.text*4000,
            }
        )
        assert response.status_code == 422


def get_fake_user(user_id, users: List[FakeUser], bad_user=False):
    for user in users:
        if bad_user and user.id != user_id:
            return user
        elif not bad_user and user.id == user_id:
            return user


@pytest.mark.order(8)
async def test_delete_post(
        ac: AsyncClient, users: List[FakeUser], posts: List[FakePost]
):
    response_result = {
        200: {
            "result": "Post with id={} successfully deleted"
        },
        401: {
            "result": HTTP_ERROR_401
        },
        403: {
            "result": {
                "detail": "You can't edit a post with id={}"
            }
        },
        404: {
            "result": {
                "detail": "Post with id={} not found"
            }
        },
    }

    async def post_delete(
            post: FakePost, bad_user=False, bad_token=False, bad_post_id=None
    ):
        user = get_fake_user(post.author.id, users, bad_user=bad_user)
        token = user.access_token if not bad_token else user.access_token+'2'
        headers = {"Authorization": f"{user.token_type} {token}"}
        return await ac.delete(
            f"/posts/{post.id if not bad_post_id else bad_post_id}",
            headers=headers,
        )

    for post in posts[90:100]:
        response = await post_delete(post, bad_user=True)
        assert response.status_code == 403
        assert response.json() == {
            "detail": response_result[403]["result"]["detail"].format(post.id)
        }

    for post in posts[90:100]:
        response = await post_delete(post)
        assert response.status_code == 200
        assert response.json() == response_result[200]["result"].format(
            post.id
        )
        post.is_deleted = True

    for post in posts[90:100]:
        response = await post_delete(post)
        assert response.status_code == 404
        assert response.json() == {
            "detail": response_result[404]["result"]["detail"].format(post.id)
        }

    for post in posts[90:100]:
        response = await post_delete(post, bad_token=True)
        assert response.status_code == 401
        assert response.json() == response_result[401]["result"]

    for post in posts[90:100]:
        response = await post_delete(post, bad_post_id="t")
        assert response.status_code == 422


@pytest.mark.order(9)
async def test_update_post(
        ac: AsyncClient, users: List[FakeUser], posts: List[FakePost]
):
    after_update = {
        "id", "title", "text", "author",
        "created", "update_date", "like", "dislike", "my_like"
    }
    response_result = {
        200: {
            "key_params": after_update
        },
        401: {
            "result": HTTP_ERROR_401
        },
        403: {
            "result": {
                "detail": "You can't edit a post with id={}"
            }
        },
        404: {
            "result": {
                "detail": "Post with id={} not found"
            }
        },
    }

    async def post_udate(
            post: FakePost, bad_user=False,
            bad_token=False, bad_post_id=None,
    ):
        user = get_fake_user(post.author.id, users, bad_user=bad_user)
        token = user.access_token if not bad_token else user.access_token+'2'
        headers = {"Authorization": f"{user.token_type} {token}"}
        title = f"TITLE Update post {post.id}"
        text = f"text updsate post {post.id}"
        return await ac.put(
            f"/posts/{post.id if not bad_post_id else bad_post_id}",
            headers=headers,
            json={
                "title": title,
                "text": text
            }
        )

    for post in posts[:20]:
        response = await post_udate(post, bad_user=True)
        assert response.status_code == 403
        assert response.json() == {
            "detail": response_result[403]["result"]["detail"].format(post.id)
        }

    for post in posts[20:40]:
        response = await post_udate(post)
        assert response.status_code == 200
        assert set(response.json()) == response_result[200]["key_params"]
        post.update(response.json())

    # these posts have been deleted
    for post in posts[90:100]:
        response = await post_udate(post)
        assert response.status_code == 404
        assert response.json() == {
            "detail": response_result[404]["result"]["detail"].format(post.id)
        }

    for post in posts[60:80]:
        response = await post_udate(post, bad_token=True)
        assert response.status_code == 401
        assert response.json() == response_result[401]["result"]

    for post in posts[40:60]:
        response = await post_udate(post, bad_post_id="t")
        assert response.status_code == 422


@pytest.mark.order(11)
async def test_like_post(
        ac: AsyncClient, users: List[FakeUser], posts: List[FakePost]
):

    response_result = {
        200: {
            "key_params": {
                1: "The reaction is like delivered",
                2: "Reaction removed",
                3: "The reaction is dislike delivered",
                4: "The reaction has not been changed",
            }
        },
        400: {
            "result": {
                "detail": 'Pass one of the "like" or "dislike" parameters'
            }
        },
        401: {
            "result": HTTP_ERROR_401
        },
        404: {
            "result": {
                "detail": "Post with id={} not found"
            }
        },
    }

    async def post_like(
            post: FakePost,
            user: FakeUser,
            bad_token=False,
            bad_post_id=None, like=None, dislike=None
    ):
        token = user.access_token if not bad_token else user.access_token+'2'
        headers = {"Authorization": f"{user.token_type} {token}"}
        data = {}
        if like is not None:
            data.update({"like": like})
        if dislike is not None:
            data.update({"dislike": dislike})
        return await ac.post(
            f"/posts/like/{post.id if not bad_post_id else bad_post_id}",
            headers=headers,
            json=data
        )

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][1]
            else:
                response = await post_like(post, user=user, like="on")
                assert response.status_code == 404
                assert response.json() == {
                    "detail": response_result[404][
                        "result"
                    ]["detail"].format(post.id)
                }

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][4]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="off")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][2]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="off")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][4]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][3]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][4]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="off")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][2]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="off")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][4]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][1]

    for post in posts[:51]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][3]

    for post in posts[90:100]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="on")
                assert response.status_code == 404
                assert response.json() == {
                    "detail": response_result[404]["result"]["detail"].format(
                        post.id)
                }

    for post in posts[:51]:
        for user in users[:3]:
            if user.id != post.author.id:
                response = await post_like(post, user=user, like="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][1]
                user.count_like += 1
                post.like += 1

    for post in posts[:51]:
        for user in users[3:]:
            if user.id != post.author.id:
                response = await post_like(post, user=user, dislike="on")
                assert response.status_code == 200
                assert response.json() == response_result[200]["key_params"][4]
                user.count_dislike += 1
                post.dislike += 1

    for post in posts[:20]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(
                    post, user=user, dislike="off", like="on"
                )
                assert response.status_code == 400
                assert response.json() == response_result[400]["result"]

    for post in posts[:20]:
        for user in users:
            if user.id != post.author.id:
                response = await post_like(
                    post, user=user, like="on", bad_token=True
                )
                assert response.status_code == 401
                assert response.json() == response_result[401]["result"]


@pytest.mark.order(12)
async def test_get_posts(
        ac: AsyncClient,
        users: List[FakeUser],
        posts: List[FakePost],
):

    after_get = {
        "id", "title", "text", "author",
        "created", "update_date", "like", "dislike", "my_like"
    }
    response_result = {
        200: {
            "key_params": after_get,
        },
        404: {
            "result": {
                "detail": "Post with id={} not found"
            }
        },
    }

    async def post_get(
            post: FakePost,
            user: FakeUser = None,
    ):
        if user:
            headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        else:
            headers = None
        return await ac.get(
            f"/posts/{post.id}",
            headers=headers,
        )

    for post in posts:
        if post.is_deleted is False:
            response = await post_get(post)
            assert response.status_code == 200
            post.author.username = response.json()["author"][
                "username"
            ]
            assert response.json() == post.model_dump(include=after_get)

    for post in posts:
        if post.is_deleted is True:
            response = await post_get(post)
            assert response.status_code == 404
            assert response.json() == {
                    "detail": response_result[404]["result"]["detail"].format(
                        post.id)
                }

    for user in users:
        for post in posts[:20]:
            if post.author.id != user.id:
                response = await post_get(post, user)
                assert response.status_code == 200
                params_post = post.model_dump(include=after_get)
                assert response.json()["my_like"] != None
                params_post["my_like"] = response.json()["my_like"]
                assert response.json() == params_post, user.username
            else:
                params_post = post.model_dump(include=after_get)
                response = await post_get(post, user)
                assert response.status_code == 200
                params_post["author"]["username"] = user.username
                assert response.json() == params_post


