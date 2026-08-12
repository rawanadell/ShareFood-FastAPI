import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db.base import Base
from db.session import get_db
from core.security import hash_password
from models.user import User, UserRole

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///./test_food_donation.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    import models  # noqa
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helper to seed a user and get their token ──────────────────────────────────

def _make_user(db, name, email, password, role) -> User:
    u = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _login(client, email, password) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def admin_user(db):
    return _make_user(db, "Admin", "admin@test.com", "Admin1234", UserRole.ADMIN)


@pytest.fixture()
def donor_user(db):
    return _make_user(db, "Donor", "donor@test.com", "Donor1234", UserRole.DONOR)


@pytest.fixture()
def charity_user(db):
    return _make_user(db, "Charity", "charity@test.com", "Charity1234", UserRole.CHARITY)


@pytest.fixture()
def volunteer_user(db):
    return _make_user(db, "Volunteer", "volunteer@test.com", "Volunteer1234", UserRole.VOLUNTEER)


@pytest.fixture()
def admin_token(client, admin_user):
    return _login(client, "admin@test.com", "Admin1234")


@pytest.fixture()
def donor_token(client, donor_user):
    return _login(client, "donor@test.com", "Donor1234")


@pytest.fixture()
def charity_token(client, charity_user):
    return _login(client, "charity@test.com", "Charity1234")


@pytest.fixture()
def volunteer_token(client, volunteer_user):
    return _login(client, "volunteer@test.com", "Volunteer1234")
