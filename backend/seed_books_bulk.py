"""
Bulk seed script for generating 1000+ books efficiently.
Uses batch inserts and batched embedding generation to avoid slowing down the system.
"""
import sys
import os
import random
from datetime import datetime, timezone
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import SessionLocal, engine
from src import models
from src.services.ai_service import get_model, get_embedding

# Data pools for generating books
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna",
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
]

GENRES = [
    "Fiction", "Non-Fiction", "Mystery", "Thriller", "Romance", "Science Fiction",
    "Fantasy", "Horror", "Biography", "History", "Self-Help", "Business",
    "Technology", "Science", "Philosophy", "Psychology", "Poetry", "Drama",
    "Travel", "Cooking", "Health", "Art", "Music", "Sports", "Education",
    "Children", "Young Adult", "Crime", "Adventure", "Western",
]

PUBLISHERS = [
    "Penguin Random House", "HarperCollins", "Macmillan", "Simon & Schuster",
    "Hachette", "Scholastic", "Oxford University Press", "Cambridge University Press",
    "MIT Press", "Wiley", "Pearson", "McGraw Hill", "Cengage Learning",
    "Springer", "Elsevier", " Routledge", "Sage Publications", "W. W. Norton",
    "Houghton Mifflin", "Harper Perennial", "Anchor Books", "Vintage Books",
    "Ballantine Books", "Doubleday", "Knopf", "Scribner", "Little Brown",
    "Grand Central Publishing", "St. Martin's Press", "Tor Books",
]

FICTION_TITLES_PREFIX = [
    "The", "A", "Beyond", "Through", "Into", "Under", "Over", "Between",
    "Within", "Without", "Against", "Among", "Behind", "Before", "After",
    "Above", "Beneath", "Across", "Along", "Around",
]

FICTION_TITLES_NOUN = [
    "Shadow", "Light", "Dark", "Silence", "Echo", "Dream", "Storm", "Wind",
    "Fire", "Water", "Stone", "Mountain", "River", "Ocean", "Forest", "Garden",
    "Castle", "Tower", "Bridge", "Gate", "Path", "Journey", "Quest", "Secret",
    "Promise", "Memory", "Hope", "Fear", "Truth", "Lie", "Mirror", "Crystal",
    "Flame", "Frost", "Thunder", "Lightning", "Dawn", "Dusk", "Midnight", "Sunrise",
    "Moon", "Star", "Sky", "Cloud", "Rain", "Snow", "Mist", "Fog", "Shadow", "Whisper",
]

FICTION_TITLES_SUFFIX = [
    "of Destiny", "of Time", "of the Lost", "of the Forgotten", "of the Brave",
    "of the Damned", "of the Free", "of the Fallen", "of the Rising", "of the End",
    "of the Beginning", "of the Heart", "of the Soul", "of the Mind", "of the Spirit",
    "of the Night", "of the Day", "of the World", "of the Stars", "of the Sea",
    "Revealed", "Unleashed", "Unbroken", "Untold", "Unseen", "Unknown", "Undone",
    "Awakening", "Ascension", "Reckoning", "Resurgence", "Revelation", "Redemption",
    "Chronicles", "Legacy", "Prophecy", "Saga", "Tales", "Stories", "Legends",
]

NONFICTION_TITLES_PREFIX = [
    "Understanding", "Mastering", "Introduction to", "Guide to", "Handbook of",
    "Principles of", "Fundamentals of", "Essentials of", "Advanced", "Modern",
    "Complete Guide to", "Art of", "Science of", "History of", "Theory of",
    "Practice of", "Study of", "Exploring", "Discovering", "Rethinking",
]

NONFICTION_TITLES_TOPIC = [
    "Machine Learning", "Artificial Intelligence", "Data Science", "Python Programming",
    "Web Development", "Software Engineering", "Project Management", "Leadership",
    "Communication", "Negotiation", "Investing", "Finance", "Marketing", "Sales",
    "Entrepreneurship", "Innovation", "Creativity", "Productivity", "Mindfulness",
    "Meditation", "Nutrition", "Fitness", "Sleep", "Habits", "Decision Making",
    "Critical Thinking", "Problem Solving", "Design Thinking", "User Experience",
    "Digital Transformation", "Cloud Computing", "Cybersecurity", "Blockchain",
    "Quantum Computing", "Robotics", "Internet of Things", "Big Data", "Statistics",
    "Mathematics", "Physics", "Chemistry", "Biology", "Neuroscience", "Genetics",
    "Evolution", "Ecology", "Climate Change", "Astronomy", "Cosmology", "Philosophy",
]

