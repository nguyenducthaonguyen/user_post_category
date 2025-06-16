import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Xác định đường dẫn tuyệt đối đến .env.test ở thư mục gốc project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env.test")
load_dotenv(dotenv_path=ENV_PATH, override=True)
TEST_DATABASE_URL = os.getenv("DATABASE_URL")
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
    ),
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Tạo lại schema mỗi lần test (tuỳ mục đích)
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


from src.cores.database import Base


# Dependency override
def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
