import json

import pytest
from fastapi import HTTPException

from src.models import Category, Post, User
from src.models.enums import RoleEnum, GenderEnum
from src.schemas.posts import PostCreate, PostUpdate
from src.services.post_service import PostService
from tests.conftest import get_test_db

@pytest.fixture
def db_session():
    session = next(get_test_db())
    yield session
    session.close()

@pytest.fixture
def sample_users(db_session):
    users = [
       User(id="user1",
            username="testuser1",
            email="user1@example.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 1",
            role = RoleEnum.user,
            is_active=True,
            gender=GenderEnum.male),
         User(id="user2",
            username="testuser2",
            email="user2@gmail.com",
            password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
            fullname="Test User 2",
            role = RoleEnum.user,
            is_active=True,
            gender=GenderEnum.female),
        User(id="user3",
             username="testuser3",
             email="user3@gmail.com",
             password="$2b$12$xykIGp6CG8KQI0MD2PGXjOuf4YzsNC91cle3ocNr9iEsVhCNtgcNu",
             fullname="Test User 3",
             role=RoleEnum.user,
             is_active=False,
             gender=GenderEnum.female)
    ]
    db_session.add_all(users)
    db_session.commit()
    return users

@pytest.fixture
def sample_categories(db_session):
    categories = [
        Category(id="3", name="Category 3"),
        Category(id="4", name="Category 4"),
    ]
    db_session.add_all(categories)
    db_session.commit()
    return categories

@pytest.fixture
def sample_posts(db_session, sample_categories):
    posts = [
        Post(id="1", title="Post 1", content="Content 1", user_id="user1"),
        Post(id="2", title="Post 2", content="Content 2", user_id="user2"),
        Post(id="3", title="Post 3", content="Content 3", user_id="user3")
    ]
    posts[0].categories.extend(sample_categories)
    posts[1].categories.append(sample_categories[1])
    posts[2].categories.append(sample_categories[0])
    db_session.add_all(posts)
    db_session.commit()
    return posts

@pytest.fixture
def post_service(db_session):
    return PostService(db=db_session)

def test_should_return_post_when_exists_and_active(post_service,sample_users,sample_categories, sample_posts):
    response = post_service.get_post_by_id("1")
    assert response.id == "1"
    assert response.title == "Post 1"
    assert response.user_id == "user1"
    assert set([c.name for c in response.categories]) == {"Category 3", "Category 4"}

def test_should_return_404_when_post_not_found(post_service):
    with pytest.raises(HTTPException) as exc_info:
        post_service.get_post_by_id("999")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Post not found"

def test_should_return_403_when_post_belongs_to_blocked_user(post_service):
    with pytest.raises(HTTPException) as exc_info:
        post_service.get_post_by_id("3")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User is blocked"

def test_should_return_404_when_user_not_found(post_service):
    with pytest.raises(HTTPException) as exc_info:
        post_service.get_posts_by_user_id("999")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_should_return_all_posts_by_user_id(post_service):
    response = post_service.get_posts_by_user_id("user1")
    assert len(response) == 1
    assert response[0].id == "1"
    assert response[0].title == "Post 1"

def test_should_return_post_when_created_successfully(post_service):
    post_data = PostCreate(
        title= "New Post",
        content= "This is a new post",
        category_ids= ["3", "4"]
    )
    response = post_service.create_post(post_data, user_id="user1")
    assert response.title == "New Post"
    assert response.content == "This is a new post"
    assert response.user_id == "user1"
    assert set([c.name for c in response.categories]) == {"Category 3", "Category 4"}

def test_should_raise_error_when_create_post_with_invalid_user(post_service):
    post_data = PostCreate(
        title= "New Post",
        content= "This is a new post",
        category_ids= ["3", "4"]
    )
    with pytest.raises(HTTPException) as exc_info:
        post_service.create_post(post_data, user_id="999")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"

def test_should_return_categories_empty_when_create_create_post_without_categories(post_service):
    post_data = PostCreate(
        title= "New Post Without Categories",
        content= "This is a new post without categories",
        category_ids= []
    )
    response = post_service.create_post(post_data, user_id="user1")
    assert response.title == "New Post Without Categories"
    assert response.content == "This is a new post without categories"
    assert response.user_id == "user1"
    assert len(response.categories) == 0


