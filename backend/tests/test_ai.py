"""
Tests for /ai router endpoints.
Covers: /ai/search, /ai/recommendations, /ai/chat, /ai/reindex (admin).
"""

from unittest.mock import MagicMock, patch
import pytest

from tests.conftest import make_user, make_book, auth_header
from src import models


def _regular_user():
    return make_user(id_=1, role=models.UserRole.user)


def _admin_user():
    return make_user(id_=99, role=models.UserRole.admin)


class TestSemanticSearch:
    def test_returns_books_list(self, client, mock_db):
        books = [make_book(id_=i, title=f"Book {i}") for i in range(1, 4)]
        with patch("src.routers.ai.semantic_search", return_value=books):
            resp = client.get("/ai/search?query=test")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_returns_empty_list_on_no_results(self, client, mock_db):
        with patch("src.routers.ai.semantic_search", return_value=[]):
            resp = client.get("/ai/search?query=nothing")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_limit_parameter_is_passed(self, client, mock_db):
        with patch("src.routers.ai.semantic_search", return_value=[]) as mock_search:
            resp = client.get("/ai/search?query=sci-fi&limit=3")
        assert resp.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args[1]  # keyword args
        assert call_kwargs.get("limit") == 3

    def test_missing_query_returns_422(self, client, mock_db):
        resp = client.get("/ai/search")
        assert resp.status_code == 422

    def test_limit_too_high_returns_422(self, client, mock_db):
        resp = client.get("/ai/search?query=test&limit=100")
        assert resp.status_code == 422


class TestRecommendations:
    def test_authenticated_user_gets_recommendations(self, client, mock_db):
        user = _regular_user()
        books = [make_book(id_=i) for i in range(1, 5)]
        mock_db.query.return_value.filter.return_value.first.return_value = user
        with patch("src.routers.ai.get_recommendations", return_value=books):
            resp = client.get("/ai/recommendations", headers=auth_header(user))
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_unauthenticated_returns_401(self, client, mock_db):
        resp = client.get("/ai/recommendations")
        assert resp.status_code == 401

    def test_empty_recommendations(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        with patch("src.routers.ai.get_recommendations", return_value=[]):
            resp = client.get("/ai/recommendations", headers=auth_header(user))
        assert resp.status_code == 200
        assert resp.json() == []


class TestChat:
    def test_chat_returns_reply(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        with patch("src.routers.ai.process_chat", return_value="Here are some great books!"):
            resp = client.post(
                "/ai/chat",
                json={"query": "Give me a recommendation"},
                headers=auth_header(user),
            )
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Here are some great books!"

    def test_chat_unauthenticated_returns_401(self, client, mock_db):
        resp = client.post("/ai/chat", json={"query": "test"})
        assert resp.status_code == 401

    def test_chat_missing_query_returns_422(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        resp = client.post("/ai/chat", json={}, headers=auth_header(user))
        assert resp.status_code == 422

    def test_chat_no_results_message(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user
        no_result_msg = "I'm sorry, I couldn't find any books that match your interest right now."
        with patch("src.routers.ai.process_chat", return_value=no_result_msg):
            resp = client.post(
                "/ai/chat",
                json={"query": "very unusual thing"},
                headers=auth_header(user),
            )
        assert resp.status_code == 200
        assert "sorry" in resp.json()["reply"].lower()


class TestReindex:
    def test_admin_can_reindex(self, client, mock_db):
        admin = _admin_user()
        books = [make_book(id_=i) for i in range(1, 4)]
        mock_db.query.return_value.filter.return_value.first.return_value = admin
        mock_db.query.return_value.all.return_value = books

        with patch("src.routers.ai.generate_book_embedding") as mock_embed:
            resp = client.post("/ai/reindex", headers=auth_header(admin))

        assert resp.status_code == 200
        data = resp.json()
        assert "3" in data["message"]
        assert mock_embed.call_count == 3

    def test_non_admin_cannot_reindex(self, client, mock_db):
        user = _regular_user()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        resp = client.post("/ai/reindex", headers=auth_header(user))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_reindex(self, client, mock_db):
        resp = client.post("/ai/reindex")
        assert resp.status_code == 401

    def test_reindex_empty_catalog(self, client, mock_db):
        admin = _admin_user()
        mock_db.query.return_value.filter.return_value.first.return_value = admin
        mock_db.query.return_value.all.return_value = []

        with patch("src.routers.ai.generate_book_embedding") as mock_embed:
            resp = client.post("/ai/reindex", headers=auth_header(admin))

        assert resp.status_code == 200
        assert "0" in resp.json()["message"]
        mock_embed.assert_not_called()
