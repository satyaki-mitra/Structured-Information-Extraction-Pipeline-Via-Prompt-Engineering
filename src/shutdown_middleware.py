# DEPENDENCIES
import logging
import warnings
from fastapi import FastAPI
from starlette.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# LOGGING 
logger = logging.getLogger(__name__)


class ShutdownMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle graceful shutdown of the FastAPI application

    This middleware intercepts incoming requests and checks if the server
    is in the process of shutting down. If so, it returns a 503 Service
    Unavailable response instead of processing the request
    """
    def __init__(self, app: FastAPI):
        """
        Initialize the ShutdownMiddleware

        Arguments:
        ----------
            app : The FastAPI application instance
        """
        super().__init__(app)
        self.is_shutting_down = False
        logger.info(msg = "ShutdownMiddleware initialized")

    async def dispatch(self, request, call_next):
        """
        Dispatch method to handle incoming requests

        This method checks if the server is shutting down. If it is, it returns a 503 response.
        Otherwise, it passes the request to the next middleware or route handler

        Arguments:
        ----------
            request : The incoming request object
            call_next : Callable to pass the request to the next middleware or route handler

        Returns:
        --------
            { PlainTextResponse } : A PlainTextResponse with a 503 status code if the server is shutting down,
                                    otherwise the response from the next middleware or route handler
        """
        if self.is_shutting_down:
            logger.warning(msg   = "Server is shutting down, returning 503 response", 
                           extra = {"request_id": str(request.state.request_id)})
            
            return PlainTextResponse("Server is shutting down", status_code=503)
        
        logger.debug(msg   = "Processing request", 
                     extra = {"request_id": str(request.state.request_id)})
        
        return await call_next(request)
