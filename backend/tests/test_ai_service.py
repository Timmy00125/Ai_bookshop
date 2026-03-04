"""
Unit tests for src/services/ai_service.py.
All external dependencies (SentenceTransformer, pgvector queries) are mocked.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.services import ai_service
from src import models


# ---------------------------------------------------------------------------
# get_embedding
# ---------------------------------------------------------------------------

class TestGetEmbedding:
    def test_returns_list_of_floats(self, mocker):
        encode_result = MagicMock()
        encode_result.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model = MagicMock()
        mock_model.encode.return_value = encode_result
        mocker.patch("src.services.ai_service.get_model", return_value=mock_model)

        result = ai_service.get_embedding("test query")
        assert isinstance(result, list)
        mock_model.encode.assert_called_once_with("test query")

    def test_model_is_loaded_lazily(self, mocker):
        ai_service._model = None
        mock_constructor = mocker.patch(
            "src.services.ai_service.SentenceTransformer",
            return_value=MagicMock(),
        )
        ai_service.get_model()
        mock_constructor.assert_called_once_with("all-MiniLM-L6-v2")

    def test_model_is_cached(self, mocker):
        sentinel = MagicMock()
        ai_service._model = sentinel
        result = ai_service.get_model()
        assert result is sentinel


# ---------------------------------------------------------------------------
# generate_book_embedding
# ---------------------------------------------------------------------------

class TestGenerateBookEmbedding:
    def _make_book(self, id_=1):
        b = models.Book()
        b.id = id_
        b.title = "1984"
        b.author = "George Orwell"
        b.genre = "Dystopian"
        b.description = "A classic."
        return b

    def test_creates_new_embedding_when_none_exists(self, mocker):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mocker.patch("src.services.ai_service.get_embedding", return_value=[0.1] * 384)

        book = self._make_book()
        ai_service.generate_book_embedding(book, mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_updates_existing_embedding(self, mocker):
        mock_db = MagicMock()
        existing = MagicMock(spec=models.BookEmbedding)
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        mocker.patch("src.services.ai_service.get_embedding", return_value=[0.2] * 384)

        book = self._make_book()
        ai_service.generate_book_embedding(book, mock_db)

        assert existing.embedding == [0.2] * 384
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    def test_embeds_correct_text(self, mocker):
        mock_embed = mocker.patch(
            "src.services.ai_service.get_embedding", return_value=[0.0] * 384
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        book = self._make_book()
        ai_service.generate_book_embedding(book, mock_db)

        expected_text = "1984 George Orwell Dystopian A classic."
        mock_embed.assert_called_once_with(expected_text)


# ---------------------------------------------------------------------------
# semantic_search
# ---------------------------------------------------------------------------

class TestSemanticSearch:
    def test_returns_books_from_embeddings(self, mocker):
        mock_db = MagicMock()
        mocker.patch("src.services.ai_service.get_embedding", return_value=[0.0] * 384)

        book1 = models.Book()
        book1.id = 1
        book1.title = "Result Book"

        embed1 = MagicMock(spec=models.BookEmbedding)
        embed1.book = book1

        q = mock_db.query.return_value
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = [embed1]

        results = ai_service.semantic_search("science fiction", mock_db, limit=1)
        assert len(results) == 1
        assert results[0].title == "Result Book"

    def test_filters_embeddings_with_no_book(self, mocker):
        mock_db = MagicMock()
        mocker.patch("src.services.ai_service.get_embedding", return_value=[0.0] * 384)

        embed_no_book = MagicMock(spec=models.BookEmbedding)
        embed_no_book.book = None

        q = mock_db.query.return_value
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = [embed_no_book]

        results = ai_service.semantic_search("test", mock_db)
        assert results == []


# ---------------------------------------------------------------------------
# get_recommendations
# ---------------------------------------------------------------------------

class TestGetRecommendations:
    def test_fallback_when_no_history(self, mocker):
        mock_db = MagicMock()
        books = [make_book_model(i) for i in range(6)]
        # history query returns empty
        history_q = MagicMock()
        history_q.filter.return_value = history_q
        history_q.order_by.return_value = history_q
        history_q.limit.return_value = history_q
        history_q.all.return_value = []

        fallback_q = MagicMock()
        fallback_q.order_by.return_value = fallback_q
        fallback_q.limit.return_value = fallback_q
        fallback_q.all.return_value = books

        mock_db.query.side_effect = [history_q, fallback_q]

        result = ai_service.get_recommendations(user_id=1, db=mock_db)
        assert len(result) == 6

    def test_fallback_when_no_embeddings(self, mocker):
        mock_db = MagicMock()

        h = MagicMock()
        h.book_id = 1
        history_q = MagicMock()
        history_q.filter.return_value = history_q
        history_q.order_by.return_value = history_q
        history_q.limit.return_value = history_q
        history_q.all.return_value = [h]

        embed_q = MagicMock()
        embed_q.filter.return_value = embed_q
        embed_q.all.return_value = []

        fallback_q = MagicMock()
        fallback_q.order_by.return_value = fallback_q
        fallback_q.limit.return_value = fallback_q
        fallback_q.all.return_value = []

        mock_db.query.side_effect = [history_q, embed_q, fallback_q]

        result = ai_service.get_recommendations(user_id=1, db=mock_db)
        assert result == []

    def test_returns_neighbor_books_excluding_history(self, mocker):
        mock_db = MagicMock()
        mocker.patch("src.services.ai_service.get_embedding", return_value=[0.0] * 384)

        h = MagicMock()
        h.book_id = 1
        history_q = MagicMock()
        history_q.filter.return_value = history_q
        history_q.order_by.return_value = history_q
        history_q.limit.return_value = history_q
        history_q.all.return_value = [h]

        emb = MagicMock()
        emb.embedding = [0.1] * 384
        embed_q = MagicMock()
        embed_q.filter.return_value = embed_q
        embed_q.all.return_value = [emb]

        book2 = make_book_model(2)
        rec_embed = MagicMock(spec=models.BookEmbedding)
        rec_embed.book = book2
        neighbor_q = MagicMock()
        neighbor_q.filter.return_value = neighbor_q
        neighbor_q.order_by.return_value = neighbor_q
        neighbor_q.limit.return_value = neighbor_q
        neighbor_q.all.return_value = [rec_embed]

        mock_db.query.side_effect = [history_q, embed_q, neighbor_q]

        result = ai_service.get_recommendations(user_id=1, db=mock_db)
        assert len(result) == 1
        assert result[0].id == 2


# ---------------------------------------------------------------------------
# process_chat
# ---------------------------------------------------------------------------

class TestProcessChat:
    def test_response_contains_book_titles(self, mocker):
        book = models.Book()
        book.title = "Dune"
        book.author = "Frank Herbert"
        mocker.patch("src.services.ai_service.semantic_search", return_value=[book])

        result = ai_service.process_chat("desert sci-fi", user_id=1, db=MagicMock())
        assert "Dune" in result
        assert "Frank Herbert" in result

    def test_no_books_returns_sorry_message(self, mocker):
        mocker.patch("src.services.ai_service.semantic_search", return_value=[])

        result = ai_service.process_chat("random query", user_id=1, db=MagicMock())
        assert "sorry" in result.lower() or "couldn't find" in result.lower()

    def test_multiple_books_all_mentioned(self, mocker):
        books = []
        for t, a in [("Book A", "Author A"), ("Book B", "Author B")]:
            b = models.Book()
            b.title = t
            b.author = a
            books.append(b)
        mocker.patch("src.services.ai_service.semantic_search", return_value=books)

        result = ai_service.process_chat("something", user_id=1, db=MagicMock())
        assert "Book A" in result
        assert "Book B" in result


def make_book_model(id_: int = 1) -> models.Book:
    from datetime import datetime, timezone
    b = models.Book()
    b.id = id_
    b.title = f"Book {id_}"
    b.author = "Author"
    b.average_rating = 4.0
    _now = datetime.now(timezone.utc)
    b.created_at = _now
    b.updated_at = _now
    return b
