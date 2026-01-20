# Thinkstruct Patent Search System - Advanced Features Roadmap

## Overview

This document records advanced features implemented and planned for future versions of the Thinkstruct patent search system.

---

## Recently Implemented Features (January 2026)

### User Authentication & Session Management ✅

| Feature | Status | Description |
|---------|--------|-------------|
| Google OAuth 2.0 | ✅ Implemented | Secure user authentication via Google accounts |
| JWT Sessions | ✅ Implemented | Token-based session management with 24-hour expiry |
| Guest Mode | ✅ Implemented | Allow anonymous users to search without login |

### Search History ✅

| Feature | Status | Description |
|---------|--------|-------------|
| Save Search History | ✅ Implemented | Automatically save search queries and results |
| View History | ✅ Implemented | Browse past searches with timestamps |
| Restore Results | ✅ Implemented | Click history entry to view full results |
| Delete History | ✅ Implemented | Remove individual or all history entries |

### Database Architecture ✅

| Feature | Status | Description |
|---------|--------|-------------|
| PostgreSQL Support | ✅ Implemented | Production-ready database for 100+ concurrent users |
| SQLite Support | ✅ Implemented | Lightweight option for development |
| Connection Pooling | ✅ Implemented | Efficient connection management (5-20 connections) |
| Redis Cache | ✅ Implemented | Optional session and data caching |
| Migration Script | ✅ Implemented | SQLite to PostgreSQL data migration |

---

## Patent Data Fields

### Current Database Fields

| Field Name | Type | Description | Status |
|------------|------|-------------|--------|
| doc_number | string | Patent document number | ✅ Implemented |
| title | string | Patent title | ✅ Implemented |
| abstract | string | Patent abstract | ✅ Implemented |
| claims | list[string] | Claims | ✅ Implemented |
| classification | string | Technical classification code | ✅ Implemented |
| detailed_description | string | Detailed description | ✅ Implemented |
| bibtex | string | Citation format information | ✅ Implemented |
| filename | string | Original filename | ✅ Implemented |
| publication_date | date | Publication date | ✅ Implemented (extracted from filename) |

---

## Key Fields to Implement

### 1. application_date (Application Date)

| Property | Description |
|----------|-------------|
| **Priority** | ⭐⭐⭐⭐⭐ Highest |
| **Affected Scenario** | Invalidity Search |
| **Field Type** | date (YYYY-MM-DD) |
| **Data Source** | `<application-reference>` tag in original XML file |

**Business Requirement:**

The core goal of invalidity search is to find "Prior Art" - technical documents published before the target patent's application date. Without the application date field:
- Cannot determine if retrieved patents are earlier than target patent
- May return large numbers of invalid search results
- Users need to manually verify dates one by one, extremely inefficient

**Implementation Suggestion:**
```python
# Add field extraction in data cleaning script
def extract_application_date(raw_record: dict) -> Optional[str]:
    """Extract application date from raw record"""
    # Option 1: Direct field
    if "application_date" in raw_record:
        return raw_record["application_date"]

    # Option 2: Infer from filename (format: US20240217263A1-20240704.XML)
    # Note: This is publication date, not application date

    # Option 3: Need to parse original XML file
    return None
```

---

### 2. publication_date (Publication Date) ✅ Implemented

| Property | Description |
|----------|-------------|
| **Status** | ✅ **Implemented** |
| **Priority** | ⭐⭐⭐⭐ High |
| **Affected Scenario** | All scenarios |
| **Field Type** | date (YYYY-MM-DD) |
| **Data Source** | Date portion from filename |

**Business Requirement:**

- **Infringement Monitoring**: Need to sort newly published patents by time, monitor if recent patents potentially infringe
- **Patentability Review**: Need to determine publication time points of prior art
- **Search Result Sorting**: Users typically want to see the newest or most relevant patents

**Implementation Suggestion:**
```python
# Can extract publication date from filename
# Filename format: patents_ipa{YYMMDD}.json
def extract_publication_date_from_filename(filename: str) -> Optional[str]:
    """Extract publication date from filename"""
    import re
    match = re.search(r'patents_ipa(\d{6})\.json', filename)
    if match:
        date_str = match.group(1)  # e.g., "240704"
        year = "20" + date_str[:2]
        month = date_str[2:4]
        day = date_str[4:6]
        return f"{year}-{month}-{day}"
    return None
```

---

### 3. priority_date (Priority Date)

| Property | Description |
|----------|-------------|
| **Priority** | ⭐⭐⭐⭐ High |
| **Affected Scenario** | Invalidity Search |
| **Field Type** | date (YYYY-MM-DD) |
| **Data Source** | `<priority-claim>` tag in original XML file |

**Business Requirement:**

In international patent applications, the priority date may be earlier than the actual application date. Some countries' patent laws use the priority date as the reference date for determining prior art validity.

**Typical Scenario:**
- Applicant files patent in the US, then submits same invention to China within 1 year
- China application date is later, but priority date is same as US application date
- Invalidity search should use priority date as reference

