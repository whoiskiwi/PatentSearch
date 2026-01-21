# Thinkstruct - Patent Intelligent Search System

A semantic search engine for US patents, supporting invalidity search, infringement monitoring, patentability assessment, and patent ID search.

**Last Updated:** January 20, 2026

## Features

- **Semantic Search**: AI-powered similarity matching using patent-specific NLP models
- **Four Search Scenarios**:
  - **Invalidity Search**: Find prior art that may invalidate a target patent
  - **Infringement Monitoring**: Monitor new patents for potential infringement risks
  - **Patentability Assessment**: Assess patentability of new inventions
  - **Patent ID Search**: Find similar patents using a patent document number
- **Google OAuth Authentication**: Secure login with Google accounts
- **Search History**: Save and retrieve past searches with full results
- **Advanced Filtering**: Classification codes (IPC/CPC), keywords, date ranges
- **Risk Assessment**: Automatic risk level calculation for infringement monitoring
- **Novelty Assessment**: Automatic novelty evaluation for patentability review

## Tech Stack

### Backend
| Technology | Version | Description |
|------------|---------|-------------|
| Python | 3.10+ | Programming language |
| FastAPI | 0.104+ | High-performance REST API framework |
| Uvicorn | 0.24+ | ASGI server |
| Sentence-Transformers | 2.2+ | Semantic embedding generation |
| PyTorch | 2.0+ | Deep learning framework |
| NumPy | 1.24+ | Vector similarity computation |
| Pydantic | 2.0+ | Data validation |

### Database
| Technology | Version | Description |
|------------|---------|-------------|
| PostgreSQL | 14+ | Production database (recommended) |
| SQLite | - | Development database (no setup required) |
| Redis | 5.0+ | Session caching (optional) |
| asyncpg | 0.29+ | PostgreSQL async driver |
| aiosqlite | 0.19+ | SQLite async driver |

### Frontend
| Technology | Version | Description |
|------------|---------|-------------|
| React | 19.2+ | UI framework |
| TypeScript | 5.9+ | Type-safe JavaScript |
| Vite | 7.2+ | Build tool and dev server |
| Axios | 1.13+ | HTTP client |
| ESLint | 9.39+ | Code linting |

### Authentication
| Technology | Description |
|------------|-------------|
| Google OAuth 2.0 | User authentication via Google |
| JWT (python-jose) | Session token management |
| httpx | Async HTTP client for OAuth |

### Semantic Search Model

