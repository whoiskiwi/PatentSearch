# Thinkstruct - Patent Intelligent Search System

A semantic search engine for US patents, supporting invalidity search, infringement monitoring, and patentability assessment.

**Last Updated:** January 20, 2026

## Features

- **Semantic Search**: AI-powered similarity matching using patent-specific NLP models
- **Three Search Scenarios**:
  - **Invalidity Search**: Find prior art that may invalidate a target patent
  - **Infringement Monitoring**: Monitor new patents for potential infringement risks
  - **Patentability Assessment**: Assess patentability of new inventions
- **Google OAuth Authentication**: Secure login with Google accounts
- **Search History**: Save and retrieve past searches with full results
- **Advanced Filtering**: Classification codes (IPC/CPC), keywords, date ranges
- **Risk Assessment**: Automatic risk level calculation for infringement monitoring
- **Novelty Assessment**: Automatic novelty evaluation for patentability review

## Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - High-performance REST API
- **Sentence-Transformers** - Semantic embedding generation
- **NumPy** - Vector similarity computation

### Database
- **PostgreSQL** - Production database for user data and search history
- **SQLite** - Development database (optional)
- **Redis** - Session caching (optional, recommended for production)

### Frontend
- **React 18** + TypeScript
- **Vite** - Build tool
- **Axios** - HTTP client

### Authentication
- **Google OAuth 2.0** - User authentication
- **JWT** - Session management

### Semantic Search Model

