# Patent Search Scenarios Guide

This guide explains the rationale behind the search scenarios, their use cases, and how to effectively use advanced filters.

**Last Updated:** January 20, 2026

## Table of Contents

1. [Why These Search Scenarios?](#why-these-search-scenarios)
2. [The Three Core Scenarios](#the-three-core-scenarios)
3. [Patent ID Search (Supplementary)](#patent-id-search-supplementary)
4. [Parameter Reference](#parameter-reference)
5. [Parameter Combinations Guide](#parameter-combinations-guide)
6. [Advanced Filtering Guide](#advanced-filtering-guide)
7. [Best Practices](#best-practices)
8. [Common Workflows](#common-workflows)

---

## Why These Search Scenarios?

### The Patent Lifecycle Problem

Patents exist in a complex legal and technical ecosystem. Different stakeholders need different types of searches at different stages:

```
Patent Lifecycle & Search Needs:

┌─────────────────────────────────────────────────────────────────┐
│                        INNOVATION                                │
│                            │                                     │
│                            ▼                                     │
│   ┌─────────────────────────────────────────┐                   │
│   │  "Is my invention patentable?"          │ ◄── Patentability │
│   │  Search: Find similar prior art         │     Assessment    │
│   └─────────────────────────────────────────┘                   │
│                            │                                     │
│                            ▼                                     │
│   ┌─────────────────────────────────────────┐                   │
│   │  Patent Application → Patent Granted    │                   │
│   └─────────────────────────────────────────┘                   │
│                            │                                     │
│              ┌─────────────┴─────────────┐                      │
│              ▼                           ▼                       │
│   ┌──────────────────┐        ┌──────────────────┐              │
│   │ "Are others      │        │ "Can I challenge │              │
│   │  copying me?"    │        │  this patent?"   │              │
│   │                  │        │                  │              │
│   │ Infringement     │        │ Invalidity       │              │
│   │ Monitoring       │        │ Search           │              │
│   └──────────────────┘        └──────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Why Not Just One Generic Search?

| Generic Search | Scenario-Specific Search |
|----------------|--------------------------|
| Returns all similar patents | Returns patents relevant to your specific need |
| No date filtering logic | Automatically applies correct date logic |
| No risk/novelty assessment | Provides actionable assessments |
| User must interpret results | Results are pre-analyzed for the use case |

**Example:** A patent published in 2025 cannot be prior art for a patent filed in 2020. Invalidity search automatically filters this out; generic search would not.

---

## The Three Core Scenarios

### 1. Invalidity Search (Finding Prior Art)

**Purpose:** Find existing patents that were published BEFORE a target date to potentially invalidate a patent.

**Who uses this:**
- Patent attorneys challenging a competitor's patent
- Companies facing patent infringement lawsuits
- Patent examiners reviewing applications

**Key characteristic:** Results must be **earlier** than the target date.

```
Timeline:
─────────────────────────────────────────────────────►
                    │                         │
              Target Date              Competitor's Patent
                    │                         │
         ◄─────────┘                         │
    Search for prior art                     │
    BEFORE this date                         │
```

**Request example:**
```json
{
  "query_claims": "A tire comprising a reinforced sidewall...",
  "target_date": "2022-06-15",    // Only find patents BEFORE this
  "classification": "B60C",
  "top_k": 20
}
```

**When to use:**
- ✅ You want to invalidate a competitor's patent
- ✅ You're defending against an infringement lawsuit
- ✅ You're conducting due diligence before licensing

---

### 2. Infringement Monitoring

**Purpose:** Find patents that may infringe on YOUR patent rights by detecting similar claims.

**Who uses this:**
- Patent owners protecting their IP
- IP management teams
- Licensing departments

**Key characteristic:** Results are typically **after** your patent date, with risk level assessment.

```
Timeline:
─────────────────────────────────────────────────────►
         │                              │
    Your Patent                   Potentially Infringing
      Granted                         Patents
         │                              │
         └────────────────────────────► │
              Monitor patents           │
              AFTER your patent         │
```

**Request example:**
```json
{
  "my_claims": "A wheel rim with integrated pressure sensor...",
  "my_doc_number": "US12345678",    // Excluded from results
  "date_from": "2023-01-01",        // Monitor from this date
  "date_to": "2025-12-31",          // To this date
  "min_similarity": 0.5,            // Minimum similarity threshold
  "top_k": 20
}
```

**Risk Level interpretation:**
| Risk Level | Similarity | Recommended Action |
|------------|------------|-------------------|
| Very High | > 90% | Immediate legal review required |
| High | 70-90% | Detailed claim comparison needed |
| Medium | 50-70% | Monitor and document |
| Low | < 50% | Low priority, periodic review |

**When to use:**
- ✅ You own patents and want to protect them
- ✅ You want to find licensing opportunities
- ✅ You're monitoring competitor activity

---

### 3. Patentability Assessment

**Purpose:** Evaluate whether a new invention is novel enough to be patented.

**Who uses this:**
- Inventors evaluating their ideas
- R&D departments before filing
- Patent attorneys advising clients

**Key characteristic:** No date filter (all prior art matters); provides novelty assessment.

```
Assessment Logic:
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Your Invention ──► Compare with ALL prior art    │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │ High Similarity (>85%)  → "Identical"       │  │
│   │ Medium Similarity (60-85%) → "Similar"      │  │
│   │ Low Similarity (<60%)   → "Novel"           │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   Lower similarity = Better patentability          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Request example:**
```json
{
  "invention_description": "An innovative tire pressure monitoring system using wireless sensors embedded in the tire wall with self-powered energy harvesting...",
  "draft_claims": "A system comprising: a wireless sensor module...",
  "classification": "B60C",
  "keywords": ["wireless", "sensor", "tire", "pressure"],
  "top_k": 20
}
```

**Novelty Assessment interpretation:**
| Assessment | Similarity | Meaning |
|------------|------------|---------|
| Novel | < 60% | Good patentability prospects |
| Similar | 60-85% | Need to differentiate claims |
| Identical | > 85% | Likely not patentable as-is |

**When to use:**
- ✅ Before investing in patent application ($10K-$50K+)
- ✅ Evaluating multiple invention ideas
- ✅ Identifying areas needing differentiation

---

## Patent ID Search (Supplementary)

**Purpose:** Find similar patents when you already know a relevant patent number.

This is a convenience feature that complements the three core scenarios:

```
Use Case Flow:
┌────────────────────────────────────────────────────────┐
│                                                        │
│  "I found patent US20240217263A1 relevant to my work" │
│                           │                            │
│                           ▼                            │
│           ┌───────────────────────────────┐           │
│           │ Patent ID Search              │           │
│           │ → Find 20 similar patents     │           │
│           └───────────────────────────────┘           │
│                           │                            │
│                           ▼                            │
│         Use results as input to core scenarios         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**When to use:**
- ✅ You found a relevant patent and want to explore the field
- ✅ You want to find related patents quickly
- ✅ You're starting research and need a starting point

---

## Parameter Reference

### All Parameters by Scenario

#### Invalidity Search Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query_claims` | string | ✅ Yes | - | Target patent claims to find prior art for |
| `query_doc_number` | string | No | "" | Reference document number (for tracking) |
| `classification` | string | No | "" | IPC/CPC code prefix filter (e.g., "B60C") |
| `keywords` | string[] | No | [] | Required keywords (AND logic) |
| `title_search` | string | No | "" | Substring match in title |
| `target_date` | string | No | null | Only return patents BEFORE this date (YYYY-MM-DD) |
| `top_k` | int | No | 20 | Maximum results (1-100) |

#### Infringement Monitoring Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `my_claims` | string | ✅ Yes | - | Your patent claims to monitor |
| `my_doc_number` | string | ✅ Yes | - | Your patent number (excluded from results) |
| `classification` | string | No | "" | IPC/CPC code prefix filter |
| `keywords` | string[] | No | [] | Required keywords (AND logic) |
| `title_search` | string | No | "" | Substring match in title |
| `date_from` | string | No | null | Only return patents AFTER this date |
| `date_to` | string | No | null | Only return patents BEFORE this date |
| `min_similarity` | float | No | 0.5 | Minimum similarity threshold (0-1) |
| `top_k` | int | No | 20 | Maximum results (1-100) |

#### Patentability Assessment Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `invention_description` | string | ✅ Yes | - | Description of your new invention |
| `draft_claims` | string | No | "" | Optional draft claims for precise search |
| `classification` | string | No | "" | Estimated IPC/CPC code filter |
| `keywords` | string[] | No | [] | Core technical terms filter |
| `title_search` | string | No | "" | Substring match in title |
| `top_k` | int | No | 20 | Maximum results (1-100) |

#### Patent ID Search Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doc_number` | string | ✅ Yes | - | Patent document number (e.g., "US20240217263A1") |
| `classification` | string | No | "" | IPC/CPC code prefix filter |
| `top_k` | int | No | 20 | Maximum results (1-100) |

---

## Parameter Combinations Guide

### Recommended Combinations by Use Case

#### Use Case 1: Quick Exploration (Few Filters)

**Goal:** Get a broad view of similar patents

```json
// Invalidity - Just claims
{
  "query_claims": "A tire with embedded sensors...",
  "top_k": 30
}

// Patentability - Description only
{
  "invention_description": "An innovative monitoring system...",
  "top_k": 30
}
```

**When to use:** Starting research, exploring a new field

---

#### Use Case 2: Focused Search (Classification + Date)

**Goal:** Narrow to specific technical field and time period

```json
// Invalidity - Find prior art in tire field before 2022
{
  "query_claims": "A tire with embedded sensors...",
  "classification": "B60C",
  "target_date": "2022-01-01",
  "top_k": 20
}

// Infringement - Monitor tire patents in 2024-2025
{
  "my_claims": "A tire with embedded sensors...",
  "my_doc_number": "US12345678",
  "classification": "B60C",
  "date_from": "2024-01-01",
  "date_to": "2025-12-31",
  "top_k": 20
}
```

**When to use:** You know the technical field and relevant time period

---

#### Use Case 3: Precision Search (Classification + Keywords)

**Goal:** Find patents with specific technical features

```json
// Patentability - Find wireless sensor patents in tire field
{
  "invention_description": "A MEMS pressure sensor with wireless...",
  "classification": "B60C",
  "keywords": ["wireless", "sensor", "MEMS"],
  "top_k": 20
}

// Invalidity - Find prior art with specific features
{
  "query_claims": "A tire pressure monitoring system...",
  "classification": "B60C",
  "keywords": ["pressure", "monitoring", "wireless"],
  "target_date": "2020-06-15",
  "top_k": 20
}
```

**When to use:** Looking for patents with specific technical elements

---

#### Use Case 4: High-Risk Focus (High Similarity Threshold)

**Goal:** Only see the most similar patents (potential threats)

```json
// Infringement - Only high similarity results
{
  "my_claims": "A wheel rim with integrated pressure sensor...",
  "my_doc_number": "US12345678",
  "classification": "B60B",
  "min_similarity": 0.7,
  "date_from": "2023-01-01",
  "top_k": 10
}
```

**When to use:** Reviewing potential infringement threats, legal analysis

---

#### Use Case 5: Comprehensive Search (All Filters)

**Goal:** Maximum precision with all available filters

```json
// Invalidity - Full precision search
{
  "query_claims": "A tire comprising: a tread portion; a sidewall...",
  "query_doc_number": "US98765432",
  "classification": "B60C23",
  "keywords": ["pressure", "sensor", "wireless"],
  "title_search": "monitoring",
  "target_date": "2021-03-15",
  "top_k": 20
}

// Infringement - Full monitoring setup
{
  "my_claims": "A wheel rim with integrated pressure sensor...",
  "my_doc_number": "US12345678",
  "classification": "B60B21",
  "keywords": ["sensor", "pressure", "rim"],
  "title_search": "wheel",
  "date_from": "2023-06-01",
  "date_to": "2025-12-31",
  "min_similarity": 0.5,
  "top_k": 20
}
```

**When to use:** Final verification, detailed legal analysis

---

### Parameter Interaction Matrix

Shows how parameters work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILTER EFFECT DIAGRAM                        │
│                                                                 │
│  All Patents in Database                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                     classification                              │
│                            ▼                                    │
│  ┌─────────────────────────────────────────┐                   │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │ (~40% remain)    │
│  └─────────────────────────────────────────┘                   │
│                            │                                    │
│                      date filter                                │
│                            ▼                                    │
│  ┌───────────────────────────────┐                             │
│  │ ████████████████████████████ │ (~25% remain)                │
│  └───────────────────────────────┘                             │
│                            │                                    │
│                       keywords                                  │
│                            ▼                                    │
│  ┌─────────────────┐                                           │
│  │ ██████████████ │ (~10% remain)                              │
│  └─────────────────┘                                           │
│                            │                                    │
│                    semantic search                              │
│                            ▼                                    │
│  ┌─────────┐                                                   │
│  │ ██████ │ (top_k results, ranked by similarity)              │
│  └─────────┘                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Filter Priority (Processing Order)

Filters are applied in this order:

```
1. Classification Filter    (fastest, reduces dataset significantly)
         ↓
2. Date Filter             (fast, time-based filtering)
         ↓
3. Keywords Filter         (medium, text matching)
         ↓
4. Title Search Filter     (medium, substring matching)
         ↓
5. Semantic Search         (slowest, AI similarity computation)
         ↓
6. Similarity Threshold    (post-processing, filters results)
         ↓
7. Top K                   (final, limits output count)
```

**Performance tip:** Use classification first to reduce the dataset before semantic search runs.

---

### Common Parameter Mistakes

#### ❌ Mistake 1: Too Many Keywords

```json
// Bad: 7 keywords, very few results
{
  "keywords": ["wireless", "sensor", "pressure", "tire", "monitoring", "battery", "embedded"]
}

// Good: 2-3 specific keywords
{
  "keywords": ["wireless", "sensor", "pressure"]
}
```

#### ❌ Mistake 2: Classification Too Specific

```json
// Bad: Very specific code, may miss relevant patents
{
  "classification": "B60C23/0408"
}

// Good: Broader code, then narrow with keywords
{
  "classification": "B60C23",
  "keywords": ["pressure"]
}
```

#### ❌ Mistake 3: Missing Date Logic

```json
// Bad: Infringement without date range (searches all time)
{
  "my_claims": "...",
  "my_doc_number": "US12345678"
}

// Good: Specific monitoring period
{
  "my_claims": "...",
  "my_doc_number": "US12345678",
  "date_from": "2023-01-01",
  "date_to": "2025-12-31"
}
```

#### ❌ Mistake 4: Short Query Text

```json
// Bad: Too short, poor semantic matching
{
  "query_claims": "A tire with sensors"
}

// Good: Detailed technical description
{
  "query_claims": "A tire comprising a tread portion and a sidewall portion, wherein a wireless pressure sensor is embedded within the sidewall portion, the sensor including a power harvesting module configured to generate electrical energy from tire deformation during vehicle operation"
}
```

---

### Quick Reference: Best Combinations

| Scenario | Best Starter Combo | Best Precision Combo |
|----------|-------------------|---------------------|
| Invalidity | `claims` + `classification` + `target_date` | + `keywords` |
| Infringement | `claims` + `doc_number` + `date_from/to` | + `classification` + `min_similarity` |
| Patentability | `description` + `classification` | + `draft_claims` + `keywords` |
| Patent ID | `doc_number` only | + `classification` |

---

## Advanced Filtering Guide

### Filter Types Overview

| Filter | Description | Best For |
|--------|-------------|----------|
| Classification | IPC/CPC code prefix (e.g., "B60C") | Narrowing to technical field |
| Keywords | Required terms in text | Ensuring specific features |
| Title Search | Substring match in title | Quick topic filtering |
| Date Range | Before/after specific dates | Temporal relevance |
| Similarity Threshold | Minimum similarity score | Quality control |

### Classification Code Filter

IPC/CPC codes organize patents by technical field. Use partial codes for broader searches:

```
Code Hierarchy Example:
B       → Performing Operations; Transporting (very broad)
B60     → Vehicles in General (broad)
B60C    → Vehicle Tyres (specific)
B60C23  → Tyre pressure monitoring (very specific)
```

**Recommended approach:**
```
Start broad → Review results → Narrow if needed

B60C (100+ results) → B60C23 (20 results) → Add keywords (10 results)
```

**Common classification codes:**
| Code | Technical Field |
|------|-----------------|
| B60B | Wheels |
| B60C | Tyres |
| B60R | Vehicle fittings |
| H01M | Batteries |
| H04W | Wireless communication |
| G06F | Computing |
| A61K | Pharmaceuticals |

### Keywords Filter

Keywords require ALL specified terms to appear in the combined text (title + abstract + claims).

**Good keyword strategy:**
```json
// ✅ Good: Specific technical terms
"keywords": ["wireless", "sensor", "pressure"]

// ❌ Bad: Generic terms (too many results)
"keywords": ["system", "method", "device"]

// ❌ Bad: Too many keywords (too few results)
"keywords": ["wireless", "sensor", "pressure", "tire", "monitoring", "battery", "embedded"]
```

**Keyword combination tips:**
| Keywords | Result |
|----------|--------|
| ["sensor"] | Very broad |
| ["sensor", "tire"] | Moderate |
| ["sensor", "tire", "wireless"] | Specific |
| ["sensor", "tire", "wireless", "MEMS"] | Very specific |

### Title Search Filter

Searches for substring match in patent title only. Useful for quick filtering.

```json
// Find patents with "monitoring" in title
"title_search": "monitoring"

// More specific
"title_search": "pressure monitoring"
```

**Best for:**
- Quick topic filtering
- Finding patents about specific concepts
- Reducing result set before detailed analysis

### Date Filters

Different scenarios use dates differently:

| Scenario | Date Logic |
|----------|------------|
| Invalidity | `target_date`: Results BEFORE this date |
| Infringement | `date_from`/`date_to`: Results WITHIN range |
| Patentability | No date filter (all prior art matters) |

**Date format:** `YYYY-MM-DD`

```json
// Invalidity: Find prior art before June 2022
"target_date": "2022-06-15"

// Infringement: Monitor 2024-2025
"date_from": "2024-01-01",
"date_to": "2025-12-31"
```

### Similarity Threshold (Infringement Only)

Sets minimum similarity score to return:

```json
"min_similarity": 0.5    // Only return ≥50% similar
"min_similarity": 0.7    // Only return ≥70% similar (stricter)
```

**Recommended values:**
| Value | Use Case |
|-------|----------|
| 0.3 | Broad exploration |
| 0.5 | Standard monitoring (default) |
| 0.7 | High-risk focus only |
| 0.8 | Very high similarity only |

---

## Best Practices

### 1. Start Broad, Then Narrow

```
Step 1: No filters
         ↓
    Review results
         ↓
Step 2: Add classification
         ↓
    Review results
         ↓
Step 3: Add keywords if needed
         ↓
    Final results
```

### 2. Write Good Query Text

**For Claims-based searches (Invalidity, Infringement):**

```
❌ Bad: Short, generic
"A tire with sensors"

✅ Good: Detailed, technical
"A tire comprising: a tread portion; a sidewall portion extending
from the tread portion; a wireless pressure sensor embedded within
the sidewall portion; and a power harvesting module configured to
generate electrical energy from tire deformation"
```

**For Invention Description (Patentability):**

```
❌ Bad: Vague concept
"A new type of tire sensor"

✅ Good: Specific technical details
"An innovative tire pressure monitoring system featuring a MEMS-based
pressure sensor embedded in the tire sidewall, utilizing piezoelectric
energy harvesting from tire flexion to power wireless transmission
of pressure data to a vehicle ECU via Bluetooth Low Energy protocol"
```

### 3. Filter Combination Strategies

| Goal | Recommended Filters |
|------|---------------------|
| Broad exploration | Classification only |
| Specific technology | Classification + 1-2 keywords |
| Exact match finding | Classification + 3+ keywords + title |
| Time-specific | Date range + classification |

### 4. Interpret Results Correctly

**Similarity scores are relative, not absolute:**

| Score | Interpretation |
|-------|----------------|
| 0.9+ | Very high overlap, likely same concept |
| 0.7-0.9 | Significant similarity, review claims carefully |
| 0.5-0.7 | Moderate similarity, some overlapping features |
| 0.3-0.5 | Low similarity, different approaches |
| <0.3 | Minimal relevance |

---

## Common Workflows

### Workflow 1: Defending Against Infringement Lawsuit

```
1. Invalidity Search
   - Input: Plaintiff's patent claims
   - Target date: Plaintiff's priority date
   - Goal: Find prior art to invalidate

2. Review results
   - Look for high similarity scores
   - Check publication dates are BEFORE target
   - Document potential invalidating references

3. Refine search
   - Add classification if too many results
   - Adjust keywords based on claim elements
```

### Workflow 2: Pre-Filing Patentability Check

```
1. Patentability Assessment
   - Input: Detailed invention description + draft claims
   - No date filter
   - Classification: Estimated IPC code

2. Analyze novelty assessments
   - "Novel" results: Good prospects
   - "Similar" results: Identify differentiating features
   - "Identical" results: May need to pivot

3. Iterate
   - Refine claims to differentiate
   - Re-run search with updated claims
```

### Workflow 3: Ongoing Patent Monitoring

```
1. Initial Setup
   - Infringement search with your patent claims
   - Set date range: Last 6 months
   - Set similarity threshold: 0.5

2. Monthly Review
   - Update date_from to last search date
   - Review new high-risk results
   - Document potential infringers

3. Deep Dive (when needed)
   - Use Patent ID Search on flagged patents
   - Find related patents in same family
```

### Workflow 4: Technology Landscape Analysis

```
1. Start with Patent ID Search
   - Input: Known relevant patent number
   - Find 20 similar patents

2. Expand with Patentability Search
   - Use key claims as query
   - Broad classification
   - No keywords (explore widely)

3. Map the landscape
   - Identify key players (assignees)
   - Identify technology clusters
   - Find white spaces (gaps)
```

---

## Summary

| Scenario | Question Answered | Date Logic | Key Output |
|----------|-------------------|------------|------------|
| Invalidity | "What prior art exists?" | Before target | Similarity + claims |
| Infringement | "Who might be copying me?" | Within range | Risk level + overlap |
| Patentability | "Is my invention novel?" | All time | Novelty assessment |
| Patent ID | "What's similar to this patent?" | None | Similar patents |

**Remember:**
- Use the right scenario for your goal
- Start broad, narrow with filters
- Write detailed, technical query text
- Combine filters strategically
- Interpret scores in context