def test_should_raise_400_when_create_post_failed(post_service, mocker):
    post_data = PostCreate(
        title="Any",
        content="Any",
        category_ids=["3"]
    )
    # Giả lập post_repo.create raise Exception
    mocker.patch.object(post_service.post_repo, "create", side_effect=Exception("Mocked DB error"))

    with pytest.raises(HTTPException) as exc_info:
        post_service.create_post(post_data, user_id="user1")
    assert exc_info.value.status_code == 400
    assert "Create post failed:" in exc_info.value.detail
    assert "Mocked DB error" in exc_info.value.detail

def test_should_raise_400_when_get_posts_by_user_id_failed(post_service, mocker):
    # Giả lập post_repo.get_posts_by_user_id raise Exception
    mocker.patch.object(post_service.post_repo, "get_posts_by_user_id", side_effect=Exception("Mocked DB error"))

    with pytest.raises(HTTPException) as exc_info:
        post_service.get_posts_by_user_id("user1")
    assert exc_info.value.status_code == 400
    assert "Get posts by user failed:" in exc_info.value.detail
    assert "Mocked DB error" in exc_info.value.detail


def test_should_return_200_when_get_all_posts_success(post_service):
    response = post_service.get_all(page=1, limit=10)
    assert response.status_code == 200

    # Parse body
    content = json.loads(response.body.decode())
    assert len(content["data"]) == 5
    assert content["pagination"]["total"] == 5
    assert content["pagination"]["limit"] == 10
    assert content["pagination"]["offset"] == 0
    assert content["data"][0]["title"] == "Post 1"

def test_should_return_400_when_get_all_posts_failed(post_service, mocker):
    # Giả lập post_repo.count_posts raise Exception
    mocker.patch.object(post_service.post_repo, "count_posts", side_effect=Exception("Mocked DB error"))

    with pytest.raises(HTTPException) as exc_info:
        post_service.get_all(page=1, limit=10)
    assert exc_info.value.status_code == 400
    assert "Get posts failed: Mocked DB error" in exc_info.value.detail

def test_should_return_post_when_updated_successfully(post_service):

    post_data = PostUpdate(
        title="Updated Post",
        content="This is an updated post",
        category_ids=["3"]
    )
    response = post_service.update_post("1", post_data,user_id="user1")
    assert response.id == "1"
    assert response.title == "Updated Post"
    assert response.content == "This is an updated post"
    assert set([c.name for c in response.categories]) == {"Category 3"}

def test_should_raise_404_when_update_post_not_found(post_service):
    post_data = PostUpdate(
        title="Updated Post",
        content="This is an updated post",
        category_ids=["3"]
    )
    with pytest.raises(HTTPException) as exc_info:
        post_service.update_post("999", post_data, user_id="user1")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Post Not Found"

def test_should_raise_403_when_update_post_not_owner(post_service):
    post_data = PostUpdate(
        title="Updated Post",
        content="This is an updated post",
        category_ids=["3"]
    )
    with pytest.raises(HTTPException) as exc_info:
        post_service.update_post("1", post_data, user_id="user2")
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User Not The Post Owner"

def test_should_return_categories_empty_when_update_post_without_categories(post_service):
    post_data = PostUpdate(
        title="Updated Post Without Categories",
        content="This is an updated post without categories",
        category_ids=[]
    )
    response = post_service.update_post("1", post_data, user_id="user1")
    assert response.id == "1"
    assert response.title == "Updated Post Without Categories"
    assert response.content == "This is an updated post without categories"
    assert len(response.categories) == 0

def test_should_raise_400_when_update_post_failed(post_service, mocker):
    post_data = PostUpdate(
        title="Any",
        content="Any",
        category_ids=["3"]
    )
    # Giả lập post_repo.update raise Exception
    mocker.patch.object(post_service.post_repo, "update", side_effect=Exception("Mocked DB error"))

    with pytest.raises(HTTPException) as exc_info:
        post_service.update_post("1", post_data, user_id="user1")
    assert exc_info.value.status_code == 400
    assert "Update post failed: Mocked DB error" in exc_info.value.detail

def test_should_return_post_when_deleted_successfully(post_service):
    response = post_service.delete_post("3", user_id="user3")
    assert response.id == "3"
    assert response.title == "Post 3"
    assert response.content == "Content 3"

def test_should_raise_400_when_delete_post_failed(post_service, mocker):
    # Giả lập post_repo.delete raise Exception
    mocker.patch.object(post_service.post_repo, "delete", side_effect=Exception("Mocked DB error"))

    with pytest.raises(HTTPException) as exc_info:
        post_service.delete_post("2", user_id="user2")
    assert exc_info.value.status_code == 400
    assert "Delete post failed: Mocked DB error" in exc_info.value.detail