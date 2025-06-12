import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from src.api import api_router
from src.cores.config import settings
from src.cores.dependencies import get_db
from src.cores.exceptions import APIException
from src.middlewares.access_log import AccessLogMiddleware
from src.middlewares.auth_middleware import AuthMiddleware
from src.middlewares.rate_limiter import RateLimiterMiddleware
from src.models import *
from src.cores.database import engine, Base
from src.services.active_access_token_service import ActiveAccessTokenService
from src.services.blacklist_token_service import BlacklistTokenService
from src.services.rate_limiter_service import RateLimiterService


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def cleanup_job():
        while True:
            db_gen = get_db()
            db = next(db_gen)
            try:
                blacklist_service = BlacklistTokenService(db)
                token_service = ActiveAccessTokenService(db)
                token_usage_log = RateLimiterService(db)
                blacklist_service.cleanup_expired_tokens(expire_minutes=settings.BLACKLIST_TOKEN_EXPIRE_MINUTES)
                token_service.cleanup_expired_tokens()
                token_usage_log.cleanup_expired_tokens(expire_minutes=settings.TOKEN_USAGE_LOG_EXPIRE_MINUTES)
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass  # Generator đã hoàn tất

            await asyncio.sleep(600)

    asyncio.create_task(cleanup_job())
    yield  # Đây là phần bắt buộc để FastAPI chạy đúng lifecycle


# Khởi tạo app
app = FastAPI(title="FastAPI Security 5", lifespan=lifespan)

# Thêm middleware
app.add_middleware(AccessLogMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimiterMiddleware, max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    period_seconds=settings.RATE_LIMIT_PERIOD_SECONDS)

# Đăng ký router
app.include_router(api_router, prefix="/api/v1")

# Tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body}),
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": exc.detail,
            "message": exc.detail
        }
    )

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": exc.error,
            "message": exc.detail,
        },
    )

