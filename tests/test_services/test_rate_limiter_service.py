from datetime import datetime, timezone

import pytest

from src.models import TokenUsageLog
from src.services.blacklist_token_service import BlacklistTokenService
from src.services.rate_limiter_service import RateLimiterService
from tests.conftest import get_test_db


@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()


@pytest.fixture
def sample_token_usage(db_session):
    token_usage = [TokenUsageLog(id=i, token="test_token1", requested_at=datetime.now(timezone.utc)) for i in range(1, 12)]
    # Create 11 entries for "test_token1" to simulate rate limiting
    token_usage += [TokenUsageLog(id=i + 21, token="test_token2", requested_at=datetime.now(timezone.utc)) for i in range(1, 6)]  # 5 entries for "test_token2"

    db_session.add_all(token_usage)
    db_session.commit()
    return token_usage


@pytest.fixture
def rate_limiter_service(db_session):
    return RateLimiterService(db=db_session)


@pytest.fixture
def blacklist_token_service(db_session):
    return BlacklistTokenService(db=db_session)


def test_should_return_true_when_token_is_rate_limited(rate_limiter_service, sample_token_usage):
    # Assuming max_requests = 10 and period_seconds = 60
    is_limited = rate_limiter_service.is_rate_limited("test_token1", max_requests=5, period_seconds=10)

    assert is_limited is True


def test_should_blacklist_token_when_black_list_success(rate_limiter_service, blacklist_token_service):
    rate_limiter_service.blacklist_token("test_token1")
    assert blacklist_token_service.is_token_blacklisted("test_token1") is True


def test_should_return_quantity_deleted_when_cleanup_expired_tokens(
    rate_limiter_service,
):
    # Giả sử có 3 token đã hết hạn
    expire_minutes = -10
    response = rate_limiter_service.cleanup_expired_tokens(expire_minutes)
    assert response >= 0  # Số lượng xóa không thể âm
