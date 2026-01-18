#!/usr/bin/env python3
"""
Patent Data Cleaning Pipeline
================================================================================

Thinkstruct Patent Search System Data Preprocessing Tool

Features:
- Traverse specified folder and read all patents_ipa{DATE}.json files
- Parse key fields from patent records
- Support field validation for three search scenarios: invalidity, infringement, patentability
- Implement missing field handling strategies
- Consolidate patent data from all files into unified data structure
- Output cleaned structured dataset

================================================================================
Scenario-based Field Configuration
================================================================================

This script supports three patent search scenarios with different field requirements:

1. Invalidity Search (invalidity)
   - Goal: Find prior art that could invalidate target patent
   - Core fields: claims, abstract (for technical feature matching)
   - Required fields: doc_number, claims, abstract, title, classification

2. Infringement Monitoring (infringement)
   - Goal: Monitor if new patents infringe your patent rights
   - Core fields: claims, classification (for identifying technical overlap)
   - Required fields: doc_number, claims, classification, title, abstract

3. Patentability Review (patentability)
   - Goal: Evaluate patentability of new inventions
   - Core fields: abstract, title (for broad prior art search)
   - Required fields: doc_number, title, abstract, claims, classification

================================================================================
Missing Value Handling Strategy
================================================================================

MISSING_FIELD_STRATEGY = "fill" (default)

Strategy B ("fill"): Keep records with missing fields, fill with default values
- Advantage: Maximize data retention, suitable for information retrieval scenarios
- Patent search principle: "Better to return more than to miss any"
- Even if detailed_description is empty, other fields still have retrieval value

================================================================================
"""

import json
import re
import logging
import time
from typing import Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================================================
# Scenario Definition and Field Configuration
# ============================================================================

class SearchScenario(Enum):
    """Search scenario enumeration"""
    INVALIDITY = "invalidity"        # Invalidity search
    INFRINGEMENT = "infringement"    # Infringement monitoring
    PATENTABILITY = "patentability"  # Patentability review
    ALL = "all"                      # Universal (satisfies all scenarios)


# Define field requirements by scenario
SCENARIO_FIELD_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    "invalidity": {
        "required": ["doc_number", "claims", "abstract"],
        "important": ["title", "classification"],
        "optional": ["detailed_description", "bibtex", "filename"]
    },
    "infringement": {
        "required": ["doc_number", "claims", "classification"],
        "important": ["title", "abstract"],
        "optional": ["detailed_description", "bibtex", "filename"]
    },
    "patentability": {
        "required": ["doc_number", "title", "abstract"],
        "important": ["claims", "classification"],
        "optional": ["detailed_description", "bibtex", "filename"]
    }
}

# Core required fields = union of required + important from all three scenarios
CORE_REQUIRED_FIELDS: list[str] = [
    "doc_number",
    "title",
    "abstract",
    "claims",
    "classification"
]

# All supported fields
ALL_FIELDS: list[str] = [
    "doc_number",
    "title",
    "abstract",
    "detailed_description",
    "claims",
    "bibtex",
    "classification",
    "filename"
]

# ============================================================================
# Configuration Constants
# ============================================================================

# Missing value handling strategy: "remove" or "fill"
MISSING_FIELD_STRATEGY: str = "fill"

# Detailed Description processing mode: "merge" or "preserve"
DESCRIPTION_MODE: str = "merge"

