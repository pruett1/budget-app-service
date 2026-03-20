from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

import uuid

from dataclasses import dataclass
from typing import Optional
from contextvars import ContextVar

@dataclass
class RequestContext:
    request_id: str
    user_id: Optional[str] = None

request_ctx: ContextVar[RequestContext] = ContextVar("request_ctx")

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = request.app.state.logger
        session_manager = request.app.state.sessionManager

        request_id = request.headers.get('request-id')
        user_id = None
        if not request_id:
            logger.debug("Request missing valid request-id header", path=request.url.path, method=request.method)
            return JSONResponse(status_code=400, content={"error": "Missing request-id header"})
        
        try:
            uuid.UUID(request_id, version=4)
        except ValueError:
            logger.debug("Request has invalid request-id header (not valid UUIDv4)", path=request.url.path, method=request.method)
            return JSONResponse(status_code=400, content={"error": "Invalid request-id header (must be UUIDv4)"})

        auth = request.headers.get('Authorization')
        
        if auth:
            try:
                scheme, token = auth.split(' ')
                if scheme.lower() != 'bearer':
                    logger.debug("Authorization header has invalid scheme", path=request.url.path, method=request.method)
                    return JSONResponse(status_code=400, content={"error": "Invalid Authorization header scheme (must be Bearer)"})
                user_id = session_manager.validate(token)
            except Exception as e:
                logger.debug("Failed to validate token", path=request.url.path, method=request.method)
                return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

        request_ctx.set(RequestContext(request_id=request_id, user_id=user_id))
        logger.debug("Request context set", path=request.url.path, method=request.method)

        response = await call_next(request)
        response.headers["request-id"] = request_id # echo back request id
        return response
