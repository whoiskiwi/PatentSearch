# Thinkstruct Frontend

React + TypeScript frontend for the Thinkstruct Patent Intelligent Search system.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Axios** - HTTP client

## Project Structure

```
src/
├── api/
│   └── searchApi.ts        # API client functions
├── components/
│   ├── Sidebar/            # Navigation & filters
│   ├── SearchForm/         # Scenario-specific forms
│   └── ResultCard/         # Result display cards
├── hooks/
│   ├── useSearch.ts        # Search logic & state
│   └── useResizableSidebar.ts
├── types/
│   └── index.ts            # Type definitions
├── App.tsx                 # Main application
└── App.css                 # Global styles
```

## Architecture

### Three-Layer Design

1. **Search Scenario** (Business Purpose)
   - Invalidity Search - Find prior art
   - Infringement Monitoring - Monitor potential infringement
   - Patentability Review - Evaluate new inventions

2. **Quick Search** (Input Method)
   - Default: Enter text directly
   - Patent ID: Auto-fetch content by patent number

3. **Advanced Filters** (Refine Results)
   - Classification prefix
   - Keywords
   - Title search
   - Result count

### Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| `api/` | HTTP communication with backend |
| `hooks/` | Business logic & state management |
| `components/` | UI rendering |
| `types/` | Type definitions |

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

## API Endpoints

The frontend communicates with the backend via:

- `POST /api/search/invalidity` - Invalidity search
- `POST /api/search/infringement` - Infringement monitoring
- `POST /api/search/patentability` - Patentability review
- `GET /api/patent/:doc_number` - Get patent by ID
- `GET /api/stats` - Get statistics
- `GET /api/health` - Health check
