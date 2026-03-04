"""
Tests for /auth endpoints.
Covers: register, login, /me
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from tests.conftest import make_user, make_book, auth_header
from src import models
from src.utils.security import get_password_hash


def _populate(obj, id_=1):
    """Simulate what db.refresh() does for a newly created ORM object."""
    _now = datetime.now(timezone.utc)
    obj.id = id_
    obj.created_at = _now
    obj.updated_at = _now
    # Column defaults that only apply after DB commit - must be set explicitly
    if not hasattr(obj, 'is_active') or obj.is_active is None:
        obj.is_active = True
    if not hasattr(obj, 'role') or obj.role is None:
        from src.models import UserRole
        obj.role = UserRole.user


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_first_user_gets_admin_role(self, client, mock_db):
        # No existing user → count=0 → admin
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.count.return_value = 0
        mock_db.refresh.side_effect = lambda obj: _populate(obj, id_=1)

        resp = client.post(
            "/auth/register",
            json={"username": "admin_guy", "email": "admin@test.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin_guy"
        assert data["role"] == "admin"

    def test_subsequent_user_gets_user_role(self, client, mock_db):
        # DB already has 1 user → role = user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.count.return_value = 1
        mock_db.refresh.side_effect = lambda obj: _populate(obj, id_=2)

        resp = client.post(
            "/auth/register",
            json={"username": "normal_user", "email": "normal@test.com", "password": "pass"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "user"

    def test_duplicate_user_raises_400(self, client, mock_db):
        existing = make_user()
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        resp = client.post(
            "/auth/register",
            json={"username": "test_user", "email": "test@example.com", "password": "pass"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    def test_register_response_shape(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.count.return_value = 5
        mock_db.refresh.side_effect = lambda obj: _populate(obj, id_=10)

        resp = client.post(
            "/auth/register",
            json={"username": "shape_user", "email": "shape@test.com", "password": "pass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ("id", "username", "email", "role", "is_active"):
            assert field in data


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client, mock_db):
        user = make_user(password="correct_pw")
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post(
            "/auth/login",
            data={"username": "test_user", "password": "correct_pw"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, mock_db):
        user = make_user(password="correct_pw")
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post(
            "/auth/login",
            data={"username": "test_user", "password": "wrong_pw"},
        )
        assert resp.status_code == 400
        assert "Incorrect username or password" in resp.json()["detail"]

    def test_login_nonexistent_user(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resp = client.post(
            "/auth/login",
            data={"username": "ghost", "password": "pass"},
        )
        assert resp.status_code == 400

    def test_login_inactive_user(self, client, mock_db):
        user = make_user(password="pass", is_active=False)
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post(
            "/auth/login",
            data={"username": "test_user", "password": "pass"},
        )
        assert resp.status_code == 400
        assert "Inactive user" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestMe:
    def test_get_current_user(self, client, mock_db):
        user = make_user(id_=5)
        # dependencies.get_current_active_user calls get_db and queries by username
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.get("/auth/me", headers=auth_header(user))
        assert resp.status_code == 200
        assert resp.json()["username"] == user.username

    def test_get_current_user_unauthenticated(self, client, mock_db):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_get_current_user_inactive(self, client, mock_db):
        user = make_user(is_active=False)
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.get("/auth/me", headers=auth_header(user))
        assert resp.status_code == 400
