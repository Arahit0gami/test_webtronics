import datetime
import random
from typing import List

import pytest
from httpx import AsyncClient, Response
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
async def test_get_post(
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
            post.update({"author": response.json()["author"]})
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


@pytest.mark.order(13)
async def test_get_posts(
        ac: AsyncClient,
        users: List[FakeUser],
        posts: List[FakePost],
        db: AsyncSession
):

    after_get = {
        "id", "title", "text", "author",
        "created", "update_date", "like", "dislike", "my_like"
    }

    spec_time = datetime.datetime(year=2020, month=1, day=1)
    created_time_posts = {}
    posts_dict = {}

    # Modify records to allow the use of a date filter
    all_posts_in_db = await db.scalars(
        select(Posts).where(Posts.is_deleted == False)
    )
    for post in all_posts_in_db:
        post.created = spec_time
        created_time_posts.update({post.id: post.created})
        spec_time += datetime.timedelta(days=1)
    await db.commit()

    for post in posts:
        if post.is_deleted is False:
            post.created = created_time_posts[
                post.id
            ].strftime("%Y-%m-%dT%H:%M:%S")
            posts_dict.update({post.id: post.model_dump(include=after_get)})

    async def posts_get(
            user: FakeUser = None,
            skip: int = None,
            limit: int = None,
            author: int = None,
            from_new_to_old: bool = None,
            date_from: datetime.datetime = None,
            date_to: datetime.datetime = None,
            my_like: bool | str = None,
    ):
        if user:
            headers = {"Authorization": f"{user.token_type} {user.access_token}"}
        else:
            headers = None
        data = {}
        if skip:
            data.update({"skip": skip})
        if limit:
            data.update({"limit": limit})
        if author:
            data.update({"author": author})
        if from_new_to_old is not None:
            data.update({"from_new_to_old": from_new_to_old})
        if date_from:
            data.update({"date_from": date_from})
        if date_to:
            data.update({"date_to": date_to})
        if my_like is not None:
            data.update({"my_like": my_like})
        return await ac.get(
            f"/posts/",
            headers=headers,
            params=data,
        )

    def compare_results(
            status_code: int, results: Response, skip: int = 0,
            limit: int = 10, author: int = None, from_new_to_old: bool = True,
            date_from: datetime.datetime = None,
            date_to: datetime.datetime = None, my_like: bool | str = None,
            total: int = None, user: FakeUser = None
    ):
        assert results.status_code == status_code
        other_parameters = results.json()
        del other_parameters["posts"]

        if date_to:
            other_parameters["date_to"] = datetime.datetime.strptime(
                other_parameters["date_to"], '%Y-%m-%dT%H:%M:%S'
            )
        if date_from:
            other_parameters["date_from"] = datetime.datetime.strptime(
                other_parameters["date_from"], '%Y-%m-%dT%H:%M:%S'
            )

        assert other_parameters == {
            "skip": skip,
            "limit": limit,
            "author": author,
            "from_new_to_old": from_new_to_old,
            "date_from": date_from,
            "date_to": date_to,
            "my_like": my_like,
            "total": total,
        }
        assert len(results.json()["posts"]) <= results.json()["limit"]

        if user and my_like is not None:
            if my_like is True and not (author or date_to or date_from):
                assert results.json()["total"] == user.count_like
            elif my_like is False and not (author or date_to or date_from):
                assert results.json()["total"] == user.count_dislike
            elif my_like == "all" and not (author or date_to or date_from):
                assert (results.json()["total"] ==
                        user.count_like + user.count_dislike)

        date_check_more = datetime.datetime(year=2022, month=1, day=1)
        date_check_less = datetime.datetime(year=2019, month=1, day=1)
        for r in results.json()["posts"]:
            if user:
                post_params = posts_dict[r["id"]]
                post_params["my_like"] = r["my_like"]
                assert r == post_params
            else:
                assert r == posts_dict[r["id"]]

            if author:
                assert r["author"]["id"] == author
                assert r == posts_dict[r["id"]]
            if from_new_to_old is not None:
                date = datetime.datetime.strptime(
                    r["created"], '%Y-%m-%dT%H:%M:%S'
                )
                if from_new_to_old:
                    assert date < date_check_more
                    date_check_more = date
                    assert r == posts_dict[r["id"]]
                elif not from_new_to_old:
                    assert date > date_check_less
                    date_check_less = date
                    assert r == posts_dict[r["id"]]
            if date_from and date_to:
                date = datetime.datetime.strptime(
                    r["created"], '%Y-%m-%dT%H:%M:%S'
                )
                assert date_from <= date <= date_to
                assert r == posts_dict[r["id"]]

    # -------------------------------------------------------------------
    # Query without filters
    response = await posts_get()
    compare_results(
        status_code=200, results=response, total=90
    )

    # Filter by author
    check_author = random.randint(1, 6)
    response = await posts_get(skip=0, limit=50, author=check_author)
    compare_results(
        status_code=200, results=response, total=response.json()["total"],
        skip=0, limit=50, author=check_author
    )

    # Filter by nonexistent author
    response = await posts_get(author=100)
    assert response.json()["posts"] == []
    assert response.json()["total"] == 0

    # Filter from old to new and from new to old
    response = await posts_get(skip=0, limit=50, from_new_to_old=False)
    compare_results(
        status_code=200, results=response, total=response.json()["total"],
        skip=0, limit=50, from_new_to_old=False
    )

    response = await posts_get(skip=0, limit=50, from_new_to_old=True)
    compare_results(
        status_code=200, results=response, total=response.json()["total"],
        skip=0, limit=50, from_new_to_old=True
    )

    # Filter by date
    response = await posts_get(
        skip=0, limit=50,
        date_from=datetime.datetime(2020, 2, 1),
        date_to=datetime.datetime(2020, 3, 1)
    )
    compare_results(
        status_code=200, results=response,
        total=response.json()["total"],
        skip=0, limit=50,
        date_from=datetime.datetime(2020, 2, 1),
        date_to=datetime.datetime(2020, 3, 1),
    )

    for user in users:
        # In the two examples we pass limit outside the diapason
        response = await posts_get(user, skip=20, limit=5)
        compare_results(
            status_code=200, results=response,
            total=90, skip=20, limit=10, user=user,
        )

        # Filter by my likes or dislikes
        response = await posts_get(user, skip=0, limit=70, my_like=True)
        compare_results(
            status_code=200, results=response,
            total=response.json()["total"], skip=0, limit=50,
            user=user, my_like=True,
        )

        response = await posts_get(user, skip=0, limit=50, my_like=False)
        compare_results(
            status_code=200, results=response,
            total=response.json()["total"], skip=0, limit=50,
            user=user, my_like=False
        )

        response = await posts_get(user, skip=20, limit=50, my_like="all")
        compare_results(
            status_code=200, results=response,
            total=response.json()["total"], skip=20, limit=50,
            user=user, my_like="all"
        )

        # Set all filters
        check_my_like = random.choice([True, False, "all"])
        check_from_new_to_old = random.choice([True, False])
        response = await posts_get(
            user,
            skip=1,
            limit=10,
            my_like=check_my_like,
            from_new_to_old=check_from_new_to_old,
            date_from=datetime.datetime(2020, 1, 1),
            date_to=datetime.datetime(2020, 4, 1),
            author=check_author
        )
        compare_results(
            status_code=200, results=response,
            user=user,
            total=response.json()["total"],
            skip=1,
            limit=10,
            my_like=check_my_like,
            from_new_to_old=check_from_new_to_old,
            date_from=datetime.datetime(2020, 1, 1),
            date_to=datetime.datetime(2020, 4, 1),
            author=check_author
        )

