# Product Requirements Document (PRD)

## AI-Enhanced Online Bookshop

**Project Title:** Design and Implementation of an AI-Enhanced Online Bookshop
**Author:** Nwamgbowo Bruno Nwachukwu (VUG/CSC/22/7793)
**Institution:** Veritas University Abuja — Dept. of Computer and Information Technology
**Version:** 1.0
**Date:** March 2026
**Status:** In Development

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Goals & Objectives](#2-goals--objectives)
3. [User Roles & Personas](#3-user-roles--personas)
4. [Tech Stack & Architecture](#4-tech-stack--architecture)
5. [Functional Requirements](#5-functional-requirements)
   - 5.1 Authentication & User Management
   - 5.2 Book Catalog & Browsing
   - 5.3 AI Semantic Search
   - 5.4 Recommendation Engine
   - 5.5 AI Chatbot Assistant
   - 5.6 Cart & Checkout (Simulated)
   - 5.7 Admin Dashboard
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [System Architecture Overview](#7-system-architecture-overview)
8. [Data Model Overview](#8-data-model-overview)
9. [Out of Scope](#9-out-of-scope)
10. [Constraints & Assumptions](#10-constraints--assumptions)
11. [Ethical & Compliance Requirements](#11-ethical--compliance-requirements)

---

## 1. Product Overview

The AI-Enhanced Online Bookshop is a web-based platform that combines standard e-commerce book purchasing functionality with intelligent, AI-driven features. Unlike traditional bookshops that rely on rigid keyword searches and static interfaces, this platform leverages:

- **Semantic search** — allowing users to query the catalog using natural language (e.g., _"novels about African history for students"_)
- **Personalized recommendations** — books surfaced based on browsing history, preferences, and content similarity
- **Conversational AI chatbot** — a virtual assistant that guides users, answers queries, and recommends books in real-time

The platform targets students, researchers, and general readers, with a secondary administrative interface for content and user management. The system is scoped as a **prototype-level academic project** that demonstrates the real-world application of AI in e-commerce.

---

## 2. Goals & Objectives

### Primary Goal

Design and implement a fully functional AI-powered online bookshop that improves book discovery, user engagement, and accessibility beyond what traditional keyword-based platforms offer.

### Specific Objectives

| #   | Objective                                                                                                  |
| --- | ---------------------------------------------------------------------------------------------------------- |
| 1   | Build a functional web-based bookshop supporting registration, authentication, browsing, and cart/checkout |
| 2   | Implement semantic search using AI embeddings to process natural language queries                          |
| 3   | Integrate a conversational chatbot for guided navigation and book discovery                                |
| 4   | Deliver a personalized recommendation engine based on user behavior and book similarity                    |
| 5   | Provide an admin dashboard for managing books, users, and orders                                           |
| 6   | Evaluate AI feature usability, performance, and effectiveness                                              |

---

## 3. User Roles & Personas

### 3.1 Regular User (Shopper / Reader)

- Students, researchers, and general readers
- Can register, log in, search, browse, add to cart, and checkout
- Receives AI recommendations and can interact with the chatbot
- Can view order history and manage their profile

### 3.2 Administrator

- Platform manager (bookshop staff or academic supervisor)
- Can create, edit, and delete book listings
- Can manage user accounts and view platform analytics
- Can moderate chatbot interactions and review system logs

---

## 4. Tech Stack & Architecture

### 4.1 Frontend

| Layer            | Technology                                 | Rationale                                          |
| ---------------- | ------------------------------------------ | -------------------------------------------------- |
| UI Framework     | **React.js**                               | Component-based, widely used, supports dynamic UIs |
| Styling          | **Tailwind CSS**                           | Utility-first; fast responsive layout development  |
| State Management | **React Context API** or **Redux Toolkit** | Manage cart, auth, and user state globally         |
| HTTP Client      | **Axios**                                  | Clean API request handling with interceptors       |
| Routing          | **React Router v6**                        | Client-side navigation                             |

### 4.2 Backend

| Layer               | Technology                          | Rationale                                                  |
| ------------------- | ----------------------------------- | ---------------------------------------------------------- |
| Runtime / Framework | **Python + FastAPI**                | High performance, async support, ideal for AI integrations |
| Authentication      | **JWT (JSON Web Tokens)**           | Stateless, secure token-based auth                         |
| Password Security   | **bcrypt**                          | Secure password hashing                                    |
| API Documentation   | **Swagger UI** (built into FastAPI) | Auto-generated, accessible at `/docs`                      |

> **Decision note:** FastAPI is chosen over Node.js/Express because the AI/ML components (embeddings, RAG pipeline) are Python-native. Using FastAPI keeps the entire backend in one language, avoids cross-language HTTP calls, and simplifies deployment.

### 4.3 Database

| Layer            | Technology                                          | Rationale                                                           |
| ---------------- | --------------------------------------------------- | ------------------------------------------------------------------- |
| Primary Database | **PostgreSQL**                                      | Relational, robust, supports complex queries for orders/users/books |
| ORM              | **SQLAlchemy** (with Alembic for migrations)        | Clean model definitions, migration support                          |
| Vector Store     | **pgvector** (PostgreSQL extension) or **ChromaDB** | Stores and queries book embeddings for semantic search              |

### 4.4 AI & Machine Learning

| Feature               | Technology                                                                                                        | Notes                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Text Embeddings       | **Sentence-BERT (SBERT)** via `sentence-transformers` or **OpenAI Embeddings API**                                | Convert book titles/descriptions and user queries into vectors                            |
| Semantic Search       | **pgvector** cosine similarity or **ChromaDB**                                                                    | Query nearest-neighbor embedding matches                                                  |
| Recommendation Engine | **Content-based filtering** using cosine similarity on embeddings; optionally hybrid with collaborative filtering | Fallback to popularity-based for new users                                                |
| Chatbot               | **RAG pipeline** — LangChain + OpenAI GPT or open-source LLM (e.g., Mistral via Ollama)                           | Retrieves relevant books from vector store, passes context to LLM for response generation |

### 4.5 Development & DevOps Tools

| Tool                      | Purpose                               |
| ------------------------- | ------------------------------------- |
| Git + GitHub              | Version control and collaboration     |
| Postman                   | API testing and documentation         |
| VS Code                   | Primary IDE                           |
| Docker (optional)         | Container-based local dev environment |
| Render / Vercel / Railway | Prototype-level cloud deployment      |
| Figma                     | UI/UX wireframes and design mockups   |

---

## 5. Functional Requirements

### 5.1 Authentication & User Management

| ID      | Requirement                                                     | Priority |
| ------- | --------------------------------------------------------------- | -------- |
| AUTH-01 | Users can register with email, username, and password           | High     |
| AUTH-02 | Registered users can log in and receive a JWT access token      | High     |
| AUTH-03 | JWT tokens must expire and be refreshable via a refresh token   | High     |
| AUTH-04 | Users can log out, invalidating their session token             | High     |
| AUTH-05 | Users can update their profile (name, email, password)          | Medium   |
| AUTH-06 | Admins have a separate role flag enforced at the API level      | High     |
| AUTH-07 | Passwords must be hashed using bcrypt before storage            | High     |
| AUTH-08 | Unauthenticated users can browse and search but cannot purchase | Medium   |

---

### 5.2 Book Catalog & Browsing

| ID     | Requirement                                                                                             | Priority |
| ------ | ------------------------------------------------------------------------------------------------------- | -------- |
| CAT-01 | The system shall display a paginated catalog of all available books                                     | High     |
| CAT-02 | Each book listing shall display: title, author, genre, price, cover image, and short description        | High     |
| CAT-03 | Users can view a full book detail page with extended description, ISBN, publisher, and publication date | High     |
| CAT-04 | Users can filter books by genre, author, price range, and publication date                              | High     |
| CAT-05 | Users can sort books by price, popularity, newest, or rating                                            | Medium   |
| CAT-06 | The catalog shall support traditional keyword search as a fallback                                      | Medium   |
| CAT-07 | Book pages shall display "Related Books" powered by the recommendation engine                           | Medium   |

---

### 5.3 AI Semantic Search

| ID        | Requirement                                                                                                 | Priority |
| --------- | ----------------------------------------------------------------------------------------------------------- | -------- |
| SEARCH-01 | Users can enter natural language queries into the search bar (e.g., _"beginner books on machine learning"_) | High     |
| SEARCH-02 | The system converts the query into a vector embedding using the configured embedding model                  | High     |
| SEARCH-03 | The system performs a nearest-neighbor similarity search against stored book embeddings                     | High     |
| SEARCH-04 | Search results are ranked by semantic similarity score                                                      | High     |
| SEARCH-05 | Results are returned within 3 seconds under normal load                                                     | High     |
| SEARCH-06 | The system falls back to keyword search if the embedding service is unavailable                             | Medium   |
| SEARCH-07 | Each book in the catalog must have a pre-computed embedding stored on ingestion                             | High     |
| SEARCH-08 | Admin can trigger a re-indexing of all book embeddings from the dashboard                                   | Medium   |

---

### 5.4 Recommendation Engine

| ID     | Requirement                                                                                                 | Priority |
| ------ | ----------------------------------------------------------------------------------------------------------- | -------- |
| REC-01 | The system shall recommend books based on a user's browsing and view history                                | High     |
| REC-02 | Book detail pages shall show up to 6 "You might also like" recommendations                                  | High     |
| REC-03 | The homepage shall include a personalized "Recommended for You" section for logged-in users                 | High     |
| REC-04 | For unauthenticated users, display trending or highest-rated books in place of personalized recommendations | Medium   |
| REC-05 | Recommendations shall use content-based filtering via cosine similarity between book embeddings             | High     |
| REC-06 | User interaction events (views, cart adds, purchases) shall be logged to improve recommendations            | Medium   |
| REC-07 | The recommendation engine shall exclude books the user has already purchased                                | Medium   |

---

### 5.5 AI Chatbot Assistant

| ID      | Requirement                                                                                                           | Priority |
| ------- | --------------------------------------------------------------------------------------------------------------------- | -------- |
| CHAT-01 | A chat widget shall be accessible on all pages (bottom-right corner)                                                  | High     |
| CHAT-02 | Users can ask the chatbot for book recommendations in natural language                                                | High     |
| CHAT-03 | Users can ask about platform navigation, ordering, and account management                                             | High     |
| CHAT-04 | The chatbot uses a RAG pipeline: retrieves relevant books from the vector store and passes them as context to the LLM | High     |
| CHAT-05 | The chatbot responds in plain, friendly English within 5 seconds                                                      | High     |
| CHAT-06 | The chatbot clearly identifies itself as an AI assistant (not a human)                                                | High     |
| CHAT-07 | Chat history is preserved within a single browser session                                                             | Medium   |
| CHAT-08 | The chatbot shall not return harmful, biased, or misleading content                                                   | High     |
| CHAT-09 | The chatbot can provide direct links to book detail pages it recommends                                               | Medium   |

---

### 5.6 Cart & Checkout (Simulated)

| ID      | Requirement                                                                  | Priority |
| ------- | ---------------------------------------------------------------------------- | -------- |
| CART-01 | Authenticated users can add books to a shopping cart                         | High     |
| CART-02 | Users can view cart contents with per-item and total price                   | High     |
| CART-03 | Users can update quantities or remove items from the cart                    | High     |
| CART-04 | A checkout flow shall simulate order placement (no real payment processing)  | High     |
| CART-05 | On order confirmation, an order record is stored in the database             | High     |
| CART-06 | Users can view their order history with status (e.g., Pending, Completed)    | Medium   |
| CART-07 | The system shall display an order confirmation message/screen after checkout | Medium   |

---

### 5.7 Admin Dashboard

| ID       | Requirement                                                                            | Priority |
| -------- | -------------------------------------------------------------------------------------- | -------- |
| ADMIN-01 | Admins can log in via the same auth system with an elevated role                       | High     |
| ADMIN-02 | Admins can add new books (title, author, genre, description, price, cover image, ISBN) | High     |
| ADMIN-03 | Admins can edit and delete existing book listings                                      | High     |
| ADMIN-04 | Admins can upload a cover image for each book                                          | Medium   |
| ADMIN-05 | Admins can view all registered users and deactivate accounts                           | Medium   |
| ADMIN-06 | Admins can view all orders and update order status                                     | Medium   |
| ADMIN-07 | Admins can view basic analytics: total books, total users, total orders                | Medium   |
| ADMIN-08 | Admins can trigger a re-index of book embeddings for semantic search                   | Medium   |
| ADMIN-09 | All admin routes shall be protected by role-based access control (RBAC)                | High     |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID      | Requirement                                                                                    |
| ------- | ---------------------------------------------------------------------------------------------- |
| PERF-01 | Regular page loads (catalog, book detail) shall respond within **2 seconds** under normal load |
| PERF-02 | Semantic search queries shall return results within **3 seconds**                              |
| PERF-03 | Chatbot responses shall be delivered within **5 seconds**                                      |
| PERF-04 | The system shall support at least **50 concurrent users** at prototype scale                   |
| PERF-05 | API endpoints shall target a **99% uptime** during evaluation periods                          |

### 6.2 Security

| ID     | Requirement                                                                                    |
| ------ | ---------------------------------------------------------------------------------------------- |
| SEC-01 | All user passwords must be hashed with **bcrypt** (minimum 12 salt rounds)                     |
| SEC-02 | All API communication shall use **HTTPS** in deployment                                        |
| SEC-03 | JWT tokens must be short-lived (e.g., 15-minute access tokens with refresh)                    |
| SEC-04 | The system must protect against **SQL injection** using parameterized queries via the ORM      |
| SEC-05 | The system must protect against **XSS** by sanitizing all user inputs                          |
| SEC-06 | Admin routes must enforce **role-based access control** — unauthorized access returns HTTP 403 |
| SEC-07 | API keys (OpenAI, etc.) must be stored in environment variables, never in source code          |
| SEC-08 | Rate limiting shall be applied to AI endpoints to prevent abuse                                |

### 6.3 Usability

| ID     | Requirement                                                                                  |
| ------ | -------------------------------------------------------------------------------------------- |
| USA-01 | The UI must be **fully responsive** and work on desktop, tablet, and mobile                  |
| USA-02 | The design must follow accessible standards (sufficient contrast ratios, alt text on images) |
| USA-03 | The semantic search bar must be prominently placed and easy to discover                      |
| USA-04 | The chatbot widget must be non-intrusive and closeable                                       |
| USA-05 | Error messages must be clear, human-readable, and actionable                                 |
| USA-06 | Loading states must be shown on all async operations (search, chatbot, recommendations)      |

### 6.4 Reliability & Availability

| ID     | Requirement                                                                                  |
| ------ | -------------------------------------------------------------------------------------------- |
| REL-01 | If the AI/embedding service is unavailable, the system gracefully degrades to keyword search |
| REL-02 | If the chatbot LLM is unavailable, a fallback message must be displayed                      |
| REL-03 | The system must handle invalid or empty search queries without crashing                      |
| REL-04 | Database migrations must be versioned and reversible using Alembic                           |

### 6.5 Maintainability

| ID       | Requirement                                                                                |
| -------- | ------------------------------------------------------------------------------------------ |
| MAINT-01 | Backend code must follow modular structure: `routers/`, `services/`, `models/`, `schemas/` |
| MAINT-02 | Frontend components must be separated by feature/module                                    |
| MAINT-03 | All public functions and modules must include docstrings/comments                          |
| MAINT-04 | Environment-specific configuration must be managed via `.env` files                        |
| MAINT-05 | A `README.md` must be maintained with setup, run, and deployment instructions              |
| MAINT-06 | No single file should exceed **400 lines** of code; split into smaller modules if needed   |

### 6.6 Scalability

| ID       | Requirement                                                                                    |
| -------- | ---------------------------------------------------------------------------------------------- |
| SCALE-01 | The embedding indexing pipeline must support batch ingestion for adding large numbers of books |
| SCALE-02 | The database schema must be designed to accommodate future features (reviews, wishlists, etc.) |
| SCALE-03 | The backend must be stateless to support future horizontal scaling                             |

### 6.7 Data Integrity

| ID      | Requirement                                                                                |
| ------- | ------------------------------------------------------------------------------------------ |
| DATA-01 | Database constraints (foreign keys, NOT NULL, UNIQUE) must be enforced at the schema level |
| DATA-02 | All financial figures (prices) must be stored as **DECIMAL**, not FLOAT                    |
| DATA-03 | Timestamps (`created_at`, `updated_at`) must be automatically managed by the ORM           |

---

## 7. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│                       React.js + Tailwind                       │
│   [ Catalog ] [ Search ] [ Cart ] [ Chatbot ] [ Admin UI ]      │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTPS / REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│                                                                  │
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

---

## 8. Data Model Overview

### Users

```
id, username, email, hashed_password, role (user|admin),
created_at, updated_at, is_active
```

### Books

```
id, title, author, genre, description, isbn, publisher,
publication_date, price, cover_image_url, stock_count,
average_rating, created_at, updated_at
```

### BookEmbeddings

```
id, book_id (FK), embedding (vector), model_version, created_at
```

### Orders

```
id, user_id (FK), total_price, status (pending|completed|cancelled),
created_at, updated_at
```

### OrderItems

```
id, order_id (FK), book_id (FK), quantity, unit_price
```

### CartItems

```
id, user_id (FK), book_id (FK), quantity, added_at
```

### UserBrowsingHistory

```
id, user_id (FK), book_id (FK), event_type (view|cart_add|purchase),
timestamp
```

---

## 9. Out of Scope

The following features are explicitly **excluded** from this project:

| Feature                                        | Reason                                     |
| ---------------------------------------------- | ------------------------------------------ |
| Real payment processing (Stripe, PayPal, etc.) | Academic prototype; checkout is simulated  |
| Mobile native apps (iOS / Android)             | Web-only project                           |
| Multi-vendor / marketplace support             | Single-store scope                         |
| Email notifications                            | Not required for prototype evaluation      |
| Social login (Google, Facebook OAuth)          | Out of academic scope                      |
| User-generated reviews/ratings (write)         | Read-only display or static data           |
| Large-scale book dataset integration           | Limited to sample/publicly available data  |
| Multi-language (i18n) support                  | English-only for prototype                 |
| Real-time inventory management                 | Static stock data sufficient for prototype |

---

## 10. Constraints & Assumptions

### Constraints

- The project is a **prototype/academic system** — production-grade SLAs are not required
- AI API usage (OpenAI) may be constrained by token/credit limits; open-source models (SBERT, Ollama) are the preferred fallback
- Deployment is at **prototype scale** — Render, Railway, or local server
- The book dataset will use **publicly available or sample data** (e.g., Open Library, Kaggle book datasets)

### Assumptions

- Users have a modern browser (Chrome, Firefox, Edge) with JavaScript enabled
- A stable internet connection is available during AI-dependent operations
- The admin account is seeded manually during initial database setup
- JWT refresh token rotation will be implemented to maintain session security

---

## 11. Ethical & Compliance Requirements

| Area                  | Requirement                                                                                        |
| --------------------- | -------------------------------------------------------------------------------------------------- |
| **Data Privacy**      | User credentials and personal data must be encrypted at rest and in transit                        |
| **Copyright**         | No pirated or unlicensed book content will be distributed; only metadata and sample data           |
| **AI Transparency**   | The chatbot must identify itself as an AI on first interaction                                     |
| **AI Bias**           | Recommendation and chatbot systems must not discriminate by demographic or promote harmful content |
| **Accessibility**     | UI must meet WCAG 2.1 AA minimum contrast and screen-reader-friendly markup                        |
| **Security**          | Protection against OWASP Top 10 vulnerabilities (SQLi, XSS, broken auth, etc.)                     |
| **Data Minimization** | Only collect user data necessary for platform functionality                                        |
