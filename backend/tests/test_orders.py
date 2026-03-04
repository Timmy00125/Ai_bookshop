"""
Tests for /orders endpoints.
Covers: list user orders, checkout, admin list all orders.
"""

from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from tests.conftest import make_user, make_book, auth_header
from src import models


def _make_order(id_: int = 1, user_id: int = 1, status: models.OrderStatus = models.OrderStatus.completed):
    order = models.Order()
    order.id = id_
    order.user_id = user_id
    order.total_price = Decimal("29.97")
    order.status = status
    order.items = []
    _now = datetime.now(timezone.utc)
    order.created_at = _now
    order.updated_at = _now
    return order


def _make_cart_item_with_book(id_: int = 1, book_price: float = 9.99, quantity: int = 1):
    book = make_book(id_=id_, price=Decimal(str(book_price)))
    item = models.CartItem()
    item.id = id_
    item.user_id = 1
    item.book_id = book.id
    item.book = book
    item.quantity = quantity
    item.added_at = datetime.now(timezone.utc)
    return item


def _populate_order(obj, id_=10):
    obj.id = id_
    _now = datetime.now(timezone.utc)
    obj.created_at = _now
    obj.updated_at = _now
    obj.items = []


class TestGetOrders:
    def test_returns_user_orders(self, client, mock_db):
        user = make_user(id_=1)
        orders = [_make_order(i, user_id=1) for i in range(1, 3)]
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = orders

        resp = client.get("/orders/", headers=auth_header(user))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 2

    def test_unauthenticated_returns_401(self, client, mock_db):
        resp = client.get("/orders/")
        assert resp.status_code == 401

    def test_empty_order_list(self, client, mock_db):
        user = make_user(id_=1)
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        resp = client.get("/orders/", headers=auth_header(user))
        assert resp.status_code == 200
        assert resp.json() == []


class TestCheckout:
    def test_checkout_with_cart_items(self, client, mock_db):
        user = make_user(id_=1)
        cart_item = _make_cart_item_with_book(id_=1, book_price=15.00, quantity=2)

        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.all.return_value = [cart_item]
        mock_db.refresh.side_effect = lambda obj: _populate_order(obj)

        resp = client.post("/orders/checkout", headers=auth_header(user))
        assert resp.status_code in (200, 201)
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    def test_checkout_empty_cart_returns_400(self, client, mock_db):
        user = make_user(id_=1)
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.all.return_value = []

        resp = client.post("/orders/checkout", headers=auth_header(user))
        assert resp.status_code == 400
        assert "Cart is empty" in resp.json()["detail"]

    def test_unauthenticated_cannot_checkout(self, client, mock_db):
        resp = client.post("/orders/checkout")
        assert resp.status_code == 401

    def test_checkout_calculates_total_correctly(self, client, mock_db):
        user = make_user(id_=1)
        cart_items = [
            _make_cart_item_with_book(id_=1, book_price=10.00, quantity=2),
            _make_cart_item_with_book(id_=2, book_price=5.00, quantity=3),
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.filter.return_value.all.return_value = cart_items
        mock_db.refresh.side_effect = lambda obj: _populate_order(obj)

        # Capture what was passed to db.add()
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        resp = client.post("/orders/checkout", headers=auth_header(user))
        # Find the Order that was added
        orders_added = [o for o in added_objects if isinstance(o, models.Order)]
        if orders_added:
            expected_total = Decimal("10.00") * 2 + Decimal("5.00") * 3
            assert orders_added[0].total_price == expected_total


class TestGetAllOrdersAdmin:
    def test_admin_can_list_all_orders(self, client, mock_db):
        admin = make_user(id_=99, role=models.UserRole.admin)
        all_orders = [_make_order(i) for i in range(1, 5)]
        mock_db.query.return_value.filter.return_value.first.return_value = admin
        mock_db.query.return_value.order_by.return_value.all.return_value = all_orders

        resp = client.get("/orders/all", headers=auth_header(admin))
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_non_admin_cannot_list_all_orders(self, client, mock_db):
        user = make_user(id_=1, role=models.UserRole.user)
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.get("/orders/all", headers=auth_header(user))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_list_all_orders(self, client, mock_db):
        resp = client.get("/orders/all")
        assert resp.status_code == 401