---

### 4. applicant / assignee (Applicant/Patent Owner)

| Property | Description |
|----------|-------------|
| **Priority** | ⭐⭐⭐ Medium |
| **Affected Scenario** | Infringement Monitoring |
| **Field Type** | string or list[string] |
| **Data Source** | `<applicants>` or `<assignees>` tags in original XML file |

**Business Requirement:**

- Identify competitor patent application activities
- Filter search results by company/organization
- Analyze patent landscape in specific fields

**Implementation Suggestion:**
```python
# Support multiple applicants/assignees
@dataclass
class PatentRecord:
    # ... other fields ...
    applicants: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
```

---

### 5. inventor (Inventor)

| Property | Description |
|----------|-------------|
| **Priority** | ⭐⭐ Medium-Low |
| **Affected Scenario** | Patentability Review |
| **Field Type** | list[string] |
| **Data Source** | `<inventors>` tag in original XML file |

**Business Requirement:**

- Track research activities of technical field experts
- Analyze inventors' technical expertise and research directions
- Support technology trend analysis

---

### 6. legal_status (Legal Status)

| Property | Description |
|----------|-------------|
| **Priority** | ⭐⭐⭐ Medium |
| **Affected Scenario** | Infringement Monitoring |
| **Field Type** | string (enumerated values) |
| **Possible Values** | pending, granted, expired, abandoned, withdrawn |
| **Data Source** | Requires additional legal status data source |

**Business Requirement:**

- **Expired patents don't pose infringement risk**: Expired or abandoned patents can be freely used
- **Uncertainty of pending patents**: Need to continuously monitor examination progress
- **Scope of granted patents**: These are the ones that truly need to be avoided

**Note:**
Legal status data typically needs to be obtained from specialized legal status databases, not in original patent application files. May need to integrate third-party data sources such as:
- USPTO Patent Center API
- EPO Open Patent Services
- WIPO PATENTSCOPE

---

## Implementation Roadmap

### Phase 1: Date Fields

```
┌─────────────────────────────────────────────────────┐
│  1. publication_date                     ✅ Done     │
│     - Extract from filename, simple implementation  │
│     - Can be used for time sorting and filtering    │
├─────────────────────────────────────────────────────┤
│  2. application_date                     ⏳ Pending  │
│     - Need to parse original XML or supplement data │
│     - Core dependency for invalidity search         │
├─────────────────────────────────────────────────────┤
│  3. priority_date                        ⏳ Pending  │
│     - Need to parse original XML                    │
│     - Complete time judgment logic for invalidity   │
└─────────────────────────────────────────────────────┘
```

### Phase 2: Entity Fields

```
┌─────────────────────────────────────────────────────┐
│  4. applicant / assignee                            │
│     - Need to parse original XML                    │
│     - Support competitor monitoring feature         │
├─────────────────────────────────────────────────────┤
│  5. inventor                                        │
│     - Need to parse original XML                    │
│     - Support expert tracking feature               │
└─────────────────────────────────────────────────────┘
```

### Phase 3: Legal Status

```
┌─────────────────────────────────────────────────────┐
│  6. legal_status                                    │
│     - Need to integrate third-party legal status    │
│     - Implement patent validity filtering           │
└─────────────────────────────────────────────────────┘
```

---

## Data Cleaning Script Extension Points

When adding new fields, update the following locations in `data/clean_patent_data.py`:

```python
# 1. Add to ALL_FIELDS list
ALL_FIELDS: list[str] = [
    # ... existing fields ...
    "application_date",    # New
    "publication_date",    # New
    "priority_date",       # New
    "applicants",          # New
    "assignees",           # New
    "inventors",           # New
    "legal_status",        # New
]

# 2. Update scenario field requirements
SCENARIO_FIELD_REQUIREMENTS = {
    "invalidity": {
        "required": ["doc_number", "claims", "abstract", "application_date"],  # Add
        # ...
    },
    # ...
}

# 3. Add default values
DEFAULT_VALUES["application_date"] = None
DEFAULT_VALUES["publication_date"] = None
# ...

# 4. Update PatentRecord data class
@dataclass
class PatentRecord:
    # ... existing fields ...
    application_date: Optional[str] = None
    publication_date: Optional[str] = None
    priority_date: Optional[str] = None
    applicants: list[str] = field(default_factory=list)
    assignees: list[str] = field(default_factory=list)
    inventors: list[str] = field(default_factory=list)
    legal_status: Optional[str] = None
```

---

## Related Resources

- [USPTO Bulk Data](https://bulkdata.uspto.gov/) - US Patent and Trademark Office bulk data
- [EPO Open Patent Services](https://www.epo.org/searching-for-patents/data/web-services/ops.html) - European Patent Office open services
- [WIPO PATENTSCOPE](https://patentscope.wipo.int/) - World Intellectual Property Organization patent database

---

*Document Version: 2.0*
*Last Updated: 2026-01-20*
