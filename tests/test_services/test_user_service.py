import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.cores import auth
from src.models.users import GenderEnum, RoleEnum, User
from src.schemas.users import PasswordChangeRequest, UserUpdateRequest
from src.services.user_service import UserService


# 1. Fixture trả về danh sách user (list)
@pytest.fixture
def mock_users():
    return [
        User(
            id="user-id-1",
            username="testuser1",
            email="user1@example.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 1",
            role=RoleEnum.user,
            is_active=True,
            gender=GenderEnum.male,
        ),
        User(
            id="user-id-2",
            username="testuser2",
            email="user2@example.com",
            password="hashed-password-2",
            fullname="Test User 2",
            role=RoleEnum.admin,
            is_active=False,
            gender=GenderEnum.female,
        ),
        User(
            id="user-id-3",
            username="testuser3",
            email="user3@example.com",
            password="hashed-password-2",
            fullname="Test User 2",
            role=RoleEnum.admin,
            is_active=True,
            gender=GenderEnum.female,
        ),
    ]


# 2. Mock repo, get_by_id/get_user_by_email dùng side_effect để tra cứu theo id/email
@pytest.fixture
def mock_repo(mock_users):
    repo = MagicMock()

    def fake_get(user_id):
        for user in mock_users:
            if user.id == user_id:
                return user
        return None

    def fake_get_user_by_email(email):
        for user in mock_users:
            if user.email == email:
                return user
        return None

    repo.get.side_effect = fake_get
    repo.get_user_by_email.side_effect = fake_get_user_by_email
    repo.get_all.return_value = mock_users
    repo.count_users.return_value = len(mock_users)
    return repo


@pytest.fixture
def user_service(mock_repo):
    with patch("src.services.user_service.UserRepository", return_value=mock_repo):
        yield UserService(db=MagicMock())


# 3. Test: User tồn tại và active
def test_should_return_user_when_user_exists_and_is_active(user_service, mock_users):
    user = user_service.get_user_by_id(mock_users[0].id)
    assert user == mock_users[0]
    assert user.is_active is True


# 4. Test: User không tồn tại (theo id)
def test_should_return_404_when_user_not_found(user_service):
    with pytest.raises(HTTPException) as exc_info:
        user_service.get_user_by_id("not-exist-id")
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


# 5. Test: User bị block (is_active=False)
def test_should_return_403_when_user_is_blocked(user_service, mock_users):
    blocked_user = mock_users[1]  # user-id-2
    with pytest.raises(HTTPException) as exc_info:
        user_service.get_user_by_id(blocked_user.id)
    assert exc_info.value.status_code == 403
    assert "User blocked" in str(exc_info.value.detail)


# 6. Test: Không tìm thấy user theo email
def test_should_return_404_when_email_not_found(user_service):
    with pytest.raises(HTTPException) as exc_info:
        user_service.get_user_by_email("notfound@example.com")
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


# 7. Test: Tìm thấy user theo email
def test_should_return_user_when_email_exists(user_service, mock_users):
    user = user_service.get_user_by_email("user1@example.com")
    assert user == mock_users[0]
    user = user_service.get_user_by_email("user2@example.com")
    assert user == mock_users[1]


# 8. Test: get_all trả về đúng list user
def test_should_return_all_users_when_all_success(user_service, mock_users):
    response = user_service.get_all(page=1, limit=10, is_active=None)
    assert response.status_code == 200
    data = json.loads(response.body.decode())
    assert len(data["data"]) == len(mock_users)
    emails = [user["email"] for user in data["data"]]
    for user in mock_users:
        assert user.email in emails


def test_should_return_200_when_update_user_with_valid_data(
    user_service, mocker, mock_users
):
    user = mock_users[0]

    updated_data = UserUpdateRequest(
        email="new_email@example.com",  # type: ignore
        fullname="New Name",
        gender=user.gender,
    )

    # Mock get trả về user cần update
    mocker.patch.object(user_service.repo, "get", return_value=user)
    # Mock get_user_by_email trả về None (email chưa ai dùng)
    mocker.patch.object(user_service.repo, "get_user_by_email", return_value=None)
    # Mock update_user
    mocker.patch.object(user_service.repo, "update_user", return_value=None)

    response = user_service.update_user(user.id, updated_data)
    assert response.email == "new_email@example.com"


