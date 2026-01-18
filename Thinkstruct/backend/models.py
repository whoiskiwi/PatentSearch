"""
Pydantic Request/Response Models
"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Request Models - By Scenario
# ============================================================================

class InvaliditySearchRequest(BaseModel):
    """Invalidity search request"""
    query_claims: str = Field(..., min_length=1, description="Target patent claims")
    query_doc_number: str = Field(default="", description="Target patent number")
    classification: str = Field(default="", description="Classification code prefix")
    target_date: Optional[str] = Field(default=None, description="Target patent date YYYY-MM-DD")
    top_k: int = Field(default=20, ge=1, le=100, description="Number of results to return")


class InfringementSearchRequest(BaseModel):
    """Infringement monitoring request"""
    my_claims: str = Field(..., min_length=1, description="Your patent claims")
    my_doc_number: str = Field(..., min_length=1, description="Your patent number")
    classification: str = Field(default="", description="Classification code prefix")
    keywords: list[str] = Field(default=[], description="Key technical terms")
    date_from: Optional[str] = Field(default=None, description="Monitoring start date YYYY-MM-DD")
    date_to: Optional[str] = Field(default=None, description="Monitoring end date YYYY-MM-DD")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")
    top_k: int = Field(default=20, ge=1, le=100, description="Number of results to return")


class PatentabilitySearchRequest(BaseModel):
    """Patentability review request"""
    invention_description: str = Field(..., min_length=1, description="New invention description")
    draft_claims: str = Field(default="", description="Draft claims")
    classification: str = Field(default="", description="Estimated classification code")
    keywords: list[str] = Field(default=[], description="Core technical terms")
    top_k: int = Field(default=20, ge=1, le=100, description="Number of results to return")


# ============================================================================
# Response Models - By Scenario
# ============================================================================

class InvalidityResultItem(BaseModel):
    """Invalidity search result item"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    matched_claims: list[str]
    independent_claims: list[str]
    claims_count: int
    all_claims: list[str]
    detailed_description: str


class InfringementResultItem(BaseModel):
    """Infringement monitoring result item"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    risk_level: str
    matched_claims: list[str]
    overlapping_features: list[str]
    all_claims: list[str]
    detailed_description: str


class PatentabilityResultItem(BaseModel):
    """Patentability review result item"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    novelty_assessment: str
    closest_prior_art: bool
    key_differences: list[str]
    matched_claims: list[str]
    technical_field: str
    all_claims: list[str]
    detailed_description: str


class InvaliditySearchResponse(BaseModel):
    """Invalidity search response"""
    success: bool
    total: int
    results: list[InvalidityResultItem]
    scenario: str = "invalidity"


class InfringementSearchResponse(BaseModel):
    """Infringement monitoring response"""
    success: bool
    total: int
    results: list[InfringementResultItem]
    scenario: str = "infringement"


class PatentabilitySearchResponse(BaseModel):
    """Patentability review response"""
    success: bool
    total: int
    results: list[PatentabilityResultItem]
    scenario: str = "patentability"


class StatsResponse(BaseModel):
    """Statistics response"""
    total_patents: int
    date_range: dict
    classification_distribution: dict
