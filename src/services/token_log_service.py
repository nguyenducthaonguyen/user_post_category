from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.cores.config import settings
from src.repositories.token_log_repository import TokenLogRepository
from src.schemas.token_log import TokenLogCreate


class TokenLogService:
    def __init__(self, db: Session):
        self.repo = TokenLogRepository(db)

    def log_token_request(self, log_create: TokenLogCreate):
        return self.repo.create(log_create)

    def get_paginated(self, skip: int = 0, limit: int = 200):
        return self.repo.get_paginated(skip, limit)

    def is_suspicious(
        self, user_id: str, current_ip: str, current_agent: str, action: str
    ) -> bool:
        """
        Kiểm tra nếu hành động hiện tại có dấu hiệu bất thường.

        Args:
            user_id (str): ID của user.
            current_ip (str): Địa chỉ IP hiện tại.
            current_agent (str): User agent hiện tại.
            action (str): Hành động ('login', 'refresh', ...).

        Returns:
            bool: True nếu phát hiện nghi vấn, False nếu không.
        """
        last_log = self.repo.get_last_log(user_id, action)
        if not last_log:
            return False

        ip_changed = last_log.ip_address != current_ip
        agent_changed = last_log.user_agent != current_agent

        # Đảm bảo last_log.timestamp là timezone-aware
        last_timestamp = (
            last_log.timestamp
            if last_log.timestamp.tzinfo
            else last_log.timestamp.replace(tzinfo=timezone.utc)
        )
        time_diff = datetime.now(timezone.utc) - last_timestamp

        if action == "login":
            return self._is_login_suspicious(ip_changed, agent_changed, time_diff)
        elif action == "refresh":
            return self._is_refresh_suspicious(time_diff)
        return False

    @staticmethod
    def _is_login_suspicious(
        ip_changed: bool, agent_changed: bool, time_diff: timedelta
    ) -> bool:
        if (
            ip_changed or agent_changed
        ) and time_diff.total_seconds() < settings.SUSPICIOUS_LOGIN_TIME_WINDOW:
            return True
        return False

    @staticmethod
    def _is_refresh_suspicious(time_diff: timedelta) -> bool:
        return time_diff.total_seconds() < settings.SUSPICIOUS_REFRESH_TIME_WINDOW
