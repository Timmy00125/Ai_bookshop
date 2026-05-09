"""
Bulk seed script for generating 1000+ books efficiently.
Fetches real books from the Open Library API so that cover images
match the actual book titles and authors.
Uses batch inserts and batched embedding generation for performance.
"""

import os
import random
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import text
from sqlalchemy.orm import Session
from src import models
from src.database import SessionLocal, engine
from src.services.ai_service import get_embedding, get_model

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_COVERS = "https://covers.openlibrary.org/b"

# Search queries to fetch a diverse set of real books
SEARCH_QUERIES = [
    "fiction bestseller",
    "mystery novel",
    "science fiction",
    "fantasy adventure",
    "romance novel",
    "thriller suspense",
    "horror novel",
    "historical fiction",
    "literary fiction",
    "classic literature",
    "detective story",
    "adventure novel",
    "dystopian fiction",
    "war novel",
    "philosophical fiction",
    "psychological thriller",
    "crime fiction",
    "dark fantasy",
    "epic fantasy",
    "space opera",
    "young adult fiction",
    "children literature",
    "fairy tales",
    "mythology",
    "poetry collection",
    "drama play",
    "biography memoir",
    "autobiography",
    "history book",
    "world history",
    "ancient history",
    "military history",
    "science popular",
    "physics book",
    "mathematics book",
    "biology book",
    "chemistry book",
    "astronomy book",
    "computer science",
    "programming book",
    "machine learning",
    "artificial intelligence",
    "data science",
    "web development",
    "software engineering",
    "philosophy book",
    "psychology book",
    "sociology book",
    "economics book",
    "political science",
    "business book",
    "leadership",
    "self-help book",
    "personal development",
    "mindfulness meditation",
    "health fitness",
    "nutrition diet",
    "cooking recipe",
    "travel guide",
    "art photography",
    "music theory",
    "sports biography",
    "nature ecology",
    "climate change",
    "space exploration",
    "quantum mechanics",
    "evolution biology",
    "neuroscience",
    "entrepreneurship",
    "investing finance",
    "marketing strategy",
    "design thinking",
    "creativity innovation",
    "stoicism philosophy",
    "existentialism",
    "eastern philosophy",
    "religious studies",
    "cultural studies",
    "anthropology book",
    "archaeology book",
    "linguistics book",
    "education pedagogy",
    "environmental science",
    "renewable energy",
]


