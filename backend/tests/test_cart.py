"""
Tests for /cart endpoints.
Covers: list cart, add to cart, update quantity, remove item.
"""

from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime, timezone
import pytest

from tests.conftest import make_user, make_book, auth_header
from src import models


def _populate_cart_item(obj, id_=1):
    obj.id = id_
    obj.added_at = datetime.now(timezone.utc)


def _regular_user():
    return make_user(id_=1, role=models.UserRole.user)


def _make_cart_item(id_: int = 1, user_id: int = 1, book_id: int = 1, quantity: int = 2):
    book = make_book(id_=book_id, price=Decimal("9.99"))
    item = models.CartItem()
    item.id = id_
    item.user_id = user_id
    item.book_id = book_id
    item.book = book
    item.quantity = quantity
    item.added_at = datetime.now(timezone.utc)
    return item


class TestGetCart:
    def test_returns_cart_items(self, client, mock_db):
        user = _regular_user()
        cart_item = _make_cart_item()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.all.return_value = [cart_item]

        resp = client.get("/cart/", headers=auth_header(user))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_unauthenticated_returns_401(self, client, mock_db):
        resp = client.get("/cart/")
        assert resp.status_code == 401

    def test_empty_cart_returns_empty_list(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.all.return_value = []

        resp = client.get("/cart/", headers=auth_header(user))
        assert resp.status_code == 200
        assert resp.json() == []


class TestAddToCart:
    def test_adds_new_item(self, client, mock_db):
        user = _regular_user()
        book = make_book(id_=5, price=Decimal("9.99"))

        # Call sequence: get_current_user (returns user), find book, find existing cart item
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            user,   # auth dependency
            book,   # book lookup
            None,   # no existing cart item
        ]

        def _refresh_with_book(obj):
            obj.id = 1
            obj.added_at = datetime.now(timezone.utc)
            obj.book = book  # Set the relationship the DB would normally load

        mock_db.refresh.side_effect = _refresh_with_book

        resp = client.post("/cart/", json={"book_id": 5, "quantity": 1}, headers=auth_header(user))
        assert resp.status_code == 201

    def test_increments_existing_item(self, client, mock_db):
        user = _regular_user()
        book = make_book(id_=5)
        existing_item = _make_cart_item(book_id=5, quantity=2)

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            user,           # auth
            book,           # book lookup
            existing_item,  # existing cart item
        ]
        mock_db.refresh.side_effect = lambda obj: None

        resp = client.post("/cart/", json={"book_id": 5, "quantity": 3}, headers=auth_header(user))
        assert resp.status_code == 201
        # quantity should have been incremented on the existing_item
        assert existing_item.quantity == 5

    def test_book_not_found_returns_404(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            user,   # auth
            None,   # book not found
        ]

        resp = client.post("/cart/", json={"book_id": 999, "quantity": 1}, headers=auth_header(user))
        assert resp.status_code == 404

    def test_unauthenticated_cannot_add(self, client, mock_db):
        resp = client.post("/cart/", json={"book_id": 1, "quantity": 1})
        assert resp.status_code == 401


class TestUpdateCartItem:
    def test_updates_quantity(self, client, mock_db):
        user = _regular_user()
        item = _make_cart_item(id_=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, item]
        mock_db.refresh.side_effect = lambda obj: None

        resp = client.put("/cart/1", json={"quantity": 10}, headers=auth_header(user))
        assert resp.status_code == 200
        assert item.quantity == 10

    def test_item_not_found_returns_404(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, None]

        resp = client.put("/cart/999", json={"quantity": 1}, headers=auth_header(user))
        assert resp.status_code == 404

    def test_unauthenticated_cannot_update(self, client, mock_db):
        resp = client.put("/cart/1", json={"quantity": 1})
        assert resp.status_code == 401


class TestRemoveFromCart:
    def test_removes_item(self, client, mock_db):
        user = _regular_user()
        item = _make_cart_item(id_=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, item]

        resp = client.delete("/cart/1", headers=auth_header(user))
        assert resp.status_code == 204
        mock_db.delete.assert_called_once_with(item)

    def test_item_not_found_returns_404(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, None]

        resp = client.delete("/cart/999", headers=auth_header(user))
        assert resp.status_code == 404

    def test_unauthenticated_cannot_remove(self, client, mock_db):
        resp = client.delete("/cart/1")
        assert resp.status_code == 401
