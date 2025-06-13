import pytest
from fastapi import HTTPException

from src.models import Category
from src.schemas.categories import CategoryCreate, CategoryUpdate
from src.services.category_service import CategoryService
from tests.conftest import get_test_db

@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()

@pytest.fixture
def sample_categories(db_session):
    categories = [
        Category(id="1", name="Category 1"),
        Category(id="2", name="Category 2"),
    ]
    db_session.add_all(categories)
    db_session.commit()
    return categories

@pytest.fixture
def category_service(db_session):
    return CategoryService(db=db_session)

def test_should_return_category_when_exists_and_active(category_service, sample_categories):
    response = category_service.get_category_by_id("1")
    assert response.id == "1"
    assert response.name == "Category 1"


def test_should_return_404_when_category_not_found(category_service):
    with pytest.raises(HTTPException) as exc_info:
        category_service.get_category_by_id("999")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"


def test_should_return_all_categories(category_service):
    response = category_service.get_all_categories()
    assert len(response) == 2
    assert response[0].name == "Category 1"


def test_should_create_category_successfully_when_valid_data_input(category_service):
    category_data = CategoryCreate(name="New Category")
    response = category_service.create_category(category_data)
    assert response.name == "New Category"


def test_should_raise_error_400_when_category_name_already_exists(category_service):
    category_data = CategoryCreate(name="Category 1")
    with pytest.raises(HTTPException) as exc_info:
        category_service.create_category(category_data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Failed to create category: 400: Category name already exists"


def test_should_update_category_successfully_when_valid_data_input(category_service):
    category_data = CategoryUpdate(name="Updated Category")
    response = category_service.update_category("1", category_data)
    assert response.name == "Updated Category"


def test_should_raise_error_404_when_updating_non_existent_category(category_service):
    category_data = CategoryUpdate(name="Updated Category")
    with pytest.raises(HTTPException) as exc_info:
        category_service.update_category("999", category_data)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"


def test_should_raise_error_400_when_updating_category_with_existing_name(category_service):
    category_data = CategoryUpdate(name="Category 2")
    with pytest.raises(HTTPException) as exc_info:
        category_service.update_category("1", category_data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Category name already exists"


def test_should_delete_category_successfully_when_exists(category_service):
    response = category_service.delete_category("1")
    assert response.id == "1"
    assert response.name == "Updated Category"


def test_should_raise_error_404_when_deleting_non_existent_category(category_service):
    with pytest.raises(HTTPException) as exc_info:
        category_service.delete_category("999")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"


def test_should_raise_400_when_db_update_error(category_service, mocker):
    category_id = "1"
    category_data = CategoryUpdate(name="Unique Category")

    # Patch get để trả về 1 mock category, đảm bảo không dính lỗi 404
    mock_category = mocker.Mock()
    mocker.patch.object(category_service.repo, "get", return_value=mock_category)
    # Patch update để raise Exception như cũ
    mocker.patch.object(category_service.repo, "update", side_effect=Exception("Database error"))

    with pytest.raises(HTTPException) as exc_info:
        category_service.update_category(category_id, category_data)

    assert exc_info.value.status_code == 400
    assert "Failed to update category: Database error" in exc_info.value.detail



def test_should_raise_error_400_when_db_error_occurs(category_service, mocker):
    # Patch phương thức get_all của repo trên category_service
    mocker.patch.object(category_service.repo, "get_all", side_effect=Exception("Database error"))

    with pytest.raises(HTTPException) as exc_info:
        category_service.get_all_categories()
    assert exc_info.value.status_code == 400
    assert "Failed to retrieve categories: Database error" in exc_info.value.detail


def test_should_raise_400_when_db_delete_error(category_service, mocker):
    category_id = "1"

    # Patch get để trả về 1 mock category, đảm bảo không dính lỗi 404
    mock_category = mocker.Mock()
    mocker.patch.object(category_service.repo, "get", return_value=mock_category)
    # Patch update để raise Exception như cũ
    mocker.patch.object(category_service.repo, "delete", side_effect=Exception("Database error"))

    with pytest.raises(HTTPException) as exc_info:
        category_service.delete_category(category_id)

    assert exc_info.value.status_code == 400
    assert "Failed to delete category: Database error" in exc_info.value.detail





