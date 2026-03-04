"""
Tests for /books endpoints.
Covers: list (search/filter/sort), get by id, create (admin), update (admin), delete (admin).
"""

import pytest
from datetime import datetime, timezone
from tests.conftest import make_user, make_book, auth_header
from src import models


def _populate(obj, id_=1):
    _now = datetime.now(timezone.utc)
    obj.id = id_
    obj.created_at = _now
    obj.updated_at = _now
    # Ensure required schema fields have values after mock DB commit
    if getattr(obj, 'stock_count', None) is None:
        obj.stock_count = 0
    if getattr(obj, 'average_rating', None) is None:
        obj.average_rating = 0.0


def _admin_user():
    return make_user(role=models.UserRole.admin, id_=99)


def _normal_user():
    return make_user(role=models.UserRole.user, id_=1)


class TestListBooks:
    def test_returns_list(self, client, mock_db):
        books = [make_book(id_=i, title=f"Book {i}") for i in range(1, 4)]
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = books

        resp = client.get("/books/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 3

    def test_pagination(self, client, mock_db):
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []

        resp = client.get("/books/?skip=10&limit=5")
        assert resp.status_code == 200

    def test_filter_by_genre(self, client, mock_db):
        book = make_book(genre="Sci-Fi")
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = [book]

        resp = client.get("/books/?genre=Sci-Fi")
        assert resp.status_code == 200

    def test_filter_by_price_range(self, client, mock_db):
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []

        resp = client.get("/books/?min_price=5&max_price=20")
        assert resp.status_code == 200

    def test_invalid_limit(self, client, mock_db):
        resp = client.get("/books/?limit=999")
        assert resp.status_code == 422  # validation error

    def test_sort_by_price(self, client, mock_db):
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []

        resp = client.get("/books/?sort_by=price")
        assert resp.status_code == 200

    def test_sort_by_rating(self, client, mock_db):
        q = mock_db.query.return_value
        q.filter.return_value = q
        q.order_by.return_value = q
        q.offset.return_value = q
        q.limit.return_value = q
        q.all.return_value = []

        resp = client.get("/books/?sort_by=rating")
        assert resp.status_code == 200


class TestGetBook:
    def test_returns_book(self, client, mock_db):
        book = make_book(id_=1)
        mock_db.query.return_value.filter.return_value.first.return_value = book

        resp = client.get("/books/1")
        assert resp.status_code == 200
        assert resp.json()["title"] == "1984"

    def test_book_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.get("/books/999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestCreateBook:
    def _payload(self):
        return {
            "title": "Brave New World",
            "author": "Aldous Huxley",
            "genre": "Dystopian",
            "price": 12.99,
            "stock_count": 30,
        }

    def test_admin_can_create_book(self, client, mock_db):
        admin = _admin_user()
        mock_db.query.return_value.filter.return_value.first.return_value = admin
        mock_db.refresh.side_effect = lambda obj: _populate(obj, id_=10)

        resp = client.post("/books/", json=self._payload(), headers=auth_header(admin))
        assert resp.status_code == 201

    def test_non_admin_cannot_create_book(self, client, mock_db):
        user = _normal_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post("/books/", json=self._payload(), headers=auth_header(user))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_book(self, client, mock_db):
        resp = client.post("/books/", json=self._payload())
        assert resp.status_code == 401

    def test_missing_required_fields(self, client, mock_db):
        admin = _admin_user()
        mock_db.query.return_value.filter.return_value.first.return_value = admin

        resp = client.post("/books/", json={"title": "No price"}, headers=auth_header(admin))
        assert resp.status_code == 422


class TestUpdateBook:
    def test_admin_can_update_book(self, client, mock_db):
        admin = _admin_user()
        book = make_book(id_=1)
        calls = [admin, book]
        mock_db.query.return_value.filter.return_value.first.side_effect = calls
        mock_db.refresh.side_effect = lambda obj: None

        resp = client.put(
            "/books/1",
            json={"price": 14.99},
            headers=auth_header(admin),
        )
        assert resp.status_code == 200

    def test_admin_update_not_found(self, client, mock_db):
        admin = _admin_user()
        # First call returns admin (auth), second returns None (book not found)
        mock_db.query.return_value.filter.return_value.first.side_effect = [admin, None]

        resp = client.put("/books/999", json={"price": 5.0}, headers=auth_header(admin))
        assert resp.status_code == 404

    def test_non_admin_cannot_update(self, client, mock_db):
        user = _normal_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.put("/books/1", json={"price": 5.0}, headers=auth_header(user))
        assert resp.status_code == 403


class TestDeleteBook:
    def test_admin_can_delete_book(self, client, mock_db):
        admin = _admin_user()
        book = make_book(id_=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [admin, book]

        resp = client.delete("/books/1", headers=auth_header(admin))
        assert resp.status_code == 204

    def test_delete_not_found(self, client, mock_db):
        admin = _admin_user()
        mock_db.query.return_value.filter.return_value.first.side_effect = [admin, None]

        resp = client.delete("/books/999", headers=auth_header(admin))
        assert resp.status_code == 404

    def test_non_admin_cannot_delete(self, client, mock_db):
        user = _normal_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.delete("/books/1", headers=auth_header(user))
        assert resp.status_code == 403
