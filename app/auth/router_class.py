import datetime
import traceback
from typing import Callable

from urllib.parse import unquote

from fastapi import Request, Response, status, Depends
from fastapi.exceptions import RequestValidationError, \
    ResponseValidationError, HTTPException
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer

from app.auth import models
from app.auth.models import UsersActivity
from app.database import async_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import DEBUG


class BaseUserLogs(APIRoute):

    u_act = UsersActivity
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    exclude_url_path: tuple[str] = ('/auth/register', '/auth/login')
    required_auth: bool = False
    http_response: dict = None
    # Anything from fastapi.security
    reuseable_oauth = None

    def get_route_handler(self) -> Callable:
        if self.required_auth and self.reuseable_oauth:
            if self.dependencies:
                self.dependencies.append(Depends(self.reuseable_oauth))
            else:
                self.dependencies = [Depends(self.reuseable_oauth)]
        elif self.required_auth and not self.reuseable_oauth:
            raise Exception(
                'required_auth is True, reuseable_oauth cannot be None'
            )
        if self.http_response:
            if isinstance(self.responses, dict):
                self.responses.update(self.http_response)
            else:
                self.responses = self.http_response

        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            async with async_session() as db:
                u_act = await self.create_log(db, request)
                try:
                    if self.required_auth and (not isinstance(
                            request.user, models.User
                    ) or not isinstance(
                        request.auth, models.AuthToken
                    )):
                        raise self.credentials_exception

                    response: Response = await original_route_handler(request)
                except Exception as exc:
                    formatted_lines = traceback.format_exc().splitlines()[-5:-1]
                    logs_errors = ''.join(formatted_lines)
                    if isinstance(exc, RequestValidationError) or \
                            isinstance(exc, ResponseValidationError):
                        await self.finish_log(
                            db, u_act, request, logs_errors=logs_errors
                        )
                        raise exc
                    elif isinstance(exc, HTTPException):
                        # manual errors write in u_act.content
                        response: Response = Response(
                            status_code=exc.status_code,
                            headers=exc.headers,
                            media_type=exc.detail
                        )
                        await self.finish_log(
                            db, u_act, request, response
                        )
                        raise exc
                    else:
                        if DEBUG:
                            raise exc
                        response: Response = Response(
                            status_code=500,
                            content='Server error'
                        )
                        await self.finish_log(
                            db, u_act, request, response, logs_errors
                        )
                        return response

                await self.finish_log(db, u_act, request, response)
                return response

        return custom_route_handler

    async def create_log(
            self, db: AsyncSession, request: Request
    ) -> UsersActivity:
        u_act = self.u_act(
            url=request.url.path,
            method=request.method,
            addr=request.client.host,
            port=request.client.port,
            user_agent=request.headers.get('user-agent'),
            content_type=request.headers.get('content-type'),
            content_length=request.headers.get('content-length'),
        )
        if request.url.path not in self.exclude_url_path:
            if request.query_params:
                u_act.query_string = str(request.query_params)
            if request.headers.get('content-type'):
                match request.headers['content-type'].split(';'):
                    case ['multipart/form-data', *_]:
                        form_data = await request.form()
                        u_act.form_data = str(form_data.multi_items())
                    case ['application/x-www-form-urlencoded', *_]:
                        u_act.body = unquote((await request.body()).decode())
                    case ['application/octet-stream', *_]:
                        pass
                    case _:
                        u_act.body = (await request.body()).decode()
        else:
            u_act.body = 'parameters removed for security'

        db.add(u_act)
        await db.commit()
        await db.refresh(u_act)
        return u_act

    @staticmethod
    async def finish_log(
            db: AsyncSession,
            u_act: UsersActivity,
            request: Request,
            result: Response | None = None,
            logs_errors: str | None = None
    ):
        if hasattr(request.user, 'id'):
            u_act.user = request.user.id
        if hasattr(request.auth, 'id'):
            u_act.auth = request.auth.id
        if result:
            u_act.result_status = result.status_code
            u_act.result_len = len(result.body)
            u_act.result_content = result.media_type
        u_act.traceback = logs_errors
        time_delta = datetime.datetime.now() - u_act.created
        u_act.millis = \
            (time_delta.seconds * 10 ** 6 + time_delta.microseconds) / 1000
        await db.commit()


class RouteAuth(BaseUserLogs):
    required_auth: bool = True
    exclude_url_path = ('/auth/change-password',)
    http_response = {
        401: {
            "description": "Unauthorized(Access_token)",
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {
                                "title": "Not authorized",
                                "description": "Could not validate credentials",
                                "example": {
                                    "description": "Could not validate credentials"
                                }
                            },
                        ]
                    }
                }
            },
        },
    }
    reuseable_oauth = OAuth2PasswordBearer(
        tokenUrl="/auth/login",
        scheme_name="JWT"
    )


class RouteWithOutAuth(BaseUserLogs):
    exclude_url_path = ('/auth/register', '/auth/login')
    required_auth: bool = False