def test_should_raise_400_when_email_already_registered(
    user_service, mocker, mock_users
):
    user = mock_users[0]

    updated_data = UserUpdateRequest(
        email="user2@example.com",  # type: ignore
        fullname="New Name",
        gender=user.gender,
    )

    mocker.patch.object(user_service.repo, "get", return_value=user)
    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user(user.id, updated_data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"


def test_should_raise_422_when_missing_email_field(mock_users):
    user = mock_users[0]
    with pytest.raises(ValidationError):
        UserUpdateRequest(fullname="New Name", gender=user.gender)  # type: ignore


def test_should_return_200_when_change_password_valid_data(
    user_service, mocker, mock_users
):
    user = mock_users[0]
    data_change_password = PasswordChangeRequest(
        password_old="11223344",
        password="1122334455",
        password_confirmation="1122334455",
    )
    # Patch repo.get trả về user
    mocker.patch.object(user_service.repo, "get", return_value=user)
    # Patch verify_password trả về True
    mocker.patch(
        "src.cores.auth.verify_password",
        return_value=auth.verify_password(
            data_change_password.password_old, user.password
        ),
    )
    # Patch get_password_hash trả về giá trị hash giả
    mocker.patch("src.cores.auth.get_password_hash", return_value="hashed_new_password")
    # Patch update_password (không quan tâm giá trị trả về)
    mocker.patch.object(user_service.repo, "update_user_password", return_value=user)

    response = user_service.update_user_password(user.id, data_change_password)
    assert response.status_code == 200
    assert "Change password successfully" in response.body.decode()


def test_should_return_400_when_change_password_password_old_fail(
    user_service, mocker, mock_users
):
    user = mock_users[0]
    data_change_password = PasswordChangeRequest(
        password_old="1122334455",
        password="1122334455",
        password_confirmation="1122334455",
    )
    # Patch repo.get trả về user
    mocker.patch.object(user_service.repo, "get", return_value=user)
    # Patch verify_password trả về False để mô phỏng pass cũ sai
    mocker.patch(
        "src.cores.auth.verify_password",
        return_value=auth.verify_password(
            data_change_password.password_old, user.password
        ),
    )
    # Patch get_password_hash (không cần dùng ở đây)
    mocker.patch("src.cores.auth.get_password_hash", return_value="hashed_new_password")
    # Patch update_password (không quan tâm giá trị trả về)
    mocker.patch.object(user_service.repo, "update_user_password", return_value=user)

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user_password(user.id, data_change_password)
    assert exc_info.value.status_code == 400
    assert "Old password is incorrect" in str(exc_info.value.detail)


def test_should_return_400_when_change_password_password_confirmation_not_match(
    user_service, mocker, mock_users
):
    user = mock_users[0]
    data_change_password = PasswordChangeRequest(
        password_old="11223344",
        password="1122334455",
        password_confirmation="11223344556",
    )
    # Patch repo.get trả về user
    mocker.patch.object(user_service.repo, "get", return_value=user)
    # Patch verify_password trả về False để mô phỏng pass cũ sai
    mocker.patch(
        "src.cores.auth.verify_password",
        return_value=auth.verify_password(
            data_change_password.password_old, user.password
        ),
    )
    # Patch get_password_hash (không cần dùng ở đây)

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user_password(user.id, data_change_password)
    assert exc_info.value.status_code == 422
    assert "Password confirmation does not match" in str(exc_info.value.detail)


def test_should_return_200_when_block_user_is_active_true(
    user_service, mocker, mock_users
):
    user = mock_users[0]  # user này đang active

    # Patch repo.get trả về user đang active
    mocker.patch.object(user_service.repo, "get", return_value=user)

    # Patch phương thức block_user để giả lập hành động block user
    def fake_block_user(u):
        u.is_active = False  # giả lập bị block

    mocker.patch.object(user_service.repo, "block_user", side_effect=fake_block_user)

    response = user_service.block_user_for_admin(user.id)
    assert response == user
    assert response.is_active is False


def test_should_return_400_when_block_user_is_active_false(user_service, mock_users):
    user = mock_users[1]
    with pytest.raises(HTTPException) as exc_info:
        user_service.block_user_for_admin(user.id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User was already blocked"


def test_should_return_200_when_unblock_user_is_active_false(
    user_service, mocker, mock_users
):
    user = mock_users[1]  # đang bị block

    mocker.patch.object(user_service.repo, "get", return_value=user)

    def fake_unblock_user(u):
        u.is_active = True

    mocker.patch.object(
        user_service.repo, "unblock_user", side_effect=fake_unblock_user
    )

    response = user_service.unblock_user_for_admin(user.id)

    # response, user và mock_users[1] đều là cùng 1 object, nên is_active đã thành True
    assert response.is_active is True
    assert user.is_active is True
    assert mock_users[1].is_active is True


def test_should_return_400_when_unblock_user_is_active_true(user_service, mock_users):
    user = mock_users[0]
    with pytest.raises(HTTPException) as exc_info:
        user_service.unblock_user_for_admin(user.id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User was already unblocked"


def test_should_return_200_when_get_all_for_admin(user_service, mocker, mock_users):
    # Patch số lượng user và danh sách user
    mocker.patch.object(user_service.repo, "count_users", return_value=len(mock_users))
    mocker.patch.object(user_service.repo, "list_users", return_value=mock_users)

    response = user_service.get_all_for_admin(page=1, limit=10, is_active=None)
    assert response["status_code"] == 200
    assert response["pagination"]["total"] == len(mock_users)

    # Kiểm tra dữ liệu trả về là list
    assert isinstance(response["data"], list)
    assert len(response["data"]) == len(mock_users)

    # Check từng user trả về có field is_active
    for user in response["data"]:
        assert user["is_active"] is not None


def test_should_raise_404_when_user_unblock_for_admin_not_found(
    user_service, mocker, mock_users
):
    mocker.patch.object(user_service.repo, "get_all", return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        user_service.unblock_user_for_admin("not-exist-id")
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


def test_should_raise_404_when_delete_user_not_found(user_service, mocker, mock_users):
    mocker.patch.object(user_service.repo, "get", return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        user_service.delete_user("not-exist-id")
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


def test_should_return_200_when_delete_user_success(user_service, mocker, mock_users):
    user = mock_users[0]
    mocker.patch.object(user_service.repo, "get", return_value=user)
    mocker.patch.object(user_service.repo, "delete_user", return_value=None)

    response = user_service.delete_user(user.id)
    assert response.id == user.id
    assert response.username == user.username


def test_should_raise_500_when_delete_user_fails(user_service, mocker, mock_users):
    user = mock_users[0]
    mocker.patch.object(user_service, "get_user_by_id_for_admin", return_value=user)
    mocker.patch.object(
        user_service.repo,
        "delete_user_and_posts",
        side_effect=Exception("Database error"),
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.delete_user(user.id)
    assert exc_info.value.status_code == 500
    assert "An error occurred while deleting the user" in str(exc_info.value.detail)


def test_should_return_500_when_get_all_user_fails(user_service, mocker):
    mocker.patch.object(
        user_service.repo, "get_all", side_effect=Exception("Database error")
    )
    mocker.patch.object(
        user_service.repo, "count_users", side_effect=Exception("Database error")
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.get_all(page=1, limit=10, is_active=True)
    assert exc_info.value.status_code == 500
    assert "An error occurred while retrieving users: Database error" in str(
        exc_info.value.detail
    )


def test_should_return_user_when_block_user_for_user(user_service, mocker, mock_users):
    user = mock_users[0]  # user đang active

    # Patch repo.get trả về user đang active
    mocker.patch.object(user_service.repo, "get", return_value=user)

    # Patch phương thức block_user để giả lập hành động block user
    def fake_block_user(u):
        u.is_active = False  # giả lập bị block

    mocker.patch.object(user_service.repo, "block_user", side_effect=fake_block_user)

    response = user_service.block_user(user.id)
    assert response == user
    assert response.is_active is False


def test_should_raise_400_when_update_user_for_email_already_registered(
    user_service, mock_users
):
    # user hiện tại
    user = mock_users[0]
    user.id = "1"
    user.email = "Nguyen2@gmail.com"

    # user khác đã dùng email muốn update
    other_user = mock_users[1]
    other_user.id = "2"
    other_user.email = "Nguyen@gmail.com"

    # Dữ liệu update: email đã có người dùng khác
    updated_data = UserUpdateRequest(
        email="Nguyen@gmail.com",  # type: ignore
        fullname="New Name",
        gender="male",  # type: ignore
    )
    updated_data2 = UserUpdateRequest(
        email="Nguyen2@gmail.com",  # type: ignore
        fullname="New Name",
        gender="male",  # type: ignore
    )

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user(user.id, updated_data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email already registered"

    # Kiểm tra nếu email không trùng với user khác thì không raise lỗi
    response = user_service.update_user(user.id, updated_data2)
    assert response.email == user.email
