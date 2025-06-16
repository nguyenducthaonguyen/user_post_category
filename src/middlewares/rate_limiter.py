from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.cores.dependencies import get_db
from src.repositories.rate_limiter_repository import RateLimiterRepository
from src.services.rate_limiter_service import RateLimiterService


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, period_seconds: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.period_seconds = period_seconds

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header.split(" ")[1]
        db = next(get_db())

        try:
            limiter = RateLimiterService(db)

            if limiter.is_rate_limited(token, self.max_requests, self.period_seconds):
                limiter.blacklist_token(token)
                return JSONResponse(
                    content={
                        "message": "Too many requests, token has been blacklisted."
                    },
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            return await call_next(request)

        except Exception as e:
            # Log và trả lỗi rõ ràng thay vì để 500 propagate
            return JSONResponse(
                content={"detail": f"Internal middleware error: {str(e)}"},
                status_code=500,
            )
        finally:
            db.close()
