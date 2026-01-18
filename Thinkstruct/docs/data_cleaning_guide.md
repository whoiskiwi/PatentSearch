# Thinkstruct Patent Data Cleaning Guide

## Overview

`data/clean_patent_data.py` is the data preprocessing tool for the Thinkstruct patent search system, used to clean, validate, and convert raw patent JSON data into searchable structured datasets.

## Features

- Automatic discovery and reading of `patents_ipa*.json` format patent files
- Field validation for three search scenarios
- Flexible missing value handling strategies
- Deduplication based on doc_number
- Detailed cleaning reports and statistics
- **Claims cleaning**: Automatic removal of numeric prefixes and invalid entries

---

## Quick Start

### Basic Usage

```bash
# Process data with default configuration
python data/clean_patent_data.py /path/to/patent/data

# View help information
python data/clean_patent_data.py --help
```

### Common Examples

```bash
# Specify output directory
python data/clean_patent_data.py /path/to/input -o /path/to/output

# Use remove strategy for missing fields
python data/clean_patent_data.py --strategy remove

# Preserve paragraph structure (don't merge detailed description)
python data/clean_patent_data.py --description-mode preserve

# Output as CSV format
python data/clean_patent_data.py --format csv

# Combine multiple options
python data/clean_patent_data.py /data/patents -o /output --strategy fill --format json
```

---

## Configuration Options

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `input_dir` | Current directory | Input folder path |
| `-o, --output` | `{input_dir}/../cleaned_output` | Output folder path |
| `--strategy` | `fill` | Missing value handling strategy: `fill` or `remove` |
| `--description-mode` | `merge` | Detailed description processing mode: `merge` or `preserve` |
| `--format` | `json` | Output format: `json` or `csv` |

### Missing Value Handling Strategies

#### Strategy A: `remove` (Discard)

Discard records with empty core required fields.

```bash
python data/clean_patent_data.py --strategy remove
```

**Use Cases:**
- Analysis tasks requiring complete data
- Data quality is more important than data coverage

**Core Required Fields:**
- doc_number
- title
- abstract
- claims
- classification

#### Strategy B: `fill` (Fill) - Recommended

Keep all records, fill missing fields with default values.

```bash
python data/clean_patent_data.py --strategy fill
```

**Use Cases:**
- Patent search (better to return more than miss any)
- Maximum data coverage required

**Default Value Definitions:**
| Field Type | Default Value |
|------------|---------------|
| String fields | `""` (empty string) |
| List fields | `[]` (empty list) |

### Detailed Description Processing Modes

#### Mode A: `merge` (Combine) - Recommended

Merge paragraph list into single text, paragraphs separated by double newlines.

```bash
python data/clean_patent_data.py --description-mode merge
```

**Output Example:**
```json
{
  "detailed_description": "First paragraph content...\n\nSecond paragraph content...\n\nThird paragraph content..."
}
```

**Use Cases:**
- Full-text search
- Keyword search

#### Mode B: `preserve` (Keep Structure)

Preserve original paragraph list structure.

```bash
python data/clean_patent_data.py --description-mode preserve
```

**Output Example:**
```json
{
  "detailed_description": [
    "First paragraph content...",
    "Second paragraph content...",
    "Third paragraph content..."
  ]
}
```

**Use Cases:**
- Paragraph-level indexing
- Document structure analysis

---

## Claims Cleaning

### Numeric Prefix Removal

Claims in raw patent data typically have numeric prefixes (e.g., `16 . A tire...`), the script automatically cleans these:

**Before Cleaning:**
```
"16 . A tire comprising a tread portion..."
"1-15 . (canceled)"
"17. The tire of claim 16..."
```

**After Cleaning:**
```
"A tire comprising a tread portion..."
(filtered out)
"The tire of claim 16..."
```

**Cleaning Rules:**
```python
# Remove leading numeric identifiers, e.g., "16 ." or "1-15 ."
text = re.sub(r'^\d+\s*\.?\s*-?\s*\d*\s*\.?\s*', '', text)
```

### Invalid Entry Filtering

The script automatically filters the following invalid claims:

| Type | Example | Handling |
|------|---------|----------|
| Canceled | `(canceled)` | Filter |
| Empty entries | `""` | Filter |
| Too short | Less than 10 characters | Filter |

**Filtering Rules:**
```python
def is_claim_valid(claim: str) -> bool:
    if not claim:
        return False
    text = claim.strip().lower()
    if text == "(canceled)" or text == "canceled":
        return False
    if len(text) < 10:
        return False
    return True
```

---

## Search Scenario Field Configuration

The script defines different field requirements for three core search scenarios:

### 1. Invalidity Search

**Goal:** Find prior art that could invalidate target patent

| Field Level | Field List |
|-------------|------------|
| **Required** | doc_number, claims, abstract |
| **Important** | title, classification |
| **Optional** | detailed_description, bibtex, filename |

### 2. Infringement Monitoring

**Goal:** Monitor if new patents infringe your patent rights

