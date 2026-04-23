# Technical Report: AI-Enhanced Online Bookshop

**Project:** AI-Enhanced Online Bookshop  
**Author:** Nwamgbowo Bruno Nwachukwu (VUG/CSC/22/7793)  
**Institution:** Veritas University Abuja — Dept. of Computer and Information Technology  
**Date:** April 2026  
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Backend Implementation](#3-backend-implementation)
4. [Frontend Implementation](#4-frontend-implementation)
5. [Database Design](#5-database-design)
6. [AI & Machine Learning Features](#6-ai--machine-learning-features)
7. [Authentication & Security](#7-authentication--security)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment & DevOps](#9-deployment--devops)
10. [Project Structure](#10-project-structure)
11. [Key Design Decisions](#11-key-design-decisions)

---

## 1. Executive Summary

This project is a **prototype-level, full-stack web application** that demonstrates the integration of Artificial Intelligence into a traditional e-commerce bookshop platform. Unlike conventional online bookstores that rely solely on keyword-based search and static catalogs, this system implements three core AI-driven features:

- **Semantic Search:** Users can search using natural language (e.g., *"books about African history for students"*), and the system returns results based on conceptual similarity rather than exact keyword matching.
- **Personalized Recommendations:** A content-based recommendation engine analyzes user browsing history to suggest relevant books using vector embeddings and cosine similarity.
- **Conversational AI Chatbot:** A Retrieval-Augmented Generation (RAG) pipeline chatbot assists users with book discovery and navigation by retrieving relevant catalog items and generating contextual responses.

The platform supports standard e-commerce functionality including user registration, authentication, book catalog browsing, shopping cart management, and simulated checkout. An administrative dashboard is provided for content management and system analytics.

---

## 2. System Architecture

The application follows a **client-server architecture** with a clear separation between the frontend and backend, communicating via RESTful APIs over HTTP.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│              React 19 + TypeScript + Tailwind CSS               │
│   [ Catalog ] [ Search ] [ Cart ] [ Chatbot ] [ Admin UI ]      │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTPS / REST API (Axios)
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Auth    │  │ Books /   │  │  Cart /  │  │  AI Services  │  │
│  │  Router  │  │ Catalog   │  │  Orders  │  │               │  │
│  │          │  │  Router   │  │  Router  │  │ ┌───────────┐ │  │
│  └──────────┘  └───────────┘  └──────────┘  │ │ Semantic  │ │  │
│                                              │ │  Search   │ │  │
│  ┌──────────────────────────────────────┐    │ └───────────┘ │  │
│  │           Services Layer             │    │ ┌───────────┐ │  │
│  │  AuthService | BookService |          │    │ │  Reco-    │ │  │
│  │  CartService | RecoService |          │    │ │  mmender  │ │  │
│  │  SearchService | ChatService          │    │ └───────────┘ │  │
│  └──────────────────────────────────────┘    │ ┌───────────┐ │  │
│                                              │ │  Chatbot  │ │  │
└────────────────────┬─────────────────────────│ │  (RAG)    │ │  │
                     │                         │ └───────────┘ │  │
          ┌──────────▼────────────┐            └───────────────┘  │
          │     PostgreSQL DB     │                    │           │
          │  + pgvector extension │◄───────────────────┘           │
          │                       │                                │
          │  Users | Books |       │     ┌──────────────────────┐  │
          │  Orders | CartItems |  │     │  External AI APIs    │  │
          │  BookEmbeddings       │     │  OpenAI / HuggingFace│  │
          └───────────────────────┘     └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4 | Modern component-based UI, fast development build tool, utility-first responsive styling |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | High-performance async Python framework with automatic OpenAPI/Swagger documentation generation |
| **Database** | PostgreSQL 15+ with `pgvector` extension | Robust relational database with native vector storage and similarity search capabilities |
| **ORM** | SQLAlchemy 2.0, Alembic | Clean declarative models and versioned database migrations |
| **AI/ML** | `sentence-transformers` (all-MiniLM-L6-v2) | Open-source embedding model for generating 384-dimensional text vectors locally without API costs |
| **Authentication** | JWT (python-jose), bcrypt | Stateless token-based authentication with secure password hashing |
| **Testing** | pytest, FastAPI TestClient | Comprehensive unit and integration testing with mocked dependencies |
| **Containerization** | Docker, Docker Compose | Standardized local development environment with database and admin tools |

---

## 3. Backend Implementation

The backend is built with **FastAPI** and organized into a modular structure following the PRD's maintainability requirements. The entry point is `src/main.py`, which initializes the application, configures CORS middleware, and mounts all API routers.

### 3.1 Application Entry Point (`src/main.py`)

```python
app = FastAPI(title="AI-Enhanced Online Bookshop", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(ai.router)
app.include_router(cart.router)
app.include_router(orders.router)
```

The application automatically creates database tables on startup using `models.Base.metadata.create_all(bind=engine)`. CORS is configured permissively (`allow_origins=["*"]`) for local development, allowing the frontend (running on a different port) to communicate with the API.

### 3.2 Database Connection (`src/database.py`)

Database connectivity uses SQLAlchemy's classic pattern:
- **`create_engine`**: Establishes the connection pool to PostgreSQL.
- **`sessionmaker`**: Creates a factory for database sessions with `autocommit=False` and `autoflush=False` to ensure explicit transaction control.
- **`get_db()`**: A dependency-injectable generator that yields a session and guarantees closure via `finally`, preventing connection leaks.

The `DATABASE_URL` is loaded from environment variables with a sensible localhost fallback for development.

### 3.3 Data Models (`src/models.py`)

The ORM layer defines seven core entities using SQLAlchemy's declarative base:

#### **User Model**
Stores account credentials and role information. The `role` field is an enumerated type (`user` | `admin`). A key design decision is implemented in the auth router: the **first registered user automatically receives the `admin` role**, simplifying initial setup without manual database seeding.

#### **Book Model**
Represents the product catalog with fields for metadata (title, author, genre, ISBN, publisher), pricing (`DECIMAL(10, 2)` to prevent floating-point errors), inventory (`stock_count`), and ratings. Relationships connect to embeddings, order items, cart items, and browsing history.

#### **BookEmbedding Model**
This is the cornerstone of the AI features. It stores a `Vector(384)` — the fixed output dimension of the `all-MiniLM-L6-v2` sentence transformer model. Each book has a one-to-one relationship with its embedding vector, which is pre-computed on ingestion.

#### **Order & OrderItem Models**
Implements a standard e-commerce order pattern. `Order` stores the transaction header (user, total price, status), while `OrderItem` stores line items with snapshots of the unit price at purchase time to maintain historical accuracy even if book prices change later.

#### **CartItem Model**
A simple association table linking users to books with a quantity field. Cart items are ephemeral and are deleted upon successful checkout.

#### **UserBrowsingHistory Model**
Tracks user interactions (`view`, `cart_add`, `purchase`) with timestamps. This event log fuels the recommendation engine by identifying user interests.

### 3.4 API Routers

#### **Authentication Router (`src/routers/auth.py`)**
- **`POST /auth/register`**: Validates uniqueness of username/email. Hashes passwords with bcrypt. Auto-assigns `admin` role to the first user.
- **`POST /auth/login`**: Accepts `OAuth2PasswordRequestForm` (username/password), verifies credentials, and returns a JWT access token with a 30-minute expiration.
- **`GET /auth/me`**: Returns the currently authenticated user's profile.

#### **Books Router (`src/routers/books.py`)**
- **`GET /books/`**: Paginated catalog listing with powerful filtering (keyword search across title/author/description, genre filter, price range) and sorting (price, rating, popularity, newest). This serves as the fallback keyword search when semantic search is unavailable.
- **`GET /books/{id}`**: Retrieves detailed information for a single book.
- **`POST /books/`**: Admin-only endpoint for creating new book listings.
- **`PUT /books/{id}`**: Admin-only endpoint for partial updates using Pydantic's `exclude_unset=True`.
- **`DELETE /books/{id}`**: Admin-only deletion with a `204 No Content` response.

#### **Cart Router (`src/routers/cart.py`)**
- **`GET /cart/`**: Returns the authenticated user's cart items, eager-loading associated book data.
- **`POST /cart/`**: Adds a book to the cart. If the book already exists in the cart, it increments the quantity rather than creating duplicate rows.
- **`PUT /cart/{item_id}`**: Updates the quantity of a specific cart item.
- **`DELETE /cart/{item_id}`**: Removes an item from the cart.

#### **Orders Router (`src/routers/orders.py`)**
- **`GET /orders/`**: Returns the order history for the authenticated user.
- **`POST /orders/checkout`**: The simulated checkout process. It calculates the total price from cart items, creates an `Order` record and corresponding `OrderItem` records, logs a `purchase` event in browsing history, and clears the cart.
- **`GET /orders/all`**: Admin-only endpoint to view all platform orders.

#### **AI Router (`src/routers/ai.py`)**
- **`GET /ai/search`**: Accepts a natural language `query` parameter and delegates to `semantic_search()`.
- **`GET /ai/recommendations`**: Returns personalized book recommendations for the authenticated user.
- **`POST /ai/chat`**: Processes user messages through the chatbot RAG pipeline.
- **`POST /ai/reindex`**: Admin-only endpoint that iterates through all books and regenerates their embedding vectors — useful when the embedding model changes or when new books are added outside the normal creation flow.

### 3.5 Services Layer (`src/services/ai_service.py`)

The AI logic is centralized in a dedicated service module to keep routers thin and testable.

#### **Embedding Model (`all-MiniLM-L6-v2`)**
The system uses the open-source `sentence-transformers` library with the `all-MiniLM-L6-v2` model. This model was chosen because:
- It produces **384-dimensional dense vectors**, balancing quality and storage efficiency.
- It runs entirely **locally** with no API costs or external dependencies.
- It has strong performance on semantic similarity tasks despite its small size.

The model is loaded lazily via a global singleton pattern (`_model = None`) to avoid unnecessary overhead during application startup or in test environments.

#### **`generate_book_embedding()`**
Concatenates a book's title, author, genre, and description into a single text string, encodes it into a vector, and persists it to the `book_embeddings` table. If an embedding already exists for the book, it updates the vector in place.

#### **`semantic_search()`**
1. Encodes the user's natural language query into a vector.
2. Uses `pgvector`'s `cosine_distance` operator to find the nearest neighbors in the `book_embeddings` table.
3. Returns the corresponding `Book` objects ordered by similarity (ascending distance).

#### **`get_recommendations()`**
1. Fetches the user's 3 most recent browsing history events.
2. Retrieves the embedding vectors for those books.
3. Computes an **average vector** representing the user's current interests.
4. Queries for the nearest neighbor books using cosine distance, explicitly excluding books the user has already interacted with.
5. **Fallback:** If the user has no browsing history, returns the highest-rated books on the platform.

#### **`process_chat()`**
Implements a simplified RAG (Retrieval-Augmented Generation) pipeline:
1. **Retrieval:** Runs `semantic_search()` with the user's query to find the top 3 relevant books.
2. **Generation:** Constructs a friendly response string that references the retrieved book titles and authors. In a production system, this step would pass the retrieved context to a large language model (LLM) like GPT-4; for this prototype, the "generation" is a templated string to avoid external API costs and dependencies.

### 3.6 Security Utilities (`src/utils/security.py`)

- **`get_password_hash()` / `verify_password()`**: Uses `passlib` with the `bcrypt_sha256` scheme. Passwords are pre-hashed with SHA-256 before bcrypt to bypass the 72-byte input limit of raw bcrypt.
- **`create_access_token()`**: Generates JWTs with configurable expiration (default 30 minutes). The payload includes the username (`sub`) and role.
- **`create_refresh_token()`**: Generates longer-lived tokens (7 days) for future session refresh implementation.

### 3.7 Dependency Injection (`src/utils/dependencies.py`)

FastAPI's dependency injection system is leveraged for clean authentication enforcement:
- **`get_current_user`**: Extracts the Bearer token from the `Authorization` header, decodes the JWT, and queries the database for the user. Returns `401 Unauthorized` on failure.
- **`get_current_active_user`**: Wraps `get_current_user` and checks the `is_active` flag.
- **`get_current_admin_user`**: Wraps `get_current_active_user` and enforces `role == admin`, returning `403 Forbidden` for non-admins.

These dependencies are declaratively applied to protected endpoints (e.g., `current_admin: models.User = Depends(get_current_admin_user)`), ensuring consistent RBAC across the API.

---

## 4. Frontend Implementation

The frontend is a **Single Page Application (SPA)** built with modern tooling and best practices.

### 4.1 Build Tool & Configuration

**Vite** is used as the build tool instead of Create React App for significantly faster cold starts and Hot Module Replacement (HMR). The configuration (`vite.config.ts`) is minimal, loading only the React plugin and the Tailwind CSS Vite plugin.

### 4.2 Routing (`src/App.tsx`)

Client-side routing is handled by **React Router v7** (using the v6-compatible API). Routes are nested under a shared `Layout` component:

| Route | Component | Access Control |
|-------|-----------|----------------|
| `/` | `Home` | Public |
| `/book/:id` | `BookDetail` | Public |
| `/cart` | `Cart` | Public (UI visible, checkout requires auth) |
| `/orders` | `Orders` | Authenticated only (`<Navigate to="/login" />`) |
| `/admin` | `AdminDashboard` | Admin only (`<Navigate to="/" />`) |
| `/login` | `Login` | Redirects to `/` if already authenticated |
| `/register` | `Register` | Redirects to `/` if already authenticated |

### 4.3 State Management

State is managed using **React Context API** rather than Redux, which is sufficient for the application's scale and avoids unnecessary boilerplate.

#### **AuthContext (`src/context/AuthContext.tsx`)**
- Persists the JWT token in `localStorage`.
- On mount (or token change), validates the token by calling `GET /auth/me`.
- Provides `login()`, `logout()`, and the current `user` object to all children.
- Exposes a `loading` state to prevent flash-of-unauthenticated-content during validation.

#### **CartContext (`src/context/CartContext.tsx`)**
- Synchronizes the frontend cart state with the backend database.
- Automatically clears the local cart when the user logs out.
- Provides `addToCart()`, `removeFromCart()`, `updateQuantity()`, and `refreshCart()` methods that mirror the backend cart API.

### 4.4 API Client (`src/api/index.ts`)

A pre-configured Axios instance is used for all HTTP communication:
- **`baseURL`**: Points to `http://localhost:8000` for local development.
- **Request Interceptor:** Automatically attaches the JWT token from `localStorage` to every outgoing request's `Authorization` header as a Bearer token. This ensures authenticated endpoints receive credentials without manual header management in every component.

### 4.5 Pages & Components

#### **Layout Component (`src/components/Layout.tsx`)**
The root layout provides the application's chrome: a responsive navigation header, a main content area (rendering `<Outlet />` from React Router), and a footer. It integrates `AuthContext` and `CartContext` to display dynamic UI elements like the authenticated user's username, admin dashboard link, and a live cart item count badge. The `Chatbot` component is mounted globally here so it appears on all pages.

#### **Home Page (`src/pages/Home.tsx`)**
The landing page features:
- A **hero section** with a prominent search bar supporting two modes: **AI Semantic** (default) and **Keyword**.
- A **recommendations section** displaying up to 6 personalized books fetched from `/ai/recommendations`.
- A **catalog grid** showing all books with cover images, ratings, genres, and quick-add-to-cart buttons.
- Search results dynamically replace the catalog grid when a query is submitted.

#### **Book Detail Page (`src/pages/BookDetail.tsx`)**
Displays comprehensive book information in a two-column layout: a large cover image on the left, and metadata (title, author, rating, price, description, publisher, publication date) with an "Add to Cart" CTA on the right.

#### **Cart Page (`src/pages/Cart.tsx`)**
Implements a full shopping cart experience:
- Lists cart items with cover thumbnails, quantity steppers (+/-), and remove buttons.
- Calculates and displays subtotal, shipping (free), tax, and total.
- A "Simulate Checkout" button that calls `POST /orders/checkout` and renders a success confirmation screen upon completion.

#### **Orders Page (`src/pages/Orders.tsx`)**
Displays the authenticated user's order history. Each order is presented as a card with a header (date, total, status, order number) and a list of purchased items with links back to the book detail pages.

#### **Admin Dashboard (`src/pages/AdminDashboard.tsx`)**
A protected interface providing:
- **Analytics cards:** Total Books, Total Orders, and Total Revenue (computed by summing order totals client-side).
- **Book Management table:** Lists all books with delete actions.
- **Add Book form:** A sticky sidebar form for creating new book listings.
- **Reindex button:** Triggers `POST /ai/reindex` to regenerate all embedding vectors.

#### **Chatbot Component (`src/components/Chatbot.tsx`)**
A floating-action-button (FAB) widget that expands into a chat interface:
- **Collapsed state:** A rounded button fixed to the bottom-right corner.
- **Expanded state:** A card with a header (branded "AI Assistant"), a scrollable message history, and an input field.
- **Message bubbles:** Differentiated styling for user (indigo, right-aligned) and bot (white, left-aligned) messages.
- **Loading state:** Animated bouncing dots while waiting for the backend response.
- **Error handling:** Displays a friendly fallback message if the API call fails.

#### **Login & Register Pages**
Clean, centered forms with validation error display, loading states on submission buttons, and links to toggle between the two views. Login submits credentials as `application/x-www-form-urlencoded` to satisfy FastAPI's `OAuth2PasswordRequestForm`.

### 4.6 Styling (Tailwind CSS v4)

The entire UI is styled with **Tailwind CSS v4** using utility classes. Key design patterns observed:
- **Color palette:** Indigo as the primary brand color, slate for neutrals, rose for destructive actions, emerald for success states.
- **Spacing:** Consistent use of the 4px grid scale (e.g., `p-4`, `gap-6`, `mb-8`).
- **Typography:** Bold, tight tracking for headings (`font-extrabold`, `tracking-tight`) with readable line-heights for body text.
- **Effects:** Subtle shadows (`shadow-sm`, `shadow-xl`), rounded corners (`rounded-2xl`, `rounded-3xl`), and backdrop blur on the sticky header for a modern glassmorphism feel.
- **Responsive design:** Mobile-first grids (`grid-cols-1` → `sm:grid-cols-2` → `lg:grid-cols-3` → `xl:grid-cols-4` / `6`).
- **Interactions:** Hover states (`hover:shadow-xl`, `hover:-translate-y-1`), active scaling (`active:scale-95`), and smooth transitions (`transition-all`, `duration-300`).

---

## 5. Database Design

The database is **PostgreSQL** with the **`pgvector` extension** enabled, which adds a native `vector` data type and similarity search operators.

### 5.1 Schema Overview

| Table | Purpose | Key Constraints |
|-------|---------|-----------------|
| `users` | Account storage | `UNIQUE(username)`, `UNIQUE(email)`, `role` enum |
| `books` | Product catalog | `UNIQUE(isbn)`, `DECIMAL` price, `NOT NULL` title/author/price |
| `book_embeddings` | AI vectors | `Vector(384)`, `UNIQUE(book_id)`, FK to `books` |
| `orders` | Purchase transactions | FK to `users`, `status` enum, `DECIMAL` total_price |
| `order_items` | Line items | FK to `orders` and `books`, `DECIMAL` unit_price |
| `cart_items` | Shopping cart | FK to `users` and `books` |
| `user_browsing_history` | Interaction log | FK to `users` and `books`, `event_type` enum |

### 5.2 Vector Storage with pgvector

The `BookEmbedding.embedding` column is defined as `Vector(384)`. `pgvector` enables high-performance approximate and exact nearest-neighbor searches directly in SQL. The application uses the exact `cosine_distance` operator (`<=>`) for precise results at the prototype scale:

```sql
SELECT * FROM book_embeddings
ORDER BY embedding <=> query_vector
LIMIT 5;
```

This query is generated by SQLAlchemy in `ai_service.py` via:
```python
.order_by(models.BookEmbedding.embedding.cosine_distance(query_vector))
```

### 5.3 Data Integrity

- **Foreign Keys:** All relationships use `ForeignKey` constraints with `nullable=False` where appropriate.
- **Enumerations:** Python `enum.Enum` classes (`UserRole`, `OrderStatus`, `HistoryEventType`) are mapped to SQL `ENUM` types to restrict values at the database level.
- **Timestamps:** `created_at` and `updated_at` fields use `datetime.now(timezone.utc)` defaults. `updated_at` includes an `onupdate` trigger for automatic modification tracking.
- **Financial Precision:** All monetary values (`price`, `total_price`, `unit_price`) use SQL `DECIMAL` (mapped to Python `Decimal`) to prevent floating-point rounding errors.

### 5.4 Migrations (Alembic)

Database schema changes are managed by **Alembic**. The `alembic.ini` file configures the migration script location and database URL. This allows the schema to be versioned, shared across environments, and rolled back if necessary.

---

## 6. AI & Machine Learning Features

### 6.1 Semantic Search

**How it works:**
1. User submits a natural language query (e.g., *"beginner python programming"*).
2. The query is encoded into a 384-dimensional vector by the `all-MiniLM-L6-v2` model.
3. The backend executes a cosine distance query against the `book_embeddings` table.
4. The top-N most similar books are returned and rendered in the catalog grid.

**Graceful Degradation:** The frontend offers a toggle between "AI Semantic" and "Keyword" search modes. If the AI service is unavailable or the user prefers exact matching, they can switch to traditional `ilike` SQL queries on the `books` table.

### 6.2 Recommendation Engine

**Algorithm:** Content-Based Filtering using Vector Similarity.

1. **Interest Vector Construction:** The system retrieves the user's last 3 interactions from `user_browsing_history`. It fetches the embedding vectors for those books and computes their arithmetic mean, creating a single "interest vector."
2. **Neighbor Search:** This interest vector is used as the query in a cosine distance search against all `book_embeddings`.
3. **Exclusion Filter:** Books already present in the user's recent history are filtered out (`NOT IN recent_book_ids`) to ensure novelty.
4. **Fallback:** For new users with no history, the system defaults to a popularity-based strategy (highest `average_rating`).

This approach is lightweight, explainable, and requires no training data beyond the user's own session history.

### 6.3 Chatbot (RAG Pipeline)

**Architecture:**
- **Retrieval:** The user's message is treated as a semantic search query. `semantic_search()` finds the 3 most relevant books.
- **Augmentation:** The titles and authors of these books are injected into a pre-defined response template.
- **Generation:** The final response is returned to the frontend.

**Current Limitation:** The "generation" step uses a templated string rather than a true LLM. This is a deliberate prototype decision to avoid external API costs and dependencies. The architecture is designed to easily swap in an LLM (e.g., OpenAI GPT, Mistral via Ollama) by replacing the string formatting logic in `process_chat()` with an actual API call that passes the retrieved context as a system prompt.

---

## 7. Authentication & Security

### 7.1 Password Security
Passwords are never stored in plaintext. The system uses:
- **bcrypt with SHA-256 pre-hashing:** Handles passwords of any length securely.
- **12+ salt rounds:** Configured via `passlib`'s `bcrypt_sha256` scheme.

### 7.2 JWT Authentication
- **Access Tokens:** Short-lived (30 minutes), signed with `HS256` and a configurable `SECRET_KEY`.
- **Token Payload:** Contains `sub` (username) and `role` (for RBAC).
- **Refresh Tokens:** A 7-day refresh token mechanism is implemented in `security.py` and can be wired into the frontend for session persistence.

### 7.3 Role-Based Access Control (RBAC)
- **Public routes:** `/books/`, `/auth/register`, `/auth/login`.
- **Authenticated routes:** `/cart/`, `/orders/`, `/ai/recommendations`, `/ai/chat`.
- **Admin routes:** `POST /books/`, `PUT /books/{id}`, `DELETE /books/{id}`, `GET /orders/all`, `POST /ai/reindex`.

Unauthorized access to protected endpoints returns standard HTTP status codes: `401 Unauthorized` (missing/invalid token) and `403 Forbidden` (valid token, insufficient privileges).

### 7.4 Input Validation
All incoming data is validated by **Pydantic v2** schemas. This prevents malformed data from reaching the database and provides automatic, detailed `422 Unprocessable Entity` error responses.

### 7.5 CORS
CORS middleware is enabled for development. In production, `allow_origins` should be restricted to the specific frontend domain(s).

---

## 8. Testing Strategy

The backend includes a comprehensive test suite using **pytest** and **FastAPI's TestClient**.

### 8.1 Testing Philosophy
To ensure tests are fast and isolated, the suite uses **mocked database sessions** rather than a real PostgreSQL instance. The `conftest.py` file overrides the `get_db` dependency globally to inject a `MagicMock` session.

### 8.2 Fixtures (`tests/conftest.py`)
- **`mock_db`**: A `MagicMock` instance wired into the FastAPI dependency overrides.
- **`client`**: A `TestClient` instance that uses the mocked DB.
- **`make_user()`, `make_book()`**: Factory functions that construct in-memory ORM objects with sensible defaults, simulating the state of database records.
- **`auth_header()`**: Helper to generate valid `Authorization: Bearer <token>` headers for authenticated requests.

### 8.3 Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_auth.py` | Registration (role assignment, duplicates), login (success, wrong password, inactive user), `/me` (authenticated, unauthenticated, inactive) |
| `test_books.py` | CRUD operations, filtering, sorting, pagination, admin protections |
| `test_cart.py` | Add to cart (new/existing items), update quantity, remove item, auth requirements |
| `test_orders.py` | Checkout flow (empty cart, success), order history, admin view-all |
| `test_ai.py` | Semantic search (results, empty, limit validation), recommendations (auth, empty), chat (response shape, auth, missing query), reindex (admin only, empty catalog) |
| `test_ai_service.py` | Unit tests for embedding generation, vector math, and cosine similarity logic |

Tests use `unittest.mock.patch` to isolate the AI service layer, ensuring that heavy model loading does not slow down the test suite.

---

## 9. Deployment & DevOps

### 9.1 Docker Compose (`compose.yml`)
The project includes a Docker Compose configuration for local development that provisions:
- **`db` service**: `ankane/pgvector:latest` (PostgreSQL with pgvector pre-installed).
  - Port: `5433` (mapped to avoid conflicts with local PostgreSQL on 5432).
  - Credentials and database name are set via environment variables.
  - Uses a named Docker volume (`bruno_pgdata`) for data persistence across container restarts.
- **`pgadmin` service**: `dpage/pgadmin4` for visual database administration.
  - Port: `5050`.
  - Connects to the `db` service via Docker's internal networking.

### 9.2 Running the Stack Locally
```bash
# 1. Start the database
docker-compose up -d

# 2. Install backend dependencies and run
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn src.main:app --reload --port 8000

# 3. Install frontend dependencies and run
cd frontend
pnpm install
pnpm dev
```

### 9.3 Environment Configuration
Sensitive configuration (database URLs, JWT secrets) is managed via `.env` files and `os.getenv()` fallbacks. The `python-dotenv` library is used in `database.py` to load variables automatically.

---

## 10. Project Structure

```
BRUNO/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── src/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── database.py       # SQLAlchemy engine & session
│   │   ├── models.py         # ORM entity definitions
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── auth.py       # JWT authentication endpoints
│   │   │   ├── books.py      # Book catalog CRUD & search
│   │   │   ├── cart.py       # Shopping cart management
│   │   │   ├── orders.py     # Checkout & order history
│   │   │   └── ai.py         # Semantic search, recommendations, chatbot
│   │   ├── services/
│   │   │   └── ai_service.py # Embedding, search, recommendation, chat logic
│   │   └── utils/
│   │       ├── security.py   # Password hashing & JWT creation
│   │       └── dependencies.py # Auth dependency injection
│   ├── tests/                # pytest test suite
│   ├── requirements.txt      # Python dependencies
│   └── alembic.ini           # Alembic configuration
├── frontend/
│   ├── src/
│   │   ├── main.tsx          # React DOM root render
│   │   ├── App.tsx           # Router configuration
│   │   ├── api/
│   │   │   └── index.ts      # Axios instance with auth interceptor
│   │   ├── context/
│   │   │   ├── AuthContext.tsx # Global auth state
│   │   │   └── CartContext.tsx # Global cart state
│   │   ├── components/
│   │   │   ├── Layout.tsx    # Page shell (nav, footer, chatbot)
│   │   │   └── Chatbot.tsx   # AI assistant widget
│   │   └── pages/
│   │       ├── Home.tsx      # Catalog, search, recommendations
│   │       ├── BookDetail.tsx # Individual book view
│   │       ├── Cart.tsx      # Shopping cart & checkout
│   │       ├── Orders.tsx    # Order history
│   │       ├── Login.tsx     # Authentication
│   │       ├── Register.tsx  # Account creation
│   │       └── AdminDashboard.tsx # Admin analytics & management
│   ├── package.json          # Node.js dependencies
│   └── vite.config.ts        # Vite build configuration
├── compose.yml               # Docker Compose dev environment
├── PRD.md                    # Product Requirements Document
└── proposal.md               # Academic research proposal
```

---

## 11. Key Design Decisions

### 11.1 FastAPI over Node.js/Express
FastAPI was chosen because the AI/ML stack (embeddings, vector search) is natively Python. Using a single language for the entire backend eliminates the complexity of inter-service HTTP calls and simplifies deployment.

### 11.2 pgvector over ChromaDB
While ChromaDB is a popular dedicated vector store, `pgvector` was selected because it allows relational and vector data to coexist in a single database. This simplifies transactions (e.g., creating a book and its embedding atomically) and reduces infrastructure overhead.

### 11.3 Open-Source Embeddings over OpenAI API
The `all-MiniLM-L6-v2` model from `sentence-transformers` runs entirely offline. This eliminates API latency, cost concerns, and external dependencies—critical for an academic prototype with potential token/credit constraints.

### 11.4 Mocked LLM Generation
The chatbot uses a templated response rather than a true LLM API call. This ensures the prototype is fully functional without requiring paid API keys or GPU resources, while the RAG retrieval architecture remains production-ready for future LLM integration.

### 11.5 First-User Admin Auto-Assignment
To streamline deployment, the first user to register is automatically granted the `admin` role. This removes the need for manual database seeding scripts while still maintaining secure RBAC for all subsequent users.

### 11.6 Simulated Checkout
Real payment processing (Stripe, PayPal) is explicitly out of scope per the academic nature of the project. The checkout flow creates valid `Order` and `OrderItem` records and clears the cart, providing a complete e-commerce simulation.

---

## 12. Future Enhancements

While the current prototype successfully demonstrates all core requirements, the following enhancements would be natural next steps:

1. **True LLM Integration:** Replace the chatbot's templated responses with calls to an open-source LLM (e.g., Llama 3 via Ollama) or a commercial API (OpenAI GPT-4o) for more natural, context-aware conversations.
2. **Collaborative Filtering:** Hybridize the recommendation engine with collaborative filtering (e.g., matrix factorization) to leverage aggregate user behavior patterns, not just individual history.
3. **Real-Time Features:** Implement WebSockets for real-time cart updates across devices or live admin analytics dashboards.
4. **Image Uploads:** Replace cover image URLs with a proper file upload service (e.g., AWS S3, Cloudinary) with image optimization.
5. **Email Notifications:** Integrate a transactional email service (SendGrid, Mailgun) for order confirmations and password resets.
6. **Production Deployment:** Containerize the backend with a production ASGI server (Gunicorn + Uvicorn workers), serve the frontend via a CDN (Vercel/Netlify), and use a managed PostgreSQL provider (AWS RDS, Supabase) with pgvector support.

---

*End of Technical Report*
