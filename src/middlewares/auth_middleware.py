from http import HTTPStatus

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import Request, HTTPException
from src.cores.dependencies import get_db
from src.services.blacklist_token_service import BlacklistTokenService
from src.cores.utils import validate_token_and_get_user
from datetime import datetime

EXCLUDE_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh"
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDE_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._unauthorized_response(
                "Missing or invalid Authorization header",
                request.url.path
            )

        token = auth_header.split(" ")[1]
        db_generator = get_db()
        db = next(db_generator)

        try:
            blacklist_service = BlacklistTokenService(db)
            if blacklist_service.is_token_blacklisted(token):
                return self._unauthorized_response("Token has been revoked", request.url.path)

            user = validate_token_and_get_user(token, db)
            request.state.user = user  # gán full user object nếu cần

        except HTTPException as e:
            return self._error_response(e.status_code, e.detail, request.url.path)
        except Exception:
            return self._error_response(500, "Internal Server Error", request.url.path)
        finally:
            try:
                db_generator.close()  # đảm bảo không rò rỉ session
            except Exception:
                pass

        return await call_next(request)

    def _error_response(self, status_code: int, message: str, path: str):
        return JSONResponse(
            status_code=status_code,
            content={
                "status_code": status_code,
                "error": HTTPStatus(status_code).phrase,
                "message": message,
                "path": path,
                "timestamp": datetime.now().isoformat()
            },
        )

    def _unauthorized_response(self, message: str, path: str):
        return self._error_response(401, message, path)
