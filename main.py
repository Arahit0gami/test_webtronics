from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from app.auth.auth import BasicAuthBackend
from app.auth.router import router_auth, router_with_out_auth


middleware = [
    Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())
]

app = FastAPI(
    middleware=middleware,
)

app.include_router(router_with_out_auth)
app.include_router(router_auth)
