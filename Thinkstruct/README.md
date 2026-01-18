# Thinkstruct - Patent Intelligent Search System

A semantic search engine for US patents, supporting invalidity search, infringement monitoring, and patentability assessment.

## Features

- **Semantic Search**: AI-powered similarity matching using patent-specific NLP models
- **Three Search Scenarios**:
  - **Invalidity Search**: Find prior art that may invalidate a target patent
  - **Infringement Monitoring**: Monitor new patents for potential infringement risks
  - **Patentability Assessment**: Assess patentability of new inventions
- **Advanced Filtering**: Classification codes (IPC/CPC), keywords, date ranges
- **Risk Assessment**: Automatic risk level calculation for infringement monitoring
- **Novelty Assessment**: Automatic novelty evaluation for patentability review

## Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - High-performance REST API
- **Sentence-Transformers** - Semantic embedding generation
- **NumPy** - Vector similarity computation

### Frontend
- **React 18** + TypeScript
- **Vite** - Build tool
- **Axios** - HTTP client

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

**Model Installation:**

The model will be downloaded automatically on first run. To pre-download manually:

```python
from sentence_transformers import SentenceTransformer

# Download PatentSBERTa_V2 (~420MB)
model = SentenceTransformer('AAUBS/PatentSBERTa_V2')
```

Or using Hugging Face CLI:

```bash
# Install huggingface_hub if not installed
pip install huggingface_hub

# Download model to cache
huggingface-cli download AAUBS/PatentSBERTa_V2
```

The model is cached locally at `~/.cache/huggingface/hub/` after download.

## Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# The model (~420MB) will be downloaded automatically on first run
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
python run.py
# Server runs on http://localhost:5000
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Get patent statistics |
| POST | `/api/search/invalidity` | Invalidity search - find prior art |
| POST | `/api/search/infringement` | Infringement monitoring - detect risks |
| POST | `/api/search/patentability` | Patentability assessment - evaluate novelty |

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

## Project Structure

```
Thinkstruct/
│
├── backend/                        # Backend Python/FastAPI
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry + CORS config
│   ├── models.py                   # Pydantic request/response models
│   ├── dependencies.py             # Dependency injection (search engine instance)
│   ├── routers/                    # API router layer
│   │   ├── __init__.py
│   │   ├── invalidity.py           # POST /api/search/invalidity
│   │   ├── infringement.py         # POST /api/search/infringement
│   │   ├── patentability.py        # POST /api/search/patentability
│   │   └── stats.py                # GET /api/stats, GET /api/health
│   └── services/                   # Business logic layer
│       ├── __init__.py
│       └── search_engine.py        # Core search engine (semantic search + filtering)
│
├── frontend/                       # Frontend React/TypeScript
│   ├── src/
│   │   ├── api/
│   │   │   └── searchApi.ts        # API client + type definitions
│   │   ├── components/             # UI components
│   │   │   ├── Sidebar/            # Sidebar (scenario selection + filters)
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Sidebar.css
│   │   │   │   └── index.ts
│   │   │   ├── SearchForm/         # Search forms (scenario-specific)
│   │   │   │   ├── InvalidityForm.tsx
│   │   │   │   ├── InfringementForm.tsx
│   │   │   │   ├── PatentabilityForm.tsx
│   │   │   │   ├── SearchForm.css
│   │   │   │   └── index.ts
│   │   │   └── ResultCard/         # Result cards (scenario-specific)
│   │   │       ├── InvalidityCard.tsx
│   │   │       ├── InfringementCard.tsx
│   │   │       ├── PatentabilityCard.tsx
│   │   │       ├── ResultCard.css
│   │   │       └── index.ts
│   │   ├── hooks/                  # Custom React Hooks
│   │   │   ├── useSearch.ts        # Search logic + state management + color utilities
│   │   │   └── useResizableSidebar.ts  # Resizable sidebar hook
│   │   ├── types/
│   │   │   └── index.ts            # Shared type definitions + constants
│   │   ├── App.tsx                 # Main component
│   │   ├── App.css                 # Global styles
│   │   ├── main.tsx                # React entry
│   │   └── index.css               # Base styles
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── data/                           # Data directory
│   ├── __init__.py
│   ├── clean_patent_data.py        # Data cleaning script
│   ├── patent_data_small/          # Raw patent data (patents_ipa*.json)
│   └── cleaned_output/             # Cleaned data + reports
│
├── docs/                           # Documentation
│   ├── advanced_features.md        # Advanced features roadmap
│   └── data_cleaning_guide.md      # Data cleaning guide
│
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
│  │  /invalidity  │  /infringement  │  /patentability       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                    ┌───────┴───────┐                           │
│                    │ SearchEngine  │  (services)                │
│                    │ PatentSBERTa  │                           │
│                    └───────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                              │
│              cleaned_output/patents_cleaned_*.json              │
└─────────────────────────────────────────────────────────────────┘
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

MIT
