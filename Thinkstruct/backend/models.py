"""
Pydantic Request/Response Models

This module defines all the data models for API request validation
and response serialization using Pydantic.

Models are organized by scenario:
- Invalidity Search: Find prior art to invalidate patents
- Infringement Monitoring: Detect potential patent infringement
- Patentability Review: Assess patentability of inventions
- Patent ID Search: Search by patent document number
"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Request Models - By Scenario
# ============================================================================

class InvaliditySearchRequest(BaseModel):
    """
    Request model for invalidity search.

    Used to find prior art patents that may invalidate a target patent.
    The query_claims field is the main search text.

    Example:
        {
            "query_claims": "A tire with reinforced sidewall...",
            "classification": "B60C",
            "target_date": "2023-01-01",
            "top_k": 20
        }
    """
    query_claims: str = Field(
        ...,
        min_length=1,
        description="Target patent claims text to search for prior art"
    )
    query_doc_number: str = Field(
        default="",
        description="Target patent document number (for reference)"
    )
    classification: str = Field(
        default="",
        description="IPC/CPC classification code prefix filter (e.g., 'B60C')"
    )
    keywords: list[str] = Field(
        default=[],
        description="Required keywords that must appear in results"
    )
    title_search: str = Field(
        default="",
        description="Filter by title substring match"
    )
    target_date: Optional[str] = Field(
        default=None,
        description="Only return patents before this date (YYYY-MM-DD)"
    )
    top_k: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )


class InfringementSearchRequest(BaseModel):
    """
    Request model for infringement monitoring.

    Used to find patents that may infringe on your patent rights.
    Requires your patent claims and document number.

    Example:
        {
            "my_claims": "A wheel rim with integrated sensor...",
            "my_doc_number": "US12345678",
            "min_similarity": 0.5,
            "top_k": 20
        }
    """
    my_claims: str = Field(
        ...,
        min_length=1,
        description="Your patent claims to monitor for infringement"
    )
    my_doc_number: str = Field(
        ...,
        min_length=1,
        description="Your patent document number (excluded from results)"
    )
    classification: str = Field(
        default="",
        description="IPC/CPC classification code prefix filter"
    )
    keywords: list[str] = Field(
        default=[],
        description="Required keywords that must appear in results"
    )
    title_search: str = Field(
        default="",
        description="Filter by title substring match"
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Only return patents after this date (YYYY-MM-DD)"
    )
    date_to: Optional[str] = Field(
        default=None,
        description="Only return patents before this date (YYYY-MM-DD)"
    )
    min_similarity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0-1)"
    )
    top_k: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )


class PatentabilitySearchRequest(BaseModel):
    """
    Request model for patentability review.

    Used to assess if a new invention is patentable by finding similar prior art.
    Lower similarity in results indicates better patentability.

    Example:
        {
            "invention_description": "An innovative tire pressure monitoring...",
            "draft_claims": "A system comprising...",
            "classification": "B60C",
            "top_k": 20
        }
    """
    invention_description: str = Field(
        ...,
        min_length=1,
        description="Description of your new invention"
    )
    draft_claims: str = Field(
        default="",
        description="Optional draft claims for more precise search"
    )
    classification: str = Field(
        default="",
        description="Estimated IPC/CPC classification code"
    )
    keywords: list[str] = Field(
        default=[],
        description="Core technical terms to filter results"
    )
    title_search: str = Field(
        default="",
        description="Filter by title substring match"
    )
    top_k: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )


class PatentIdSearchRequest(BaseModel):
    """
    Request model for patent ID search.

    Used to find similar patents by providing a patent document number.
    The system looks up the patent and finds semantically similar patents.

    Example:
        {
            "doc_number": "US20240217263A1",
            "classification": "B60C",
            "top_k": 20
        }
    """
    doc_number: str = Field(
        ...,
        min_length=1,
        description="Patent document number to use as query"
    )
    classification: str = Field(
        default="",
        description="IPC/CPC classification code prefix filter"
    )
    top_k: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )


# ============================================================================
# Response Models - Result Items
# ============================================================================

class InvalidityResultItem(BaseModel):
    """
    Single result item for invalidity search.

    Contains patent information, similarity score, and matched claims
    that could be used to invalidate a target patent.
    """
    doc_number: str               # Patent document number
    title: str                    # Patent title
    abstract: str                 # Patent abstract
    classification: str           # IPC/CPC classification code
    publication_date: str         # Publication date (YYYY-MM-DD)
    similarity_score: float       # Semantic similarity (0-1)
    matched_claims: list[str]     # Claims matching the query
    independent_claims: list[str] # Independent claims only
    claims_count: int             # Total number of claims
    all_claims: list[str]         # All claims (up to 10)
    detailed_description: str     # Truncated description


class InfringementResultItem(BaseModel):
    """
    Single result item for infringement monitoring.

    Contains patent information, risk level assessment, and overlapping
    technical features that may indicate infringement.
    """
    doc_number: str                  # Patent document number
    title: str                       # Patent title
    abstract: str                    # Patent abstract
    classification: str              # IPC/CPC classification code
    publication_date: str            # Publication date (YYYY-MM-DD)
    similarity_score: float          # Semantic similarity (0-1)
    risk_level: str                  # Risk: Very High/High/Medium/Low
    matched_claims: list[str]        # Claims matching your patent
    overlapping_features: list[str]  # Technical features that overlap
    all_claims: list[str]            # All claims (up to 10)
    detailed_description: str        # Truncated description


class PatentabilityResultItem(BaseModel):
    """
    Single result item for patentability review.

    Contains patent information, novelty assessment, and key differences
    from prior art that could support patentability.
    """
    doc_number: str              # Patent document number
    title: str                   # Patent title
    abstract: str                # Patent abstract
    classification: str          # IPC/CPC classification code
    publication_date: str        # Publication date (YYYY-MM-DD)
    similarity_score: float      # Semantic similarity (0-1)
    novelty_assessment: str      # Assessment: Novel/Similar/Identical
    closest_prior_art: bool      # True if this is the closest match
    key_differences: list[str]   # Differences from prior art
    matched_claims: list[str]    # Related claims from prior art
    technical_field: str         # Technical field name
    all_claims: list[str]        # All claims (up to 10)
    detailed_description: str    # Truncated description


class PatentIdResultItem(BaseModel):
    """
    Single result item for patent ID search.

    Contains similar patent information found by searching
    using another patent as the query source.
    """
    doc_number: str           # Patent document number
    title: str                # Patent title
    abstract: str             # Patent abstract
    classification: str       # IPC/CPC classification code
    publication_date: str     # Publication date (YYYY-MM-DD)
    similarity_score: float   # Semantic similarity (0-1)
    matched_claims: list[str] # Claims matching the source patent
    all_claims: list[str]     # All claims (up to 10)
    detailed_description: str # Truncated description


# ============================================================================
# Response Models - Full Responses
# ============================================================================

class InvaliditySearchResponse(BaseModel):
    """
    Full response for invalidity search.

    Contains success status, result count, search results,
    and performance metrics.
    """
    success: bool                        # Whether search succeeded
    total: int                           # Number of results returned
    results: list[InvalidityResultItem]  # List of matching patents
    scenario: str = "invalidity"         # Search scenario identifier
    search_time_ms: float = Field(
        default=0,
        description="Search execution time in milliseconds"
    )


class InfringementSearchResponse(BaseModel):
    """
    Full response for infringement monitoring.

    Contains success status, result count, search results
    with risk assessments, and performance metrics.
    """
    success: bool                          # Whether search succeeded
    total: int                             # Number of results returned
    results: list[InfringementResultItem]  # List of potentially infringing patents
    scenario: str = "infringement"         # Search scenario identifier
    search_time_ms: float = Field(
        default=0,
        description="Search execution time in milliseconds"
    )


class PatentabilitySearchResponse(BaseModel):
    """
    Full response for patentability review.

    Contains success status, result count, prior art results
    with novelty assessments, and performance metrics.
    """
    success: bool                           # Whether search succeeded
    total: int                              # Number of results returned
    results: list[PatentabilityResultItem]  # List of prior art patents
    scenario: str = "patentability"         # Search scenario identifier
    search_time_ms: float = Field(
        default=0,
        description="Search execution time in milliseconds"
    )


class SourcePatentInfo(BaseModel):
    """
    Information about the source patent in patent ID search.

    Contains the patent details that was used as the search query.
    """
    doc_number: str       # Patent document number
    title: str            # Patent title
    abstract: str         # Patent abstract
    classification: str   # IPC/CPC classification code
    publication_date: str # Publication date
    claims: list[str]     # Patent claims


class PatentIdSearchResponse(BaseModel):
    """
    Full response for patent ID search.

    Contains the source patent information, similar patents found,
    and performance metrics.
    """
    success: bool                                # Whether search succeeded
    source_patent: Optional[SourcePatentInfo] = None  # Source patent info
    total: int                                   # Number of results returned
    results: list[PatentIdResultItem]            # List of similar patents
    scenario: str = "patent_id"                  # Search scenario identifier
    search_time_ms: float = Field(
        default=0,
        description="Search execution time in milliseconds"
    )


# ============================================================================
# Other Response Models
# ============================================================================

class StatsResponse(BaseModel):
    """
    Response for patent statistics endpoint.

    Contains aggregate statistics about the patent database.
    """
    total_patents: int              # Total number of patents in database
    date_range: dict                # Min/max publication dates
    classification_distribution: dict  # Count by classification code
