from datetime import datetime, timezone

import pytest

from src.models import User
from src.models.enums import RoleEnum, GenderEnum
from src.models.token_logs import TokenLog
from src.schemas.token_log import TokenLogCreate
from src.services.token_log_service import TokenLogService
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
            id="user11",
            username="testuser11",
            email="Nguyen11@gmail.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 11",
            role=RoleEnum.user,
            is_active=True,
            gender = GenderEnum.male
        ),
        User(
            id="user12",
            username="testuser12",
            email="Nguyen12@gmail.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 12",
            role=RoleEnum.user,
            is_active=True,
            gender = GenderEnum.male
        )
    ]
    db_session.add_all(users)
    db_session.commit()
    return users


@pytest.fixture
def sample_token_logs(db_session):
    token_logs = [
        TokenLog (id= i, user_id= "user11", username="testuser11", ip_address = "127.0.0.1",user_agent="PostmanRuntime/7.44.0", action = "login", timestamp=datetime.now(timezone.utc))
        for i in range(1, 6)
    ]
    token_logs += [
        TokenLog(id=i + 5, user_id="user12", username="testuser12", ip_address="127.0.0.1", user_agent="PostmanRuntime/7.44.0", action="refresh", timestamp=datetime.now(timezone.utc))
        for i in range(1, 6)  # 5 entries for "user2"
    ]
    token_logs += [
        TokenLog(id=i + 10, user_id="user11", username="testuser11", ip_address="127.0.2", user_agent="PostmanRun/7.44.0", action="acb", timestamp=datetime.now(timezone.utc))
        for i in range(1, 6)  # 5 entries for "user1" with suspicious IP
    ]
    db_session.add_all(token_logs)
    db_session.commit()
    return token_logs



@pytest.fixture
def token_log_service(db_session):
    return TokenLogService(db=db_session)


def test_should_return_token_log_when_created_successfully(token_log_service, sample_users, sample_token_logs):
    token_log = TokenLogCreate(
        user_id="user11",
        username="testuser11",
        ip_address="127.0.0.1",
        user_agent="PostmanRuntime/7.44.0",
        action="login"
    )
    response = token_log_service.log_token_request(token_log)
    assert response.user_id == "user11"
    assert response.username == "testuser11"
    assert response.ip_address == "127.0.0.1"
    assert response.user_agent == "PostmanRuntime/7.44.0"
    assert response.action == "login"

def test_should_return_list_token_when_paginated_token_logs(token_log_service):
    response = token_log_service.get_paginated(skip=0, limit=5)
    assert len(response) == 5
    assert all(isinstance(log, TokenLog) for log in response)

def test_should_return_true_when_is_suspicious(token_log_service):
    token_log = TokenLogCreate(
        user_id="user11",
        username="testuser11",
        ip_address="127.0.2",
        user_agent="PostmanRun/7.44.0",
        action="login"
    )
    token_log_service.log_token_request(token_log)
    response = token_log_service.is_suspicious(
        user_id=token_log.user_id,
        current_ip=token_log.ip_address,
        current_agent=token_log.user_agent,
        action=token_log.action
    )
    assert response is True  # Assuming the previous log was suspicious enough to trigger this


def test_should_return_false_when_not_suspicious(token_log_service):
    token_log = TokenLogCreate(
        user_id="user12",
        username="testuser12",
        ip_address="127.0.0.1",
        user_agent="PostmanRuntime/7.44.0",
        action="login"
    )
    token_log_service.log_token_request(token_log)
    response = token_log_service.is_suspicious(
        user_id=token_log.user_id,
        current_ip=token_log.ip_address,
        current_agent=token_log.user_agent,
        action=token_log.action
    )
    assert response is False  # Assuming the previous log was not suspicious enough to trigger this

def test_should_return_true_when_is_suspicious_for_refresh(token_log_service):
    token_log = TokenLogCreate(
        user_id="user12",
        username="testuser12",
        ip_address="127.0.2",
        user_agent="PostmanRun/7.44.0",
        action="refresh"
    )
    token_log_service.log_token_request(token_log)
    response = token_log_service.is_suspicious(
        user_id=token_log.user_id,
        current_ip=token_log.ip_address,
        current_agent=token_log.user_agent,
        action=token_log.action
    )
    assert response is True  # Assuming the previous log was suspicious enough to trigger this

def test_should_return_false_when_not_suspicious_for_refresh(token_log_service):
    token_log = TokenLogCreate(
        user_id="user11",
        username="testuser11",
        ip_address="127.0.0.1",
        user_agent="PostmanRuntime/7.44.0",
        action="refresh"
    )
    response = token_log_service.is_suspicious(
        user_id=token_log.user_id,
        current_ip=token_log.ip_address,
        current_agent=token_log.user_agent,
        action=token_log.action
    )
    assert response is False  # Assuming the previous log was not suspicious enough to trigger this

def test_should_return_false_when_no_previous_log(token_log_service):
    token_log = TokenLogCreate(
        user_id="user11",
        username="testuser11",
        ip_address="127.0.0.1",
        user_agent="PostmanRuntime/7.44.0",
        action="abc"
    )

    token_log2 = TokenLogCreate(
        user_id="user11",
        username="testuser11",
        ip_address="127.0.0.1",
        user_agent="PostmanRuntime/7.44.0",
        action="abc"
    )
    token_log_service.log_token_request(token_log)
    token_log_service.log_token_request(token_log2)
    response = token_log_service.is_suspicious(
        user_id=token_log2.user_id,
        current_ip=token_log2.ip_address,
        current_agent=token_log2.user_agent,
        action=token_log2.action
    )
    assert response is False  # No previous log, so it should not be suspicious