DESCRIPTION_TEMPLATES_FICTION = [
    "A captivating {genre} novel that takes readers on an unforgettable journey through {theme}.",
    "In this gripping tale, {protagonist} must face {conflict} in a world where {setting}.",
    "A powerful story of {theme} that explores the depths of human nature and the bonds that connect us.",
    "Set against the backdrop of {setting}, this novel weaves together {element1} and {element2} in a masterful narrative.",
    "An epic {genre} that challenges everything we thought we knew about {theme}.",
    "When {protagonist} discovers {secret}, nothing will ever be the same in this thrilling {genre}.",
    "A beautifully crafted tale of {theme} that will leave readers breathless until the very last page.",
    "This {genre} masterpiece combines {element1} with {element2} to create an unforgettable reading experience.",
    "Through the eyes of {protagonist}, we explore the complexities of {theme} in a world on the brink of {conflict}.",
    "A haunting and beautiful {genre} that delves into the mysteries of {theme} and the power of {element1}.",
]

DESCRIPTION_TEMPLATES_NONFICTION = [
    "A comprehensive guide to {topic}, offering practical insights and strategies for {audience}.",
    "This groundbreaking book explores {topic} and reveals how it can transform your understanding of {field}.",
    "Drawing on years of research, the author presents a compelling case for {topic} and its impact on {field}.",
    "An essential read for anyone interested in {topic}, this book provides {benefit} through clear explanations and real-world examples.",
    "This authoritative work on {topic} combines {approach1} with {approach2} to deliver actionable knowledge.",
    "From the basics to advanced concepts, this book covers everything you need to know about {topic}.",
    "A thought-provoking exploration of {topic} that challenges conventional wisdom in {field}.",
    "Written for both beginners and experts, this book demystifies {topic} and shows how to apply it in {context}.",
    "The definitive resource on {topic}, featuring case studies, frameworks, and practical tools for {audience}.",
    "This book reveals the hidden connections between {topic} and {field}, offering a fresh perspective on both.",
]

THEMES = [
    "love and loss", "power and corruption", "identity and belonging",
    "good and evil", "freedom and oppression", "truth and deception",
    "courage and fear", "hope and despair", "life and death",
    "family and betrayal", "justice and injustice", "dreams and reality",
    "war and peace", "nature and civilization", "technology and humanity",
]

PROTAGONISTS = [
    "a young detective", "an unlikely hero", "a brilliant scientist",
    "a troubled artist", "a fearless journalist", "a seasoned explorer",
    "a gifted musician", "a determined student", "a retired soldier",
    "a mysterious stranger", "a devoted mother", "a ambitious entrepreneur",
]

CONFLICTS = [
    "unimaginable dangers", "their deepest fears", "a conspiracy that threatens everything",
    "the consequences of their past", "a force beyond comprehension", "an impossible choice",
]

SETTINGS = [
    "a distant future", "a small coastal town", "the bustling streets of a metropolis",
    "a war-torn landscape", "a magical realm", "the depths of the ocean",
    "the vastness of space", "a forgotten civilization", "the modern corporate world",
    "a secluded island",
]

SECRETS = [
    "a hidden truth", "an ancient artifact", "a forbidden knowledge",
    "a long-buried secret", "a shocking revelation", "a mysterious message",
]

ELEMENTS = [
    "mystery", "romance", "adventure", "suspense", "intrigue", "wonder",
    "danger", "passion", "betrayal", "redemption", "discovery", "transformation",
]

TOPICS = [
    "modern technology", "human behavior", "organizational success",
    "personal growth", "financial freedom", "scientific discovery",
    "creative expression", "effective leadership", "strategic thinking",
    "innovative design", "sustainable living", "digital innovation",
]

AUDIENCES = [
    "professionals", "students", "entrepreneurs", "leaders", "creatives",
    "researchers", "practitioners", "enthusiasts", "beginners", "experts",
]

FIELDS = [
    "modern business", "contemporary science", "everyday life",
    "the tech industry", "education", "healthcare", "the arts",
    "public policy", "social dynamics", "the global economy",
]

BENEFITS = [
    "proven strategies", "actionable frameworks", "step-by-step guidance",
    "real-world solutions", "practical techniques", "evidence-based methods",
]

APPROACHES = [
    "theoretical foundations", "practical applications", "case studies",
    "expert interviews", "data-driven analysis", "historical context",
]

CONTEXTS = [
    "your daily routine", "the workplace", "your personal projects",
    "team environments", "global markets", "local communities",
]


