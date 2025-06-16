import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tests.load_env  # noqa: F401
from src.cores.database import Base

TEST_DATABASE_URL = os.getenv("DATABASE_URL")
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args=({"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}),
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Tạo lại schema mỗi lần test (tuỳ mục đích)
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# Dependency override
def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