This project uses [PatentSBERTa_V2](https://huggingface.co/AAUBS/PatentSBERTa_V2) as the semantic search model.

PatentSBERTa is a Sentence-BERT model fine-tuned specifically for patent text, trained on patent claims data. It outperforms general-purpose models on patent similarity tasks.

| Property | Value |
|----------|-------|
| Model | `AAUBS/PatentSBERTa_V2` |
| Dimensions | 768 |
| Max Sequence | 512 tokens |
| Pooling | Mean Pooling |
| Model Size | ~420MB |

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
# Clone the repository
cd Thinkstruct

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# The PatentSBERTa model (~420MB) will be downloaded automatically on first run
```

#### Python Dependencies (requirements.txt)

```
# Backend API
fastapi>=0.104.0
uvicorn>=0.24.0

# NLP & Machine Learning
sentence-transformers>=2.2.0
torch>=2.0.0
numpy>=1.24.0

# Utilities
pydantic>=2.0.0
python-dotenv>=1.0.0

# Authentication
python-jose[cryptography]>=3.3.0
httpx>=0.27.0

# Database
asyncpg>=0.29.0
aiosqlite>=0.19.0

# Cache
redis>=5.0.0
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

# Install Node.js dependencies
npm install

# Dependencies installed:
# - react@19.2.0
# - react-dom@19.2.0
# - axios@1.13.2
# - typescript@5.9.3
# - vite@7.2.4
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
# Output in frontend/dist/
```

## API Endpoints

### Core Search APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Get patent database statistics |
| GET | `/api/patent/{doc_number}` | Get single patent by ID |
| POST | `/api/search/invalidity` | Invalidity search - find prior art |
| POST | `/api/search/infringement` | Infringement monitoring - detect risks |
| POST | `/api/search/patentability` | Patentability assessment - evaluate novelty |
| POST | `/api/search/by-patent-id` | Patent ID search - find similar patents |

### Authentication APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/login/google` | Initiate Google OAuth login |
| GET | `/api/auth/callback/google` | OAuth callback handler |
| GET | `/api/auth/status` | Check authentication status |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/logout` | Logout current user |

### Search History APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/history` | Save search to history |
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

### 4. Patent ID Search

Find similar patents using a patent document number as input.

**Request:**
```json
POST /api/search/by-patent-id
{
  "doc_number": "US20240217263A1",
  "classification": "B60C",
  "top_k": 20
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether patent was found |
| `source_patent` | object | Information about the query patent |
| `results` | list | Similar patents found |
| `similarity_score` | float | Semantic similarity (0-1) |
| `matched_claims` | list[str] | Claims matching the source patent |
| `all_claims` | list[str] | All claims (up to 10) |

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
│   ├── dependencies.py             # Dependency injection (search engine)
│   ├── auth/                       # Authentication module
│   │   ├── __init__.py
│   │   ├── config.py               # Settings from environment
│   │   ├── database.py             # Database interface (SQLite/PostgreSQL)
│   │   ├── cache.py                # Redis cache layer
│   │   ├── models.py               # Auth Pydantic models
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
│   │   ├── patent_id.py            # POST /api/search/by-patent-id
│   │   └── stats.py                # GET /api/stats, /api/health
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
│   │   │   └── Auth/               # Auth components
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
│   └── cleaned_output/             # Cleaned data + embeddings
│       ├── cleaned_patents_*.json  # Cleaned patent data
│       └── embeddings.npy          # Pre-computed embeddings
│
├── docs/                           # Documentation
│   ├── semantic_model_guide.md     # Model and performance guide
│   ├── advanced_features.md        # Advanced features roadmap
│   └── data_cleaning_guide.md      # Data cleaning guide
│
├── .env                            # Environment variables (not in git)
├── run.py                          # Backend entry point
├── requirements.txt                # Python dependencies
└── README.md
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React 19)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Sidebar   │  │ SearchForm  │  │      ResultCard         │ │
│  │  (scenario) │  │   (input)   │  │      (results)          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │   useSearch   │  (hooks)                   │
│                    └───────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Routers                             │   │
│  │  /auth  │  /history  │  /invalidity  │  /infringement   │   │
│  │         │            │  /patentability  │  /by-patent-id │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  AuthModule │   │SearchEngine │   │  Database   │          │
│  │ (OAuth+JWT) │   │(PatentSBERTa)│   │ (PostgreSQL)│          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   Patent Data   │ │  PostgreSQL │ │    Redis    │
│  (JSON + .npy)  │ │  (users,    │ │  (session   │
│                 │ │   history)  │ │   cache)    │
└─────────────────┘ └─────────────┘ └─────────────┘
```

## Performance Optimization

### Pre-computed Embeddings

Patent embeddings are pre-computed and saved to `embeddings.npy` file to avoid recalculating on every startup:

- **Without pre-computation**: ~56 seconds on first search
- **With pre-computation**: ~1-2 seconds search time

The embeddings file is automatically generated on first run and reused on subsequent starts.

### Database Connection Pooling

PostgreSQL uses asyncpg with connection pooling (5-20 connections) for better performance under load.

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

- [Search Scenarios Guide](docs/search_scenarios_guide.md) - Why these scenarios, how to use filters effectively
- [Semantic Model Guide](docs/semantic_model_guide.md) - Model selection and performance optimization
- [Data Cleaning Guide](docs/data_cleaning_guide.md) - Data preprocessing documentation
- [Advanced Features](docs/advanced_features.md) - Future features roadmap

## Quick Start

```bash
# 1. Setup backend
pip install -r requirements.txt

# 2. Setup database (PostgreSQL)
createdb thinkstruct

# 3. Configure environment (create .env file with settings above)

# 4. Start backend
python run.py

# 5. Setup frontend (new terminal)
cd frontend
npm install
npm run dev

# 6. Open browser
# http://localhost:3000
```

## License

MIT License
