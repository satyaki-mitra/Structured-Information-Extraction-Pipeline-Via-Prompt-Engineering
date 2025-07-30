# DEPENDENCIES
from fastapi import Request
from starlette.types import Scope
from starlette.types import Send
from starlette.types import ASGIApp
from starlette.types import Receive
from starlette.middleware.base import BaseHTTPMiddleware


# REQUEST COUNTER MIDDLEWARE
class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.counter = 0

    async def dispatch(self, request: Request, call_next):
        self.counter                    += 1
        request_id                       = self.counter
        request.state.request_id         = request_id
        response                         = await call_next(request)
        response.headers["X-Request-ID"] = str(request_id)
        return response