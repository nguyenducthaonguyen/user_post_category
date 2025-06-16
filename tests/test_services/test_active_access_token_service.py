from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from src.models import User
from src.models.active_access_tokens import ActiveAccessToken
from src.models.enums import GenderEnum, RoleEnum
from src.schemas.active_access_tokens import ActiveAccessTokenCreate
from tests.conftest import get_test_db


@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()


@pytest.fixture
def sample_users(db_session):
    users = [
        User(
            id="user4",
            username="testuser4",
            email="user4@example.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 1",
            role=RoleEnum.user,
            is_active=True,
            gender=GenderEnum.male,
        ),
        User(
            id="user5",
            username="testuser5",
            email="user5@gmail.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 2",
            role=RoleEnum.user,
            is_active=True,
            gender=GenderEnum.female,
        ),
        User(
            id="user7",
            username="testuser7",
            email="user7@gmail.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 3",
            role=RoleEnum.user,
            is_active=False,
            gender=GenderEnum.female,
        ),
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


@pytest.fixture()
def sample_active_access_tokens(db_session):
    tokens = [
        ActiveAccessToken(
            id=1,
            user_id="user4",
            access_token="token1",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=30),  # Assuming this constant is defined in settings
        ),
        ActiveAccessToken(
            id=4,
            user_id="user4",
            access_token="token4",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            # Assuming this constant is defined in settings
        ),
        ActiveAccessToken(
            id=2,
            user_id="user5",
            access_token="token2",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        ),
        ActiveAccessToken(
            id=3,
            user_id="user7",
            access_token="token3",
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        ),
        ActiveAccessToken(
            id=5,
            user_id="user7",
            access_token="expired_token",
            created_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired token
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
    ]
    db_session.add_all(tokens)
    db_session.commit()
    return tokens


@pytest.fixture
def active_access_token_service(db_session):
    from src.services.active_access_token_service import ActiveAccessTokenService

    return ActiveAccessTokenService(db=db_session)


def test_should_create_active_access_token_when_data_valid(
    active_access_token_service, sample_users, sample_active_access_tokens
):

    token_data = ActiveAccessTokenCreate(user_id="user4", access_token="new_token")
    response = active_access_token_service.create_token(token_data)

    assert response.user_id == "user4"
    assert response.access_token == "new_token"


def test_should_get_active_access_tokens_when_get_by_user_id(
    active_access_token_service,
):
    response = active_access_token_service.get_tokens_by_user_id("user4")

    assert len(response) == 3
    assert response[0].user_id == "user4"
    assert response[0].access_token == "token1"
    assert response[1].access_token == "token4"
    assert response[2].access_token == "new_token"  # The newly created token


def test_should_return_true_when_delete_token_success(active_access_token_service):
    token_to_delete = "new_token"
    response = active_access_token_service.delete_token(token_to_delete)
    assert response is True


def test_should_raise_404_when_delete_token_not_found(active_access_token_service):
    token_to_delete = "non_existent_token"
    with pytest.raises(HTTPException) as exc_info:
        active_access_token_service.delete_token(token_to_delete)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Token not found"


def test_should_raise_400_when_delete_token_failed(active_access_token_service, mocker):
    # Mock the repository method to raise an exception
    mocker.patch.object(
        active_access_token_service.repo,
        "delete_token",
        side_effect=Exception("Deletion failed"),
    )
    token_to_delete = "invalid_token"
    with pytest.raises(HTTPException) as exc_info:
        active_access_token_service.delete_token(token_to_delete)
    assert exc_info.value.status_code == 400
    assert "Deletion failed: Deletion failed" in exc_info.value.detail


def test_should_return_true_when_delete_tokens_by_user_id_success(
    active_access_token_service,
):
    user_id = "user5"
    response = active_access_token_service.delete_tokens_by_user_id(user_id)
    assert response is True


def test_should_raise_404_when_delete_tokens_by_user_id_not_found(
    active_access_token_service,
):
    user_id = "non_existent_user"
    with pytest.raises(HTTPException) as exc_info:
        active_access_token_service.delete_tokens_by_user_id(user_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No tokens found for user"


def test_should_raise_400_when_delete_tokens_by_user_id_failed(
    active_access_token_service, mocker
):
    # Mock the repository method to raise an exception
    mocker.patch.object(
        active_access_token_service.repo,
        "delete_tokens_by_user_id",
        side_effect=Exception("Deletion failed"),
    )
    user_id = "invalid_user"
    with pytest.raises(HTTPException) as exc_info:
        active_access_token_service.delete_tokens_by_user_id(user_id)
    assert exc_info.value.status_code == 400
    assert "Deletion failed" in exc_info.value.detail


def test_should_cleanup_expired_tokens(active_access_token_service):
    # Before cleanup, there should be
    response_user7 = active_access_token_service.get_tokens_by_user_id("user7")
    assert len(response_user7) == 2  # user6 has 1 expired token
    response_user4 = active_access_token_service.get_tokens_by_user_id("user4")
    assert len(response_user4) == 2  # user4 has 3 tokens
    response_user5 = active_access_token_service.get_tokens_by_user_id("user5")
    assert len(response_user5) == 0  # user5 has 1 token

    response = active_access_token_service.cleanup_expired_tokens()
    assert response == 2  # Only one expired token should be cleaned up
