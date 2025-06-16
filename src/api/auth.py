from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.cores import auth
from src.cores.config import settings
from src.cores.dependencies import get_db
from src.models.users import User
from src.schemas.active_access_tokens import ActiveAccessTokenCreate
from src.schemas.response import StandardResponse, TokenResponse
from src.schemas.session import SessionCreate
from src.schemas.token_log import TokenLogCreate
from src.schemas.users import UserCreate, UserRead
from src.services.active_access_token_service import ActiveAccessTokenService
from src.services.auth_service import AuthService
from src.services.blacklist_token_service import BlacklistTokenService
from src.services.session_service import SessionService
from src.services.token_log_service import TokenLogService

router = APIRouter()


@router.post("/register", response_model=StandardResponse[UserRead])
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra username và email đã tồn tại chưa
    auth_service = AuthService(db)
    new_user = auth_service.register_user(user)
    return {"status_code": 200, "message": "Success", "data": new_user}


@router.post("/login", response_model=StandardResponse[TokenResponse])
def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user_current: Optional[User] = (
        db.query(User).filter(User.username == form_data.username).first()
    )
    if not user_current or not auth.verify_password(
        form_data.password, user_current.password
    ):
        if user_current:
            safe_log_token_action(db, user_current, "login failed", request)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user_current.is_active:
        raise HTTPException(status_code=401, detail="User blocked")

    # Tạo access token và refresh token
    access_token = auth.create_access_token(
        username=str(user_current.username), role=user_current.role
    )
    generated_refresh_token = auth.create_refresh_token(
        username=str(user_current.username), role=user_current.role
    )

    # Lưu access token vào DB
    save_access_token(db, access_token, user_current.id)

    # Set refresh token trong cookie HttpOnly
    response.set_cookie(
        key="refresh_token",
        value=generated_refresh_token,
        httponly=True,
        secure=True,  # chỉ dùng HTTPS
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    safe_log_token_action(db, user_current, "login", request)
    log_session(db, generated_refresh_token, request, user_current)

    return {
        "status_code": 200,
        "message": "Success",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "id": user_current.id,
            "username": user_current.username,
            "role": user_current.role,
        },
    }


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
def refresh_token(request: Request, db: Session = Depends(get_db)):
    generated_refresh_token = request.cookies.get("refresh_token")
    if not generated_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    username = decode_refresh_token_or_raise(generated_refresh_token)
    print(username)

    user: Optional[User] = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        print(user)

        raise HTTPException(status_code=401, detail="User not found or blocked")

    validate_refresh_session_or_raise(db, generated_refresh_token)

    # Xoá refresh token cũ khỏi session
    new_access_token = auth.create_access_token(
        username=str(user.username), role=user.role
    )
    save_access_token(db, new_access_token, user.id)
    safe_log_token_action(db, user, "refresh", request)
    # Trả token mới (client dùng để gọi API)
    return {
        "status_code": 200,
        "message": "Success",
        "data": {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
    }


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    generated_refresh_token = request.cookies.get("refresh_token")
    if not generated_refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token missing")

    session_service = SessionService(db)
    token_service = ActiveAccessTokenService(db)
    success = session_service.revoke_session(generated_refresh_token)

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
        blacklist_service = BlacklistTokenService(db)
        blacklist_service.blacklist_token(access_token)
        token_service.delete_token(access_token)
    response.delete_cookie("refresh_token")

    if not success:
        raise HTTPException(status_code=400, detail="Session not found")

    return {"status_code": 200, "message": "Logged out successfully"}


@router.post("/logout-all")
def logout_all(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    user = request.state.user

    session_service = SessionService(db)
    session_service.revoke_all_sessions(user.id)

    token_service = ActiveAccessTokenService(db)
    blacklist_service = BlacklistTokenService(db)

    active_tokens = token_service.get_tokens_by_user_id(user.id)
    print(active_tokens)
    for token in active_tokens:
        blacklist_service.blacklist_token(token.access_token)

    token_service.delete_tokens_by_user_id(user.id)

    response.delete_cookie("refresh_token")
    return {"status_code": 200, "message": "Logged out from all sessions"}


# --- Helper functions ---
def safe_log_token_action(db: Session, user: User, action: str, request: Request):
    """Ghi log hành động token, tránh lỗi gây crash."""
    try:
        log_token_action(db, user, action, request)
    except Exception as e:
        print(e)


def log_token_action(db: Session, user: User, action: str, request: Request):
    log_service = TokenLogService(db)
    ip = request.client.host
    agent = request.headers.get("user-agent")

    log_data = TokenLogCreate(
        user_id=user.id,
        username=user.username,
        ip_address=ip,
        user_agent=agent,
        action=action,
    )
    log_service.log_token_request(log_data)

    if log_service.is_suspicious(user.id, ip, agent, action):
        suspicious_log = TokenLogCreate(
            **{**log_data.model_dump(), "action": f"suspicious {action}"}
        )
        log_service.log_token_request(suspicious_log)


def log_session(
    db: Session, generated_refresh_token: str, request: Request, user: User
):
    session_service = SessionService(db)
    session_data = SessionCreate(
        user_id=user.id,
        refresh_token=generated_refresh_token,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    try:
        session_service.create_session(session_data)
    except Exception:
        raise HTTPException(status_code=401, detail="Session creation failed")


def decode_refresh_token_or_raise(token: str) -> str:
    """Giải mã refresh token và trả về username hoặc raise lỗi."""
    try:
        payload = auth.decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


def validate_refresh_session_or_raise(db: Session, generated_refresh_token: str):
    session_service = SessionService(db)
    if not session_service.validate_refresh_session(generated_refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")


def save_access_token(db: Session, access_token: str, user_id: str):
    token_service = ActiveAccessTokenService(db)
    token_create = ActiveAccessTokenCreate(
        user_id=user_id,
        access_token=access_token,
    )
    token_service.create_token(token_create)
