"""
Thinkstruct Patent Hybrid Search Engine

Supports three search scenarios:
1. Invalidity Search - Find prior art earlier than the target patent
2. Infringement Monitoring - Monitor new patents for potential infringement
3. Patentability Review - Evaluate patentability of new inventions

Uses PatentSBERTa_V2 patent-specific model for semantic search
https://huggingface.co/AAUBS/PatentSBERTa_V2
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes - By Scenario
# ============================================================================

@dataclass
class InvalidityResult:
    """Invalidity search result"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    matched_claims: list[str] = field(default_factory=list)
    independent_claims: list[str] = field(default_factory=list)
    claims_count: int = 0
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class InfringementResult:
    """Infringement monitoring result"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    risk_level: str = ""
    matched_claims: list[str] = field(default_factory=list)
    overlapping_features: list[str] = field(default_factory=list)
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class PatentabilityResult:
    """Patentability review result"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    novelty_assessment: str = ""
    closest_prior_art: bool = False
    key_differences: list[str] = field(default_factory=list)
    matched_claims: list[str] = field(default_factory=list)
    technical_field: str = ""
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class PatentIdSearchResult:
    """Patent ID search result"""
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    matched_claims: list[str] = field(default_factory=list)
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


# ============================================================================
# Search Engine Core Class
# ============================================================================

