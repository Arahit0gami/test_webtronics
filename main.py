from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from app.auth.auth import BasicAuthBackend
from app.auth.router import router_auth, router_with_out_auth
from app.posts.router import router_posts, router_posts_wa
from app.users.router import router_users

middleware = [
    Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
]

app = FastAPI(
    middleware=middleware,
)

app.include_router(router_with_out_auth)
app.include_router(router_auth)
app.include_router(router_posts)
app.include_router(router_posts_wa)
app.include_router(router_users)
