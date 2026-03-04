import pytest

from src import models

@pytest.fixture(scope="function")
def admin_user(db_session):
    user = models.User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_secret",
        role=models.UserRole.admin,
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_user(db_session):
    user = models.User(
        username="test_user",
        email="test_user@example.com",
        hashed_password="hashed_secret",
        role=models.UserRole.user,
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_book(db_session):
    book = models.Book(
        title="1984",
        author="George Orwell",
        genre="Dystopian",
        price=9.99,
        stock_count=50
    )
    db_session.add(book)
    db_session.commit()
    return book
