import pytest

from src.services.blacklist_token_service import BlacklistTokenService
from tests.conftest import get_test_db


@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()


@pytest.fixture
def blacklist_token_service(db_session):
    return BlacklistTokenService(db=db_session)


def test_should_return_blacklisted_token_when_created(blacklist_token_service):
    token = "test_token"
    response = blacklist_token_service.blacklist_token(token)
    assert response.token == token


def test_should_return_true_when_token_is_blacklisted(blacklist_token_service):
    is_blacklisted = blacklist_token_service.is_token_blacklisted("test_token")
    assert is_blacklisted is True


def test_should_return_false_when_token_is_not_blacklisted(blacklist_token_service):
    is_blacklisted = blacklist_token_service.is_token_blacklisted("non_existent_token")
    assert is_blacklisted is False


def test_should_return_quantity_delete_when_cleanup_expired_tokens(
    blacklist_token_service,
):
    # Giả sử có 3 token đã hết hạn
    expire_minutes = 10
    response = blacklist_token_service.cleanup_expired_tokens(expire_minutes)
    assert isinstance(response, int)  # Kiểm tra xem response là số lượng token đã xóa
    assert response >= 0  # Số lượng xóa không thể âm