class PatentSearchEngine:
    """Patent Hybrid Search Engine"""

    CLASSIFICATION_FIELDS = {
        'A': 'Human Necessities',
        'B': 'Performing Operations; Transporting',
        'C': 'Chemistry; Metallurgy',
        'D': 'Textiles; Paper',
        'E': 'Fixed Constructions',
        'F': 'Mechanical Engineering',
        'G': 'Physics',
        'H': 'Electricity',
    }

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.patents: list[dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.model = None
        self._load_data()

    def _load_data(self) -> None:
        """Load patent data"""
        logger.info(f"Loading patent data: {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.patents = json.load(f)
        logger.info(f"Load complete: {len(self.patents)} patent records")
        # Build doc_number index for fast lookup
        self._doc_index = {p["doc_number"]: i for i, p in enumerate(self.patents)}

    def get_patent_by_id(self, doc_number: str) -> Optional[dict]:
        """Get patent by document number"""
        # Normalize doc_number (remove prefix like US, spaces, etc.)
        normalized = doc_number.strip().upper().replace("US", "").replace("-", "").replace(" ", "")

        # Try exact match first
        if doc_number in self._doc_index:
            return self.patents[self._doc_index[doc_number]]

        # Try normalized match
        for patent in self.patents:
            patent_num = patent["doc_number"].upper().replace("US", "").replace("-", "").replace(" ", "")
            if patent_num == normalized or patent["doc_number"] == doc_number:
                return patent

        return None

    def _load_model(self) -> None:
        """Lazy load semantic search model"""
        if self.model is None:
            logger.info("Loading semantic search model PatentSBERTa_V2...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('AAUBS/PatentSBERTa_V2')
            logger.info("Model loaded successfully")

    def _build_embeddings(self) -> None:
        """Build vector representations of patent texts"""
        if self.embeddings is not None:
            return

        self._load_model()
        logger.info("Building patent vector index...")

        texts = []
        for patent in self.patents:
            claims_text = " ".join(patent.get("claims", [])[:3])
            combined = f"{patent['title']} {patent['abstract']} {claims_text}"
            texts.append(combined)

        self.embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        logger.info(f"Index built: {self.embeddings.shape}")

    def _compute_similarity(self, query: str, top_k: int = 100) -> list[tuple[int, float]]:
        """Compute semantic similarity between query and all patents"""
        self._build_embeddings()

        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    def _extract_independent_claims(self, claims: list[str]) -> list[str]:
        """Extract independent claims"""
        independent = []
        for i, claim in enumerate(claims):
            if not re.search(r'claim\s+\d+|claims\s+\d+', claim.lower()):
                independent.append(claim)
            elif i == 0:
                independent.append(claim)
        return independent[:3]

    def _find_matched_claims(self, query: str, claims: list[str], threshold: float = 0.5) -> list[str]:
        """Find claims matching the query"""
        if not claims or self.model is None:
            return []

        self._load_model()

        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        claims_embeddings = self.model.encode(claims, convert_to_numpy=True)

        matched = []
        for i, claim_emb in enumerate(claims_embeddings):
            sim = np.dot(query_embedding, claim_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(claim_emb)
            )
            if sim >= threshold:
                matched.append(claims[i])

        return matched[:5]

    def _extract_technical_features(self, text: str) -> list[str]:
        """Extract technical features from text"""
        features = []
        patterns = [
            r'comprising\s+([^,;.]+)',
            r'including\s+([^,;.]+)',
            r'having\s+([^,;.]+)',
            r'configured to\s+([^,;.]+)',
            r'adapted to\s+([^,;.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                feature = match.strip()
                if 10 < len(feature) < 100:
                    features.append(feature)

        return list(set(features))[:10]

    def _find_overlapping_features(self, query_features: list[str], patent: dict) -> list[str]:
        """Find overlapping technical features"""
        patent_text = f"{patent['title']} {patent['abstract']} {' '.join(patent.get('claims', []))}"
        patent_text_lower = patent_text.lower()

        overlapping = []
        for feature in query_features:
            keywords = [w for w in feature.split() if len(w) > 3]
            if keywords:
                match_count = sum(1 for kw in keywords if kw in patent_text_lower)
                if match_count >= len(keywords) * 0.5:
                    overlapping.append(feature)

        return overlapping

    def _calculate_risk_level(self, similarity: float) -> str:
        """Calculate infringement risk level"""
        if similarity > 0.9:
            return "Very High"
        elif similarity >= 0.7:
            return "High"
        elif similarity >= 0.5:
            return "Medium"
        return "Low"

    def _assess_novelty(self, similarity: float) -> str:
        """Assess novelty"""
        if similarity > 0.85:
            return "Identical"
        elif similarity >= 0.6:
            return "Similar"
        return "Novel"

    def _identify_key_differences(self, query: str, patent: dict) -> list[str]:
        """Identify key differences from prior art"""
        query_features = set(self._extract_technical_features(query))
        patent_features = set(self._extract_technical_features(
            f"{patent['abstract']} {' '.join(patent.get('claims', [])[:3])}"
        ))

        unique_features = query_features - patent_features
        return [f"Novel feature: {f}" for f in list(unique_features)[:5]]

    def _get_technical_field(self, classification: str) -> str:
        """Get technical field from classification code"""
        if classification:
            first_char = classification[0].upper()
            return self.CLASSIFICATION_FIELDS.get(first_char, "Unknown")
        return "Unknown"

    def _filter_by_classification(self, candidates: list[tuple[int, float]], prefix: str) -> list[tuple[int, float]]:
        """Filter by classification code prefix"""
        if not prefix:
            return candidates
        prefix_upper = prefix.upper()
        return [
            (idx, score) for idx, score in candidates
            if self.patents[idx].get("classification", "").upper().startswith(prefix_upper)
        ]

    def _filter_by_date(self, candidates: list[tuple[int, float]],
                        date_from: Optional[str], date_to: Optional[str]) -> list[tuple[int, float]]:
        """Filter by date range"""
        if not date_from and not date_to:
            return candidates

        filtered = []
        for idx, score in candidates:
            pub_date = self.patents[idx].get("publication_date", "")
            if not pub_date:
                continue
            if date_from and pub_date < date_from:
                continue
            if date_to and pub_date > date_to:
                continue
            filtered.append((idx, score))

        return filtered

    def _filter_by_keywords(self, candidates: list[tuple[int, float]], keywords: list[str]) -> list[tuple[int, float]]:
        """Filter by keywords in title, abstract, or claims"""
        if not keywords:
            return candidates

        filtered = []
        for idx, score in candidates:
            patent = self.patents[idx]
            # Combine searchable text fields
            searchable_text = (
                patent.get("title", "") + " " +
                patent.get("abstract", "") + " " +
                " ".join(patent.get("claims", []))
            ).lower()

            # Check if all keywords are present (AND logic)
            if all(kw.lower() in searchable_text for kw in keywords):
                filtered.append((idx, score))

        return filtered

    def _filter_by_title(self, candidates: list[tuple[int, float]], title_query: str) -> list[tuple[int, float]]:
        """Filter by title (case-insensitive substring match)"""
        if not title_query:
            return candidates

        title_query_lower = title_query.lower().strip()
        return [
            (idx, score) for idx, score in candidates
            if title_query_lower in self.patents[idx].get("title", "").lower()
        ]

    # ========================================================================
    # Scenario-based Search APIs
    # ========================================================================

    def invalidity_search(
        self,
        query_claims: str,
        query_doc_number: str = "",
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        target_date: Optional[str] = None,
        top_k: int = 20
    ) -> list[InvalidityResult]:
        """Invalidity search: Find prior art earlier than target patent"""
        logger.info(f"Executing invalidity search: query_length={len(query_claims)}")

        candidates = self._compute_similarity(query_claims, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)

        if target_date:
            candidates = self._filter_by_date(candidates, None, target_date)

        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = InvalidityResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                matched_claims=self._find_matched_claims(query_claims, claims),
                independent_claims=self._extract_independent_claims(claims),
                claims_count=len(claims),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Invalidity search complete: {len(results)} results returned")
        return results

    def infringement_search(
        self,
        my_claims: str,
        my_doc_number: str,
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_similarity: float = 0.5,
        top_k: int = 20
    ) -> list[InfringementResult]:
        """Infringement monitoring: Monitor new patents for potential infringement"""
        logger.info(f"Executing infringement monitoring: my_doc_number={my_doc_number}")

        my_features = self._extract_technical_features(my_claims)
        candidates = self._compute_similarity(my_claims, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_date(candidates, date_from, date_to)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)
        candidates = [(idx, score) for idx, score in candidates if score >= min_similarity]

        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]

            if patent["doc_number"] == my_doc_number:
                continue

            claims = patent.get("claims", [])
            overlapping = self._find_overlapping_features(my_features, patent)

            result = InfringementResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                risk_level=self._calculate_risk_level(score),
                matched_claims=self._find_matched_claims(my_claims, claims),
                overlapping_features=overlapping,
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Infringement monitoring complete: {len(results)} results returned")
        return results

    def patentability_search(
        self,
        invention_description: str,
        draft_claims: str = "",
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        top_k: int = 20
    ) -> list[PatentabilityResult]:
        """Patentability review: Evaluate patentability of new invention"""
        logger.info(f"Executing patentability review: desc_length={len(invention_description)}")

        query = invention_description
        if draft_claims:
            query = f"{invention_description} {draft_claims}"

        candidates = self._compute_similarity(query, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)

        results = []
        for i, (idx, score) in enumerate(candidates[:top_k]):
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = PatentabilityResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                novelty_assessment=self._assess_novelty(score),
                closest_prior_art=(i == 0),
                key_differences=self._identify_key_differences(query, patent),
                matched_claims=self._find_matched_claims(query, claims),
                technical_field=self._get_technical_field(patent["classification"]),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Patentability review complete: {len(results)} results returned")
        return results

    def search_by_patent_id(
        self,
        doc_number: str,
        classification: str = "",
        top_k: int = 20
    ) -> tuple[Optional[dict], list[PatentIdSearchResult]]:
        """Search similar patents using a patent ID as input

        Returns:
            tuple: (source_patent, similar_patents)
            - source_patent: The patent matching the doc_number, or None if not found
            - similar_patents: List of similar patents found
        """
        logger.info(f"Executing patent ID search: doc_number={doc_number}")

        # Find the source patent
        source_patent = self.get_patent_by_id(doc_number)
        if source_patent is None:
            logger.warning(f"Patent not found: {doc_number}")
            return None, []

        # Build query from source patent's claims and abstract
        claims_text = " ".join(source_patent.get("claims", [])[:5])
        query = f"{source_patent['abstract']} {claims_text}"

        # Search for similar patents
        candidates = self._compute_similarity(query, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)

        # Exclude the source patent itself
        source_idx = self._doc_index.get(source_patent["doc_number"])
        candidates = [(idx, score) for idx, score in candidates if idx != source_idx]

        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = PatentIdSearchResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                matched_claims=self._find_matched_claims(query, claims),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Patent ID search complete: {len(results)} results returned")
        return source_patent, results


# ============================================================================
# Utility Functions
# ============================================================================

def get_latest_data_file(output_dir: str | Path) -> Path:
    """Get the latest cleaned data file"""
    output_path = Path(output_dir)
    files = sorted(output_path.glob("patents_cleaned_*.json"))
    if not files:
        raise FileNotFoundError(f"Cleaned data file not found: {output_path}")
    return files[-1]
