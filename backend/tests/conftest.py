"""
conftest.py - shared pytest fixtures for the AI Bookshop backend.

Strategy
--------
The models use pgvector's Vector column type. Since the conda env has all
the real dependencies installed, we simply import normally without any
sys.modules patching.

We override `get_db` with a factory that returns a MagicMock session so
tests don't need a live database.
"""

from unittest.mock import MagicMock
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.database import get_db
from src import models
from src.utils.security import get_password_hash, create_access_token


# ---------------------------------------------------------------------------
# Mock-session db override
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_db():
    """A MagicMock Session injected via dependency override."""
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def client(mock_db):
    """FastAPI TestClient with the mock DB already wired up."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Model factory helpers
# ---------------------------------------------------------------------------

def make_user(
    id_: int = 1,
    username: str = "test_user",
    email: str = "test@example.com",
    password: str = "password",
    role: models.UserRole = models.UserRole.user,
    is_active: bool = True,
) -> models.User:
    u = models.User()
    u.id = id_
    u.username = username
    u.email = email
    u.hashed_password = get_password_hash(password)
    u.role = role
    u.is_active = is_active
    _now = datetime.now(timezone.utc)
    u.created_at = _now
    u.updated_at = _now
    return u


def make_book(
    id_: int = 1,
    title: str = "1984",
    author: str = "George Orwell",
    genre: str = "Dystopian",
    price: float = 9.99,
    stock_count: int = 50,
    average_rating: float = 4.5,
    description: str = "A dystopian novel.",
) -> models.Book:
    b = models.Book()
    b.id = id_
    b.title = title
    b.author = author
    b.genre = genre
    b.price = price
    b.stock_count = stock_count
    b.average_rating = average_rating
    b.description = description
    _now = datetime.now(timezone.utc)
    b.created_at = _now
    b.updated_at = _now
    return b


def make_token(user: models.User) -> str:
    return create_access_token(data={"sub": user.username, "role": user.role.value})


def auth_header(user: models.User) -> dict:
    return {"Authorization": f"Bearer {make_token(user)}"}