# Default values
DEFAULT_VALUES: dict[str, Any] = {
    "doc_number": "",
    "title": "",
    "abstract": "",
    "detailed_description": "",
    "claims": [],
    "bibtex": "",
    "classification": "",
    "filename": ""
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Class Definitions
# ============================================================================

@dataclass
class FieldValidationResult:
    """Field validation result"""
    is_valid: bool
    missing_required: list[str] = field(default_factory=list)
    missing_important: list[str] = field(default_factory=list)
    empty_required: list[str] = field(default_factory=list)
    empty_important: list[str] = field(default_factory=list)


@dataclass
class ScenarioStats:
    """Scenario validation statistics"""
    scenario: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    missing_field_counts: dict[str, int] = field(default_factory=dict)
    empty_field_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class CleaningStats:
    """Data cleaning statistics"""
    total_files: int = 0
    total_records_raw: int = 0
    total_records_kept: int = 0
    total_records_removed: int = 0
    duplicate_count: int = 0
    invalid_count: int = 0
    field_missing_stats: dict[str, int] = field(default_factory=dict)
    field_empty_stats: dict[str, int] = field(default_factory=dict)
    scenario_stats: dict[str, ScenarioStats] = field(default_factory=dict)
    files_processed: list[str] = field(default_factory=list)
    files_with_errors: list[dict] = field(default_factory=list)
    duplicate_doc_numbers: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0

    def to_dict(self) -> dict:
        result = asdict(self)
        # Convert ScenarioStats to dict
        result["scenario_stats"] = {
            k: asdict(v) for k, v in self.scenario_stats.items()
        }
        return result


@dataclass
class PatentRecord:
    """Cleaned patent record"""
    doc_number: str
    title: str
    abstract: str
    detailed_description: str | list[str]
    claims: list[str]
    bibtex: str
    classification: str
    source_file: str
    publication_date: str = ""  # Publication date extracted from filename (YYYY-MM-DD)
    is_description_empty: bool = False
    # Scenario validity flags
    valid_for_invalidity: bool = True
    valid_for_infringement: bool = True
    valid_for_patentability: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def extract_publication_date(filename: str) -> str:
    """
    Extract publication date from filename

    Filename format: patents_ipa{YYMMDD}.json
    Example: patents_ipa240704.json -> 2024-07-04

    Args:
        filename: Source filename

    Returns:
        Formatted date string (YYYY-MM-DD), empty string if extraction fails
    """
    match = re.search(r'patents_ipa(\d{6})\.json', filename)
    if match:
        date_str = match.group(1)  # e.g., "240704"
        year = "20" + date_str[:2]
        month = date_str[2:4]
        day = date_str[4:6]
        return f"{year}-{month}-{day}"
    return ""


# ============================================================================
# Module 1: File Reading
# ============================================================================

def discover_patent_files(input_dir: str | Path) -> list[Path]:
    """
    Discover and return all patent JSON files matching the pattern in specified directory

    Args:
        input_dir: Input folder path

    Returns:
        List of file paths matching patents_ipa*.json pattern, sorted by filename
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_path}")

    if not input_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {input_path}")

    # Use glob to match patents_ipa*.json pattern
    pattern = "patents_ipa*.json"
    all_files = list(input_path.glob(pattern))

    # Filter out already processed files
    exclude_pattern = re.compile(r"_(cleaned|final|merged)\.json$")
    patent_files = [f for f in all_files if not exclude_pattern.search(f.name)]

    # Sort by filename
    patent_files.sort(key=lambda x: x.name)

    logger.info(f"Found {len(patent_files)} patent files to process")

    return patent_files


def read_patent_file(file_path: Path) -> tuple[list[dict], Optional[str]]:
    """
    Read a single patent JSON file

    Args:
        file_path: JSON file path

    Returns:
        (patent record list, error message or None)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            return [], f"File content is not a list: {type(data)}"

        return data, None

    except json.JSONDecodeError as e:
        return [], f"JSON parsing error: {str(e)}"
    except UnicodeDecodeError as e:
        return [], f"Encoding error: {str(e)}"
    except Exception as e:
        return [], f"Read error: {str(e)}"


# ============================================================================
# Module 2: Field Validation and Parsing
# ============================================================================

def is_field_empty(value: Any) -> bool:
    """
    Check if field value is empty

    Empty value definition:
    - None
    - Empty string or string containing only whitespace
    - Empty list
    - List where all elements are empty strings
    """
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    if isinstance(value, list):
        if len(value) == 0:
            return True
        return all(
            isinstance(item, str) and item.strip() == ""
            for item in value
        )

    return False


def validate_for_scenario(
    record: dict,
    scenario: str
) -> FieldValidationResult:
    """
    Validate if record meets field requirements for specific scenario

    Args:
        record: Patent record dictionary
        scenario: Search scenario name

    Returns:
        FieldValidationResult validation result
    """
    if scenario not in SCENARIO_FIELD_REQUIREMENTS:
        raise ValueError(f"Unknown scenario: {scenario}")

    requirements = SCENARIO_FIELD_REQUIREMENTS[scenario]
    result = FieldValidationResult(is_valid=True)

    # Check required fields
    for field_name in requirements["required"]:
        if field_name not in record:
            result.missing_required.append(field_name)
            result.is_valid = False
        elif is_field_empty(record[field_name]):
            result.empty_required.append(field_name)
            result.is_valid = False

    # Check important fields (does not affect validity, but record statistics)
    for field_name in requirements["important"]:
        if field_name not in record:
            result.missing_important.append(field_name)
        elif is_field_empty(record[field_name]):
            result.empty_important.append(field_name)

    return result


def validate_for_all_scenarios(record: dict) -> dict[str, FieldValidationResult]:
    """
    Validate record validity for all scenarios

    Args:
        record: Patent record dictionary

    Returns:
        Dictionary of validation results for each scenario
    """
    return {
        scenario: validate_for_scenario(record, scenario)
        for scenario in SCENARIO_FIELD_REQUIREMENTS.keys()
    }


def process_detailed_description(
    description: Any,
    mode: str = "merge"
) -> tuple[str | list[str], bool]:
    """
    Process Detailed Description field

    Args:
        description: Raw description field (usually a list of paragraphs)
        mode: Processing mode - "merge" (combine) or "preserve" (keep structure)

    Returns:
        (processed description, is_empty)
    """
    is_empty = is_field_empty(description)

    if is_empty:
        return ("" if mode == "merge" else []), True

    if isinstance(description, list):
        paragraphs = [
            p.strip() for p in description
            if isinstance(p, str) and p.strip()
        ]

        if not paragraphs:
            return ("" if mode == "merge" else []), True

        if mode == "merge":
            return "\n\n".join(paragraphs), False
        else:
            return paragraphs, False

    if isinstance(description, str):
        text = description.strip()
        if mode == "merge":
            return text, len(text) == 0
        else:
            return [text] if text else [], len(text) == 0

    try:
        text = str(description).strip()
        if mode == "merge":
            return text, len(text) == 0
        else:
            return [text] if text else [], len(text) == 0
    except Exception:
        return ("" if mode == "merge" else []), True


def clean_single_claim(claim: str) -> str:
    """
    Clean a single claim

    Processing:
    1. Remove leading numeric prefixes (e.g., "2 .", "16 .", "1 .- 14 .")
    2. Remove extra whitespace

    Args:
        claim: Original claim text

    Returns:
        Cleaned claim text
    """
    if not claim:
        return ""

    text = claim.strip()

    # Remove leading numeric prefixes, supports formats:
    # "2 . The apparatus..." -> "The apparatus..."
    # "16. The method..." -> "The method..."
    # "1 .- 14 . (canceled)" -> "(canceled)"
    # Regex matches: leading numbers (possibly with range like 1-14), followed by period and space
    text = re.sub(r'^\d+\s*\.?\s*-?\s*\d*\s*\.?\s*', '', text)

    return text.strip()


def is_claim_valid(claim: str) -> bool:
    """
    Check if claim is valid

    Invalid cases:
    1. Empty string
    2. Only contains "(canceled)" or "(Canceled)"
    3. Too short (less than 10 characters, might be leftover numbering)

    Args:
        claim: Claim text

    Returns:
        Whether valid
    """
    if not claim:
        return False

    text = claim.strip().lower()

    # Check if canceled
    if text == "(canceled)" or text == "canceled":
        return False

    # Check if too short
    if len(text) < 10:
        return False

    return True


def process_claims(claims: Any) -> list[str]:
    """
    Process Claims field

    Processing logic:
    1. Remove leading numeric prefixes (e.g., "2 .", "16 .")
    2. Filter out "(canceled)" entries
    3. Remove whitespace and invalid entries

    Args:
        claims: Original claims field

    Returns:
        Cleaned claims list
    """
    if is_field_empty(claims):
        return []

    result = []

    if isinstance(claims, list):
        for c in claims:
            if isinstance(c, str):
                cleaned = clean_single_claim(c)
                if is_claim_valid(cleaned):
                    result.append(cleaned)
    elif isinstance(claims, str):
        cleaned = clean_single_claim(claims)
        if is_claim_valid(cleaned):
            result.append(cleaned)

    return result


def parse_patent_record(
    raw_record: dict,
    source_file: str,
    stats: CleaningStats
) -> Optional[PatentRecord]:
    """
    Parse a single patent record

    Args:
        raw_record: Raw patent record dictionary
        source_file: Source filename
        stats: Statistics object (will be modified)

    Returns:
        Parsed PatentRecord, or None if record is invalid
    """
    # Validate all scenarios
    scenario_results = validate_for_all_scenarios(raw_record)

    # Update field statistics
    for field_name in ALL_FIELDS:
        if field_name not in raw_record:
            stats.field_missing_stats[field_name] = \
                stats.field_missing_stats.get(field_name, 0) + 1
        elif is_field_empty(raw_record[field_name]):
            stats.field_empty_stats[field_name] = \
                stats.field_empty_stats.get(field_name, 0) + 1

    # Update scenario statistics
    for scenario, result in scenario_results.items():
        if scenario not in stats.scenario_stats:
            stats.scenario_stats[scenario] = ScenarioStats(scenario=scenario)

        scenario_stat = stats.scenario_stats[scenario]
        scenario_stat.total_records += 1

        if result.is_valid:
            scenario_stat.valid_records += 1
        else:
            scenario_stat.invalid_records += 1

        # Count missing fields
        for field_name in result.missing_required + result.missing_important:
            scenario_stat.missing_field_counts[field_name] = \
                scenario_stat.missing_field_counts.get(field_name, 0) + 1

        # Count empty fields
        for field_name in result.empty_required + result.empty_important:
            scenario_stat.empty_field_counts[field_name] = \
                scenario_stat.empty_field_counts.get(field_name, 0) + 1

    # Check if core required fields are satisfied (intersection of all scenarios)
    core_valid = True
    if MISSING_FIELD_STRATEGY == "remove":
        for field_name in CORE_REQUIRED_FIELDS:
            if field_name not in raw_record or is_field_empty(raw_record[field_name]):
                core_valid = False
                break

        if not core_valid:
            stats.invalid_count += 1
            return None

    # Extract and process fields
    doc_number = str(raw_record.get("doc_number", "")).strip() or DEFAULT_VALUES["doc_number"]
    title = str(raw_record.get("title", "")).strip() or DEFAULT_VALUES["title"]
    abstract = str(raw_record.get("abstract", "")).strip() or DEFAULT_VALUES["abstract"]
    bibtex = str(raw_record.get("bibtex", "")).strip() or DEFAULT_VALUES["bibtex"]
    classification = str(raw_record.get("classification", "")).strip() or DEFAULT_VALUES["classification"]
    filename = str(raw_record.get("filename", "")).strip() or DEFAULT_VALUES["filename"]

    # Process Detailed Description
    raw_description = raw_record.get("detailed_description", [])
    detailed_description, is_desc_empty = process_detailed_description(
        raw_description,
        mode=DESCRIPTION_MODE
    )

    # Process Claims
    claims = process_claims(raw_record.get("claims", []))

    # Extract publication date from filename
    publication_date = extract_publication_date(source_file)

    return PatentRecord(
        doc_number=doc_number,
        title=title,
        abstract=abstract,
        detailed_description=detailed_description,
        claims=claims,
        bibtex=bibtex,
        classification=classification,
        source_file=source_file,
        publication_date=publication_date,
        is_description_empty=is_desc_empty,
        valid_for_invalidity=scenario_results["invalidity"].is_valid,
        valid_for_infringement=scenario_results["infringement"].is_valid,
        valid_for_patentability=scenario_results["patentability"].is_valid
    )


# ============================================================================
# Module 3: Data Consolidation and Deduplication
# ============================================================================

def deduplicate_records(
    records: list[PatentRecord],
    stats: CleaningStats
) -> list[PatentRecord]:
    """
    Deduplicate based on doc_number

    Args:
        records: Patent record list
        stats: Statistics object (will be modified)

    Returns:
        Deduplicated record list
    """
    seen_doc_numbers: dict[str, int] = {}
    unique_records: list[PatentRecord] = []

    for record in records:
        doc_num = record.doc_number

        if not doc_num:
            doc_num = f"_empty_{len(unique_records)}"

        if doc_num in seen_doc_numbers:
            stats.duplicate_count += 1
            stats.duplicate_doc_numbers.append(doc_num)
        else:
            seen_doc_numbers[doc_num] = len(unique_records)
            unique_records.append(record)

    logger.info(f"Deduplication complete: removed {stats.duplicate_count} duplicate records")

    return unique_records


# ============================================================================
# Module 4: Main Processing Flow
# ============================================================================

def clean_patent_data(
    input_dir: str | Path,
    output_dir: Optional[str | Path] = None
) -> tuple[list[dict], CleaningStats]:
    """
    Main data cleaning function

    Args:
        input_dir: Input folder path
        output_dir: Output folder path (optional)

    Returns:
        (cleaned data list, statistics)
    """
    start_time = time.time()
    stats = CleaningStats()

    # Initialize statistics fields
    for field_name in ALL_FIELDS:
        stats.field_missing_stats[field_name] = 0
        stats.field_empty_stats[field_name] = 0

    # Initialize scenario statistics
    for scenario in SCENARIO_FIELD_REQUIREMENTS.keys():
        stats.scenario_stats[scenario] = ScenarioStats(scenario=scenario)

    # Discover files
    input_path = Path(input_dir)
    patent_files = discover_patent_files(input_path)
    stats.total_files = len(patent_files)

    if not patent_files:
        logger.warning("No patent files found")
        return [], stats

    # Process all files
    all_records: list[PatentRecord] = []

    for i, file_path in enumerate(patent_files, 1):
        logger.info(f"[{i}/{len(patent_files)}] Processing file: {file_path.name}")

        records, error = read_patent_file(file_path)

        if error:
            logger.error(f"  Error: {error}")
            stats.files_with_errors.append({
                "filename": file_path.name,
                "error": error
            })
            continue

        stats.files_processed.append(file_path.name)
        file_record_count = len(records)
        stats.total_records_raw += file_record_count

        file_valid_count = 0
        for raw_record in records:
            parsed = parse_patent_record(
                raw_record,
                source_file=file_path.name,
                stats=stats
            )
            if parsed:
                all_records.append(parsed)
                file_valid_count += 1

        logger.info(f"  Parsing complete: {file_valid_count}/{file_record_count} valid records")

    # Deduplicate
    logger.info("Performing deduplication...")
    unique_records = deduplicate_records(all_records, stats)

    # Update statistics
    stats.total_records_kept = len(unique_records)
    stats.total_records_removed = stats.total_records_raw - stats.total_records_kept
    stats.processing_time_seconds = round(time.time() - start_time, 2)

    # Convert to dictionary list
    cleaned_data = [record.to_dict() for record in unique_records]

    return cleaned_data, stats


# ============================================================================
# Module 5: Output
# ============================================================================

def save_output(
    cleaned_data: list[dict],
    stats: CleaningStats,
    output_dir: str | Path,
    output_format: str = "json"
) -> dict[str, Path]:
    """
    Save cleaned data and report

    Args:
        cleaned_data: Cleaned data list
        stats: Statistics
        output_dir: Output directory
        output_format: Output format ("json" or "csv")

    Returns:
        Dictionary containing output file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = {}

    # Save main data file
    if output_format == "json":
        data_file = output_path / f"patents_cleaned_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        output_files["data"] = data_file
        logger.info(f"Data saved to: {data_file}")

    elif output_format == "csv":
        import csv
        data_file = output_path / f"patents_cleaned_{timestamp}.csv"

        if cleaned_data:
            fieldnames = list(cleaned_data[0].keys())
            with open(data_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in cleaned_data:
                    row = {}
                    for k, v in record.items():
                        if isinstance(v, list):
                            row[k] = json.dumps(v, ensure_ascii=False)
                        else:
                            row[k] = v
                    writer.writerow(row)

        output_files["data"] = data_file
        logger.info(f"Data saved to: {data_file}")

    # Generate and save cleaning report
    report = generate_report(stats)
    report_file = output_path / f"cleaning_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    output_files["report"] = report_file
    logger.info(f"Report saved to: {report_file}")

    # Print summary
    print_report_summary(report)

    return output_files


def generate_report(stats: CleaningStats) -> dict:
    """
    Generate data cleaning report

    Args:
        stats: Statistics

    Returns:
        Report dictionary
    """
    # Calculate valid record counts for each scenario
    scenario_summary = {}
    for scenario, scenario_stat in stats.scenario_stats.items():
        scenario_summary[scenario] = {
            "valid_records": scenario_stat.valid_records,
            "invalid_records": scenario_stat.invalid_records,
            "validity_rate": round(
                scenario_stat.valid_records / scenario_stat.total_records * 100, 2
            ) if scenario_stat.total_records > 0 else 0,
            "missing_fields": scenario_stat.missing_field_counts,
            "empty_fields": scenario_stat.empty_field_counts
        }

    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "missing_field_strategy": MISSING_FIELD_STRATEGY,
            "description_mode": DESCRIPTION_MODE,
            "processing_time_seconds": stats.processing_time_seconds
        },
        "summary": {
            "total_files_processed": len(stats.files_processed),
            "total_files_with_errors": len(stats.files_with_errors),
            "total_records_raw": stats.total_records_raw,
            "total_records_kept": stats.total_records_kept,
            "total_records_removed": stats.total_records_removed,
            "removal_breakdown": {
                "invalid_records": stats.invalid_count,
                "duplicate_records": stats.duplicate_count
            }
        },
        "scenario_validation": scenario_summary,
        "field_statistics": {
            "missing_fields": stats.field_missing_stats,
            "empty_fields": stats.field_empty_stats,
            "most_frequent_empty_field": max(
                stats.field_empty_stats.items(),
                key=lambda x: x[1],
                default=("none", 0)
            )
        },
        "files_processed": stats.files_processed,
        "files_with_errors": stats.files_with_errors,
        "duplicate_doc_numbers_sample": stats.duplicate_doc_numbers[:20]
    }

    return report


def print_report_summary(report: dict) -> None:
    """Print report summary to console"""
    print("\n" + "=" * 70)
    print("Data Cleaning Report Summary")
    print("=" * 70)

    summary = report["summary"]
    metadata = report["metadata"]
    field_stats = report["field_statistics"]
    scenario_validation = report["scenario_validation"]

    print(f"\n[Configuration]")
    print(f"  Missing value strategy: {metadata['missing_field_strategy']}")
    print(f"  Description processing mode: {metadata['description_mode']}")
    print(f"  Processing time: {metadata['processing_time_seconds']} seconds")

    print(f"\n[Processing Statistics]")
    print(f"  Files processed: {summary['total_files_processed']}")
    print(f"  Files with errors: {summary['total_files_with_errors']}")
    print(f"  Total raw records: {summary['total_records_raw']}")
    print(f"  Total records kept: {summary['total_records_kept']}")
    print(f"  Total records removed: {summary['total_records_removed']}")

    print(f"\n[Scenario Validity Validation]")
    for scenario, stats in scenario_validation.items():
        scenario_names = {
            "invalidity": "Invalidity Search",
            "infringement": "Infringement Monitoring",
            "patentability": "Patentability Review"
        }
        name = scenario_names.get(scenario, scenario)
        print(f"  {name}:")
        print(f"    Valid records: {stats['valid_records']} ({stats['validity_rate']}%)")
        print(f"    Invalid records: {stats['invalid_records']}")
        if stats['empty_fields']:
            top_empty = sorted(stats['empty_fields'].items(), key=lambda x: -x[1])[:3]
            print(f"    Top empty fields: {', '.join(f'{k}({v})' for k, v in top_empty)}")

    print(f"\n[Field Empty Value Statistics]")
    empty_stats = field_stats["empty_fields"]
    for field_name, count in sorted(empty_stats.items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count * 100 / summary['total_records_raw'] if summary['total_records_raw'] > 0 else 0
            print(f"  {field_name}: {count} records ({pct:.2f}%)")

    print("\n" + "=" * 70)


# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    """Command line entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Thinkstruct Patent Data Cleaning Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Basic usage
  python clean_patent_data.py /path/to/patent/data

  # Specify output directory
  python clean_patent_data.py /path/to/input -o /path/to/output

  # Use remove strategy (discard records with empty core fields)
  python clean_patent_data.py --strategy remove

  # Preserve paragraph structure
  python clean_patent_data.py --description-mode preserve

  # Output as CSV format
  python clean_patent_data.py --format csv

Scenario field requirements:
  Invalidity:    Required [doc_number, claims, abstract] + Important [title, classification]
  Infringement:  Required [doc_number, claims, classification] + Important [title, abstract]
  Patentability: Required [doc_number, title, abstract] + Important [claims, classification]
        """
    )

    # Default path: patent_data_small under script directory
    script_dir = Path(__file__).parent
    default_input = script_dir / "patent_data_small"

    parser.add_argument(
        "input_dir",
        nargs="?",
        default=str(default_input),
        help="Input folder path (default: data/patent_data_small)"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output folder path (default: cleaned_output at same level as input)"
    )

    parser.add_argument(
        "--strategy",
        choices=["fill", "remove"],
        default="fill",
        help="Missing value handling strategy (default: fill)"
    )

    parser.add_argument(
        "--description-mode",
        choices=["merge", "preserve"],
        default="merge",
        help="Detailed description field processing mode (default: merge)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output file format (default: json)"
    )

    args = parser.parse_args()

    # Update global configuration
    global MISSING_FIELD_STRATEGY, DESCRIPTION_MODE
    MISSING_FIELD_STRATEGY = args.strategy
    DESCRIPTION_MODE = args.description_mode

    # Update default values
    DEFAULT_VALUES["detailed_description"] = "" if DESCRIPTION_MODE == "merge" else []

    # Set output directory
    input_path = Path(args.input_dir)
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = input_path.parent / "cleaned_output"

    print(f"\nThinkstruct Patent Data Cleaning Pipeline")
    print(f"=" * 70)
    print(f"Input directory: {input_path}")
    print(f"Output directory: {output_dir}")
    print(f"Missing value strategy: {MISSING_FIELD_STRATEGY}")
    print(f"Description processing mode: {DESCRIPTION_MODE}")
    print(f"Output format: {args.format}")
    print(f"=" * 70 + "\n")

    # Execute cleaning
    cleaned_data, stats = clean_patent_data(input_path, output_dir)

    # Save results
    if cleaned_data:
        save_output(cleaned_data, stats, output_dir, args.format)
    else:
        logger.warning("No data to save")
        print_report_summary(generate_report(stats))

    return cleaned_data, stats


if __name__ == "__main__":
    main()