| Field Level | Field List |
|-------------|------------|
| **Required** | doc_number, claims, classification |
| **Important** | title, abstract |
| **Optional** | detailed_description, bibtex, filename |

### 3. Patentability Review

**Goal:** Evaluate patentability of new inventions

| Field Level | Field List |
|-------------|------------|
| **Required** | doc_number, title, abstract |
| **Important** | claims, classification |
| **Optional** | detailed_description, bibtex, filename |

---

## Output File Description

### Data File

**Filename Format:** `patents_cleaned_{timestamp}.json` or `.csv`

**Field Description:**

| Field | Type | Description |
|-------|------|-------------|
| `doc_number` | string | Patent document number (unique identifier) |
| `title` | string | Patent title |
| `abstract` | string | Patent abstract |
| `detailed_description` | string/list | Detailed description (depends on processing mode) |
| `claims` | list[string] | Claims list |
| `bibtex` | string | BibTeX citation format |
| `classification` | string | Technical classification code |
| `source_file` | string | Source filename |
| `is_description_empty` | bool | Whether detailed description is empty |
| `valid_for_invalidity` | bool | Whether meets invalidity search field requirements |
| `valid_for_infringement` | bool | Whether meets infringement monitoring field requirements |
| `valid_for_patentability` | bool | Whether meets patentability review field requirements |

### Cleaning Report

**Filename Format:** `cleaning_report_{timestamp}.json`

**Report Structure:**

```json
{
  "metadata": {
    "generated_at": "2026-01-16T15:56:41.808492",
    "missing_field_strategy": "fill",
    "description_mode": "merge",
    "processing_time_seconds": 0.04
  },
  "summary": {
    "total_files_processed": 64,
    "total_files_with_errors": 0,
    "total_records_raw": 640,
    "total_records_kept": 640,
    "total_records_removed": 0,
    "removal_breakdown": {
      "invalid_records": 0,
      "duplicate_records": 0
    }
  },
  "scenario_validation": {
    "invalidity": {
      "valid_records": 640,
      "invalid_records": 0,
      "validity_rate": 100.0
    },
    "infringement": { ... },
    "patentability": { ... }
  },
  "field_statistics": {
    "missing_fields": { ... },
    "empty_fields": { ... }
  }
}
```

---

## Deduplication Rules

### Deduplication Criteria

Deduplication based on `doc_number` field:
- Keep the first occurrence of each record
- Subsequent records with the same doc_number are removed
- Records with empty doc_number are assigned temporary unique identifiers

### Deduplication Statistics

The report records:
- Number of duplicate records
- Sample of duplicate doc_numbers (up to 20)

---

## Programming Interface

### Import as Module

```python
from data.clean_patent_data import clean_patent_data, save_output

# Execute cleaning
cleaned_data, stats = clean_patent_data(
    input_dir="/path/to/patents",
    output_dir="/path/to/output"
)

# Save results
output_files = save_output(
    cleaned_data=cleaned_data,
    stats=stats,
    output_dir="/path/to/output",
    output_format="json"
)

# Access statistics
print(f"Records processed: {stats.total_records_raw}")
print(f"Records kept: {stats.total_records_kept}")
print(f"Scenario validation: {stats.scenario_stats}")
```

### Custom Field Validation

```python
from data.clean_patent_data import (
    validate_for_scenario,
    SCENARIO_FIELD_REQUIREMENTS
)

# Validate single record
record = {"doc_number": "123", "title": "Test", ...}
result = validate_for_scenario(record, "invalidity")

print(f"Valid: {result.is_valid}")
print(f"Missing required fields: {result.missing_required}")
print(f"Empty required fields: {result.empty_required}")
```

---

## FAQ

### Q: Why is `fill` strategy the default?

The core principle of patent search is "don't miss any". Even if some fields are empty (like detailed_description), other fields (title, abstract, claims) still have important retrieval value. Using the `fill` strategy:
- Maximizes data coverage
- Preserves potentially relevant patent information
- Lets users decide how to handle incomplete records

### Q: Does empty `detailed_description` affect search?

Data analysis shows about 18.6% of records have empty detailed_description, but these records' other core fields (title, abstract, claims, classification) are usually complete. For most search scenarios, these fields are sufficient for effective technical matching.

### Q: How to handle large amounts of data?

The script is optimized for performance:
- Stream processing of files, avoiding loading all data at once
- O(1) deduplication using dictionaries
- Real-time statistics updates, no need for second pass

For very large datasets, consider:
- Processing files in batches
- Using CSV format output (smaller storage)
- Using database storage

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-01-17 | Added claims cleaning (numeric prefix removal, canceled entry filtering) |
| 2.0 | 2026-01-16 | Added scenario-based field validation, restructured code |
| 1.0 | 2026-01-16 | Initial version |

---

## Related Documentation

- [Advanced Features](./advanced_features.md) - Future features roadmap
- [README](../README.md) - Project main documentation

---

*Document Version: 2.1*
*Last Updated: 2026-01-17*
