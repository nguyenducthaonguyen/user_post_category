import pytest

from src.models.enums import GenderEnum
from src.schemas.users import UserCreate
from src.services.auth_service import AuthService
from tests.conftest import get_test_db
from tests.test_services.test_active_access_token_service import sample_users


@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()


@pytest.fixture
def auth_service(db_session):
    return AuthService(db=db_session)


def test_should_return_user_when_data_valid(auth_service):
    user_data = UserCreate(
        username="newuser",
        email="Nguyen@gmail.com",
        password="password123",
        fullname="Nguyen Van A",
        gender=GenderEnum.male,
    )
    created_user = auth_service.register_user(user_data)
    assert created_user.username == "newuser"
    assert created_user.email == "Nguyen@gmail.com"
    assert created_user.fullname == "Nguyen Van A"


def test_should_raise_400_when_register_user_username_already(auth_service):
    user_data = UserCreate(
        username="newuser",
        email="Nguyen1@gmail.com",
        password="password123",
        fullname="Nguyen Van A",
        gender=GenderEnum.male,
    )
    with pytest.raises(Exception) as exc_info:
        auth_service.register_user(user_data)
    assert "Username already exists" in str(exc_info.value)


def test_should_raise_400_when_register_user_email_already(auth_service):
    user_data = UserCreate(
        username="newuser1",
        email="Nguyen@gmail.com",
        password="password123",
        fullname="Nguyen Van A",
        gender=GenderEnum.male,
    )
    with pytest.raises(Exception) as exc_info:
        auth_service.register_user(user_data)
    assert "Email already exists" in str(exc_info.value)
