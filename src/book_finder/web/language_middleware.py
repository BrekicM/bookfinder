from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from book_finder.i18n.resolve import resolve_language

COOKIE_NAME = "lang"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


class LanguageMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        query_param = request.query_params.get("lang")
        cookie = request.cookies.get(COOKIE_NAME)
        accept_language = request.headers.get("accept-language")

        language = resolve_language(query_param, cookie, accept_language)
        request.state.lang = language

        response = await call_next(request)

        if query_param is not None and query_param == language:
            response.set_cookie(COOKIE_NAME, language, max_age=_COOKIE_MAX_AGE)

        return response
