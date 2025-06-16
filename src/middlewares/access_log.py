from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
from src.cores.logger import get_logger

logger = get_logger("access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        client_host = request.client.host if request.client else "unknown"
        log_msg = (
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration_ms:.2f}ms "
            f"client={client_host}"
        )
        logger.info(log_msg)

        return response