This project uses [PatentSBERTa_V2](https://huggingface.co/AAUBS/PatentSBERTa_V2) as the semantic search model.

PatentSBERTa is a Sentence-BERT model fine-tuned specifically for patent text, trained on patent claims data. It outperforms general-purpose models on patent similarity tasks.

| Property | Value |
|----------|-------|
| Model | `AAUBS/PatentSBERTa_V2` |
| Dimensions | 768 |
| Max Sequence | 512 tokens |
| Pooling | Mean Pooling |

**Reference Paper:**
> Bekamiri, H., Hain, D. S., & Jurowetzki, R. (2024).
> *PatentSBERTa: A deep NLP based hybrid model for patent distance and classification using augmented SBERT.*
> Technological Forecasting and Social Change, 206, 123536.
> [DOI: 10.1016/j.techfore.2024.123536](https://doi.org/10.1016/j.techfore.2024.123536)

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (for production)
- Redis (optional, for caching)

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# The model (~420MB) will be downloaded automatically on first run
```

### Database Setup

#### Option 1: PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb thinkstruct

# Configure environment variables in .env
DATABASE_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=thinkstruct
PG_USER=postgres
PG_PASSWORD=your_password
```

#### Option 2: SQLite (Development)

```bash
# No setup required, just configure .env
DATABASE_TYPE=sqlite
DATABASE_PATH=./backend/thinkstruct.db
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Set authorized redirect URI: `http://localhost:5000/api/auth/callback/google`
6. Copy Client ID and Client Secret to `.env`:

```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback/google
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback/google

# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Database Configuration
DATABASE_TYPE=postgresql  # or "sqlite"

# PostgreSQL (when DATABASE_TYPE=postgresql)
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=thinkstruct
PG_USER=postgres
PG_PASSWORD=your_password

# SQLite (when DATABASE_TYPE=sqlite)
DATABASE_PATH=./backend/thinkstruct.db

# Redis Cache (Optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

## Running the Application

### Start Backend Server

```bash
# From project root
python run.py
# Server runs on http://localhost:5000
```

Or using uvicorn directly:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 5000 --reload
```

### Start Frontend Dev Server

```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### Build Frontend for Production

```bash
cd frontend
npm run build
```

## API Endpoints

### Core Search APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Get patent statistics |
| POST | `/api/search/invalidity` | Invalidity search - find prior art |
| POST | `/api/search/infringement` | Infringement monitoring - detect risks |
| POST | `/api/search/patentability` | Patentability assessment - evaluate novelty |

### Authentication APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/login/google` | Initiate Google OAuth login |
| GET | `/api/auth/callback/google` | OAuth callback handler |
| GET | `/api/auth/status` | Check authentication status |
| POST | `/api/auth/logout` | Logout current user |

### Search History APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history` | Get user's search history |
| GET | `/api/history/{id}` | Get specific history entry |
| DELETE | `/api/history/{id}` | Delete history entry |
| DELETE | `/api/history` | Clear all history |

---

### 1. Invalidity Search

Find prior art patents that could invalidate a target patent.

**Request:**
```json
POST /api/search/invalidity
{
  "query_claims": "A tire with reinforced sidewall structure for improved durability",
  "query_doc_number": "US12345678",
  "classification": "B60C",
  "target_date": "2023-01-01",
  "top_k": 20
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `similarity_score` | float | Semantic similarity (0-1) |
| `matched_claims` | list[str] | Claims matching the query |
| `independent_claims` | list[str] | Independent claims only |
| `claims_count` | int | Total number of claims |
| `all_claims` | list[str] | All claims (up to 10) |
| `detailed_description` | str | Truncated description (up to 500 chars) |

---

### 2. Infringement Monitoring

Monitor for patents that may infringe on your patent rights.

**Request:**
```json
POST /api/search/infringement
{
  "my_claims": "A wheel rim with integrated pressure sensor",
  "my_doc_number": "US98765432",
  "classification": "B60B",
  "keywords": ["sensor", "pressure"],
  "date_from": "2024-01-01",
  "date_to": "2025-12-31",
  "min_similarity": 0.5,
  "top_k": 20
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `similarity_score` | float | Semantic similarity (0-1) |
| `risk_level` | string | Risk assessment: Very High / High / Medium / Low |
| `matched_claims` | list[str] | Claims matching your patent |
| `overlapping_features` | list[str] | Technical features that overlap |
| `all_claims` | list[str] | All claims (up to 10) |
| `detailed_description` | str | Truncated description (up to 500 chars) |

**Risk Level Thresholds:**
| Score Range | Risk Level |
|-------------|------------|
| > 0.9 | Very High |
| >= 0.7 | High |
| >= 0.5 | Medium |
| < 0.5 | Low |

---

### 3. Patentability Assessment

Evaluate the patentability of a new invention against prior art.

**Request:**
```json
POST /api/search/patentability
{
  "invention_description": "An innovative tire pressure monitoring system using wireless sensors embedded in the tire wall",
  "draft_claims": "A system comprising a wireless sensor...",
  "classification": "B60C",
  "keywords": ["wireless", "sensor", "tire"],
  "top_k": 20
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `similarity_score` | float | Semantic similarity (0-1) |
| `novelty_assessment` | string | Assessment: Novel / Similar / Identical |
| `closest_prior_art` | bool | True if this is the closest match |
| `key_differences` | list[str] | Differences from prior art |
| `technical_field` | string | Technical field category |
| `matched_claims` | list[str] | Related claims from prior art |
| `all_claims` | list[str] | All claims (up to 10) |
| `detailed_description` | str | Truncated description (up to 500 chars) |

**Novelty Assessment Thresholds:**
| Score Range | Assessment |
|-------------|------------|
| > 0.85 | Identical |
| >= 0.6 | Similar |
| < 0.6 | Novel |

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    picture_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);
```

### Search History Table
```sql
CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,
    query_data JSONB NOT NULL,
    results_data JSONB,
    result_count INTEGER DEFAULT 0,
    search_time_ms REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Project Structure

```
Thinkstruct/
│
├── backend/                        # Backend Python/FastAPI
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry + CORS config
│   ├── models.py                   # Pydantic request/response models
│   ├── dependencies.py             # Dependency injection (search engine instance)
│   ├── auth/                       # Authentication module
│   │   ├── __init__.py
│   │   ├── config.py               # Settings and configuration
│   │   ├── database.py             # Database interface (SQLite/PostgreSQL)
│   │   ├── cache.py                # Redis cache layer
│   │   ├── models.py               # Auth-related Pydantic models
│   │   ├── jwt_handler.py          # JWT token management
│   │   ├── oauth.py                # Google OAuth implementation
│   │   └── dependencies.py         # Auth dependencies
│   ├── routers/                    # API router layer
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── history.py              # Search history endpoints
│   │   ├── invalidity.py           # POST /api/search/invalidity
│   │   ├── infringement.py         # POST /api/search/infringement
│   │   ├── patentability.py        # POST /api/search/patentability
│   │   └── stats.py                # GET /api/stats, GET /api/health
│   └── services/                   # Business logic layer
│       ├── __init__.py
│       └── search_engine.py        # Core search engine
│
├── frontend/                       # Frontend React/TypeScript
│   ├── src/
│   │   ├── api/
│   │   │   ├── searchApi.ts        # Search API client
│   │   │   └── historyApi.ts       # History API client
│   │   ├── auth/                   # Authentication module
│   │   │   ├── AuthContext.tsx     # Auth context provider
│   │   │   ├── authApi.ts          # Auth API client
│   │   │   └── index.ts
│   │   ├── components/             # UI components
│   │   │   ├── Sidebar/
│   │   │   ├── SearchForm/
│   │   │   ├── ResultCard/
│   │   │   └── Auth/               # Auth components (LoginButton, UserMenu)
│   │   ├── pages/                  # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   └── useResizableSidebar.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── data/                           # Data directory
│   ├── __init__.py
│   ├── clean_patent_data.py        # Data cleaning script
│   ├── patent_data_small/          # Raw patent data
│   └── cleaned_output/             # Cleaned data + reports
│
├── docs/                           # Documentation
│   ├── advanced_features.md        # Advanced features roadmap
│   └── data_cleaning_guide.md      # Data cleaning guide
│
├── .env                            # Environment variables (not in git)
├── run.py                          # Backend entry point
├── requirements.txt                # Python dependencies
└── README.md
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Sidebar   │  │ SearchForm  │  │      ResultCard         │ │
│  │  (scenario) │  │   (input)   │  │      (results)          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │   useSearch   │  (hooks)                   │
│                    └───────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Routers                             │   │
│  │  /auth  │  /history  │  /invalidity  │  /infringement   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  AuthModule │   │SearchEngine │   │  Database   │          │
│  │   (OAuth)   │   │(PatentSBERTa)│   │ (PostgreSQL)│          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   Patent Data   │ │  PostgreSQL │ │    Redis    │
│  (JSON files)   │ │  (users,    │ │  (cache)    │
│                 │ │   history)  │ │             │
└─────────────────┘ └─────────────┘ └─────────────┘
```

## Data Preprocessing

The `data/clean_patent_data.py` script processes raw patent data:

```bash
# Clean patent data with default settings
python data/clean_patent_data.py

# See all options
python data/clean_patent_data.py --help
```

**Key Features:**
- Removes numeric prefixes from claims (e.g., "16 . A tire..." → "A tire...")
- Filters out canceled claims
- Extracts publication dates from filenames
- Validates data for each search scenario

See [Data Cleaning Guide](docs/data_cleaning_guide.md) for details.

## Documentation

- [Data Cleaning Guide](docs/data_cleaning_guide.md) - Data preprocessing documentation
- [Advanced Features](docs/advanced_features.md) - Future features roadmap

## License

MIT License