def fetch_books_from_openlibrary(
    query: str, limit: int = 100, offset: int = 0
) -> list[dict]:
    """Fetch real books from Open Library search API. Sorted by editions to get popular books."""
    try:
        params = {
            "q": query,
            "limit": limit,
            "offset": offset,
            "sort": "editions",
            "fields": "key,title,author_name,first_publish_year,publisher,subject,cover_i,isbn,number_of_pages_median",
        }
        with httpx.Client(timeout=30) as client:
            resp = client.get(OPEN_LIBRARY_SEARCH, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("docs", [])
    except Exception as e:
        print(f"  Warning: Failed to fetch books for query '{query}': {e}")
        return []


def build_cover_url(cover_id: int | None) -> str | None:
    """Build a cover image URL from an Open Library cover ID."""
    if cover_id:
        return f"{OPEN_LIBRARY_COVERS}/id/{cover_id}-L.jpg"
    return None


def map_subject_to_genre(subjects: list[str] | None) -> str:
    """Map Open Library subject tags to our genre list."""
    if not subjects:
        return "Fiction"

    subject_text = " ".join(subjects).lower()

    genre_keywords = {
        "Science Fiction": [
            "science fiction",
            "sci-fi",
            "space",
            "dystopia",
            "cyberpunk",
        ],
        "Fantasy": ["fantasy", "magic", "dragon", "sword", "sorcery", "fairy"],
        "Mystery": ["mystery", "detective", "crime", "whodunit", "noir"],
        "Thriller": ["thriller", "suspense", "espionage", "spy"],
        "Romance": ["romance", "love story", "romantic"],
        "Horror": ["horror", "ghost", "supernatural", "vampire", "zombie"],
        "Biography": ["biography", "memoir", "autobiography", "life story"],
        "History": ["history", "historical", "war", "civilization", "ancient"],
        "Self-Help": ["self-help", "personal development", "motivation", "mindfulness"],
        "Business": [
            "business",
            "management",
            "leadership",
            "entrepreneurship",
            "marketing",
        ],
        "Technology": [
            "computer",
            "programming",
            "software",
            "technology",
            "internet",
            "web",
        ],
        "Science": [
            "science",
            "physics",
            "chemistry",
            "biology",
            "mathematics",
            "astronomy",
        ],
        "Philosophy": ["philosophy", "ethics", "metaphysics", "logic", "stoicism"],
        "Psychology": ["psychology", "psychotherapy", "mental health", "cognitive"],
        "Poetry": ["poetry", "poems", "verse", "sonnet"],
        "Drama": ["drama", "plays", "theater", "theatre"],
        "Travel": ["travel", "geography", "guidebook", "exploration"],
        "Cooking": ["cooking", "recipe", "food", "culinary", "baking"],
        "Health": ["health", "medical", "fitness", "nutrition", "wellness"],
        "Children": ["children", "juvenile", "picture book", "kids"],
        "Young Adult": ["young adult", "teen", "ya ", "adolescent"],
        "Adventure": ["adventure", "exploration", "survival", "expedition"],
    }

    for genre, keywords in genre_keywords.items():
        for keyword in keywords:
            if keyword in subject_text:
                return genre

    # Check for fiction vs non-fiction indicators
    non_fiction_indicators = [
        "non-fiction",
        "nonfiction",
        "textbook",
        "manual",
        "handbook",
        "guide",
        "reference",
        "study",
        "academic",
        "scholarly",
    ]
    for indicator in non_fiction_indicators:
        if indicator in subject_text:
            return "Non-Fiction"

    return "Fiction"


def convert_openlibrary_book(doc: dict) -> dict | None:
    """Convert an Open Library search result to our book schema format."""
    title = doc.get("title")
    if not title or len(title.strip()) < 2:
        return None

    authors = doc.get("author_name", ["Unknown Author"])
    author = ", ".join(authors[:3])  # Max 3 authors

    cover_id = doc.get("cover_i")
    cover_url = build_cover_url(cover_id)
    if not cover_url:
        return None  # Skip books without covers

    genre = map_subject_to_genre(doc.get("subject"))

    pub_year = doc.get("first_publish_year", random.randint(1990, 2024))
    if not isinstance(pub_year, int) or pub_year < 1800 or pub_year > 2026:
        pub_year = random.randint(1990, 2024)

    publishers = doc.get("publisher", ["Unknown Publisher"])
    publisher = publishers[0] if publishers else "Unknown Publisher"

    isbn_list = doc.get("isbn", [])
    isbn = isbn_list[0] if isbn_list else f"978{random.randint(1000000000, 9999999999)}"

    pages = doc.get("number_of_pages_median")
    description = f"A {genre.lower()} book by {author}."
    if pages:
        description += f" {pages} pages."

    price = round(random.uniform(5.99, 49.99), 2)
    stock = random.randint(5, 200)
    rating = round(random.uniform(3.0, 5.0), 2)

    pub_month = random.randint(1, 12)
    pub_day = random.randint(1, 28)

    return {
        "title": title.strip()[:500],
        "author": author.strip()[:500],
        "genre": genre,
        "description": description,
        "isbn": isbn[:20],
        "publisher": publisher.strip()[:200],
        "publication_date": datetime(pub_year, pub_month, pub_day, tzinfo=timezone.utc),
        "price": Decimal(str(price)),
        "stock_count": stock,
        "average_rating": Decimal(str(rating)),
        "cover_image_url": cover_url,
    }


def fetch_all_books(target: int = 1200) -> list[dict]:
    """Fetch real books from Open Library across multiple search queries."""
    all_books = []
    seen_titles = set()

    queries = SEARCH_QUERIES.copy()
    random.shuffle(queries)

    per_query = max(100, (target // len(queries)) + 20)

    for i, query in enumerate(queries):
        if len(all_books) >= target:
            break

        print(
            f"  [{i + 1}/{len(queries)}] Fetching books for '{query}' (have {len(all_books)}/{target})..."
        )

        # Fetch up to 2 pages per query for diversity
        for page in range(2):
            offset = page * 100
            docs = fetch_books_from_openlibrary(query, limit=100, offset=offset)

            if not docs:
                break

            for doc in docs:
                if len(all_books) >= target:
                    break

                book = convert_openlibrary_book(doc)
                if not book:
                    continue

                # Deduplicate by title+author
                dedup_key = f"{book['title'].lower()}|{book['author'].lower()}"
                if dedup_key in seen_titles:
                    continue
                seen_titles.add(dedup_key)

                all_books.append(book)

        # Be polite to the API
        time.sleep(0.5)

    return all_books


def clear_all_books():
    """Removes all existing books and embeddings from the database."""
    db: Session = SessionLocal()
    try:
        print("Clearing all existing books and embeddings from the database...")
        db.query(models.BookEmbedding).delete()
        db.query(models.Book).delete()
        db.commit()
        print("Database cleared successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


def seed_bulk(num_books=1000, batch_size=100, clear_first=False):
    """
    Seed books in batches for performance.
    Fetches real books from Open Library so covers match the actual books.
    Generates embeddings in batches using the sentence transformer's batch encoding.
    """
    if clear_first:
        clear_all_books()

    db: Session = SessionLocal()
    try:
        existing = db.query(models.Book).count()
        print(f"Database currently has {existing} books.")

        remaining = num_books - existing
        if remaining <= 0:
            print(
                f"Database already has {existing} books (target: {num_books}). Skipping seed."
            )
            return

        print(f"Fetching {remaining} real books from Open Library API...")
        all_books_data = fetch_all_books(
            target=remaining + 200
        )  # Fetch extra to account for skips

        # Trim to exact count needed
        all_books_data = all_books_data[:remaining]
        print(f"Got {len(all_books_data)} books with matching cover images.")

        if not all_books_data:
            print("No books fetched. Check your internet connection.")
            return

        print("Inserting books in batches...")
        for batch_start in range(0, len(all_books_data), batch_size):
            batch_end = min(batch_start + batch_size, len(all_books_data))
            batch_data = all_books_data[batch_start:batch_end]

            books = [models.Book(**data) for data in batch_data]
            db.bulk_save_objects(books, return_defaults=True)
            db.commit()

            print(
                f"  Inserted books {existing + batch_start + 1}-{existing + batch_end}"
            )

        print("Generating embeddings in batches...")
        model = get_model()

        books_without_embeddings = (
            db.query(models.Book)
            .outerjoin(models.BookEmbedding)
            .filter(models.BookEmbedding.id == None)
            .all()
        )

        total_books = len(books_without_embeddings)
        for batch_start in range(0, total_books, batch_size):
            batch_end = min(batch_start + batch_size, total_books)
            batch_books = books_without_embeddings[batch_start:batch_end]

            texts = [
                f"{b.title} {b.author} {b.genre} {b.description or ''}"
                for b in batch_books
            ]
            vectors = model.encode(texts).tolist()

            embeddings = [
                models.BookEmbedding(
                    book_id=book.id,
                    embedding=vector,
                    model_version="all-MiniLM-L6-v2",
                )
                for book, vector in zip(batch_books, vectors)
            ]
            db.bulk_save_objects(embeddings)
            db.commit()

            print(
                f"  Generated embeddings for books {batch_start + 1}-{batch_end}/{total_books}"
            )

        print("Creating database indexes for performance...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_price ON books(price)"))
        db.commit()

        print(
            f"\nSuccessfully seeded {len(all_books_data)} real books with matching covers!"
        )
        print(f"Total books in database: {db.query(models.Book).count()}")
        print("Database indexes created for optimal query performance.")

    finally:
        db.close()


def find_cover_for_title(title: str, author: str = "") -> str | None:
    """Search Open Library for a book by title+author and return its cover URL."""
    try:
        query = title
        if author:
            query += f" {author.split(',')[0].strip()}"

        params = {
            "q": query,
            "limit": 5,
            "fields": "title,author_name,cover_i",
        }
        with httpx.Client(timeout=15) as client:
            resp = client.get(OPEN_LIBRARY_SEARCH, params=params)
            resp.raise_for_status()
            docs = resp.json().get("docs", [])

        title_lower = title.lower().strip()
        for doc in docs:
            doc_title = (doc.get("title") or "").lower().strip()
            cover_id = doc.get("cover_i")
            if not cover_id:
                continue
            # Accept if title is a close match
            if (
                doc_title in title_lower
                or title_lower in doc_title
                or len(set(title_lower.split()) & set(doc_title.split())) >= 2
            ):
                return f"{OPEN_LIBRARY_COVERS}/id/{cover_id}-L.jpg"

        # Fallback: use first result with a cover
        for doc in docs:
            cover_id = doc.get("cover_i")
            if cover_id:
                return f"{OPEN_LIBRARY_COVERS}/id/{cover_id}-L.jpg"

        return None
    except Exception:
        return None


def fix_existing_covers():
    """Update cover_image_url for existing books that have random/broken covers."""
    db: Session = SessionLocal()
    try:
        books = db.query(models.Book).all()
        if not books:
            print("No books in database.")
            return

        print(f"Checking {len(books)} books for mismatched covers...")
        updated = 0
        skipped = 0

        for i, book in enumerate(books):
            if (i + 1) % 50 == 0:
                print(
                    f"  Progress: {i + 1}/{len(books)} (updated: {updated}, skipped: {skipped})"
                )

            # Check if current cover looks random (uses the old random ID pattern)
            current_url = book.cover_image_url or ""
            if "/b/id/" in current_url and current_url.endswith("-L.jpg"):
                # Likely a random ID from the old script — try to find a real one
                new_cover = find_cover_for_title(book.title, book.author)
                if new_cover:
                    book.cover_image_url = new_cover
                    updated += 1
                else:
                    skipped += 1

                # Rate limit: don't hammer the API
                time.sleep(0.25)
            else:
                skipped += 1

        db.commit()
        print(f"\nDone! Updated {updated} covers, skipped {skipped}.")
        print(f"Total books: {db.query(models.Book).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    num = 1000
    if len(sys.argv) > 1 and sys.argv[1] == "fix-covers":
        fix_existing_covers()
    elif len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_all_books()
    elif len(sys.argv) > 1 and sys.argv[1] == "reseed":
        seed_bulk(num_books=num, clear_first=True)
    elif len(sys.argv) > 1:
        num = int(sys.argv[1])
        seed_bulk(num_books=num)
    else:
        seed_bulk(num_books=num)