def generate_isbn():
    """Generate a random ISBN-13."""
    prefix = random.choice(["978", "979"])
    group = random.randint(0, 5)
    publisher = random.randint(10000, 99999)
    title = random.randint(100, 999)
    base = f"{prefix}{group}{publisher:05d}{title:03d}"
    # Calculate check digit
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base))
    check = (10 - (total % 10)) % 10
    return f"{base}{check}"


def generate_book(index):
    """Generate a single book dict."""
    genre = random.choice(GENRES)
    is_fiction = genre in [
        "Fiction", "Mystery", "Thriller", "Romance", "Science Fiction",
        "Fantasy", "Horror", "Poetry", "Drama", "Crime", "Adventure", "Western",
        "Children", "Young Adult",
    ]

    if is_fiction:
        title = f"{random.choice(FICTION_TITLES_PREFIX)} {random.choice(FICTION_TITLES_NOUN)} {random.choice(FICTION_TITLES_SUFFIX)}"
        template = random.choice(DESCRIPTION_TEMPLATES_FICTION)
        description = template.format(
            genre=genre.lower(),
            theme=random.choice(THEMES),
            protagonist=random.choice(PROTAGONISTS),
            conflict=random.choice(CONFLICTS),
            setting=random.choice(SETTINGS),
            secret=random.choice(SECRETS),
            element1=random.choice(ELEMENTS),
            element2=random.choice(ELEMENTS),
        )
    else:
        title = f"{random.choice(NONFICTION_TITLES_PREFIX)} {random.choice(NONFICTION_TITLES_TOPIC)}"
        template = random.choice(DESCRIPTION_TEMPLATES_NONFICTION)
        description = template.format(
            topic=random.choice(TOPICS),
            audience=random.choice(AUDIENCES),
            field=random.choice(FIELDS),
            benefit=random.choice(BENEFITS),
            approach1=random.choice(APPROACHES),
            approach2=random.choice(APPROACHES),
            context=random.choice(CONTEXTS),
        )

    author = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    publisher = random.choice(PUBLISHERS)
    price = round(random.uniform(5.99, 89.99), 2)
    stock = random.randint(5, 200)
    rating = round(random.uniform(3.0, 5.0), 2)
    pub_year = random.randint(1990, 2025)
    pub_month = random.randint(1, 12)
    pub_day = random.randint(1, 28)

    return {
        "title": title,
        "author": author,
        "genre": genre,
        "description": description,
        "isbn": generate_isbn(),
        "publisher": publisher,
        "publication_date": datetime(pub_year, pub_month, pub_day, tzinfo=timezone.utc),
        "price": Decimal(str(price)),
        "stock_count": stock,
        "average_rating": Decimal(str(rating)),
        "cover_image_url": f"https://covers.openlibrary.org/b/id/{random.randint(1, 12000000)}-L.jpg",
    }


def seed_bulk(num_books=1000, batch_size=100):
    """
    Seed books in batches for performance.
    Generates embeddings in batches using the sentence transformer's batch encoding.
    """
    db: Session = SessionLocal()
    try:
        existing = db.query(models.Book).count()
        print(f"Database currently has {existing} books.")

        # Calculate how many more books we need
        remaining = num_books - existing
        if remaining <= 0:
            print(f"Database already has {existing} books (target: {num_books}). Skipping seed.")
            return

        print(f"Generating {remaining} additional books to reach target of {num_books}...")
        all_books_data = [generate_book(i) for i in range(remaining)]

        print("Inserting books in batches...")
        for batch_start in range(0, remaining, batch_size):
            batch_end = min(batch_start + batch_size, remaining)
            batch_data = all_books_data[batch_start:batch_end]

            # Bulk insert books
            books = [models.Book(**data) for data in batch_data]
            db.bulk_save_objects(books, return_defaults=True)
            db.commit()

            print(f"  Inserted books {existing + batch_start + 1}-{existing + batch_end}")

        print("Generating embeddings in batches...")
        model = get_model()

        # Get all books without embeddings
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

            # Batch encode all texts at once (much faster than one-by-one)
            texts = [
                f"{b.title} {b.author} {b.genre} {b.description or ''}"
                for b in batch_books
            ]
            vectors = model.encode(texts).tolist()

            # Create embedding records
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

            print(f"  Generated embeddings for books {batch_start + 1}-{batch_end}/{total_books}")

        # Create indexes for performance
        print("Creating database indexes for performance...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_books_price ON books(price)"))
        db.commit()

        print(f"\nSuccessfully seeded {remaining} additional books!")
        print(f"Total books in database: {db.query(models.Book).count()}")
        print("Database indexes created for optimal query performance.")

    finally:
        db.close()


if __name__ == "__main__":
    num = 1000
    if len(sys.argv) > 1:
        num = int(sys.argv[1])
    seed_bulk(num_books=num)
